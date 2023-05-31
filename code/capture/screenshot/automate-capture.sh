#!/usr/bin/bash

memkill() {
    pkill -f geckodriver
    pkill -f firefox
}

cleanup() {
    memkill
    echo "Interrupted"
    exit 1
}
trap "cleanup" HUP INT TERM

OUTPUT_FOLDER=dataset

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
        read -p "You are not in \"screen\". Continue ?" yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi

# Careful, merging ${OUTPUT_FOLDER} could be good or bad, better double check
if [ -d ${OUTPUT_FOLDER} ]; then
    while true; do
        read -p "Careful: Output folder \"${OUTPUT_FOLDER}\" already exists. Contents will be merged, pre-existing data will be skipped. Impartial captures will be overwritten. Continue ?" yn
        case $yn in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer [y]es or [n]o.";;
        esac
    done
fi


mkdir -p "${OUTPUT_FOLDER}"
chmod ugo+rwx "${OUTPUT_FOLDER}" #tshark sometimes chokes on this

count=-1

realname=urls
if [ `readlink urls` != "" ]; then
    realname=`readlink urls`
fi

while read url; 
do
    ((count=count+1))
    # if mode "modulo" is enabled, skip non-matching entries
    if [ ${mod} != -1 ] && [ $(expr $count % $mod) != "$inc" ]; then
        continue
    fi


    for i in {1..10}
    do

        png="${OUTPUT_FOLDER}/${url}_${i}.png"

        if [ -f "${png}" ] && [ -s "${png}" ]; then
            t=$(date +%T)
            echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Skipping ${url}"
        else
            memkill

            t=$(date +%T)
            echo "[${realname}, ${count}, ${t}, ${mod}, ${inc}] Crawling ${url}"
            timeout -s HUP -k 10 60 python3 -u firefox-screenshot-query.py "${url}" "${png}"

            memkill
        fi
    done
done < urls

echo "All done."
exit 0