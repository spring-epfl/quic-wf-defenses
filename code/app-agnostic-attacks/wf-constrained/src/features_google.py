# a more limited version with less features

import numpy as np
import pandas as pd
import sys


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


def split_incoming_outgoing(data):
    incoming = []
    outgoing = []
    for p in data:
        isIncoming = (p[2] < 0) # p[2] is size
        if isIncoming:
            incoming.append(p)
        else:
            outgoing.append(p)
    return incoming, outgoing


def get_packet_inter_times(data):
    if len(data) == 0:
        return [0]
    times = [x[1] for x in data]
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

    incoming_times = [x[1] for x in incoming]
    outgoing_times = [x[1] for x in outgoing]
    times = [x[1] for x in data]

    add_percentiles(incoming_times, 'incoming_')
    add_percentiles(outgoing_times, 'outgoing_')
    add_percentiles(times, '')

    features['times_sum'] = sum(times)


def add_counts_in_out_last_first_30(features, data):
    # counts (incoming, outgoing) packets in the (first, last) 30 packets

    first30 = data[:30]
    last30 = data[-30:]
    first30in = []
    first30out = []
    for p in first30:
        if p[2] < 0: # incoming
            first30in.append(p)
        if p[2] >= 0:
            first30out.append(p)
    last30in = []
    last30out = []
    for p in last30:
        if p[2] < 0: # incoming
            last30in.append(p)
        if p[2] >= 0:
            last30out.append(p)

    features['f30_n_incoming'] = len(first30in)
    features['f30_n_outgoing'] = len(first30out)
    features['l30_n_incoming'] = len(last30in)
    features['l30_n_outgoing'] = len(last30out)

def add_average_pkt_ordering(features, data):
    # counts the cumulative number of (incoming, outgoing) packet for a given time

    def add_stats(trace, suffix=''):
        if len(trace) == 0:
            features['order_avg'+suffix] = 0
            features['order_std'+suffix] = 0
        else:
            features['order_avg'+suffix] = average(trace)
            features['order_std'+suffix] = np.std(trace)

    c_out = 0
    c_in = 0
    outgoing = []
    incoming = []
    for p in data:
        if p[2] >= 0: # outgoing
            outgoing.append(c_out)
            c_out += 1
        if p[2] < 0:
            incoming.append(c_in)
            c_in += 1

    add_stats(outgoing, '_out')
    add_stats(incoming, '_in')



def extract_features_Google(data, max_size=43):
    features = dict()


    if len(data) == 0:
        return array_to_fix_size([], max_size, pad_with=('*', 0))

    incoming, outgoing = split_incoming_outgoing(data)
    features['n_incoming'] = len(incoming)
    features['n_outgoing'] = len(outgoing)
    features['n_total'] = len(data)
    features['%_in'] = len(incoming) / float(len(data))
    features['%_out'] = len(outgoing) / float(len(data))

    features['bytes_incoming'] = sum([d[2] for d in incoming])
    features['bytes_outgoing'] = sum([d[2] for d in outgoing])
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
    add_average_pkt_ordering(features, data)

    #add_outgoing_concentrations_stats(features, data)

    #add_delta_rates_stats(features, data)

    # unmap feature dictionnary for padding
    tuples = [(k, v) for k, v in features.items()]
    features = array_to_fix_size(tuples, max_size, pad_with=('*', 0))

    return features


def features_from_trace(trace, discard_sizes=False, discard_packet_type=False, discard_timings=False):
    def sign(x):
        if x >= 0:
            return 1
        return -1

    if discard_sizes:
        trace = [[x[0], x[1], sign(x[2])] for x in trace]

    if discard_packet_type:
        trace = [[0, x[1], x[2]] for x in trace]

    if discard_timings:
        trace = [[x[0], 0, x[2]] for x in trace]
        
    return extract_features(trace)

def trace_starts_at_time0(X):
    if len(X) == 0:
        return X

    t0 = X[0][1]
    i = 0
    while i<len(X):
        X[i][1] -= t0
        i += 1

    return X

def trace_starts_at_time0_netflows(X):
    if len(X) == 0:
        return X

    t0 = X[0]['t_first']
    i = 0
    while i<len(X):
        X[i]['t_first'] -= t0
        i += 1

    return X

def build(summary_quic_tls_merged_npy, output_name=None):

    result = dict(feature_names=None, feature=[], label=[])
    raw_data = np.load(summary_quic_tls_merged_npy, allow_pickle=True).item()

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y

    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")

        samples = raw_data[url]["quic"]
        empty_samples = [s for s in samples if len(raw_data[url]["quic"][s]) == 0]

        if len(samples) < 35:
            print("Skipping", url, "only", len(samples), "samples")
            continue

        if len(empty_samples) > 5:
            print("Skipping", url, ",", len(empty_samples), "empty samples")
            continue

        for sample_id in samples:
            X = raw_data[url]["quic"][sample_id]

            X = trace_starts_at_time0(X)
            f = features_from_trace(X)

            feature_names = [x[0] for x in f]
            feature_values = [x[1] for x in f]

            # NaN check
            if np.any(np.isnan(feature_values)):
                for i, v in enumerate(feature_values):
                    if np.isnan(v):
                        print("ALERT: you've got NaNs.")
                        print(feature_names[i])
                        print(feature_values[i])
                        sys.exit(1)
            
            if result['feature_names'] is None:
                result['feature_names'] = feature_names
            result['features'].append(feature_values)
            result['labels'].append([url, sample_id])

    print("[closed-world] Number of classes", len(set([y[0] for y in result['labels']])))
    print("[closed-world] Number of features", len(result['features'][0]))
    print("[closed-world] Number of samples", len(result['features']))
    print("[closed-world] Number of labels", len(result['labels']))

    np.save(output_name, result)


def build_netflow(summary_quic_tls_merged_npy, output_name=None):

    result = dict(feature_names=None, feature=[], label=[])
    raw_data = np.load(summary_quic_tls_merged_npy, allow_pickle=True).item()

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y


    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")

        samples = raw_data[url]["quic"]

        if len(samples) < 40:
            print("Skipping", url, "only", len(samples), "samples")
            continue

        for sample_id in samples:
            X = raw_data[url]["quic"][sample_id]

            X = trace_starts_at_time0_netflows(X)
            f = extract_features_netflow(X)

            feature_names = [x[0] for x in f]
            feature_values = [x[1] for x in f]

            # NaN check
            if np.any(np.isnan(feature_values)):
                for i, v in enumerate(feature_values):
                    if np.isnan(v):
                        print("ALERT: you've got NaNs.")
                        print(feature_names[i])
                        print(feature_values[i])
                        sys.exit(1)
            
            if result['feature_names'] is None:
                result['feature_names'] = feature_names
            result['features'].append(feature_values)
            result['labels'].append([url, sample_id])

    print("[closed-world] Number of classes", len(set([y[0] for y in result['labels']])))
    print("[closed-world] Number of features", len(result['features'][0]))
    print("[closed-world] Number of samples", len(result['features']))
    print("[closed-world] Number of labels", len(result['labels']))

    np.save(output_name, result)

def sign(x):
    if x >= 0:
        return 1
    return -1


def build_Google_variant(summary_quic_tls_merged_npy, output_name=None):

    result = dict(feature_names=None, feature=[], label=[])
    raw_data = np.load(summary_quic_tls_merged_npy, allow_pickle=True).item()

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y

    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")

        if url not in allow_list:
            continue


        samples = raw_data[url]["quic"]

        if len(samples) < 40:
            print("Skipping", url, "only", len(samples), "samples")
            continue

        for sample_id in samples:
            X = raw_data[url]["quic"][sample_id]

            X = trace_starts_at_time0(X)

            X = [[0, x[1], sign(x[2])] for x in X] # remove type and size
                
            f = extract_features_Google(X)

            feature_names = [x[0] for x in f]
            feature_values = [x[1] for x in f]

            # NaN check
            if np.any(np.isnan(feature_values)):
                for i, v in enumerate(feature_values):
                    if np.isnan(v):
                        print("ALERT: you've got NaNs.")
                        print(feature_names[i])
                        print(feature_values[i])
                        sys.exit(1)
            
            if result['feature_names'] is None:
                result['feature_names'] = feature_names
            result['features'].append(feature_values)
            result['labels'].append([url, sample_id])

    print("[closed-world] Number of classes", len(set([y[0] for y in result['labels']])))
    print("[closed-world] Number of features", len(result['features'][0]))
    print("[closed-world] Number of samples", len(result['features']))
    print("[closed-world] Number of labels", len(result['labels']))

    np.save(output_name, result)
