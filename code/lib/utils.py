import glob
import multiprocessing as mp
import numpy as np
import itertools
import ntpath
import operator
import sys
import constants as cst
import os


PARALLEL_ENABLED = True


# Returns [function(task) for task in tasks] in parallel or not (depending on PARALLEL_ENABLED)
def parallel(tasks, function, n_jobs=20):
    if PARALLEL_ENABLED:
        print(f"Starting pool of {n_jobs} workers...")
        pool = mp.Pool(n_jobs)
        data_dict = pool.map(function, tasks)
        return data_dict
    else:
        res = []
        for t in tasks:
            res.append(function(t))
        return res


# returns a dictionary containing two lists: the first being features, the second labels
def parallel_and_zip(files, function):
    d = dict()
    list_of_tuples = parallel(files, function)
    d["feature"], d["label"] = zip(*list_of_tuples)
    return d


def label_from_path(filepath):
    filename = filepath
    if "/" in filename:
        filename = filename.split("/")[-1]
    if "." in filename:  # some end by .cell
        filename = filename.split(".")[0]

    parts = filename.split("-")

    if len(parts) == 2:
        # close-world sample format: /label-repetition
        return (int(parts[0]), int(parts[1]))
    else:
        # open-world sample format: /repetition
        return ("-1", int(filename))



def dataset_to_X_y(filename="dataset.npy"):
    d = np.load(filename, allow_pickle=True).item()

    X = np.array(d["feature"])
    label_repetition = np.array(d["label"])
    y = np.array([label[0] for label in label_repetition])

    return X, y


def str_replace_for_path(f, path1, path2):
    # this is just a str.replace() that discards *
    # f is a/b/c/file, path1 is /a/b/c/* , path2 is /a/b/d/*
    if path1.endswith('*'):
        path1 = path1[:-1]
    if not path1.endswith("/"):
        path1 += '/'
    if not path2.endswith("/"):
        path2 += '/'

    return f.replace(path1, path2)



def mean_and_95p(data):
    mean = np.mean(data)
    std = np.std(data)
    p95 = 1.645 * std
    return mean, p95
