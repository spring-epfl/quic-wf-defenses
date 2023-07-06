#!/bin/bash

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

URLS_FILE="${1}"
OUTPUT_FOLDER="${2}"


while :
do
    python3 firefox-har-capture.py "${URLS_FILE}" "${OUTPUT_FOLDER}"
    exitcode="$?"
    if [ "${exitcode}" == 0 ]; then
        exit 0
    fi

    memkill
    echo "Sleep 10"
    sleep 10
done

echo "All done."
exit 0
