#!/usr/bin/python3

import src.attack_cross as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder
import itertools

#Provide list of NPYs to test the attack on. 

NPY_LIST = ['firefox-paper.npy', 'chrome-paper.npy']

json_list = [x.replace('.npy', '.json') for x in NPY_LIST]
permutations = list(itertools.permutations(NPY_LIST, 2))

for permutation in permutations:

    train = permutation[0]
    test = permutation[1]
    json_file = 'cross_' + train.replace('.npy', '.json')
    if os.path.isfile(json_file):
        print("Already present", train, test)
        continue

    results = attack.run(permutation)
    #plot_builder.serialize(json_file, results)
