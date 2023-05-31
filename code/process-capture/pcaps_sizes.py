#!/usr/bin/python3

import sys
import os
import glob
import numpy as np
from pathlib import Path

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

    pcaps = glob.glob(dataset_path + '**/*.pcap', recursive=True)
    
    sizes = dict()
    for p in pcaps:
        f = p.replace(dataset_path, '')
        parts = f.split('/')
        url = parts[0]

        if not url in sizes:
            sizes[url] = []

        size = os.path.getsize(p)
        sizes[url].append(size)

    keys = list(sizes.keys())
    means = []
    
    for k in keys:
        mean = round(np.mean(sizes[k])/1024, 2)
        means.append(mean)

    print("Overall mean", np.min(means), np.mean(means), np.max(means), np.var(means))