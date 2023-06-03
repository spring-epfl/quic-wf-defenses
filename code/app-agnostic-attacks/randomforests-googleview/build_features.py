#!/usr/bin/python3

import src.features_from_pcaps_Google_dest as kffeatures_pcaps_Google
import os
import sys
import glob

def build_if_not_exists(path, output):
    output = 'datasets/' + output
    if not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_pcaps_Google.build_Google_variant(path+"/summary_quic_tls_merged.npy", output_name=output)
    else:
        print(f"{output} already exists, skipping")


#build_if_not_exists("../../cf-clusters-datasets/quic-80p-122-google/npys", 'quic-80p-122-google.npy')
build_if_not_exists("../../cf-clusters-datasets/quic-100p-150-google/npys", 'quic-100p-150-google.npy')
