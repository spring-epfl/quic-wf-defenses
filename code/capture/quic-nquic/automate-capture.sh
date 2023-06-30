#!/bin/bash

cleanup() {
    pkill geckodriver
    pkill chromedriver
    pkill browsermob-proxy
    pkill dumpcap
    pkill tshark
    pkill firefox
    pkill chrome
    echo "Interrupted"
    exit 1
}
trap "cleanup" HUP INT TERM

CAPTURE_INTERFACE=veth1
OUTPUT_FOLDER=dataset

# Choose 1 capture profiles

# Firefox with quic enabled and default options (cache and updates disabled)
#PROFILE="firefox-quic-default"

# Firefox with quic enabled and tweaked options to disable telemetry and other sources of network traffic
PROFILE="firefox-quic-tweaked"

# Chrome with quic enabled and default options (cache and updates disabled)
#PROFILE="chrome-quic-default"

# Chrome with quic enabled and tweaked options to disable telemetry and other sources of network traffic
# Warning: still need extra tweaks...
#PROFILE="chrome-quic-tweaked"


# mod "modulo" that skips some entries
mod=-1
inc=-1
if [ $# == 2 ]; then
    mod=$1
    inc=$2
    while true; do
        read -p "Modulo mode, mod=${mod}, inc=${inc}. Continue ? [yn] " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

# test if in screen
if [ "$STY" == "" ]; then
    while true; do
        read -p "You are not in \"screen\". note: this detection sometimes fails, try with screen -ls. Continue ? [yn] " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

# Ensure we're in the correct netns
if ! sudo ip link | grep "${CAPTURE_INTERFACE}"; then
    echo "Cannot find interface ${CAPTURE_INTERFACE}, are you in the correct network namespace?";
    exit 1
fi
if [ "$(whoami)" == "root" ]; then
    echo "Script must be run as user, don't forget to 'su USERNAME' after entering the virtual network env"
    exit 1
fi

# Careful, merging ${OUTPUT_FOLDER} could be good or bad, better double check
if [ -d ${OUTPUT_FOLDER} ]; then
    while true; do
        read -p "Careful: Output folder \"${OUTPUT_FOLDER}\" already exists. Contents will be merged, pre-existing data will be skipped. Impartial captures will be overwritten. Continue ? [yn] " yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

mkdir -p "${OUTPUT_FOLDER}"
chmod ugo+rwx "${OUTPUT_FOLDER}" #tshark sometimes chokes on this

realname=urls
if [ `readlink urls` != "" ]; then
    realname=`readlink urls`
fi

count=-1
while read url;
do
    ((count=count+1))
    # if mode "modulo" is enabled, skip non-matching entries
    if [ ${mod} != -1 ] && [ $(expr $count % $mod) != "$inc" ]; then
        continue
    fi

    # note: this is important after all, even with a mounted drive on AWS
    echo
    rm -rf /tmp/Temp* /tmp/rust* >/dev/null 2>&1 # clean space on my VPS, nothing else is running anyway
    df -h / # print remaining space
    echo

    for i in {1..45}
    do
        filename="${count}"
        #filename=$(echo "${url}" | sed 's/https:\/\///g' | sed 's/\///g')

        pcap="${OUTPUT_FOLDER}/${filename}/${i}/${PROFILE}/capture.pcap"

        if [ -f "${pcap}" ] && [ -s "${pcap}" ]; then
            t=$(date +%T)
            echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Crawling ${url}, ${i}, skipped, pcap exists."
        else
            rm -rf "${OUTPUT_FOLDER}/${filename}/${i}/"
            mkdir -p "${OUTPUT_FOLDER}/${filename}/${i}/"

            t=$(date +%T)
            echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Crawling ${url}, ${i}, output in ${OUTPUT_FOLDER}/${filename}/${i}."

            # crawl; wait 70 sec, afterwards send HUP, and send KILL after 10 additional seconds still if not done
            timeout -s HUP -k 80 70 ./capture-url.sh "${CAPTURE_INTERFACE}" "${url}" "${PROFILE}" "${OUTPUT_FOLDER}/${filename}/${i}" > "${OUTPUT_FOLDER}/${filename}/${i}/automation_log.txt" 2>&1

            exitcode="$?"

            t=$(date +%T)
            if [ "${exitcode}" == 124 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Timed out, consider increasing timeout value. Continuing..."
            elif [ "${exitcode}" == 1 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Something very wrong happened. Quitting."
                exit 1
            elif [ "${exitcode}" == 2 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Website behind CAPTCHA, skipping website..." | tee "${OUTPUT_FOLDER}/${filename}/warning"
                break
            elif [ "${exitcode}" == 3 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] We are being rate-limited by Cloudflare, skipping website..." | tee "${OUTPUT_FOLDER}/${filename}/warning"
                break
            elif [ "${exitcode}" == 4 ] ||  [ "${exitcode}" == 5 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Website throwed an exception (perhaps 404?), skipping website..." | tee "${OUTPUT_FOLDER}/${filename}/warning"
                break
            elif [ "${exitcode}" != 0 ]; then
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Unexpected exit code ${exitcode}."
                exit 1
            fi

            if [ ! -f "${pcap}" ]; then
                t=$(date +%T)
                echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] ERROR: PCAP Not created at all ! ${pcap} sleeping 120 to cool down..."
                pkill firefox
                pkill dumpcap
                sleep 120
            fi
        fi

    done
done < urls

echo "All done."
exit 0
