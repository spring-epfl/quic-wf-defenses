#!/bin/bash
mkdir -p outputscamper
#Read from urls folder
for filename in $2/*
do
  onlyfilename=$(basename -- "$filename")
  echo "Processing: $onlyfilename"
  mkdir -p outputscamper/$onlyfilename
  while IFS= read -r line
  do
    echo "Traceroute for: $line"
    #Provide number of tracerts per domain as input
    for i in $(seq 1 $1)
    do
      #run scamper with Paris
      ./bin/traixroute -thread -stats -ojson outputscamper/$onlyfilename/$line.json -asn probe -sc -dest $line
    done
  done < "$filename"
done
