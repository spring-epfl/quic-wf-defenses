import os
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from math import *

# simply to keep track of the format
def HAR_ENTRY_FORMAT(host, full_url, query_time_since_initial, query_header_size, query_body_size, resp_time_since_initial, resp_header_size, resp_body_size):
    return [host, full_url, query_time_since_initial, query_header_size, query_body_size, resp_time_since_initial, resp_header_size, resp_body_size]

def add(a, b):
    x = 0
    if a is not None:
        x += a
    if b is not None:
        x += b
    return x

def find_interval(t1, t2):
    if "+" in t1:
        t1 = t1[:t1.find('+')]
    if "+" in t2:
        t2 = t2[:t2.find('+')]

    t1_datetime = datetime.strptime(t1, '%Y-%m-%dT%H:%M:%S.%f')
    t2_datetime = datetime.strptime(t2, '%Y-%m-%dT%H:%M:%S.%f')
    interval = (t2_datetime - t1_datetime).total_seconds()

    return interval

def read_folder(har_folder):
    har_fnames = os.listdir(har_folder)
    har_fnames_full = [os.path.join(har_folder, x) for x in har_fnames]
    sites = {}

    for har_filename in har_fnames_full:

        site_name = har_filename.replace(har_folder, '')[:-4] # remove .har
        
        data = []
        try:
            with open(har_filename) as f:
                data = json.loads(f.read())
        except:
            continue

        sites[site_name] = []

        if len(data) == 0:
            continue

        start_time = data[0]['time']  

        for e in data:
            if e['status'] == 0:
                continue # blocked request, invisible from the network

            url = e['url']
            host = e['host']
            req_time = e['time']
            query_time = find_interval(start_time, req_time)

            delay_ms = 0
            try:
                # sometimes the following is missing
                delay_ms = float(e['timings']['connect']) + float(e['timings']['ssl']) + float(e['timings']['send']) + float(e['timings']['wait'])
            except:
                pass
            resp_time = query_time + delay_ms / 1000


            query_size = e['request_size']
            answer_size = e['response_size']

            if query_size[0] is None or isnan(query_size[0]):
                query_size[0] = 0
            if query_size[1] is None or isnan(query_size[1]):
                query_size[1] = 0
            if answer_size[0] is None or isnan(answer_size[0]):
                answer_size[0] = 0
            if answer_size[1] is None or isnan(answer_size[1]):
                answer_size[1] = 0


            if answer_size[0] == -1 or answer_size[1] == -1:
                print(e)

            formattedHar = HAR_ENTRY_FORMAT(host, url, query_time, query_size[0], query_size[1], resp_time, answer_size[0], answer_size[1])
            sites[site_name].append(formattedHar)

    return sites
    

HAR_FOLDER = 'quic-100p-150-40runs/'
URL_FILE = 'quic-100p-150.txt'
OUTPUT_FILE = 'quic-100p-150-40runs.npy'

urls_filters = []
with open(URL_FILE) as f:
    for line in f:
        urls_filters.append(line.strip())

all_data = dict()

for subdir in ["dataset_adblock", "dataset_both", "dataset_nofilter", "dataset_decentraleyes"]:
    
    subdir_key = subdir.replace('dataset_', '')

    all_data[subdir_key] = dict()

    for i in range(1, 41):
        if not os.path.isdir(f"{FOLDER}loop_{i}/{subdir}"):
            print(f"Skipping {FOLDER}loop_{i}/{subdir}")
            continue

        print(f"{FOLDER}loop_{i}/{subdir}")

        sites = read_folder(f"{FOLDER}loop_{i}/{subdir}/")

        j = 0
        for site in sites:
            if site not in urls_filters:
                print("Skipping", site)
                continue
        
            if site not in all_data[subdir_key]:
                all_data[subdir_key][site] = dict()
            all_data[subdir_key][site][str(i)] = sites[site]

            j += 1
        print(f"Processed {j} sites")

np.save(OUTPUT_FILE, all_data)
print("Done")