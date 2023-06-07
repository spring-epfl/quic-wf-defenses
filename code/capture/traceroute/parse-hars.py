#!/usr/bin/python3

import glob
import shutil
import sys
import json
import numpy as np
import multiprocessing as mp
import re
import ntpath
import os
import csv

H3_PATTERN = re.compile("h3-[TQ0-9]+=|quic=", re.IGNORECASE)

def make_data_dict(data):

    subquery_data = []
    subqueries = data[-1]
    for sq in subqueries:
        data_dict = {   'host': sq[0],
                        'url': sq[1],
                        'uses_quic': sq[2],
                        'query_header_size': sq[3][0],
                        'query_body_size': sq[3][1],
                        'response_header_size': sq[4][0],
                        'response_body_size': sq[4][1]
                    }
        subquery_data.append(data_dict)

    return subquery_data

def dict_from_headers(headers):
    res = dict()
    for header in headers:
        k = header['name'].strip().lower()
        v = header['value'].strip()
        res[k] = v
    return res


def parse_har(file):
    global seen_responses

    print("Processing", file)

    expected_host = ntpath.basename(file).replace('.har', '')

    # will contain triplets (subresource_domain, subresource_url, uses_quic, query_size, response_size)
    subqueries = []

    with open(file) as json_file:
        requests = json.load(json_file)


    root_host = None

    for request in requests:
        
        # format comes from capture/har-capture-faster/firefox-har-capture.py
        # request is [url, host, alt-svc, [request header size, body size], [response header size, body size]]
        url = request[0]
        host = request[1]
        altsvc = request[2]
        query_size = request[3]
        answer_size = request[4]
 
        # sometimes the cut between two captures [x.com, y.com] is not exact.
        # While we haven't seen a query for "y.com", discard all other queries before: they must come from "x.com"
        if root_host is None and (host != expected_host):
            print("Probable overlapping requests, skipping request {} in file {}.".format(host, file))
            continue


        if root_host is None:
            root_host = host  # we started capturing the right domain

        uses_quic = False
        if altsvc is not None and H3_PATTERN.match(altsvc):
            uses_quic = True

        subqueries.append((host, url, uses_quic, query_size, answer_size))

    return (root_host, file, subqueries)


if len(sys.argv) != 3:
    print("Usage: script.py HAR_DATASET_FOLDER OUTPUT_FOLDER")
    sys.exit(1)
dataset = sys.argv[1]
if not dataset.endswith('/'):
    dataset += '/'
output = sys.argv[2]

if not os.path.exists(output):
    os.makedirs(output)
    os.makedirs(os.path.join(output, "all"))
    os.makedirs(os.path.join(output, "urls"))

har_files = glob.glob(dataset+"*", recursive=False)
errored_files = []

for file in har_files:
    try:
        data = parse_har(file)
        url_fname = os.path.join(output, "urls", data[0])
        urls = [x[0] for x in data[-1]]
        urls = set(urls)
        # Make host files for traceroute experiments
        with open(url_fname, 'w') as f:
            for item in urls:
                f.write(item + "\n")
        data_dict = make_data_dict(data)
        all_fname = os.path.join(output, "all", data[0] + ".json")
        # Make JSON files containing all output for future analysis
        with open(all_fname, "w") as f:
            f.write(json.dumps(data_dict, indent=4))
    except Exception as e:
        print("Error in file:", file, e)
        errored_files.append(file)

print("All done.")
print("Number of errored files:", len(errored_files))
print("Errored files:")
for item in errored_files:
    print(item.split("/")[-1])
