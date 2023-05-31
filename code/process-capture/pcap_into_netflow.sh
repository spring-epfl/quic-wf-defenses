#!/bin/bash
pcap_in=$1
dest_folder=$2

mkdir -p "${dest_folder}"
rm -rf "${dest_folder}*"

