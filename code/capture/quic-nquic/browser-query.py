import logging
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time
from typing import List

import psutil
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium import webdriver
import traceback

PATH_GECKO_DRIVER = Path.home() / "geckodriver"
PATH_CHROME_DRIVER = Path.home() / "chromedriver"


def stop_dumpcap() -> None:
    for proc in psutil.process_iter():
        if proc.name() == "dumpcap":
            proc.kill()


def start_dumpcap(interface: str, pcap_output: str) -> None:
    stop_dumpcap()
    bin_path = shutil.which('dumpcap')
    bin_path = '/usr/bin/dumpcap' # quick fix
    subprocess.Popen(
        [bin_path, "-i", interface, "-w", pcap_output]
    )
    time.sleep(2)


def add_protocol(url: str) -> str:
    url = url.strip()
    if not url.startswith('https://'):
        url = "https://" + url
    return url


def prepare_environment(profile_url: str, use_default_settings: bool, use_quic: bool) -> None:
    """Prepare the system environment for the experiment."""
    # nuke and recreate profile
    if use_quic:
        if use_default_settings:
            profile = "prefs_default_quic.js"
        else:
            profile = "prefs_quic.js"
    else:
        if use_default_settings:
            profile = "prefs_default_non_quic.js"
        else:
            profile = "prefs_non_quic.js"

    shutil.rmtree(profile_url, ignore_errors=True)
    os.makedirs(profile_url)
    shutil.copyfile(profile, profile_url + "/prefs.js")


def build_firefox_driver(use_default_settings: bool, use_quic: bool) -> webdriver.Firefox:
    """Build a Selenium driver for Firefox."""
    if use_quic:
        profile_url = "./profiles/firefox-quic"
    else:
        profile_url = "./profiles/firefox-non-quic"

    prepare_environment(profile_url, use_default_settings, use_quic)

    options = FirefoxOptions()
    options.headless = True
    options.add_argument("-devtools")
    profile = webdriver.FirefoxProfile(profile_url)

    service = FirefoxService(PATH_GECKO_DRIVER)
    driver = webdriver.Firefox(service=service, firefox_profile=profile, options=options)
    return driver


def build_chrome_driver(use_default_settings: bool, use_quic: bool) -> webdriver.Chrome:
    """Build a Selenium driver for Chrome."""

    # List of available options:
    # https://peter.sh/experiments/chromium-command-line-switches/
    # https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md
    # https://source.chromium.org/search?q=file:switches.cc&ss=chromium%2Fchromium%2Fsrc
    # https://chromium.googlesource.com/chromium/src/+/master/chrome/common/chrome_switches.cc
    # https://chromium.googlesource.com/chromium/src/+/master/headless/app/headless_shell_switches.cc
    # https://chromium.googlesource.com/chromium/src/+/master/chrome/common/pref_names.cc
    options = [
        "--headless",
        "--disable-application-cache",
        "--disable-component-update",
        "--disable-crash-reporter",
        "--disable-domain-reliability",
        "--disable-extensions",
        "--disable-infobars",
        "--disable-gpu",
        "--no-default-browser-check",
        "--no-first-run",
    ]

    if not use_default_settings:
        options += [
            "--disable-background-networking",
            "--disable-client-side-phishing-detection",
            "--disable-default-apps",
            "--disable-features=Translate",
            "--disable-sync",
            "--no-service-autorun",
        ]

    chrome_options = ChromeOptions()

    for option in options:
        chrome_options.add_argument(option)

    if not use_quic:
        chrome_options.add_argument("--disable-quic")

    service = ChromeService(PATH_CHROME_DRIVER)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def main(argv: List[str]) -> None:
    """Entrypoint of the program."""

    if len(argv) != 4:
        print("Usage: script.py INTERFACE PROFILE={firefox-quic-default,firefox-quic-tweaked,chromium-quic-default,chromium-quic-tweaked} URL")
        sys.exit(1)

    iface = argv[1].strip()
    arg_profile = argv[2].strip().lower()
    url = add_protocol(argv[3])

    os.environ["SSLKEYLOGFILE"] = "sslkeys.txt"

    # Toggle between QUIC and non-QUIC
    if arg_profile == "firefox-quic-default":
        driver = build_firefox_driver(True, True)
    elif arg_profile == "firefox-quic-tweaked":
        driver = build_firefox_driver(False, True)
    elif arg_profile == "chrome-quic-default":
        driver = build_chrome_driver(True, True)
    elif arg_profile == "chrome-quic-tweaked":
        driver = build_chrome_driver(False, True)
    else:
        raise ValueError("Invalid PROFILE argument '{arg_profile}'")

    # Capture loop
    logging.info(f"Fetching {url} on interface {iface} using profile {arg_profile}")

    logging.info("Browser started, starting dumpcap...")

    start_dumpcap(iface, "capture.pcap")

    logging.info("Dumpcap started, fetching URL")

    try:
        driver.get(url)

        logging.info(f"Capture done! {driver.title}")

        if "Attention Required!" in driver.title and "Cloudflare" in driver.title:
            logging.error("ALERT: Cloudflare Captcha")
            driver.quit()
            sys.exit(2)

        if "Access denied" in driver.title and "You are being rate limited" in driver.page_source:
            logging.error("ALERT: RATE-LIMITING")
            driver.quit()
            sys.exit(3)

    except Exception as error:
        traceback.print_exc()
        logging.exception(error)
        sys.exit(4)

    logging.info("Done, quitting")
    driver.quit()


if __name__ == "__main__":
    main(sys.argv)
