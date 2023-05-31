#!/usr/bin/python3

# This scripts converts a folder of pcaps (e.g., cluster-150-3/pcaps/) to a bunch of parsed .npys (cluster-150-3/npys/) using tshark

import sys
import os
import glob
import subprocess
import multiprocessing as mp
import numpy as np
from pathlib import Path
from pathlib import Path

if True:
    sys.path.append("../../lib")
    import utils
    import constants
    import pcap_parsing

FORCE_REBUILD = False
NPY_SPLIT = 'summary_quic_tls_split.npy'
NPY_MERGED = 'summary_quic_tls_merged.npy'


def get_destination(folder):
    return folder.replace('/pcaps/', '/npys/')


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


def create_npy_quic_and_tls_separated(folder, npy_path):
    files = glob.glob(folder + '**/*.pcap', recursive=True)

    label, quic = get_label(files[0])
    url, _ = label

    summary = dict()
    summary[url] = dict()
    summary[url]['quic'] = dict()
    summary[url]['non-quic'] = dict()

    def getSplitRecords(f):
        label, quic = get_label(f)
        url, repeat = label

        txt = pcap_parsing.pcap_to_txt(f)
        quic_records, tls_records = pcap_parsing.text_to_timestamp_sizes_separate_quic_tls_traffic(txt)

        summary[url][quic][repeat] = dict(quic=quic_records, tls=tls_records)

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

                trace_quic = d[website][quic_enabled][repetition]['quic']
                trace_tls = d[website][quic_enabled][repetition]['tls']

                trace_quic = [['quic', t[0], t[1]] for t in trace_quic]
                trace_tls = [['tls', t[0], t[1]] for t in trace_tls]

                result = trace_quic + trace_tls
                result.sort()
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
        print("Usage: script DATASET_PATH/pcaps/")
        sys.exit(1)

    dataset_path = sys.argv[1].strip()
    if not dataset_path[-1] == '/':
        dataset_path += '/'

    if not dataset_path.endswith('/pcaps/'):
        print("DATASET_PATH should end with /pcaps/")
        sys.exit(1)

    folders = glob.glob(dataset_path + '*/', recursive=False)
    maximum = len(folders)

    utils.parallel(folders, process_folder, n_jobs=8)

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
