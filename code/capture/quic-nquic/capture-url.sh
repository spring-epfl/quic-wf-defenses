#!/usr/bin/sh

rmfiles() {
    rm -rf *.log sslkeys.txt *.pcap profiles
}

stop_processes() {
    pkill geckodriver
    pkill chromedriver
    pkill browsermob-proxy
    pkill dumpcap
    pkill tshark
    pkill firefox
    pkill chrome
}

cleanup() {
    stop_processes
    rmfiles
    echo "Interrupted"
    exit 1
}

trap "cleanup" INT TERM

timedout() {
    # in case of timeout, save what we have

    stop_processes #first, stop dumpcap

    cp *.log "${OUTPUT_PATH}/${QUIC}/"
    cp *.pcap "${OUTPUT_PATH}/${QUIC}/"
    cp sslkeys.txt "${OUTPUT_PATH}/${QUIC}/sslkeys.txt"

    rmfiles
    t=$(date +%T)
    echo "[${t}] Timed out gracefully"
    exit 124
}

trap "timedout" HUP

capture_loop() {
    iface="$1"
    url="$2"
    profile="$3" # string firefox-quic-default,firefox-quic-tweaked,chromium-quic-default,chromium-quic-tweaked
    output="$4"

    stop_processes
    rmfiles
    mkdir -p "${output}/${profile}/"

    t=$(date +%T)
    echo "[${t}] Performing query to ${url}, capturing on ${iface}. First timeout in 30s, hard-timeout in 40s."
    timeout -k 10 60 python3 -u browser-query.py "${iface}" "${profile}" "${url}" > "${output}/${profile}/python_log.txt" 2>&1

    exitcode=$?

    t=$(date +%T)
    echo "[${t}] Done, exit code = ${exitcode}, saved in ${output}/${profile}}"
    stop_processes

    cp *.log "${output}/${profile}/"
    cp *.pcap "${output}/${profile}/"
    cp sslkeys.txt "${output}/${profile}/sslkeys.txt"

    rmfiles

    if [ "${exitcode}" != 0 ]; then
        t=$(date +%T)
        echo "[${t}] Exit code non zero, quitting prematurely"
        exit "${exitcode}"
    fi

    return "${exitcode}"
}

if [ "$#" -ne 4 ]; then
    echo "Usage: ./capture-url.sh INTERFACE URL PROFILE OUTPUT_FOLDER"
    exit 1
fi

CAPTURE_INTERFACE="$1"
URL="$2"  # without protocol nor trailing slash, e.g., blog.cloudflare.com
PROFILE="$3"
OUTPUT_PATH="$4" #e.g. dataset/URL_LIKE

capture_loop "${CAPTURE_INTERFACE}" "${URL}" "${PROFILE}" "${OUTPUT_PATH}"
