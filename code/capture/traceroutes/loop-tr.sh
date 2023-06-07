#!/bin/bash
mkdir -p output
#Read from urls file
input="urls"
count=0
while IFS= read -r line
do
  echo "Traceroute for: $line"
  #Provide number of tracerts per domain as input
  for i in $(seq 1 $1)
  do
  	traceroute $line > output/out$count\_$i.log 2>/dev/null
  done
  count=$((count+1))
done < "$input"