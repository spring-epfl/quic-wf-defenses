# feature extraction

import numpy as np
import math
import sys
import random

def average(array):
    if array is None or len(array) == 0:
        return 0
    return np.average(array)

def array_to_fix_size(array, length, pad_with=0):
    if len(array) < length:
        array.extend([pad_with] * (length - len(array)))
    elif len(array) > length:
        array = array[:length]
    return array

def split_in_chunks(array, num_splits):
    avg = len(array) / float(num_splits)
    out = []
    last = 0.0
    while last < len(array):
        out.append(array[int(last): int(last + avg)])
        last += avg
    return out

def get_packet_inter_times(data):
    if len(data) == 0:
        return [0]
    times = [x[0] for x in data]
    result = []
    for elem, next_elem in zip(times, times[1:] + [times[0]]):
        result.append(next_elem - elem)
    return result[:-1]

def add_intertimes_stats(features, data, incoming, outgoing):
    # statistics about the inter-packet durations

    def add_stats(trace, prefix=''):
        if trace is not None and len(trace) > 0:
            features['intertime_'+prefix+'max'] = max(trace)
            features['intertime_'+prefix + 'avg'] = average(trace)
            features['intertime_'+prefix+'std'] = np.std(trace)
            features['intertime_'+prefix+'p75'] = np.percentile(trace, 75)
        else:
            features['intertime_'+prefix+'p25'] = 0
            features['intertime_'+prefix+'p50'] = 0
            features['intertime_'+prefix+'p75'] = 0
            features['intertime_'+prefix+'p100'] = 0

    incoming_intertimes = get_packet_inter_times(incoming)
    outgoing_intertimes = get_packet_inter_times(outgoing)
    all_intertimes = get_packet_inter_times(data)

    add_stats(incoming_intertimes, 'incoming_')
    add_stats(outgoing_intertimes, 'outgoing_')
    add_stats(all_intertimes, '')


def add_time_percentiles(features, data, incoming, outgoing):
    # percentiles about the times in which packets where sent/received

    def add_percentiles(trace, prefix=''):
        if trace is not None and len(trace) > 0:
            features['time_'+prefix+'p25'] = np.percentile(trace, 25)
            features['time_'+prefix+'p50'] = np.percentile(trace, 50)
            features['time_'+prefix+'p75'] = np.percentile(trace, 75)
            features['time_'+prefix+'p100'] = np.percentile(trace, 100)
        else:
            features['time_'+prefix+'p25'] = 0
            features['time_'+prefix+'p50'] = 0
            features['time_'+prefix+'p75'] = 0
            features['time_'+prefix+'p100'] = 0

    incoming_times = [x[0] for x in incoming]
    outgoing_times = [x[0] for x in outgoing]
    times = [x[0] for x in data]

    add_percentiles(incoming_times, 'incoming_')
    add_percentiles(outgoing_times, 'outgoing_')
    add_percentiles(times, '')

    features['times_sum'] = sum(times)


def add_counts_in_out_last_first_30(features, data):
    # counts (incoming, outgoing) packets in the (first, last) 30 packets

    # NB: these features don't make much sense for HARs

    first30 = data[:30]
    last30 = data[-30:]
    first30in = []
    first30out = []
    for p in first30:
        if p[1] > 0: 
            first30in.append(p)
        if p[2] >= 0:
            first30out.append(p)
    last30in = []
    last30out = []
    for p in last30:
        if p[1] > 0:
            last30in.append(p)
        if p[2] >= 0:
            last30out.append(p)

    features['f30_n_incoming'] = len(first30in)
    features['f30_n_outgoing'] = len(first30out)
    features['l30_n_incoming'] = len(last30in)
    features['l30_n_outgoing'] = len(last30out)


def add_outgoing_concentrations_stats(features, data):
    # concentration of outgoing packets in chunks of 20 packets

    chunks = [data[x: x + 20] for x in range(0, len(data), 20)]
    concentrations = []
    for item in chunks:
        c = 0
        for p in item:
            if p[2] >= 0: # outgoing packets
                c += 1
        concentrations.append(c)

    concentrations = array_to_fix_size(concentrations, 40)

    features['outgoing_concentrations_std'] = np.std(concentrations)
    features['outgoing_concentrations_mean'] = average(concentrations)
    features['outgoing_concentrations_p50'] = np.percentile(concentrations, 50)
    features['outgoing_concentrations_min'] = min(concentrations)
    features['outgoing_concentrations_max'] = max(concentrations)

    i = 0
    while i < len(concentrations):
        features['outgoing_concentrations_'+str(i)] = concentrations[i]
        i += 1

    # Same think, but for trace divided in 70 fixed chunks

    outgoing_concentrations_70 = [
        sum(x) for x in split_in_chunks(concentrations, 70)]

    i = 0
    while i < len(outgoing_concentrations_70):
        features['outgoing_concentrations_70_' +
                 str(i)] = outgoing_concentrations_70[i]
        i += 1

    features['outgoing_concentrations_70_sum'] = sum(
        outgoing_concentrations_70)


def add_delta_rates_stats(features, data):
    # Average number packets sent and received per second

    last_time = data[-1][1]
    last_second = math.ceil(last_time)

    count_per_sec = []
    for sec in range(1, int(last_second) + 1):
        count = 0
        for p in data:
            if p[0] <= sec: # p[0] is packet time
                count += 1
        count_per_sec.append(count)

    count_per_sec = array_to_fix_size(count_per_sec, 10)

    delta_count_per_sec = [0]  # first difference is 0
    i = 1
    while i < len(count_per_sec):
        diff = count_per_sec[i] - count_per_sec[i-1]
        delta_count_per_sec.append(diff)
        i += 1

    features['delta_rate_avg'] = average(delta_count_per_sec)
    features['delta_rate_std'] = np.std(delta_count_per_sec)
    features['delta_rate_p50'] = np.percentile(delta_count_per_sec, 50)
    features['delta_rate_min'] = min(delta_count_per_sec)
    features['delta_rate_max'] = max(delta_count_per_sec)

    i = 1
    while i < len(delta_count_per_sec):
        features['delta_rate_'+str(i)] = delta_count_per_sec[i]
        i += 1

    # Same thing, but trace divided in 20 fixed chunks

    delta_counts_20 = [sum(x)
                       for x in split_in_chunks(delta_count_per_sec, 20)]

    i = 0
    while i < len(delta_counts_20):
        features['delta_rates_20_'+str(i)] = delta_counts_20[i]
        i += 1

    features['delta_rates_20_sum'] = sum(delta_counts_20)


def extract_features(data, max_size=123):
    features = dict()


    if len(data) == 0:
        return array_to_fix_size([], max_size, pad_with=('*', 0))

    def quic_to_1(s):
        if s=='quic':
            return 1
        return 0

    outgoing = [pkt for pkt in data if pkt[1] > 0]
    incoming = [pkt for pkt in data if pkt[2] > 0]

    features['n_incoming'] = len(incoming)
    features['n_outgoing'] = len(outgoing)
    features['n_total'] = len(data)
    features['%_in'] = len(incoming) / float(len(data))
    features['%_out'] = len(outgoing) / float(len(data))
    
    features['bytes_incoming'] = sum([d[2] for d in incoming])
    features['bytes_outgoing'] = sum([d[1] for d in outgoing])
    features['bytes_total'] = features['bytes_incoming'] + features['bytes_outgoing']
    if features['bytes_total'] > 0:
        features['bytes_%_in'] = features['bytes_incoming'] / float(features['bytes_total'])
        features['bytes_%_out'] = features['bytes_outgoing'] / float(features['bytes_total'])
    else:
        features['bytes_%_in'] = 0
        features['bytes_%_out'] = 0

    add_intertimes_stats(features, data, incoming, outgoing)
    add_time_percentiles(features, data, incoming, outgoing)
    add_counts_in_out_last_first_30(features, data)

    add_delta_rates_stats(features, data)

    # added size features; TLS max is -16K +16k
    incoming_sizes = [x[2] for x in incoming]
    bins = np.linspace(0, 16*1024, 50)
    hist, bin_edges = np.histogram(incoming_sizes, bins=bins, density=False)

    i = 0
    while i < len(hist):
        features['hist_'+str(round(bin_edges[i]))] = hist[i]
        i += 1

    # unmap feature dictionnary for padding
    tuples = [(k, v) for k, v in features.items()]

    features = array_to_fix_size(tuples, max_size, pad_with=('*', 0))

    return features

def trace_starts_at_time0(X):

    if len(X) == 0:
        return X

    t0 = X[0][0]
    i = 0
    while i<len(X):
        X[i][0] -= t0
        i += 1

    return X

def get_features(hars):
    result = dict(feature_names=None, feature=[], label=[])

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y

    for i, url in enumerate(hars):
        samples = hars[url]
        empty_samples = [s for s in samples if len(samples[s]) == 0]

        if len(samples) < 20:
            print("Skipping", url, "only", len(samples), "samples")
            continue

        if len(empty_samples) > 5:
            print("Skipping", url, ",", len(empty_samples), "empty samples")
            continue

        for sample_id in samples:
            X = samples[sample_id]

            X = trace_starts_at_time0(X)
            f = extract_features(X)

            feature_names = [x[0] for x in f]
            feature_values = [x[1] for x in f]

            if result['feature_names'] is None:
                result['feature_names'] = feature_names
            result['features'].append(feature_values)
            result['labels'].append([url, sample_id])

    print("[feature_extract] Number of classes", len(set([y[0] for y in result['labels']])))
    print("[feature_extract] Number of features", len(result['features'][0]))
    print("[feature_extract] Number of samples", len(result['features']))
    print("[feature_extract] Number of labels", len(result['labels']))

    return result
