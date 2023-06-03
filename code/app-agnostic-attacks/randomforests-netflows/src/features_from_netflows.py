# Taken from WTF-PAD or Front/Glue, modified and fixed for non-Tor cells (with real sizes)
# Added size features

import numpy as np
import math
import sys
import datetime


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

def get_flows_inter_times(data):
    if len(data) == 0:
        return [0]
    times = [x['t'] for x in data]
    result = []
    for elem, next_elem in zip(times, times[1:] + [times[0]]):
        result.append(next_elem - elem)
    return result[:-1]


def add_netflow_intertimes_stats(features, data, incoming, outgoing):
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

    incoming_intertimes = get_flows_inter_times(incoming)
    outgoing_intertimes = get_flows_inter_times(outgoing)
    all_intertimes = get_flows_inter_times(data)

    add_stats(incoming_intertimes, 'incoming_')
    add_stats(outgoing_intertimes, 'outgoing_')
    add_stats(all_intertimes, '')


def add_netflow_time_percentiles(features, data, incoming, outgoing):
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

    incoming_times = [x['t'] for x in incoming]
    outgoing_times = [x['t'] for x in outgoing]
    times = [x['t'] for x in data]

    add_percentiles(incoming_times, 'incoming_')
    add_percentiles(outgoing_times, 'outgoing_')
    add_percentiles(times, '')

    features['times_sum'] = sum(times)



def add_netflow_counts_in_out_last_first_30(features, data):
    # counts (incoming, outgoing) packets in the (first, last) 30 packets

    first30 = data[:30]
    last30 = data[-30:]
    first30in = []
    first30out = []
    for p in first30:
        if p['direction'] < 0: # incoming
            first30in.append(p)
        if p['direction'] >= 0:
            first30out.append(p)
    last30in = []
    last30out = []
    for p in last30:
        if p['direction'] < 0: # incoming
            last30in.append(p)
        if p['direction'] >= 0:
            last30out.append(p)

    features['f30_n_incoming'] = len(first30in)
    features['f30_n_outgoing'] = len(first30out)
    features['l30_n_incoming'] = len(last30in)
    features['l30_n_outgoing'] = len(last30out)


def add_netflow_outgoing_concentrations_stats(features, data):
    # concentration of outgoing packets in chunks of 5 packets

    chunks = [data[x: x + 5] for x in range(0, len(data), 5)]
    concentrations = []
    for item in chunks:
        c = 0
        for p in item:
            if p['direction'] >= 0: # outgoing packets
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


def add_netflow_delta_rates_stats(features, data):
    # Average number packets sent and received per second

    last_time = data[-1]['t']
    last_second = math.ceil(last_time)

    count_per_sec = []
    for sec in range(1, int(last_second) + 1):
        count = 0
        for p in data:
            if p['t'] <= sec: # p[1] is packet time
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


def add_netflow_average_pkt_ordering(features, data):
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
        if p['direction'] >= 0: # outgoing
            outgoing.append(c_out)
            c_out += 1
        if p['direction'] < 0:
            incoming.append(c_in)
            c_in += 1

    add_stats(outgoing, '_out')
    add_stats(incoming, '_in')

def extract_features_netflow(data, max_size=172):
    features = dict()

    if len(data) == 0:
        return array_to_fix_size([], max_size, pad_with=('*', 0))


    for d in data:
        d['t'] = d['t_first'].total_seconds()

    incoming = [d for d in data if d['direction'] == -1]
    outgoing = [d for d in data if d['direction'] == 1]

    features['n_incoming'] = sum([d['packets'] for d in incoming])
    features['n_outgoing'] = sum([d['packets'] for d in outgoing])
    features['n_total'] = features['n_incoming'] + features['n_outgoing']
    if features['n_total'] > 0:
        features['%_in'] = features['n_incoming'] / float(features['n_total'])
        features['%_out'] = features['n_outgoing'] / float(features['n_total'])
    else:
        features['%_in'] = 0
        features['%_out'] = 0

    
    features['bytes_incoming'] = sum([d['bytes'] for d in incoming])
    features['bytes_outgoing'] = sum([d['bytes'] for d in outgoing])
    features['bytes_total'] = features['bytes_incoming'] + features['bytes_outgoing']
    if features['bytes_total'] > 0:
        features['bytes_%_in'] = features['bytes_incoming'] / float(features['bytes_total'])
        features['bytes_%_out'] = features['bytes_outgoing'] / float(features['bytes_total'])
    else:
        features['bytes_%_in'] = 0
        features['bytes_%_out'] = 0

    add_netflow_intertimes_stats(features, data, incoming, outgoing)
    add_netflow_time_percentiles(features, data, incoming, outgoing)
    add_netflow_counts_in_out_last_first_30(features, data)
    add_netflow_average_pkt_ordering(features, data)

    add_netflow_outgoing_concentrations_stats(features, data)

    add_netflow_delta_rates_stats(features, data)

    # added size features; TLS max is -16K +16k
    incoming_sizes = [-x['bytes'] for x in incoming]
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



def trace_starts_at_time0_netflows(X):
    if len(X) == 0:
        return X

    t0 = X[0]['t_first']
    i = 0
    while i<len(X):
        X[i]['t_first'] -= t0
        i += 1

    return X


def npot(x):
    return 2**math.ceil(math.log(x, 2))

def padme(L):
    if L < 3:
        return int(L)
    E = math.floor(math.log(L, 2))
    S = math.floor(math.log(E, 2))+1
    lastBits = E-S
    bitMask = (2 ** lastBits - 1)
    return (L + bitMask) & ~bitMask



def defend_nosize(X):
    for f in X:
        f['bytes'] = 0
        f['packets'] = 0
    return X, 0



def newNetflow(time, direction, packets, bytes):
    src='x'
    dst='x'
    if direction == -1:
        dst='10.1.1.1'
    else:
        src='10.1.1.1'
    return {'t_first': time, 't_last': time + datetime.timedelta(seconds=1), 'direction': direction, 'src': src, 'dst': dst, 'packets': packets, 'bytes': bytes, 'proto': 0}

def defend_nototalsize(X, paddedPackets=10000, paddedBytes=10000):

    if len(X) == 0:
        return X, 0
    
    totsizeinc = 0
    totpacketsinc = 0
    totsizeout = 0
    totpacketsout = 0
    last_time = None

    cost_bw = []

    # count the sizes
    flows_out = 0
    flows_in = 0

    for f in X:
        if f['direction'] == -1:
            totsizeinc += f['bytes']
            totpacketsinc += f['packets']
            flows_in += 1
        else:
            totsizeout += f['bytes']
            totpacketsout += f['packets']
            flows_out += 1

    # pad to the following multiples

    totpacketsout_padremaining = paddedPackets - totpacketsout%paddedPackets
    totpacketsin_padremaining = paddedPackets - totpacketsinc%paddedPackets

    totbytesout_padremaining = paddedBytes - totsizeout%paddedBytes
    totbytesin_padremaining = paddedBytes - totsizeinc%paddedBytes

    totpacketsout_step = 0
    totpacketsin_step = 0
    totbytesout_step = 0
    totbytesin_step = 0

    if flows_out > 0:
        totpacketsout_step = int(math.floor(float(totpacketsout_padremaining)/flows_out))
        totbytesout_step = int(math.floor(float(totbytesout_padremaining)/flows_out))

    if flows_in > 0:
        totpacketsin_step = int(math.floor(float(totpacketsin_padremaining)/flows_in))
        totbytesin_step = int(math.floor(float(totbytesin_padremaining)/flows_in))

    for f in X:
        if f['direction'] == -1:
            f['bytes'] += totbytesin_step
            f['packets'] += totpacketsin_step

            totbytesin_padremaining -= totbytesin_step
            totpacketsin_padremaining -= totpacketsin_step

        else:
            f['bytes'] += totbytesout_step
            f['packets'] += totpacketsout_step

            totbytesout_padremaining -= totbytesout_step
            totpacketsout_padremaining -= totpacketsout_step

        # we don't want proto to help the classifier (even if in practice it might)
        f['proto'] = 0

        # for now, let's say all netflows' duration is padded
        duration = f['t_last'] - f['t_first']
        dur_s = duration.total_seconds()
        padded_dur = 1.0 # s
        new_duration = dur_s + padded_dur - dur_s%padded_dur
        f['t_last'] = f['t_first'] + datetime.timedelta(seconds=new_duration) # datetime.timedelta(seconds=new_duration)
        last_time = f['t_last']

    # add to one
    if totbytesout_padremaining > 0:
        for f in X:
            if f['direction'] != -1:
                f['bytes'] += totbytesout_padremaining
                f['packets'] += totpacketsout_padremaining

                totbytesout_padremaining -= totbytesout_padremaining
                totpacketsout_padremaining -= totpacketsout_padremaining
                break
                # screw these costs

    # if does not exist create flow
    if totbytesout_padremaining > 0:
        X.append(newNetflow(X[0]['t_first'], 1, totpacketsout_padremaining, totbytesout_padremaining))

    # add to one
    if totbytesin_padremaining > 0:
        for f in X:
            if f['direction'] == -1:
                f['bytes'] += totbytesin_padremaining
                f['packets'] += totpacketsin_padremaining

                totbytesin_padremaining -= totbytesin_padremaining
                totpacketsin_padremaining -= totpacketsin_padremaining
                break
                # screw these costs
    # if does not exist create flow
    if totbytesout_padremaining > 0:
        X.append(newNetflow(X[0]['t_first'], -1, totpacketsin_padremaining, totbytesin_padremaining))

    psize, ppacket = 0, 0
    for f in X:
        if f['direction'] != -1:
            psize += f['bytes']
            ppacket += f['packets']
        
    #print(f"Padded: {psize} {ppacket}")

    psize, ppacket = 0, 0
    for f in X:
        if f['direction'] == -1:
            psize += f['bytes']
            ppacket += f['packets']
        
    #print(f"Padded: {psize} {ppacket}")

    return X, (paddedBytes - totsizeout%paddedBytes) + (paddedBytes - totsizeinc%paddedBytes)



def defend_netflow(X):

    for f in X:
        # pad overall size
        f['bytes'] = npot(f['packets'])

        # not quite sure what to do yet with n_packets
        f['packets'] = npot(f['packets'])

        # we don't want proto to help the classifier (even if in practice it might)
        f['proto'] = 0

        # for now, let's say all netflows' duration is padded
        duration = f['t_last'] - f['t_first']
        dur_s = duration.total_seconds()
        padded_dur = 1.0 # s
        new_duration = dur_s + padded_dur - dur_s%padded_dur
        #f2['t_last'] = f2['t_first'] + datetime.timedelta(seconds=100) # datetime.timedelta(seconds=new_duration)

    return X, 0

def build_netflow(summary_quic_tls_merged_npy, output_name=None, defense=None):

    result = dict(feature_names=None, feature=[], label=[])
    raw_data = np.load(summary_quic_tls_merged_npy, allow_pickle=True).item()

    result = dict()
    result['feature_names'] = None
    result['features'] = [] #X
    result['labels'] = [] #y

    costs = []

    max_nbytes = 0
    max_npackets = 0
    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")

        samples = raw_data[url]["quic"]

        for sample_id in samples:
            X = raw_data[url]["quic"][sample_id]
            totB = 0
            totP = 0
            for flow in X:
                totB += flow['bytes']
                totP += flow['packets']
            
            if totB>max_nbytes:
                max_nbytes = totB
            if totP > max_npackets:
                max_npackets = totP

    print(f"{output_name}, max bytes {max_nbytes} max packets {max_npackets}")
                

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

            # apply defense flow by flow for this website
            if defense is not None:
                X, cost = defense(X)
                costs.append(cost)

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
    print(f"Cost for {summary_quic_tls_merged_npy} [B/trace]:", np.mean(costs), np.var(costs))


    np.save(output_name, result)

def sign(x):
    if x >= 0:
        return 1
    return -1
