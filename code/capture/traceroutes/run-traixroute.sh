#!/bin/bash

INPUT_URLS="${1}"
OUTPUT_DIR="${2}"

mkdir -p "${OUTPUT_DIR}"

count=0
while IFS= read -r line
do
  echo "Traceroute for: $line"
  #Provide number of tracerts per domain as input
  for i in $(seq 1 $1)
  do
  	#run scamper with Paris
  	./bin/traixroute -thread -stats -ojson "${OUTPUT_DIR}/out${count}_${i}.json" -asn probe -sc -dest "${line}"
  	#run normal
  	#./bin/traixroute -thread -stats -ojson ${OUTPUT_DIR}/out${count}_${i}.json" -asn probe -t -dest "${line}"
  done
  count=$((count+1))
done < "${INPUT_URLS}"
