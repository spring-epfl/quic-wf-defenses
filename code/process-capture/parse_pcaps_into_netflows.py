#!/usr/bin/python3

# This scripts converts a folder of pcaps (e.g., cluster-150-3/pcaps/) to a bunch of netflows (cluster-150-3/netflows/) using nfpcapd/nfdump
# WARNING: sometimes nfpcapd hangs, I don't know why. Keep an eye on the terminal, and kill using `pkill -f -9 nfpcapd` if stuck for too long.

import sys
import os
import glob
import subprocess
import multiprocessing as mp
import numpy as np
from pathlib import Path
import json
import socket
from scapy.all import *
from scapy.layers.tls.all import *
import subprocess
import shlex

SAMPLE_RATES = [1,10,100,1000] # 100%, 10%, 1%, 0.1%

if True:
    sys.path.append("../lib")
    import utils

def run_and_wait(cmd, stdout=None):
    parts = shlex.split(cmd)
    p = None
    if stdout is None:
        try:
            p = subprocess.run(parts, timeout=3)
        except:
            pass
        print("Ran", cmd)
    else:
        with open(stdout, "w") as outfile:
            subprocess.run(parts, stdout=outfile, timeout=3)
        print("Ran", cmd, "redirected to", stdout)
    try:
        os.waitpid(p.pid, 0)
    except:
        pass

def pcap_to_netflow(pcap_in, destination_folder, sample_rate=1):

    # if needs be, sample the pcap
    if sample_rate > 1:
        sampled_pcap = pcap_in.replace(".pcap", f"_{sample_rate}.pcap")
        if not os.path.isfile(sampled_pcap):
            print(f"Sampling {pcap_in} -> {sampled_pcap}")
            pkts = rdpcap(pcap_in)
            sampled_pkts = pkts[::sample_rate]
            wrpcap(sampled_pcap, sampled_pkts)
        else:
            print(f"Skipping {sampled_pcap}")
        pcap_in = sampled_pcap

        # output to netflows_samplerate if samplerate>1
        destination_folder = destination_folder.replace("/netflows/", f"/netflows_{sample_rate}/")

    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    print(f"Processing {pcap_in} -> {destination_folder}")

    run_and_wait(f"rm -f {destination_folder}nfcapd*")
    run_and_wait(f"nfpcapd -r {pcap_in} -l {destination_folder}")
    fnames = glob(f"{destination_folder}nfcapd*")
    fname = None
    
    # if nfpcapd only generated one file, pick it. Otherwise, pick the largest
    if len(fnames) == 0:
        print("No files in", f"{destination_folder}")
        sys.exit(0)
    elif len(fnames)==1:
        fname=fnames[0]
    else:
        sizes = [(f, os.path.getsize(f)) for f in fnames]
        sizes.sort(key=lambda row: row[1], reverse=True)
        fname = sizes[0][0]

    run_and_wait(f"nfdump -r {fname} -O tstart -q -o json", f"{destination_folder}nfdump.json")
    run_and_wait(f"rm -f {destination_folder}nfcapd*")
    run_and_wait(f"sed -i '1s/^/[/' {destination_folder}nfdump.json") #somehow the json file lacks the initial [, insert it

def process_pcap(pcap_in):
    destination_folder = pcap_in.replace('/pcaps/', '/netflows/').replace('capture.pcap', '')

    for sample_rate in SAMPLE_RATES:
        pcap_to_netflow(pcap_in, destination_folder, sample_rate)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: script DATASET_PATH/pcaps/")
        sys.exit(1)

    dataset_path = sys.argv[1].strip()
    if not dataset_path[-1] == '/':
        dataset_path += '/'

    if not dataset_path.endswith('/pcaps/'):
        print("DATASET_PATH should end with /pcaps/")
        sys.exit(1)

    pcaps = glob(dataset_path + '**/capture.pcap', recursive=True)
    pcaps.sort()
    for p in pcaps:
        process_pcap(p)
