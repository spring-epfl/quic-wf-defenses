#!/usr/bin/python3

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import sys
import os
from browsermobproxy import Server
import psutil
import time
import json
import subprocess
import signal
import sys
from os import path
import random
import shutil
import re
import ntpath
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

PROFILE_QUIC = './prefs_quic.js'
PROFILE_URL = "./profile"
H3_PATTERN = re.compile("h3-[TQ0-9]+=|quic=", re.IGNORECASE)


# old version (parsing was done outside of the browser, but that was buggy)
script = """HAR.triggerExport().then(harLog => {
            for(i in harLog['entries']) { try{ delete harLog['entries'][i]['response']['content'] } catch {} };
            document.documentElement.innerHTML = '<div id="lb_json">' + JSON.stringify(harLog) + '<div id="lb_end"></div></div>';
    });"""

# parses a Har log from within the browser using JS
# exports a list of resources, format: [url, host, alt-svc, [request header size, body size], [response header size, body size]]
script = """
function headerCompress(headers) { res={}; for(i in headers){ res[headers[i]['name'].toLowerCase().trim()] = headers[i]['value'].toLowerCase().trim()}; return res }
function compress(entry) { request_headers = headerCompress(entry['request']['headers']); response_headers = headerCompress(entry['response']['headers']); return [entry['request']['url'], request_headers['host'], response_headers['alt-svc'], [entry['request']['headersSize'], entry['request']['bodySize']], [entry['response']['headersSize'], entry['response']['bodySize']], entry['response']['status']] }
HAR.triggerExport().then(harLog => {
            for(i in harLog['entries']) { try{ delete harLog['entries'][i]['response']['content'] } catch {} };
            out = []; for(i in harLog['entries']) { out.push(compress(harLog['entries'][i])) };
            document.documentElement.innerHTML = '<div id="lb_json">' + JSON.stringify(out) + '<div id="lb_end"></div></div>';
    });
"""


 
if len(sys.argv) != 3:
    print("Usage: script.py URL_LIST OUTPUT_FOLDER")
    sys.exit(1)

url_list = sys.argv[1].strip()
output_folder = sys.argv[2].strip()

if not output_folder.endswith('/'):
    output_folder += '/'


options = FirefoxOptions()
options.headless = True
options.add_argument("-devtools")

# nuke and recreate profile
shutil.rmtree(PROFILE_URL, ignore_errors=True)
os.makedirs(PROFILE_URL)
shutil.copyfile(PROFILE_QUIC, PROFILE_URL+"/prefs.js")

profile = webdriver.FirefoxProfile(PROFILE_URL)
profile.set_preference("http.response.timeout", 5)
profile.set_preference("dom.max_script_run_time", 5)
profile.add_extension("bin/har_export_trigger-0.6.1-an+fx.xpi")
driver = webdriver.Firefox(firefox_profile=profile, options=options)
driver.set_page_load_timeout(15)
driver.implicitly_wait(15)

def touch(file_name, times=None):
    if os.path.exists(file_name):
        os.utime(file_name, None)
    else:
        open(file_name, 'a').close()

n_consecutive_errors = 0

def fetch_url(i, url):
    output_file = output_folder+url
    har_path = output_file+".har"

    if path.isfile(har_path):
        print(f"[{i}] Skipping", url, ", already collected")
        return

    print(f"[{i}] Fetching", url, "saving in", har_path)

    if not url.startswith('https://'):
        url = "https://"+url

    try:
        driver.get(url)

        if "Access denied" in driver.title and "You are being rate limited" in driver.page_source:
            print("ALERT: RATE-LIMITING")
            time.sleep(60)
            sys.exit(1)

    except Exception as e:
        print("Couldn't fetch", url, ".", e)
        touch(har_path)
        return

    try:
        driver.execute_script(script)

    except Exception as e:
        print("Script exception", url, ".", e)
        touch(har_path)
        return

    time.sleep(1)
    har_simplified = ""
    txt = ""

    delay = 3
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'lb_json')))

        # cut the stringified JSON
        txt =  driver.page_source 
        txt = txt[txt.find('<div id="lb_json">'):]
        txt = txt[:txt.find('<div id="lb_end">')]
        txt = txt.replace('<div id="lb_json">', '').replace('<div id="lb_end">', '')


        # parse and filter
        json_har = json.loads(txt)
        # write HAR
        with open(har_path, 'w') as har_file:
            json.dump(json_har, har_file)

        print("Written", har_path, "(", os.path.getsize(har_path), "bytes)")
        n_consecutive_errors = 0
        
    except TimeoutException:
        print("Timeout", url)
    except Exception as e:
        n_consecutive_errors += 1
        
        print("Other error", e, url)

        print(txt)
        sys.exit(0)

        with open(har_path+".log", 'w') as har_file:
            json.dump(txt, har_file)

    touch(har_path)


with open(url_list) as f:
    for i, line in enumerate(f):
        url = line.strip()
        fetch_url(i, url)

        if n_consecutive_errors > 100:
            break
driver.quit()