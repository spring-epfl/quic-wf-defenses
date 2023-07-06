#!/usr/bin/python3

import src.features_from_pcaps as kffeatures_pcaps
import os
import sys
import glob
import argparse


def build_if_not_exists(path, output, defense):
    #output = 'datasets/' + output
    if True or not os.path.isfile(output):
        print(f"Working on {output}")
        kffeatures_pcaps.build(path+"/npys/summary_quic_tls_merged.npy", output_name=output, defense=defense)
    else:
        print(f"{output} already exists, skipping")

def main(program, args):

    # Create argument parser and arguments
    parser = argparse.ArgumentParser(prog=program, description="Run feature extraction.")
    parser.add_argument(
        "--input",
        type=str,
        help="Folder path containing NPY traces.",
        default="/data/"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output NPY file containing features.",
        default="quic-100p-150-undefended.npy"
    )
    parser.add_argument(
        "--defense",
        type=str,
        help="Defense type. Can be one of 5: none, nosize, nototalsize, notiming, nosizetiming",
        default="none"
    )

    ns = parser.parse_args(args)
    
    if ns.defense == 'nosize':
        build_if_not_exists(ns.input, ns.output, defense=kffeatures_pcaps.defend_nosize)
    elif ns.defense == 'nototalsize':        
        build_if_not_exists(ns.input, ns.output, defense=kffeatures_pcaps.defend_nototalsize)
    elif ns.defense == 'notiming':
        build_if_not_exists(ns.input, ns.output, defense=kffeatures_pcaps.defend_notiming)
    elif ns.defense == 'nosizetiming':
        build_if_not_exists(ns.input, ns.output, defense=kffeatures_pcaps.defend_nosizetiming)
    else:
        build_if_not_exists(ns.input, ns.output, defense=None)  

if __name__ == "__main__":

    main(sys.argv[0], sys.argv[1:])
