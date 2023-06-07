#!/usr/bin/python3

import src.attack_google_timings as attack
import sys
import glob
import os
import lib.plot_builder as plot_builder

INPUT_DIR = "datasets/"
npys = glob.glob(INPUT_DIR + '*.npy', recursive=False)

for npy_file in npys:
    json_file = npy_file.replace('.npy', '.json')

    if os.path.isfile(json_file):
        print("Skipping", npy_file)
        continue
    
    results = attack.run(npy_file)
    plot_builder.serialize(json_file, results)
