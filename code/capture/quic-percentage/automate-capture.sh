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

OUTPUT_FOLDER=dataset



while : 
do
    python3 firefox-quic-percentage.py urls "${OUTPUT_FOLDER}"
    exitcode="$?"
    if [ "${exitcode}" == 0 ]; then
        exit 0
    fi

    memkill
    echo "Sleep 10"
    sleep 10
    find dataset -size 0 -delete
done

echo "All done."
exit 0
