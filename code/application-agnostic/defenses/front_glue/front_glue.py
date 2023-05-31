import sys
import argparse
import configparser
import numpy as np
import glob
from os import mkdir, listdir
from os.path import join, isdir
import os
from time import strftime
import front_glue.constants as cst
import subprocess
import numpy as np
from operator import itemgetter

if True:
    sys.path.append("..")
    import utils
    import overheads

config = None
noise_files = []


def front(trace):
    global config

    client_min_dummy_pkt_num = int(config.get('client_min_dummy_pkt_num', 1))
    server_min_dummy_pkt_num = int(config.get('server_min_dummy_pkt_num', 1))
    client_dummy_pkt_num = int(config.get('client_dummy_pkt_num', 300))
    server_dummy_pkt_num = int(config.get('server_dummy_pkt_num', 300))
    start_padding_time = int(config.get('start_padding_time', 0))
    max_wnd = float(config.get('max_wnd', 10))
    min_wnd = float(config.get('min_wnd', 10))

    client_wnd = np.random.uniform(min_wnd, max_wnd)
    server_wnd = np.random.uniform(min_wnd, max_wnd)

    if client_min_dummy_pkt_num != client_dummy_pkt_num:
        client_dummy_pkt = np.random.randint(
            client_min_dummy_pkt_num, client_dummy_pkt_num)
    else:
        client_dummy_pkt = client_dummy_pkt_num
    if server_min_dummy_pkt_num != server_dummy_pkt_num:
        server_dummy_pkt = np.random.randint(
            server_min_dummy_pkt_num, server_dummy_pkt_num)
    else:
        server_dummy_pkt = server_dummy_pkt_num

    #print("client_wnd:", client_wnd)
    #print("server_wnd:", server_wnd)
    #print("client pkt:", client_dummy_pkt)
    #print("server pkt:", server_dummy_pkt)

    # LB: working for now, but careful, this assumes <0 == INCOMING
    try:
        first_incoming_pkt_time = trace[np.where(trace[:, 2] < 0)][0][1]
    except:
        first_incoming_pkt_time = 0  # lb: ugly hack
    last_pkt_time = trace[-1][1]

    client_timetable = generate_timestamps_from_noise(
        client_wnd, client_dummy_pkt)
    client_timetable = client_timetable[np.where(
        start_padding_time+client_timetable[:, 0] <= last_pkt_time)]

    server_timetable = generate_timestamps_from_noise(
        server_wnd, server_dummy_pkt)
    server_timetable[:, 0] += first_incoming_pkt_time
    server_timetable = server_timetable[np.where(
        start_padding_time+server_timetable[:, 0] <= last_pkt_time)]

    # print("client_timetable")
    # print(client_timetable[:10])

    client_pkts = np.concatenate(
        (np.ones((len(client_timetable), 1)), client_timetable, cst.PADDED_SIZE_QUIC * np.ones((len(client_timetable), 1))), axis=1)
    server_pkts = np.concatenate(
        (np.ones((len(server_timetable), 1)), server_timetable, -cst.PADDED_SIZE_QUIC * np.ones((len(server_timetable), 1))), axis=1)

    noisy_trace = np.concatenate(
        (trace, client_pkts, server_pkts), axis=0).tolist()
    noisy_trace.sort(key=itemgetter(1))
    return noisy_trace


def generate_timestamps_from_noise(wnd, num):
    # timestamps = sorted(np.random.exponential(wnd/2.0, num))
    # print(wnd, num)
    # timestamps = sorted(abs(np.random.normal(0, wnd, num)))
    timestamps = sorted(np.random.rayleigh(wnd, num))
    # print(timestamps[:5])
    # timestamps = np.fromiter(map(lambda x: x if x <= wnd else wnd, timestamps),dtype = float)
    return np.reshape(timestamps, (len(timestamps), 1))


def estimate_interarrivaltime(trace):
    trace_1 = np.concatenate((trace[1:], trace[0:1]), axis=0)
    itas = trace_1[:-1, 1] - trace[:-1, 1]
    return np.random.uniform(np.percentile(itas, 20), np.percentile(itas, 80))


def find_random_trace_to_glue():
    global noise_files

    noise_file = np.random.choice(noise_files, 1)[0]
    Xs, ys = np.load(noise_files[0], allow_pickle=True)
    return Xs[0]


def glue(trace, mean_dwell_time=10):
    # LB: note: mean dwell time is U[1,10] in the paper, =20 in implementation

    noise = find_random_trace_to_glue()

    dwell_time = np.random.uniform(mean_dwell_time, mean_dwell_time+5)

    # used as a short pause between [trace] and [noise]
    small_time = estimate_interarrivaltime(trace)
    # first, cut noise between [0, cutoff], then shift everything by last_packet_t + IAT
    cutoff = dwell_time-small_time+0.5
    last_packet_t = trace[-1][1]
    t_shift = last_packet_t + small_time

    noise = [p for p in noise if p[1] <= cutoff]
    noise_shifted = [[p[0], p[1]+t_shift, p[2]] for p in noise]

    defended = np.concatenate((trace, noise_shifted), axis=0).tolist()

    defended.sort(key=itemgetter(0))

    return defended


def process_file(params):
    global config

    path_in, path_out = params
    print("[front/glue] Processing file %s" % path_in, end='\r')

    Xs, ys = np.load(path_in, allow_pickle=True)

    Xs_def = []
    overhead = []

    count = len(Xs)
    i = 0
    while i < count:
        X = Xs[i]

        front_defended = front(np.array(X))
        glued = glue(np.array(front_defended))
        X_def = [[x[0], x[1], round(x[2])] for x in glued]

        bw, lat = overheads.get_overhead_for_defense(Xs[i], X_def)
        Xs_def.append(X_def)

        overhead.append(dict(bw=bw, lat=lat))
        i += 1

    np.save(path_out, (Xs_def, ys))
    return overhead


def run(input_folder, output_folder):
    global config, noise_files

    # read .ini
    conf_parser = configparser.RawConfigParser()
    conf_parser.read(cst.CONFIG_FILE)
    config = conf_parser._sections['default']

    # prepare folders
    clean(output_folder)
    subprocess.run(["mkdir", "-p", output_folder])
    sources_files = glob.glob(input_folder+"*")
    noise_files = sources_files

    input_output_pairs = [(f, utils.str_replace_for_path(f, input_folder, output_folder))
                          for f in sources_files]

    process_file(input_output_pairs[0])
    data = utils.parallel(input_output_pairs, process_file)

    oh_deep = utils.parallel(input_output_pairs, process_file)

    # flatten
    oh_flatten = []
    for oh in oh_deep:
        oh_flatten.extend(oh)

    np.save('overheads', oh_flatten)

    return overheads.summarise_overhead_for_defense(oh_flatten)


def clean(outpath):
    subprocess.run(["rm", "-rf", outpath])


if __name__ == "__main__":
    dataset = sys.argv[1]
    if not dataset.endswith("/"):
        dataset += '/'

    # todo fix
    clean()
    run()
