# Build sources

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
load_layer("tls")

def parallel(files, function, n_jobs=20):
    pool = mp.Pool(n_jobs)
    data_dict = pool.map(function, files)
    return data_dict

def get_destination(folder):
    return folder.replace('/data/', '.pcaps/')

def process_pcap(pcap_in):
    global google_ips, google_domains

    pcap_out = get_destination(pcap_in)
    destination_folder = pcap_out.replace('capture.pcap', '')
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    print(f"Processing {pcap_in} -> {pcap_out}")

    try:
        new_pkts = []
        pkts = rdpcap(pcap_in)

        for pkt in pkts:

            if not pkt.haslayer(TLS) or pkt[TLS].type != 22: # only client hello
                continue
            new_pkts.append(pkt)

        print(f"Filtered {len(pkts)} down to {len(new_pkts)}")

        wrpcap(pcap_out, new_pkts)

    except Exception as e:
        print("Error processing pcap:", pcap_in, e)



dataset_path = '/data/google-pcaps/'
pcaps = glob(dataset_path + '**/capture.pcap', recursive=True)
parallel(pcaps, process_pcap, n_jobs=8)
print("Done creating individual .npy's.")



