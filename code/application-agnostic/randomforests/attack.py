#!/usr/bin/python3

import src.attack as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder

npys = glob.glob('all_datasets_2/*.npy', recursive=False)

for npy_file in npys:
    json_file = npy_file.replace('.npy', '.json')

    if os.path.isfile(json_file):
        print("Skipping", npy_file)
        continue
    
    results = attack.run(npy_file)
    plot_builder.serialize(json_file, results)
