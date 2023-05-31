import os
import numpy as np
import sys
import matplotlib.pyplot as plt
import json
import overheads as oh
import pathlib

PADDED_SIZE_QUIC = 1400

def mean_and_95p(data):
    mean = np.mean(data)
    std = np.std(data)
    p95 = 1.645 * std
    return mean, p95

def makedirs(d):
    path = pathlib.Path(d)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.mkdir(d)
    except:
        pass

def pad_quic_to_max_size(X):
    X_copy = []
    for packet in X:
        protocol, time, size = packet
        if protocol == 'quic':
            if size < 0:
                size = -PADDED_SIZE_QUIC
            else:
                size = PADDED_SIZE_QUIC
            X_copy.append([protocol, time, size])
        else:
            # break up TLS packets
            sign = 1
            if packet[2] < 0:
                sign = -1
            size = abs(size)

            while size > PADDED_SIZE_QUIC:
                X_copy.append([protocol, time, sign*PADDED_SIZE_QUIC])
                size -= PADDED_SIZE_QUIC
            X_copy.append([protocol, time, sign*PADDED_SIZE_QUIC])
    
    return X_copy


def apply_defense(folder_in, folder_out, datasets_folder='../../cf-clusters-datasets/'):
    makedirs(datasets_folder+folder_out + "/npys/")
    npy_in = datasets_folder+folder_in+"/npys/summary_quic_tls_merged.npy"
    npy_out = datasets_folder+folder_out + "/npys/summary_quic_tls_merged.npy"

    if os.path.isfile(npy_out):
        #print("Skipping", npy_out)
        #return
        pass

    dataset = np.load(npy_in, allow_pickle=True).item()
    
    overhead = dict()
    defended_traces = dict()

    for website in dataset:
        defended_traces[website] = dict(quic=dict())
        overhead[website] = dict(quic=dict())

        for sample in dataset[website]['quic']:
            trace = dataset[website]['quic'][sample]

            trace_def = pad_quic_to_max_size(trace)
            bw, lat = oh.get_overhead_for_defense(trace, trace_def)

            overhead[website]['quic'][sample] = dict(bw=bw, lat=lat)
            defended_traces[website]['quic'][sample] = trace_def

    oh_flat = []
    for website in overhead:
        for sample in overhead[website]['quic']:
            oh_flat.append(overhead[website]['quic'][sample])
            
    oh_summarized = oh.summarise_overhead_for_defense(oh_flat)

    np.save(npy_out, defended_traces)
    np.save(datasets_folder+folder_out+"/overheads.npy", overhead)
    with open(datasets_folder+folder_out+"/overheads.txt", "w") as f:
        s = "overhead: {:.2f}% QUIC and {:.2f}% TLS bandwidth, {:.2f}s latency".format(
        100 * oh_summarized[0][0], 100 * oh_summarized[0][1], oh_summarized[1])
        f.write(s)
        print(s)

    return defended_traces, overhead

#apply_defense('cluster-150-3', 'cluster-150-3-pad')
#apply_defense('cluster-203-2', 'cluster-203-2-pad')
apply_defense('quic-100p-338', 'quic-100p-338-pad')
apply_defense('quic-100p-338-AS-view', 'quic-100p-338-AS-view-pad')
