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

PROFILE_QUIC = '../quic-nquic-capture/prefs_quic.js'
PROFILE_URL = "./profile"
 
if len(sys.argv) != 3:
    print("Usage: script.py url OUTPUT_FOLDER")
    sys.exit(1)

url = sys.argv[1].strip()
output_folder = sys.argv[2].strip()

if not output_folder.endswith('/'):
    output_folder += '/'

output_file = output_folder+url
har_path = output_file+".har"

if path.isfile(har_path):
    print("Skipping", url, ", already collected")
    sys.exit(0)

print("Fetching", url, "saving in", har_path)

# Start Browsermob Proxy + Firefox
print("Starting up proxy...")
server = Server("./bin/browsermob-proxy")
server.start()
proxy = server.create_proxy()

options = FirefoxOptions()
options.headless = True
options.add_argument("-devtools")


# nuke and recreate profile
shutil.rmtree(PROFILE_URL, ignore_errors=True)
os.makedirs(PROFILE_URL)
shutil.copyfile(PROFILE_QUIC, PROFILE_URL+"/prefs.js")


profile = webdriver.FirefoxProfile(PROFILE_URL)
profile.set_proxy(proxy.selenium_proxy())
driver = webdriver.Firefox(firefox_profile=profile, options=options)
driver.set_page_load_timeout(15)
driver.implicitly_wait(15)


def fetch_url(url, har_path):
    if not url.startswith('https://'):
        url = "https://"+url

    # query
    proxy.new_har('myhar', options={'captureHeaders': True})

    try:
        driver.get(url)

        if "Access denied" in driver.title and "You are being rate limited" in driver.page_source:
            print("ALERT: RATE-LIMITING")
            time.sleep(60)
            sys.exit(1)

    except Exception as e:
        print("Couldn't fetch", url, ".", e)
        return

    # write HAR
    with open(har_path, 'w') as har_file:
        json.dump(proxy.har, har_file)


fetch_url(url, har_path)

print("Stopping proxy...")
server.stop()
driver.quit()
