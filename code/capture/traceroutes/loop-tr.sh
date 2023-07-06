#!/bin/bash

#Read from urls file
INPUT_URLS="$1"
OUTPUT_DIR="$2"
NUM="$3"
count=0

mkdir -p "${OUTPUT_DIR}"

while IFS= read -r line
do
  echo "Traceroute for: ${line}"
  #Provide number of tracerts per domain as INPUT_URLS
  for i in $(seq 1 "${NUM}")
  do
  	traceroute "${line}" > "${OUTPUT_DIR}/out${count}_${i}.log" 2>/dev/null
  done
  count=$((count+1))
done < "$INPUT_URLS"
