import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import accuracy_score
from sklearn import metrics
import random
import sys
import pathlib
from sklearn.feature_selection import RFE
from functools import partial
import constants as cst
import pandas
import sklearn
from sklearn.utils.multiclass import unique_labels
import matplotlib.pyplot as plt
sys.path.append("../..")
import lib.plot_builder as plot_builder
import json
import itertools

def get_k_neighbor(params):
    y_train_predicted, y_test_predicted, y_train, K = (
        params[0],
        params[1],
        params[2],
        params[3],
    )

    atile = np.tile(y_test_predicted, (y_train_predicted.shape[0], 1))
    dists = np.sum(atile != y_train_predicted, axis=1)
    k_neighbors = y_train[np.argsort(dists)[:K]]

    return k_neighbors


def parallel_get_k_neighbors(
    y_train_predicted, y_test_predicted, y_train, K=3, n_jobs=20
):
    n = len(y_test_predicted)

    Y_train_predicted = [y_train_predicted] * n
    Y_train = [y_train] * n
    Ks = [K] * n

    zipped = zip(Y_train_predicted, y_test_predicted, Y_train, Ks)

    pool = mp.Pool(n_jobs)
    neighbors = pool.map(get_k_neighbor, zipped)
    return np.array(neighbors)


def random_forest(features_names, X_train, y_train, X_test, y_test, n_trees=1000, rfe_nfeatures=800, rfe_steps=10, n_classes=-1):
    clf=RandomForestClassifier(n_jobs=-1, n_estimators=n_trees, random_state=0)
    selector = RFE(estimator=clf, n_features_to_select=rfe_nfeatures, step=rfe_steps)

    selector = selector.fit(X_train, y_train)
    X_train = selector.transform(X_train)
    X_test = selector.transform(X_test)
    
    clf2=RandomForestClassifier(n_jobs=-1, n_estimators=n_trees, random_state=0)
    clf2.fit(X_train, y_train)
    y_pred=clf2.predict(X_test)
    predicted_probas = clf2.predict_proba(X_test)


    min_n_samples = 0
    c = {}
    for y in y_test:
        if not y in c:
            c[y] = 0
        c[y] += 1
    min_n_samples = min([x[1] for x in c.items()])
    n_uniq_classes = len(list(set(y_test)))

    scores = dict(
        n_classes = n_uniq_classes,
        min_n_samples = min([x[1] for x in c.items()]),
        max_n_samples = max([x[1] for x in c.items()]),
        accuracy = metrics.accuracy_score(y_test, y_pred),
        precision = metrics.precision_score(y_test, y_pred, average='macro'),
        recall = metrics.recall_score(y_test, y_pred, average='macro'),
        f1score = metrics.f1_score(y_test, y_pred, average='macro'),
    )

    if n_classes>-1 and n_uniq_classes != n_classes:
        y_test_ext = [y for y in y_test]
        y_pred_ext = [y for y in y_pred]
        
        n_to_add = n_classes - n_uniq_classes
        next_value = 900 # arbitrary, just not a url
        i = 0
        while i < n_to_add:
            y_test_ext.extend([next_value + i] * min_n_samples)
            y_pred_ext.extend([-1] * min_n_samples)
            i += 1


        c = {}
        for y in y_test_ext:
            if not y in c:
                c[y] = 0
            c[y] += 1

        print(f"{n_classes} but only found {n_uniq_classes}")

        scores['n_classes_corr'] = len(list(set(y_test_ext)))
        scores['accuracy_corr'] = metrics.accuracy_score(y_test_ext, y_pred_ext)
        scores['precision_corr'] = metrics.precision_score(y_test_ext, y_pred_ext, average='macro')
        scores['recall_corr'] = metrics.recall_score(y_test_ext, y_pred_ext, average='macro')
        scores['f1score_corr'] = metrics.f1_score(y_test_ext, y_pred_ext, average='macro')

        print(f"Scores were {scores['f1score']} but were corrected to {scores['f1score_corr']}.")

    selected_features = []
    i = 0
    while i<len(features_names):
        if selector.support_[i] == 1:
            selected_features.append(features_names[i])
        i+=1

    feature_importance = sorted(zip(clf2.feature_importances_, selected_features), reverse=True)

    return scores, feature_importance, y_pred, predicted_probas


def rf_folds(train_data, train_labels, test_data, test_labels, feature_names, rfe_nfeatures=50, rfe_steps=100, n_trees=30, n_classes=-1):

    sss = StratifiedShuffleSplit(n_splits=cst.K_FOLDS, test_size=cst.TEST_PERCENTAGE, random_state=0)

    # print("Training stats:")
    # print("Number of classes", len(set(train_labels)))
    # print("Number of features", len(train_data[0]))
    # print("Number of samples", len(train_data))
    # print("Number of labels", len(train_labels))
    # print("Test stats:")
    # print("Number of classes", len(set(test_labels)))
    # print("Number of features", len(test_data[0]))
    # print("Number of samples", len(test_data))
    # print("Number of labels", len(test_labels))

    scores = []
    y_test_all = []
    y_pred_all = []
    feature_ranks = dict()

    i = 0

    for i in range(0, 10):

        print("Fold", i, end="\r")

        X_train, X_test = train_data[i], test_data[i]
        y_train, y_test = train_labels[i], test_labels[i]
        
        s, features, y_pred, _  = random_forest(feature_names, X_train, y_train, X_test, y_test, n_trees=n_trees, rfe_nfeatures=rfe_nfeatures, rfe_steps=rfe_steps, n_classes=n_classes)

        y_test_all.extend(y_test) 
        y_pred_all.extend(y_pred.tolist())
        
        for proba, feature in features:
            if not feature in feature_ranks:
                feature_ranks[feature] = []

            feature_ranks[feature].append(proba)

        scores.append(s)
        i += 1

    # average scores
    score = {k: (np.mean([value[k] for value in scores]), np.std([value[k] for value in scores])) for k in scores[0]}

    # average features importance
    for f in feature_ranks:
        if len(feature_ranks[f]) < cst.K_FOLDS:
            feature_ranks[f].extend([0] * (cst.K_FOLDS - len(feature_ranks[f])))

    features_and_percentages = []
    for f in feature_ranks:
        features_and_percentages.append((f, np.mean(feature_ranks[f]), np.std(feature_ranks[f])))
        

    return score, features_and_percentages, y_test_all, y_pred_all



def trim(elements, n):
    if len(elements) >= n:
        elements[:n] = True
    return elements


def trim_df(X, y, num_insts):
    """Return a dataframe with the same number of instances per class.
    The dataframe, `df`, has a field with the class id called `class_label`.
    """
    X2 = X.copy() 
    y2 = y.copy() 

    X['selected'] = False  # initialize all instances to not selected
    classes = y2.groupby('class_label')  # group instances by class
    trim_part = partial(trim, n=num_insts)  # partial trim to n=NUM_INSTS
    X['selected'] = classes.selected.transform(trim_part)  # mark as selected
    selected = X[X2.selected]  # get the selected instances
    return selected


def sample_classes(df, classes=None):
    if type(classes) is int:
        sample = random.sample(df.class_label.unique(), classes)
    elif type(classes) is list:
        sample = classes
    else:
        raise Exception("Type of classes not recognized.")
    selected_classes = df.class_label.isin(sample)
    return df[selected_classes]

def labels_strings_to_ids(labels):
    mapping = dict()
    i = 0
    for l in labels:
        if l in mapping:
            continue
        mapping[l] = i
        i += 1
    
    labels2 = [mapping[l] for l in labels]

    return labels2, mapping

def process_npy(path, tag="train"):

    all_X = []
    all_y = []

    for i in range(0, 10):

        print("Processing", i)
        dataset_npy = path + tag + str(i) + ".npy"

        dic = np.load(dataset_npy, allow_pickle=True).item()
        feature_names = dic["feature_names"]
        X = np.array(dic["features"])
        Y = np.array(dic["labels"])
        y_str = np.array([label[0] for label in Y])

        y_i, mapping = labels_strings_to_ids(y_str)

        # mapfile = 'plots/'+dataset_npy.replace('datasets/', '').replace('.npy', '.map.json')
        # with open(mapfile, 'w') as f:
        #     print("Writting map", mapfile)
        #     f.write(json.dumps(mapping))
        y_i = np.array(y_i)

        if len(X) == 0:
            print(f"Warning: empty dataset {dataset_npy}")
            score = dict(
                n_classes = 0,
                min_n_samples = 0,
                max_n_samples = 0,
                accuracy = [0,0],
                precision =  [0,0],
                recall = [0,0],
                f1score = [0,0]
            )
            return 'N/A', 'N/A', 'N/A'

        all_X.append(X)
        all_y.append(y_i)
    
    return all_X, all_y, feature_names

def run(path):

    train_data, train_labels, feature_names = process_npy(path, tag="train")
    test_data, test_labels, feature_names = process_npy(path, tag="test")

    if (train_data != 'N/A') & (test_data != 'N/A'):
        #print(f"Loaded {len(train_data)} rows, {len(feature_names)} feature names for {len(train_data[0])} features")
        #print(f"Loaded {len(test_data)} rows, {len(feature_names)} feature names for {len(test_data[0])} features")
        score, features_and_percentages, y_test_all, y_pred_all = \
            rf_folds(train_data, train_labels, test_data, test_labels, feature_names, 
                rfe_nfeatures=cst.KF_RFE_NFEATURES_TO_SELECT, 
                rfe_steps=cst.KF_RFE_STEPS, n_trees=cst.N_TREES, 
                n_classes=cst.N_CLASSES)

        #plot_builder.confusion_matrix("het-exp1-cm", y_test_all, y_pred_all)
        #plot_builder.feature_importance("het-exp1-fi", features_and_percentages)

        return dict(score=score, features=features_and_percentages)

    else:
        return dict(score=score, features=[])
