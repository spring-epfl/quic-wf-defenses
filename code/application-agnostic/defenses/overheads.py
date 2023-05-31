# Taken from https://github.com/websitefingerprinting/WebsiteFingerprinting and adapted

import os
import sys
import numpy as np


def duration(trace):
    if len(trace) < 2:
        return 0.0

    # return last timestamp - first timestamp
    return trace[-1][1] - trace[0][1]


def bandwidth(trace):
    quic_packets = [p for p in trace if p[0] == 'quic']
    tls_packets = [p for p in trace if p[0] == 'tls']
    total_quic = sum([abs(p[2]) for p in quic_packets])
    total_tls = sum([abs(p[2]) for p in tls_packets])

    return total_quic, total_tls


def ratio_or_0(a, b):
    if b == 0.0:
        return 0
    return 1.0 * a/b


def bandwidth_ovhd(old, new):
    cost_old = bandwidth(old)
    cost_new = bandwidth(new)

    overheads = [0] * 2
    for i in range(2):
        overheads[i] = ratio_or_0(cost_new[i], cost_old[i])

    return overheads


def latency_ovhd(new, old):
    lat_old = duration(old)
    if lat_old == 0.0:
        return 0.0
    return 1.0 * duration(new) / lat_old


def get_overhead_for_defense(original, defended):
    bw = bandwidth_ovhd(original, defended)
    lat = latency_ovhd(original, defended)
    return bw, lat


def summarise_overhead_for_defense(overhead_pairs):
    bandwidths = [o['bw'] for o in overhead_pairs]
    latencies = [o['lat'] for o in overhead_pairs]

    med_bws = [0] * 2
    for i in range(2):
        bw = [b[i] for b in bandwidths if b[i] > 0.0]
        if len(bw) > 0:
            med_bws[i] = np.median(bw)
    med_lat = np.median([l for l in latencies if l > 0.0])

    return med_bws, med_lat
