#!/usr/bin/python3

import src.features_from_hars as kffeatures
import os
import sys
import glob


def build_if_not_exists(path, output, defense, VARIANT='nofilter'):
    output = 'datasets/' + output
    if not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures.build(path+"/quic-100p-338-40-loops-har.npy", output_name=output, defense=defense, VARIANT=VARIANT)
    else:
        print(f"{output} already exists, skipping")


build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338.npy', defense=None, VARIANT="nofilter")
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-adblock.npy', defense=None, VARIANT="adblock")
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-decentraleyes.npy', defense=None, VARIANT="decentraleyes")
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-ad+de.npy', defense=None, VARIANT="both")

build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-nosize.npy', defense=kffeatures.defend_nosize)
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-notime.npy', defense=kffeatures.defend_notimes)
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-dummies.npy', defense=kffeatures.defend_dummies)
build_if_not_exists('../../cf-clusters-datasets/just_hars/quic-100p-338-40-loops', 'quic-100p-338-dummies2.npy', defense=lambda trace: kffeatures.defend_smart_dummies(trace, load=1))