#!/usr/bin/python3

from numpy.lib.arraypad import pad
import src.features_from_netflows as kffeatures_netflows
import os
import sys
import glob
import argparse


def build_if_not_exists(path, output, defense):
    
    output = 'datasets/' + output
    if not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_netflows.build_netflow(path+"/summary_quic_tls_merged.npy", output_name=output, defense=defense)
    else:
        print(f"{output} already exists, skipping")


INPUT_DIR = 'netflow_npys/'
OUTPUT_FILE = 'netflow_undefended.npy'

build_if_not_exists(INPUT_DIR, OUTPUT_FILE, defense=None)

#To apply a defense for 1% sampling rate
#build_if_not_exists(INPUT_DIR, OUTPUT_FILE, lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*10**4, paddedBytes=23*10**6))

#For other sampling rates
#10%
#build_if_not_exists(INPUT_DIR, OUTPUT_FILE, lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*1000, paddedBytes=23 * 10**5))
#100%
#build_if_not_exists(INPUT_DIR, OUTPUT_FILE, lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*100, paddedBytes=23*10**4))
#1000%
#build_if_not_exists(INPUT_DIR, OUTPUT_FILE, lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*10, paddedBytes=23 *10**3))
