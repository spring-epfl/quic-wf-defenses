# standard variant

# Taken from WTF-PAD or Front/Glue, modified and fixed for non-Tor cells (with real sizes)
# Added size features

import numpy as np
import math
import sys
import traceback

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
            if p[1] <= sec: # p[1] is packet time
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


def extract_features(data, max_size=244):
    features = dict()

    if len(data) == 0:
        return array_to_fix_size([], max_size, pad_with=('*', 0))

    def quic_to_1(s):
        if s=='quic':
            return 1
        return 0

    data = [[quic_to_1(p[0]), p[1], p[2]] for p in data]

    total_number_of_packets = len(data)
    total_number_of_quic_pkts = sum([x[0] for x in data])

    features['quic_ratio'] = 0#total_number_of_quic_pkts / total_number_of_packets

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

    add_outgoing_concentrations_stats(features, data)

    add_delta_rates_stats(features, data)

    # added size features; TLS max is -16K +16k
    incoming_sizes = [-x[2] for x in incoming]
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

    t0 = X[0][1]
    i = 0
    while i<len(X):
        X[i][1] -= t0
        i += 1

    return X


def addPackets(minTime, maxTime, totalSize, maxPacketSize, direction):
    newPackets = []

    if totalSize == 0:
        return []

    remaining = totalSize
    while remaining > 0:
        t = np.random.uniform(minTime, maxTime)
        nextSize = remaining
        if nextSize > maxPacketSize:
            nextSize = maxPacketSize
        remaining -= nextSize
        newPackets.append([0, t, nextSize])

    newPackets.sort(key=lambda row: row[1])

    newPackets = [[p[0], p[1], direction*p[2]] for p in newPackets]

    return newPackets


def defend_nototalsize(trace):
    trace2 = []
    cost_bw = 0
    cost_dummies = 0

    # pad individual packets
    for x in trace:
        trace2.append([0, x[1], sign(x[2])])
        if abs(x[2]) < 1400: # only consider the cost of padding QUIC packets
            cost_bw += 1400-abs(x[2])
        else:
            pad = abs(x[2]) % 1400
            cost_bw += pad
    
    # pad total size
    sizeOut = sum([p[2] for p in trace2 if p[2]>0])
    sizeInc = sum([abs(p[2]) for p in trace2 if p[2]<0])

    padsize = 1000000 # 1 MB

    if sizeOut % padsize != 0:
        cost_bw += abs(padsize - (sizeOut%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1], abs(padsize - (sizeOut%padsize)), 1400, 1)
        trace2.extend(newPackets)

    if sizeInc % padsize != 0:
        cost_bw += abs(padsize - (abs(sizeInc)%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1], abs(padsize - (sizeInc%padsize)), 1400, -1)
        trace2.extend(newPackets)


    trace2.sort(key=lambda p: p[1])

    return trace2, cost_bw, cost_dummies


def defend_nosize(trace):
    
    trace2 = []
    cost_bw = 0
    cost_dummies = 0

    # pad individual packets
    for x in trace:
        trace2.append([0, x[1], sign(x[2])])
        if abs(x[2]) < 1400: # only consider the cost of padding QUIC packets
            cost_bw += 1400-abs(x[2])
        else:
            pad = abs(x[2]) % 1400
            cost_bw += pad
    
    return trace2, cost_bw, cost_dummies


def defend_zerodelay(trace, n_dummies=1.0):
    trace2 = []
    cost_bw = 0
    cost_dummies = 0

    for x in trace:
        trace2.append([0, x[1], sign(x[2])])
        if abs(x[2]) < 1400: # only consider the cost of padding QUIC packets
            cost_bw += 1400-abs(x[2])
        else:
            pad = abs(x[2]) % 1400
            cost_bw += pad

    n_additional = int(len(trace)*n_dummies)
    for i in range(n_additional):
        t = np.random.uniform(0, trace2[-1][1]+60)
        dir = -1
        if np.random.uniform(0, 1) > 0.5:
            dir = 1
        trace2.append([0, t, dir])
        cost_dummies += 1400
    
    if n_additional > 0:
        trace2.sort(key=lambda p: p[1])
    return trace2, cost_bw, cost_dummies

def defend_zerodelay_alsohidetotalsizeandtime(trace, n_dummies=1.0):
    
    trace2 = []
    cost_bw = 0
    cost_dummies = 0

    # pad individual packets
    for x in trace:
        trace2.append([0, x[1], sign(x[2])])
        if abs(x[2]) < 1400: # only consider the cost of padding QUIC packets
            cost_bw += 1400-abs(x[2])
        else:
            pad = abs(x[2]) % 1400
            cost_bw += pad

    # pad total size
    sizeOut = sum([p[2] for p in trace2 if p[2]>0])
    sizeInc = sum([abs(p[2]) for p in trace2 if p[2]<0])

    padsize = 1000000 # 1 MB

    if sizeOut % padsize != 0:
        cost_bw += abs(padsize - (sizeOut%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1]+60, abs(padsize - (sizeOut%padsize)), 1400, 1) # between [end, end+10s]
        trace2.extend(newPackets)

    if sizeInc % padsize != 0:
        cost_bw += abs(padsize - (abs(sizeInc)%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1]+60, abs(padsize - (sizeInc%padsize)), 1400, -1) # between [end, end+10s]
        trace2.extend(newPackets)

    n_additional = int(len(trace)*n_dummies)
    for i in range(n_additional):
        t = np.random.uniform(0, trace2[-1][1]+60)
        dir = -1
        if np.random.uniform(0, 1) > 0.5:
            dir = 1
        trace.append([0, t, dir])
    
    trace.sort(key=lambda p: p[1])
    
    incoming = [p for p in trace if p[2]<0]
    outgoing = [p for p in trace if p[2]>=0]

    if incoming[-1][1] != int(incoming[-1][1]): # pad to the next second
        trace.append([0, int(incoming[-1][1]), -1])

    if outgoing[-1][1] != int(outgoing[-1][1]): # pad to the next second
        trace.append([0, int(outgoing[-1][1]), 1])

    trace2.sort(key=lambda p: p[1])
    trace2 = [[0, 0, x[2]] for x in trace2] # then hide timings
    
    return trace2, cost_bw, cost_dummies

def defend_zerodelay_alsohidetotalsize(trace, n_dummies=1.0):
    trace2 = []
    cost_bw = 0
    cost_dummies = 0

    # pad individual packets
    for x in trace:
        trace2.append([0, x[1], sign(x[2])])
        if abs(x[2]) < 1400: # only consider the cost of padding QUIC packets
            cost_bw += 1400-abs(x[2])
        else:
            pad = abs(x[2]) % 1400
            cost_bw += pad
    
    # pad total size
    sizeOut = sum([p[2] for p in trace2 if p[2]>0])
    sizeInc = sum([abs(p[2]) for p in trace2 if p[2]<0])

    padsize = 1000000 # 1 MB

    if sizeOut % padsize != 0:
        cost_bw += abs(padsize - (sizeOut%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1], abs(padsize - (sizeOut%padsize)), 1400, 1) # between [end, end+10s]
        trace2.extend(newPackets)

    if sizeInc % padsize != 0:
        cost_bw += abs(padsize - (abs(sizeInc)%padsize))
        newPackets = addPackets(trace2[-1][1], trace2[-1][1], abs(padsize - (sizeInc%padsize)), 1400, -1) # between [end, end+10s]
        trace2.extend(newPackets)

    n_additional = int(len(trace2)*n_dummies)
    for i in range(n_additional):
        t = np.random.uniform(0, trace2[-1][1])
        dir = -1
        if np.random.uniform(0, 1) > 0.5:
            dir = 1
        trace2.append([0, t, dir])
        cost_dummies += 1400

    trace2.sort(key=lambda p: p[1])
    

    return trace2, cost_bw, cost_dummies

def defend_notiming(trace):
    return defend(trace, discard_timings=True)

def defend_nosizetiming(trace):
    return defend(trace, discard_sizes=True, discard_timings=True)
    
def defend(trace, discard_sizes=False, discard_timings=False):
    def sign(x):
        if x >= 0:
            return 1
        return -1

    if discard_sizes:
        trace = [[0, x[1], sign(x[2])] for x in trace]

    if discard_timings:
        trace = [[0, 0, x[2]] for x in trace]

    return trace, 0, 0


def build(summary_quic_tls_merged_npy, output_name=None, defense=None):
    result = dict(feature_names=None, feature=[], label=[])
    raw_data = np.load(summary_quic_tls_merged_npy, allow_pickle=True).item()

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y

    max_dur = 0

    cost_bw_tot, cost_dummies_tot = [], []

    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")

        samples = raw_data[url]["quic"]
        empty_samples = [s for s in samples if len(raw_data[url]["quic"][s]) == 0]

        #if len(samples) < 35:
        #    print("Skipping", url, "only", len(samples), "samples")
        #    continue

        #if len(empty_samples) > 5:
        #    print("Skipping", url, ",", len(empty_samples), "empty samples")
        #    continue

        cost_bw, cost_dummies = [], []

        for sample_id in samples:
            X = raw_data[url]["quic"][sample_id]

             # apply defense flow by flow for this website
            if defense is not None:
                X, cost1, cost2 = defense(X)
                cost_bw.append(np.mean(cost1))
                cost_dummies.append(np.mean(cost2))

            X = trace_starts_at_time0(X)
            f = extract_features(X)

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

        if len(cost_bw) > 0:
            cost_bw_tot.append(np.mean(cost_bw))
        if len(cost_dummies) > 0:
            cost_dummies_tot.append(np.mean(cost_dummies))


    if len(cost_bw_tot):
        print(f"Cost BW {np.mean(cost_bw_tot)} {np.std(cost_bw_tot)}")
    if len(cost_dummies_tot):
        print(f"Cost dummies {np.mean(cost_dummies_tot)} {np.std(cost_dummies_tot)}")

    try:
        np.save(output_name, result)

        print("[closed-world] Number of classes", len(set([y[0] for y in result['labels']])))
        print("[closed-world] Number of features", len(result['features'][0]))
        print("[closed-world] Number of samples", len(result['features']))
        print("[closed-world] Number of labels", len(result['labels']))

    except:
        traceback.print_exc()
        print(f"can't save {output_name}, no data")


def sign(x):
    if x >= 0:
        return 1
    return -1
