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

URL_FILE="${1}"
BASE_OUTPUT_DIR="${2}"
OUTPUT_FOLDER="${BASE_OUTPUT_DIR}/percentage"

if [[ ! -f "${URL_FILE}" ]]
then
    echo "URL file does not exists."
    exit 1
fi

mkdir -p "${OUTPUT_FOLDER}"

while :
do
    python3 firefox-quic-percentage.py "${URL_FILE}" "${OUTPUT_FOLDER}"
    exitcode="$?"
    if [ "${exitcode}" == 0 ]; then
        exit 0
    fi

    memkill
    echo "Sleep 10"
    sleep 10
    find "${OUTPUT_FOLDER}" -size 0 -delete
done

echo "All done."
exit 0
