#!/usr/bin/python3

import src.attack_het as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder
import itertools

INPUT_DIRECTORY_TAG = "datasets/exp2_"
json_file = 'het_exp2.json'

results = attack.run(INPUT_DIRECTORY_TAG)
#plot_builder.serialize(json_file, results)
