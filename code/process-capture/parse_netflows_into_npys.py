#!/usr/bin/python3

# This scripts converts a folder of pcaps (e.g., cluster-150-3/pcaps/) to a bunch of parsed .npys (cluster-150-3/npys/) using tshark

import sys
import os
import json
import glob
import subprocess
import multiprocessing as mp
import numpy as np
from pathlib import Path
from pathlib import Path
from datetime import datetime

if True:
    sys.path.append("../lib")
    import utils
    import constants
    import pcap_parsing

FORCE_REBUILD = True
NPY_SPLIT = 'summary_quic_tls_split.npy'
NPY_MERGED = 'summary_quic_tls_merged.npy'
PROTO_TCP = 6
PROTO_UDP = 17
DIRECTION_INCOMING = -1
DIRECTION_OUTGOING = 1
SOURCE_IP = '10.1.1.1'

def get_destination(folder):
    return folder.replace('/netflows', '/netflow_npys')


def get_label(f):

    relative_path = f.replace(dataset_path, '')

    parts = relative_path.split('/')
    url = parts[0]
    repeat = int(parts[1])
    quic = parts[2]

    if quic != "quic" and quic != "non-quic":
        print(f"Panic parsing path ${f}, quic should be \"quic\" or \"non-quic\".")
        sys.exit(1)

    label = (url, repeat)
    return label, quic


def extract_info_from_flow(d):
    t_first = datetime.strptime(d['t_first'], '%Y-%m-%dT%H:%M:%S.%f')
    t_last = datetime.strptime(d['t_last'], '%Y-%m-%dT%H:%M:%S.%f')
    src = d['src4_addr']
    dst = d['dst4_addr']
            
    direction = DIRECTION_INCOMING
    if src == SOURCE_IP:
       direction = DIRECTION_OUTGOING

    in_packets = d['in_packets']
    in_bytes = d['in_bytes']

    stats = dict(t_first=t_first,t_last=t_last,direction=direction,src=src,dst=dst,packets=in_packets,bytes=in_bytes,proto=d['proto'])
    return stats

def create_npy_quic_and_tls_separated(folder, npy_path):

    files = glob.glob(folder + '**/*.json', recursive=True)

    label, _ = get_label(files[0])
    url, _ = label

    summary = dict()
    summary[url] = dict()
    summary[url]['quic'] = dict()
    summary[url]['non-quic'] = dict()

    def getSplitRecords(f):
        label, quic = get_label(f)
        url, repeat = label

        data = []
        try:
            with open(f, 'r') as file:
                data = json.load(file)
        except:
            print("Couldn't parse", f, "ignoring")
            summary[url][quic][repeat] = dict(udp=[], tcp=[])
            return

        tcp = [extract_info_from_flow(d) for d in data if d['proto'] == PROTO_TCP]
        udp = [extract_info_from_flow(d) for d in data if d['proto'] == PROTO_UDP]

        summary[url][quic][repeat] = dict(udp=udp, tcp=tcp)

    for f in files:
        getSplitRecords(f)

    np.save(npy_path, summary)
    print(f"Processed {url} -> {npy_path}. Loaded", len(summary[url]['quic']), "pcaps for quic,", len(summary[url]['non-quic']), "pcaps for non-quic.")


def create_npy_both_protocols(npy_split_path, npy_merged_path):
    d = np.load(npy_split_path, allow_pickle=True).item()

    merged = dict()

    for website in d:
        merged[website] = dict()
        for quic_enabled in d[website]:
            merged[website][quic_enabled] = dict()
            for repetition in d[website][quic_enabled]:
                merged[website][quic_enabled][repetition] = dict()

                flow_udp = d[website][quic_enabled][repetition]['udp']
                flow_tcp = d[website][quic_enabled][repetition]['tcp']

                result = flow_udp + flow_tcp
                result.sort(key=lambda flow: flow['t_first'])
                merged[website][quic_enabled][repetition] = result

    np.save(npy_merged_path, merged)
    print(f"Merged {npy_split_path} into {npy_merged_path}")

def process_folder(folder):

    if not folder.endswith('/'):
        folder += '/'
    destination_folder = get_destination(folder)
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    print(f"Processing {folder} -> {destination_folder}")

    if FORCE_REBUILD or not os.path.isfile(destination_folder+NPY_SPLIT):
        create_npy_quic_and_tls_separated(folder, destination_folder+NPY_SPLIT)

    if FORCE_REBUILD or not os.path.isfile(destination_folder+NPY_MERGED):
        create_npy_both_protocols(destination_folder+NPY_SPLIT, destination_folder+NPY_MERGED)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script DATASET_PATH/netflows/")
        sys.exit(1)

    dataset_path = sys.argv[1].strip()
    if not dataset_path[-1] == '/':
        dataset_path += '/'

    if not "/netflows" in dataset_path:
        print("DATASET_PATH should end with /netflows_SAMPLERATE/")
        sys.exit(1)

    folders = glob.glob(dataset_path + '*/', recursive=False)
    maximum = len(folders)

    for f in folders:
        process_folder(f)

    print("Done creating individual .npy's.")
    
    # merge split version
    main_summary_quic_tls_split = dict()

    i = 0
    for f in folders:
        print(round(100*float(i)/len(folders)), end="\r")
        i += 1
        d = np.load(get_destination(f)+NPY_SPLIT, allow_pickle=True).item()
        for website in d:
            main_summary_quic_tls_split[website] = d[website]
    np.save(get_destination(dataset_path) + NPY_SPLIT,main_summary_quic_tls_split)

    # merge combined version
    main_summary_merged = dict()

    i = 0
    for f in folders:
        print(round(100*float(i)/len(folders)), end="\r")
        i += 1
        d = np.load(get_destination(f)+NPY_MERGED, allow_pickle=True).item()
        for website in d:
            main_summary_merged[website] = d[website]

    np.save(get_destination(dataset_path) + NPY_MERGED, main_summary_merged)

    print("All done, written", get_destination(dataset_path)+ "{" + NPY_MERGED +","+ NPY_SPLIT + "}")
