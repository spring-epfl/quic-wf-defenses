#!/usr/bin/python3

import src.features_from_pcaps as kffeatures_pcaps
import os
import sys
import glob


def build_if_not_exists(path, output, defense):
    #output = 'datasets/' + output
    if True or not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_pcaps.build(path+"/npys/summary_quic_tls_merged.npy", output_name=output, defense=defense)
    else:
        print(f"{output} already exists, skipping")

# undefended

#clusters = glob.glob('../../cf-clusters-datasets/*/')
#clusters = [c for c in clusters if "old-dataset" not in c]

#for path in clusters:
#    continue
#    if not os.path.isdir(path+"npys/"):
#        continue

#    if "google" in path:
#        continue

#    if not "150" in path:
#        continue
    
#    output = path.replace('../../cf-clusters-datasets/', '').replace('/', '')+ ".npy"
#    build_if_not_exists(path, output, defense=None)


# defenses

#build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/', 'quic-100p-150-nosize.npy', defense=kffeatures_pcaps.defend_nosize)
#build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/', 'quic-100p-150-nototsize.npy', defense=kffeatures_pcaps.defend_nototalsize)
#build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/', 'quic-100p-150-notime.npy', defense=kffeatures_pcaps.defend_notiming)
#build_if_not_exists('../../cf-clusters-datasets/quic-100p-150/', 'quic-100p-150-nosizetime.npy', defense=kffeatures_pcaps.defend_nosizetiming)
build_if_not_exists('../../capture/quic-nquic-capture/dataset_het/', 'het-1.npy', defense=None)
