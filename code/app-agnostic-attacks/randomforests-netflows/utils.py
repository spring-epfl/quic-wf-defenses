import glob
import multiprocessing as mp
import numpy as np
import itertools
import ntpath
import operator
import sys
import constants as cst
import os


def parallel(files, function, n_jobs=20):
    if cst.PARALLEL_ENABLED:
        pool = mp.Pool(n_jobs)
        data_dict = pool.map(function, files)
        return data_dict
    else:
        res = []
        for f in files:
            res.append(function(f))
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


def closed_world_acc(neighbors, y_test):
    tp, p = 0, len(neighbors)

    for trueclass, neighbor in zip(y_test, neighbors):
        if len(set(neighbor)) == 1:  # if all guesses are of the same class
            if trueclass == neighbor[0]:
                tp += 1
    return tp / p


def open_world_acc(neighbors, y_test, MON_SITE_NUM):
    logger.info("Calculate the precision...")
    tp, wp, fp, p, n = 0, 0, 0, 0, 0
    neighbors = np.array(neighbors)

    p += np.sum(y_test != "-1")
    n += np.sum(y_test == "-1")

    for trueclass, neighbor in zip(y_test, neighbors):
        if len(set(neighbor)) == 1:
            guessclass = neighbor[0]
            if guessclass != MON_SITE_NUM:
                if guessclass == trueclass:
                    tp += 1
                else:
                    if trueclass != MON_SITE_NUM:  # is monitored site
                        wp += 1
                        # logger.info('Wrong positive:{},{}'.format(trueclass,neighbor))
                    else:
                        fp += 1
                        # logger.info('False positive:{},{}'.format(trueclass,neighbor))

    return tp, wp, fp, p, n


def mean_and_95p(data):
    mean = np.mean(data)
    std = np.std(data)
    p95 = 1.645 * std
    return mean, p95
