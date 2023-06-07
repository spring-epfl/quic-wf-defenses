#!/usr/bin/python3

import src.features_google_timings as kffeatures_google
import os
import sys
import glob

def build_if_not_exists(path, output):
    output = 'datasets/' + output
    if not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_google.build(path+"/summary_quic_tls_merged.npy", output_name=output)
    else:
        print(f"{output} already exists, skipping")


INPUT_DIR = 'google_npys/'
OUTPUT_FILE = 'google.npy'

build_if_not_exists(INPUT_DIR, OUTPUT_FILE)
