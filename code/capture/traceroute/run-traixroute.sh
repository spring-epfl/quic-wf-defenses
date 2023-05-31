#!/bin/bash
mkdir -p outputscamper
#mkdir -p outputtraceroute
#Read from urls file
input="urls"
count=0
while IFS= read -r line
do
  echo "Traceroute for: $line"
  #Provide number of tracerts per domain as input
  for i in $(seq 1 $1)
  do
  	#run scamper with Paris
  	./bin/traixroute -thread -stats -ojson outputscamper/out$count\_$i.json -asn probe -sc -dest $line
  	#run normal
  	#./bin/traixroute -thread -stats -ojson outputtraceroute/out$count\_$i.json -asn probe -t -dest $line
  done
  count=$((count+1))
done < "$input"