#!/usr/bin/python3

import src.attack_cross as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder
import itertools

# npy_list = ['datasets/350sites_noempty.npy', 'datasets/failures.npy']
# json_list = [x.replace('.npy', '.json') for x in npy_list]

# permutations = list(itertools.permutations(npy_list, 2))

# for permutation in permutations:

#     train = permutation[0]
#     test = permutation[1]
#     json_file = 'cross_' + train.replace('datasets/', '').replace('.npy', '.json')
#     if os.path.isfile(json_file):
#         print("Skipping", train, test)
#         continue

#     results = attack.run(permutation)
#     plot_builder.serialize(json_file, results)


npy_list = ['all_datasets_2/main_exclude.npy', 'all_datasets_2/time-new.npy']
json_list = [x.replace('.npy', '.json') for x in npy_list]

permutations = list(itertools.permutations(npy_list, 2))

for permutation in permutations:

    train = permutation[0]
    test = permutation[1]
    json_file = 'cross_' + train.replace('all_datasets_2/', '').replace('.npy', '.json')
    if os.path.isfile('all_datasets_2/' + json_file):
        print("Skipping", train, test)
        continue

    results = attack.run(permutation)
    plot_builder.serialize(json_file, results)
