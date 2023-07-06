#!/bin/bash

INPUT_DIR="${1}"
OUTPUT_DIR="${2}"

mkdir -p "${OUTPUT_DIR}"
#Read from urls folder
for filename in "${INPUT_DIR}"/*
do
  onlyfilename=$(basename -- "${filename}")
  echo "Processing: ${onlyfilename}"
  mkdir -p "${OUTPUT_DIR}/${onlyfilename}"
  while IFS= read -r line
  do
    echo "Traceroute for: ${line}"
    #Provide number of tracerts per domain as input
    for i in $(seq 1 $3)
    do
      #run scamper with Paris
      python3 -m traixroute -thread -stats -ojson "${OUTPUT_DIR}/${onlyfilename}/${line}.json" -asn probe -sc -dest "${line}"
    done
  done < "${filename}"
done
