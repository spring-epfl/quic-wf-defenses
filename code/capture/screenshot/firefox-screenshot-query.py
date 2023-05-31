#!/usr/bin/python3

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import sys
import os
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
    print("Usage: script.py url output_file")
    sys.exit(1)

url = sys.argv[1].strip()
screenshot_path = sys.argv[2].strip()

print("Fetching", url, "saving screenshot in", screenshot_path)

# nuke and recreate profile
shutil.rmtree(PROFILE_URL, ignore_errors=True)
os.makedirs(PROFILE_URL)
shutil.copyfile(PROFILE_QUIC, PROFILE_URL+"/prefs.js")

options = FirefoxOptions()
options.headless = True
options.add_argument("-devtools")
options.add_argument("--width=1024")
options.add_argument("--height=1024")
profile = webdriver.FirefoxProfile(PROFILE_URL)
driver = webdriver.Firefox(firefox_profile=profile, options=options)

driver.set_page_load_timeout(45)
driver.implicitly_wait(45)


def fetch_url(url, screenshot_path):
    if not url.startswith('https://'):
        url = "https://"+url

    # query
    try:
        driver.get(url)

        if "Access denied" in driver.title and "You are being rate limited" in driver.page_source:
            print("ALERT: RATE-LIMITING")
            time.sleep(60)
            sys.exit(1)

    except Exception as e:
        print("Couldn't fetch", url, ".", e)
        return

    driver.save_screenshot(screenshot_path)


fetch_url(url, screenshot_path)

print("Stopping proxy...")
driver.quit()
