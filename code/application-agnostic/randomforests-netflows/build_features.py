#!/usr/bin/python3

from numpy.lib.arraypad import pad
import src.features_from_netflows as kffeatures_netflows
import os
import sys
import glob


def build_if_not_exists(path, output, defense):
    output = 'datasets/' + output
    if not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_netflows.build_netflow(path+"/summary_quic_tls_merged.npy", output_name=output, defense=defense)
    else:
        print(f"{output} already exists, skipping")


clusters = glob.glob('../../cf-clusters-datasets/*/')
clusters = [c for c in clusters if "100p-150" in c]

# build datasets from netflows
for path in clusters:

    subpaths = glob.glob(path+"netflow_npy*")
    for subpath in subpaths: # for each sampling rate

        output = subpath.replace('../../cf-clusters-datasets/', '').replace('netflow_npys_', 'netflow_npys').replace('netflow_npys', 'netflow').replace('/', '-')+ ".npy"
        build_if_not_exists(subpath, output, defense=None)


build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/netflow_npys/', 'quic-100p-150-netflow-nototsize.npy', lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*10**4, paddedBytes=23*10**6))
build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/netflow_npys_10/', 'quic-100p-150-netflow10-nototsize.npy', lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*1000, paddedBytes=23 * 10**5))
build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/netflow_npys_100/', 'quic-100p-150-netflow100-nototsize.npy', lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*100, paddedBytes=23*10**4))
build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/netflow_npys_1000/', 'quic-100p-150-netflow1000-nototsize.npy', lambda X: kffeatures_netflows.defend_nototalsize(X, paddedPackets=3*10, paddedBytes=23 *10**3))
# build the netflows from Google

clusters = glob.glob('../../cf-clusters-datasets/*/')
clusters = [c for c in clusters if "google" in c]

# build datasets from netflows
for path in clusters:
    subpaths = glob.glob(path+"netflow_npy*")
    for subpath in subpaths: # for each sampling rate

        output = subpath.replace('../../cf-clusters-datasets/', '').replace('netflow_npys_', 'netflow_npys').replace('netflow_npys', 'netflow').replace('/', '-')+ ".npy"
        build_if_not_exists(subpath, output, defense=None)

