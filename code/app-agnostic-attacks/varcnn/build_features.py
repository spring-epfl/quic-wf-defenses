import sys
import os
import numpy as np
import random
from sklearn.preprocessing import StandardScaler
import h5py
from keras.utils.np_utils import to_categorical
import json
import time
import constants as cst


def extract_features_and_sec(packets):
    """Extract dir seq, time seq, metadata for particular trace."""

    dir_seq = np.zeros(5000, dtype=np.int8)
    time_seq = np.zeros(5000, dtype=np.float32)
    metadata = np.zeros(7, dtype=np.float32)

    if len(packets) == 0:
        return dir_seq, time_seq, metadata

    total_time = float(packets[-1][1])
    total_incoming = 0
    total_outgoing = 0

    for i, packet in enumerate(packets):
        curr_time = float(packet[1])
        curr_dir = np.sign(int(packet[2]))

        if i < 5000:
            dir_seq[i] = curr_dir
            time_seq[i] = curr_time

        if curr_dir == 1:
            total_outgoing += 1
        elif curr_dir == -1:
            total_incoming += 1

    total_packets = total_incoming + total_outgoing
    if total_packets == 0:
        metadata = np.zeros(7, dtype=np.float32)
    else:
        metadata = np.array([total_packets, total_incoming, total_outgoing,
                             total_incoming / total_packets,
                             total_outgoing / total_packets,
                             total_time, total_time / total_packets],
                            dtype=np.float32)
    return dir_seq, time_seq, metadata

def label_str_to_i(labels):
    mapping = dict()
    i = 0
    for l in labels:
        if l in mapping:
            continue
        mapping[l] = i
        i += 1

    return [mapping[l] for l in labels], mapping

def create_npy(input_npy, output_npy, config_template):
    raw_data = np.load(input_npy, allow_pickle=True).item()

    urls = list(raw_data.keys()) # copy to allow editing while looping
    for url in urls:
        samples = raw_data[url]['quic']
        if len(samples) < 40:
            print("Skipping", url, "only", len(samples), "samples")
            del raw_data[url]

    num_mon_sites = len(raw_data)
    n_samples = 999999
    for url in raw_data:
        n_samples = min(n_samples, len(raw_data[url]['quic']))

    num_mon_inst_test = int(n_samples * cst.TEST_PERCENTAGE)
    num_mon_inst_train = n_samples - num_mon_inst_test

    print(f"Min number of samples {n_samples}, {num_mon_sites} sites")

    num_mon_inst = num_mon_inst_test + num_mon_inst_train
    num_unmon_sites = 0
    
    # set up the output
    mon_idx = 0
    dir_seq_mon = [None] * (num_mon_sites * num_mon_inst)
    time_seq_mon = [None] * (num_mon_sites * num_mon_inst)
    metadata_mon = [None] * (num_mon_sites * num_mon_inst)
    labels_mon = [None] * (num_mon_sites * num_mon_inst)

    unmon_idx = 0
    dir_seq_unmon = [None] * num_unmon_sites
    time_seq_unmon = [None] * num_unmon_sites
    metadata_unmon = [None] * num_unmon_sites
    labels_unmon = [None] * num_unmon_sites

    _, labels_map = label_str_to_i([url for url in raw_data])


    # write config for varcnn
    config = dict()
    for k in config_template:
        config[k] = config_template[k]

    num_unmon_sites_train = 0
    num_unmon_sites_test = 0
    
    config['num_mon_sites'] = num_mon_sites
    config['num_mon_inst_test'] = num_mon_inst_test
    config['num_mon_inst_train'] = num_mon_inst_train
    config['num_unmon_sites_test'] = num_unmon_sites_train
    config['num_unmon_sites_train'] = num_unmon_sites_test
    # unimportant. renaming files to match what cnnvar looks for
    config['h5file'] = '%s%d_%d_%d_%d.h5' % (config['data_dir'], num_mon_sites, num_mon_inst, num_unmon_sites_train, num_unmon_sites_test)
    
    with open(output_npy+'.config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # create npy

    for i, url in enumerate(raw_data):
        print(f"[{i}] Processing {url}...", end="\r")
        for sample in raw_data[url]['quic']:
            packets = raw_data[url]['quic'][sample]
            dir_seq, time_seq, metadata = extract_features_and_sec(packets)

            if False: #label == 0:  # unmon site
                dir_seq_unmon[unmon_idx] = dir_seq
                time_seq_unmon[unmon_idx] = time_seq
                metadata_unmon[unmon_idx] = metadata
                labels_unmon[unmon_idx] = "unmon"
                unmon_idx += 1
            else:
                dir_seq_mon[mon_idx] = dir_seq
                time_seq_mon[mon_idx] = time_seq
                metadata_mon[mon_idx] = metadata
                labels_mon[mon_idx] = labels_map[url]
                mon_idx += 1

    # save monitored traces
    dir_seq_mon = np.array(dir_seq_mon, dtype=np.int8)
    time_seq_mon = np.array(time_seq_mon, dtype=np.float32)
    metadata_mon = np.array(metadata_mon, dtype=np.float32)

    print('number of monitored traces: %d' % len(labels_mon))
    np.save(output_npy, dict(dir_seq=dir_seq_mon,
                        time_seq=time_seq_mon, metadata=metadata_mon,
                        labels=labels_mon, labels_map=labels_map))


    return config

    # save unmonitored traces
    dir_seq_unmon = np.array(dir_seq_unmon, dtype=np.int8)
    time_seq_unmon = np.array(time_seq_unmon, dtype=np.float32)
    metadata_unmon = np.array(metadata_unmon, dtype=np.float32)

    print('number of unmonitored traces: %d' % len(labels_unmon))
    np.savez_compressed(data_dir + 'all_open_world.npz', dir_seq=dir_seq_unmon,
                        time_seq=time_seq_unmon, metadata=metadata_unmon,
                        labels=labels_unmon)



def create_h5(config, input_npy, h5_out):
    data = np.load(input_npy, allow_pickle=True).item()

    mon_dir_seq = data['dir_seq']
    mon_time_seq = data['time_seq']
    mon_metadata = data['metadata']
    mon_labels = data['labels']
    labels_map = data['labels_map']
    
    num_mon_sites = config['num_mon_sites']
    num_mon_inst_test = config['num_mon_inst_test']
    num_mon_inst_train = config['num_mon_inst_train']
    num_mon_inst = num_mon_inst_test + num_mon_inst_train
    num_unmon_sites_test = config['num_unmon_sites_test']
    num_unmon_sites_train = config['num_unmon_sites_train']
    num_unmon_sites = num_unmon_sites_test + num_unmon_sites_train
    data_dir = config['data_dir']

    inter_time = config['inter_time']
    scale_metadata = config['scale_metadata']


    print(f"Starting {h5_out}")
    start = time.time()

    train_seq_and_labels = []
    test_seq_and_labels = []
    print('reading monitored data')
    
    start = time.time()

    mon_site_data = {}
    mon_site_labels = {}

    print('getting enough monitored websites')
    for dir_seq, time_seq, metadata, site_name in zip(mon_dir_seq, mon_time_seq, mon_metadata, mon_labels):
        if site_name not in mon_site_data:
            if len(mon_site_data) >= num_mon_sites:
                continue
            else:
                mon_site_data[site_name] = []
                mon_site_labels[site_name] = len(mon_site_labels)

        mon_site_data[site_name].append(
            [dir_seq, time_seq, metadata, mon_site_labels[site_name]])

    print('randomly choosing instances for training and test sets')
    assert len(mon_site_data) == num_mon_sites
    for instances in mon_site_data.values():
        random.shuffle(instances)
        assert len(instances) >= num_mon_inst
        for inst_num, all_data in enumerate(instances):
            if inst_num < num_mon_inst_train:
                train_seq_and_labels.append(all_data)
            elif inst_num < num_mon_inst:
                test_seq_and_labels.append(all_data)
            else:
                break

    del mon_dir_seq, mon_time_seq, mon_metadata, mon_labels, mon_site_data, mon_site_labels

    print('reading unmonitored data')

    # LB: we don't have any unmonitored data
    unmon_dataset = dict(dir_seq=[], time_seq=[], metadata=[]) #np.load(unmon_data_loc)
    unmon_dir_seq = unmon_dataset['dir_seq']
    unmon_time_seq = unmon_dataset['time_seq']
    unmon_metadata = unmon_dataset['metadata']

    unmon_site_data = [[dir_seq, time_seq, metadata, num_mon_sites] for
                       dir_seq, time_seq, metadata in
                       zip(unmon_dir_seq, unmon_time_seq, unmon_metadata)]

    random.shuffle(unmon_site_data)
    assert len(unmon_site_data) >= num_unmon_sites
    for inst_num, all_data in enumerate(unmon_site_data):
        if inst_num < num_unmon_sites_train:
            train_seq_and_labels.append(all_data)
        elif inst_num < num_unmon_sites:
            test_seq_and_labels.append(all_data)
        else:
            break

    del unmon_dataset, unmon_dir_seq, unmon_time_seq, \
        unmon_metadata, unmon_site_data

    # skipping work on unmonitored websites

    print('processing data')

    # Removes mon site ordering
    random.shuffle(train_seq_and_labels)
    random.shuffle(test_seq_and_labels)

    train_dir = []
    train_time = []
    train_metadata = []
    train_labels = []

    test_dir = []
    test_time = []
    test_metadata = []
    test_labels = []

    for dir_seq, time_seq, metadata, label in train_seq_and_labels:
        train_dir.append(dir_seq)
        train_time.append(time_seq)
        train_metadata.append(metadata)
        train_labels.append(label)
    for dir_seq, time_seq, metadata, label in test_seq_and_labels:
        test_dir.append(dir_seq)
        test_time.append(time_seq)
        test_metadata.append(metadata)
        test_labels.append(label)

    train_dir = np.array(train_dir)
    train_time = np.array(train_time)
    train_metadata = np.array(train_metadata)

    test_dir = np.array(test_dir)
    test_time = np.array(test_time)
    test_metadata = np.array(test_metadata)

    # Converts from absolute times to inter-packet times.
    # Each spot holds time diff between curr packet and prev packet
    if inter_time:
        inter_time_train = np.zeros_like(train_time)
        inter_time_train[:, 1:] = train_time[:, 1:] - train_time[:, :-1]
        train_time = inter_time_train

        inter_time_test = np.zeros_like(test_time)
        inter_time_test[:, 1:] = test_time[:, 1:] - test_time[:, :-1]
        test_time = inter_time_test

    # Reshape to add 3rd dim for CNN input
    train_dir = np.reshape(train_dir,
                           (train_dir.shape[0], train_dir.shape[1], 1))
    test_dir = np.reshape(test_dir, (test_dir.shape[0], test_dir.shape[1], 1))

    train_time = np.reshape(train_time,
                            (train_time.shape[0], train_time.shape[1], 1))
    test_time = np.reshape(test_time,
                           (test_time.shape[0], test_time.shape[1], 1))

    if scale_metadata:
        metadata_scaler = StandardScaler()
        train_metadata = metadata_scaler.fit_transform(train_metadata)
        test_metadata = metadata_scaler.transform(test_metadata)

    # One-hot encoding of labels, using one more class for
    # unmonitored sites if in open-world

    num_classes = num_mon_sites if num_unmon_sites == 0 else num_mon_sites + 1
    train_labels = to_categorical(train_labels, num_classes=num_classes)
    test_labels = to_categorical(test_labels, num_classes=num_classes)

    print('training data stats:')
    print(train_dir.shape)
    print(train_time.shape)
    print(train_metadata.shape)
    print(train_labels.shape)

    print('testing data stats:')
    print(test_dir.shape)
    print(test_time.shape)
    print(test_metadata.shape)
    print(test_labels.shape)

    print(f'saving data as {h5_out}')
    with h5py.File(h5_out, "w") as f:
        f.create_group('training_data')
        f.create_group('validation_data')
        f.create_group('test_data')
        for ds_name, arr in [['dir_seq', train_dir],
                             ['time_seq', train_time],
                             ['metadata', train_metadata],
                             ['labels', train_labels]]:
            f.create_dataset('training_data/' + ds_name,
                             data=arr[:int(cst.TRAIN_PERCENTAGE * len(arr))])
        for ds_name, arr in [['dir_seq', train_dir],
                             ['time_seq', train_time],
                             ['metadata', train_metadata],
                             ['labels', train_labels]]:
            f.create_dataset('validation_data/' + ds_name,
                             data=arr[int(cst.TRAIN_PERCENTAGE * len(arr)):])
        for ds_name, arr in [['dir_seq', test_dir],
                             ['time_seq', test_time],
                             ['metadata', test_metadata],
                             ['labels', test_labels]]:
            f.create_dataset('test_data/' + ds_name,
                             data=arr)

config_template = None
with open('config_template.json') as config_file:
    config_template = json.load(config_file)

clusters = []
clusters.append('../../cf-clusters-datasets/cluster-150-3/npys/')
clusters.append('../../cf-clusters-datasets/quic-100p-150/npys/')
clusters.append('../../cf-clusters-datasets/quic-100p-150-again/npys/')

for path in clusters:
    npy_out = path.replace('../../cf-clusters-datasets/', '').replace('/npys/', '') + ".npy"
    h5_out = path.replace('../../cf-clusters-datasets/', '').replace('/npys/', '') + ".h5"

    if not os.path.isfile(npy_out) or not os.path.isfile(h5_out):
        print("Working on", h5_out)
        config = create_npy(path+"summary_quic_tls_merged.npy", output_npy=npy_out, config_template=config_template)
        create_h5(config, npy_out, h5_out)
        