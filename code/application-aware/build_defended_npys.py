# imports and functions, does nothing

from math import isnan
from IPython.display import Image
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.model_selection import StratifiedShuffleSplit
import matplotlib.pyplot as plt
import numpy as np
import os
import random
from json import JSONEncoder
import json
from lib.features import *
from lib.rf import *

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def serialize(uri, o, version=''):
    try:
        os.remove(".cache/"+uri)
    except:
        pass
    with open(".cache/"+uri, "w") as f:
        if version != '':
            f.write('#version: '+version+'\n')
        json.dump(o, f, cls=NumpyArrayEncoder)

def deserialize(uri, version=''):
    if os.path.isfile(".cache/"+uri):
        with open(".cache/"+uri, "r") as f:
            data = []
            for line in f:
                if not line.startswith('#version:'):
                    data.append(line)
            return json.loads(''.join(data))
    return None

def load_or_compute(uri, compute_function, rebuild=False):
    data = None
    if not rebuild:
        data = deserialize(uri)
    if data is None:
        data = compute_function()
        serialize(uri, data)
        return data
    return data

data_all = np.load('datasets/quic-100p-150-40runs.npy', allow_pickle=True).item()
data = data_all['both'] # adblock + decentraleyes
urls = [url for url in data]

def add(a, b):
    x = 0
    if a is not None:
        x += abs(a)
    if b is not None:
        x += abs(b)
    return x

def toOldHARFormat(data):
    data2 = {}
    for url in data:
        data2[url] = {}
        for sample in data[url]:
            data2[url][sample] = []
            for request in data[url][sample]:
                domain, fullurl, t, out_h, out_b, t_resp, inc_h, inc_b = request
                data2[url][sample].append([t, add(out_h, out_b), add(inc_h, inc_b)])
    return data2

# sanitize, because I was dumb enough not to do it before...
data = toOldHARFormat(data)

HEAVY_WEBSITES_SUBRESOURCES = []
for url in data:
    for sample in data[url]:
        if len(data[url][sample]) > 40: # magic number
            HEAVY_WEBSITES_SUBRESOURCES.append(data[url][sample])

print(f"Identified {len(HEAVY_WEBSITES_SUBRESOURCES)} request-heavy websites")

# how many subresources do we need to inject ?
def deepcopy(data):
    data2 = {}
    for url in data:
        data2[url] = {}
        for sample in data[url]:
            data2[url][sample] = []
            for request in data[url][sample]:
                data2[url][sample].append(request)
    return data2

# same thing, no padding
def inject_dummy_request_overall(data, samples_to_inject, p=0.5, howmany=-1):
    costs = []

    for url in data:
        costs_this_website = []
        for sample in data[url]:
            requests = data[url][sample]
            last_t = 0
            if len(requests) > 0:
                last_t = requests[-1][2]

            extra_bw = 0
            extra_time = 0
            extra_req = 0

            if random.random() < p:
                # pick a sample at random
                chosen_sample = random.choice(samples_to_inject)

                # pick a starting subresource at random in the first half
                random_start = random.randint(0, int(len(chosen_sample)/2))

                end = len(chosen_sample)
                if howmany > -1 :
                    end = random_start + 2*howmany # twice, so E[length] = howmany

                if end > len(chosen_sample):
                    end = len(chosen_sample)

                # pick the end
                random_end = random.randint(random_start, end)

                # shift by last_t
                new_samples = chosen_sample[random_start:random_end]
                #shifted_samples = [[domain, fullurl, t+last_t, out_h, out_b, t_resp, inc_h, inc_b] for domain, fullurl, t, out_h, out_b, t_resp, inc_h, inc_b in new_samples]

                for extra_request in new_samples:
                    data[url][sample].append(extra_request)
                    extra_bw += extra_request[1] + extra_request[2] # add up and down
                    extra_time = extra_request[0] # max (they are sorted)
                extra_req += len(new_samples)

            costs_this_website.append([extra_bw, extra_time, extra_req])

        med_bw = np.median([cost[0] for cost in costs_this_website])
        mean_bw = np.mean([cost[0] for cost in costs_this_website])
        added_time = np.mean([cost[1] for cost in costs_this_website])
        added_req = np.mean([cost[2] for cost in costs_this_website])
        costs.append([med_bw, mean_bw, added_time, added_req])

    cost_summary = []

    med_bw = np.mean([cost[0] for cost in costs])
    mean_bw = np.mean([cost[1] for cost in costs])
    added_time = np.mean([cost[2] for cost in costs])
    added_req = np.mean([cost[3] for cost in costs])
    cost_summary = [med_bw, mean_bw, added_time, added_req]

    return data, cost_summary

for p in [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
    for howmany in [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:

        out = f"datasets/clf_res_{p}_{howmany}.npy"
        if os.path.isfile(out):
            print("Skipping", out)
            continue

        if p==0 and howmany > 1:
            continue

        print(f"***************** Working on p={p}, howmany={howmany}")
        data2 = deepcopy(data)
        data_with_dummies, dummies_cost = inject_dummy_request_overall(data2, HEAVY_WEBSITES_SUBRESOURCES, p=p, howmany=howmany)
        print("Dummies cost", dummies_cost)

        features = get_features(data_with_dummies)
        clf_res = rf_with_rfe(features)

        print(clf_res)
        np.save(out, [clf_res, dummies_cost])