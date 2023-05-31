#!/usr/bin/python3

import src.attack_het as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder
import itertools

path = "all_datasets/exp2_"

json_file = 'revision_results/het_exp2.json'
#if os.path.isfile(json_file):
#    print("Skipping", train, test)

results = attack.run(path)
plot_builder.serialize(json_file, results)
