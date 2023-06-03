# RF with CV
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
import pandas
import sklearn
from sklearn.utils.multiclass import unique_labels
import matplotlib.pyplot as plt

def random_forest(features_names, X_train, y_train, X_test, y_test, n_trees, rfe_nfeatures, rfe_steps=10, n_classes=-1):
    clf=RandomForestClassifier(n_jobs=-1, n_estimators=n_trees, random_state=0)
    
    selector = RFE(estimator=clf, n_features_to_select=rfe_nfeatures, step=rfe_steps)

    selector = selector.fit(X_train, y_train)
    X_train = selector.transform(X_train)
    X_test = selector.transform(X_test)
    
    clf2=RandomForestClassifier(n_jobs=-1, n_estimators=n_trees, random_state=0)
    clf2.fit(X_train, y_train)
    y_pred=clf2.predict(X_test)
    predicted_probas = clf2.predict_proba(X_test)

    scores = dict(
        accuracy = metrics.accuracy_score(y_test, y_pred),
        precision = metrics.precision_score(y_test, y_pred, average='macro'),
        recall = metrics.recall_score(y_test, y_pred, average='macro'),
        f1score = metrics.f1_score(y_test, y_pred, average='macro'),
    )

    n_uniq_classes = len(list(set(y_test)))
    if n_classes>-1 and n_uniq_classes != n_classes:
        y_test_ext = [y for y in y_test]
        y_pred_ext = [y for y in y_pred]
        
        n_to_add = n_classes - n_uniq_classes
        next_value = 900 # arbitrary, just not a url
        i = 0
        while i < n_to_add:
            y_test_ext.append(str(next_value + i))
            y_pred_ext.append("-1")
            i += 1

        print(f"{n_classes} but only found {n_uniq_classes}")

        scores_corrected = dict(
            accuracy = metrics.accuracy_score(y_test_ext, y_pred_ext),
            precision = metrics.precision_score(y_test_ext, y_pred_ext, average='macro'),
            recall = metrics.recall_score(y_test_ext, y_pred_ext, average='macro'),
            f1score = metrics.f1_score(y_test_ext, y_pred_ext, average='macro'),
        )

        print(f"Scores were {scores['f1score']} but were corrected to {scores_corrected['f1score']}.")
        scores = scores_corrected

    selected_features = []
    i = 0
    while i<len(features_names):
        if selector.support_[i] == 1:
            selected_features.append(features_names[i])
        i+=1

    feature_importance = sorted(zip(clf2.feature_importances_, selected_features), reverse=True)

    return scores, feature_importance, y_pred, predicted_probas


def rf_folds(X, y, feature_names, rfe_nfeatures=10, rfe_steps=100, n_trees=30, folds=10, test_size=0.2, n_classes=-1):
    sss = StratifiedShuffleSplit(n_splits=folds, test_size=test_size, random_state=0)

    print("Number of classes", len(set(y)))
    print("Number of features", len(X[0]))
    print("Number of samples", len(X))
    print("Number of labels", len(y))

    scores = []
    y_test_all = []
    y_pred_all = []
    feature_ranks = dict()

    i = 0
    for train_index, test_index in sss.split(X, y):
        print("Fold", i)

        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
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
        if len(feature_ranks[f]) < folds:
            feature_ranks[f].extend([0] * (folds - len(feature_ranks[f])))

    features_and_percentages = []
    for f in feature_ranks:
        features_and_percentages.append((f, np.mean(feature_ranks[f]), np.std(feature_ranks[f])))
        

    return score, features_and_percentages, y_test_all, y_pred_all


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


def rf_with_rfe(features_array, n_classes=-1):
    feature_names = features_array["feature_names"]
    X = np.array(features_array["features"])
    Y = np.array(features_array["labels"])
    y_str = np.array([label[0] for label in Y])
    score, features_and_percentages, y_test_all, y_pred_all = rf_folds(X, y_str, feature_names, n_classes=n_classes)

    return dict(score=score, features=features_and_percentages)
