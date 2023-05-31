#!/usr/bin/python3

# This scripts converts a folder of pcaps (e.g., cluster-150-3/pcaps/) to a bunch of parsed .npys (cluster-150-3/npys/) using tshark

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

if True:
    sys.path.append("../lib")
    import utils

FORCE_REBUILD = False
GOOGLE_ASN = '15169'

def get_destination(folder):
    return folder.replace('/pcaps/', '-google/pcaps/')


def get_as_hops(filename):
    with open(filename) as f:
        data = json.loads(f.read())

    asn_list = []
    result = data[0]['result']

    for item in result:
        hop_result = item['result'][0]
        asn = hop_result['asn']
        asn_list.append(asn)

    return asn_list

def get_google_hosted_resources(traceroutes_folder):

    domains_on_google = set()
    non_google_domains = set()
    traceroute_jsons = glob(traceroutes_folder + '**/*.json', recursive=True)

    for traceroute_json in traceroute_jsons:
        filepath = traceroute_json.replace(traceroutes_folder, '').replace('.json', '')
        parts = filepath.split('/')
        if len(parts) != 2:
            print("Can't split in two", filepath)
            sys.exit(1)
        site, resource = parts
        
        hops = get_as_hops(traceroute_json)
        good_asn_list = [x for x in hops if x != '*'] # remove *

        if len(good_asn_list) > 0 and good_asn_list[-1] == GOOGLE_ASN:
            remove_subdomain = resource
            parts = remove_subdomain.split('.')
            d = parts[-2]+"."+parts[-1]

            if is_google_domain(d):
                domains_on_google.add(d)
            else:
                non_google_domains.add(d)

    return domains_on_google

def is_google_domain(d):
    d = d.lower().strip()

    if d.endswith('ggpht.com'):
        return True
    if "google" in d or "youtube" in d or "doubleclick" in d or "gstatic.com" in d:
        return True

    return False

def process_pcap(pcap_in):
    global google_ips, google_domains

    pcap_out = get_destination(pcap_in)
    destination_folder = pcap_out.replace('capture.pcap', '')
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    print(f"Processing {pcap_in} -> {pcap_out}")

    try:
        # We first do a simple IP comparison. If the destination IP of a packet is in the
        # IP list, we keep that packet. We also log this IP.
        seen_ips = []
        new_pkts = []
        pkts = rdpcap(pcap_in)

        for pkt in pkts:
            take = False
            if pkt.haslayer(IP):
                src = pkt[IP].src
                dst = pkt[IP].dst
                if dst in google_ips:
                    seen_ips.append(dst)
                    new_pkts.append(pkt)
                elif src in google_ips:
                    seen_ips.append(src)
                    new_pkts.append(pkt)

        # Our resource-IP mapping might not be perfect. IPs could have changed.
        # For example A.com might now correspond to 1.2.3.5 instead of 1.2.3.4.
        # We do the next step to handle this case.
        # We look at the SNI in the ClientHellos to see if the host name corresponds to the resource.
        # If it does, we log that IP, and also keep the packet corresponding to the IP.

        missed_ips = set(google_ips) - set(seen_ips)
        ips_to_keep = []

        if len(missed_ips) > 0:
            for pkt in pkts:
                if pkt.haslayer(TLS_Ext_ServerName):
                    if pkt.haslayer(ServerName):
                        servername = pkt[ServerName].servername.decode()
                        if servername in google_domains or is_google_domain(servername):
                            dst = pkt[IP].dst
                            if dst not in seen_ips:
                                ips_to_keep.append(dst)

            for pkt in pkts:
                if pkt.haslayer(IP):
                    dst = pkt[IP].dst
                    src = pkt[IP].src
                    if dst in ips_to_keep:
                        new_pkts.append(pkt)
                    elif src in ips_to_keep:
                        new_pkts.append(pkt)

        # We sort the selected packets by timestamp.
        sorted_new_pkts = sorted(new_pkts, key=lambda ts: ts.time)
        # We write the packets to output.
        wrpcap(pcap_out, sorted_new_pkts)

    except Exception as e:
        print("Error processing pcap:", pcap_in, e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script DATASET_PATH/pcaps/")
        sys.exit(1)

    dataset_path = sys.argv[1].strip()
    if not dataset_path[-1] == '/':
        dataset_path += '/'

    if not dataset_path.endswith('/pcaps/'):
        print("DATASET_PATH should end with /pcaps/")
        sys.exit(1)

    google_domains = get_google_hosted_resources(dataset_path.replace('/pcaps/', '/traceroutes/'))
    google_ips = []
    for d in google_domains:
        try:
            ip = socket.gethostbyname(d)
            google_ips.append(ip)
        except Exception as e:
            print("Error with IP mapping:", e, d)


    pcaps = glob(dataset_path + '**/capture.pcap', recursive=True)
    utils.parallel(pcaps, process_pcap, n_jobs=8)

    print("Done creating individual .npy's.")



