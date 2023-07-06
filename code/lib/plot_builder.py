
import sklearn.metrics
from sklearn.utils.multiclass import unique_labels
import matplotlib.pyplot as plt
import numpy as np
from json import JSONEncoder
import pandas as pd
import os
import json
import subprocess
import re
from operator import itemgetter

PLOT_DIR = 'plots/'

# plotting constants
CONFUSION_MATRIX_XTICKS_SIZE=20
CONFUSION_MATRIX_LABELS_SIZE=20

CONFUSION_MATRIX_HIGHRES_FIGSIZE=(18,16)
CONFUSION_MATRIX_HIGHRES_XTICKS_SIZE=14
CONFUSION_MATRIX_HIGHRES_LABELS_SIZE=20

FEATURE_IMPORTANCE_XTICKS_SIZE=14
FEATURE_IMPORTANCE_LABELS_SIZE=14

LONGRUN_LABEL_SIZE = 14

def print_classifier_score(score):
    def r(i):
        return str(round(i, 2))
    print(",".join([k+": "+r(score[k]) for k in score]))


def plot_confusion_matrix(y_true, y_pred, normalize=True, title=True, classes=None, noTextBox=False, figsize=(9, 8), dpi= 80, colorbar=False, labelfontsize=12, nolabel=True):

    # Compute confusion matrix
    cm = sklearn.metrics.confusion_matrix(y_true, y_pred, labels=classes, normalize='true')

    # Only use the labels that appear in the data
    if classes is None:
        classes = unique_labels(y_true, y_pred)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    im = ax.imshow(cm, interpolation='none', aspect='auto', cmap=plt.cm.Blues, vmin=0, vmax=1.0)
    ax.tick_params(labelsize=labelfontsize)

    plt.xlabel('Predicted label', fontsize=labelfontsize)
    plt.ylabel('True label', fontsize=labelfontsize)

    if nolabel:
        plt.xlabel('', fontsize=labelfontsize)
        plt.ylabel('', fontsize=labelfontsize)

    if colorbar:
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.5)
        cbar = plt.colorbar(im, cax=cax)

        cbar.ax.tick_params(labelsize=labelfontsize)  # set your label size here


    #plt.setp(ax.get_xticklabels(), rotation=90, ha="right", rotation_mode="anchor")

    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    ax.set(xticks=np.arange(cm.shape[1]),
            yticks=np.arange(cm.shape[0]),
            xticklabels=classes, yticklabels=classes,
            title=title)
    

    # Rotate the tick labels and set their alignment.
    # plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    if not noTextBox:
        fmt = '.2f' if normalize else 'd'
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], fmt),
                        fontsize=labelfontsize,
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black")

    return cm, fig, ax


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def serialize(uri, o, version=''):
    try:
        os.remove(uri)
    except:
        pass
    with open(uri, "w") as f:
        if version != '':
            f.write('#version: '+version+'\n')
        json.dump(o, f, cls=NumpyArrayEncoder)

def deserialize(uri, version=''):
    if os.path.isfile(uri):
        with open(uri, "r") as f:
            data = []
            for line in f:
                if not line.startswith('#version:'):
                    data.append(line)
            return json.loads(''.join(data))
    return None

def getHeader():
    return """
import sys
sys.path.append("../../..")
from lib.plot_builder import deserialize, plot_confusion_matrix, table_precision_recall_f1
import matplotlib.pyplot as plt
"""

def confusion_matrix(filename, y_test, y_pred, title=''):
    table_filename = filename + '.tex'
    script_filename = filename + '.py'
    data_filename = filename + '.json'
    plot_filename = filename + '.png'

    data = [y_test, y_pred]
    serialize(PLOT_DIR + data_filename, data)

    s = getHeader() + """
[y_test, y_pred] = deserialize("{0}")
plot_confusion_matrix(y_test, y_pred, normalize=True, nolabel=True, noTextBox=True, title="{3}")
plt.tight_layout()
plt.savefig('{1}', format='png')
plt.savefig('{1}'.replace('.png', '.eps'), format='eps')
print("Written {1}/eps")
""".format(data_filename, plot_filename, table_filename, title)

    if os.path.isfile(PLOT_DIR + script_filename):
        print("Not overwriting", PLOT_DIR +script_filename, "but using existing one...")
    else:
        with open(PLOT_DIR +script_filename, "w") as f:
            f.write(s)

    os.system("cd "+PLOT_DIR+" && python3 "+script_filename)

def table_precision_recall_f1(y_true, y_pred, classes=None, mapping=None, sort=None):

    # Only use the labels that appear in the data
    if classes is None:
        classes = unique_labels(y_true, y_pred)

    precision,recall,fscore,support = sklearn.metrics.precision_recall_fscore_support(y_true, y_pred, labels=classes)

    header = ['Label', 'Precision', 'Recall', 'F1-score']#, 'Support']
    contents = []
    i = 0

    def r(i):
        return round(i, 2)

    for thisClass in classes:
        label = thisClass
        if mapping is not None and label in mapping:
            label = mapping[label]
        contents.append([label, r(precision[i]), r(recall[i]), r(fscore[i])]) #, support[i]])
        i += 1

    if sort is not None:
        contents.sort(key=sort)

    out = [header]
    out.extend(contents)
    precision,recall,fscore,support = sklearn.metrics.precision_recall_fscore_support(y_true, y_pred, labels=classes, average='micro')
    out.append(["\\emph{Average}", r(precision), r(recall), r(fscore)])#, len(y_true)])

    return out

def feature_importance(filename, features_and_percentages):
    # features_and_percentages is [(feature name, mean, std), ...]

    script_filename = filename + '.py'
    data_filename = filename + '.json'
    plot_filename = filename + '.png'

    features_and_percentages = sorted(features_and_percentages, key=itemgetter(1))

    serialize(PLOT_DIR + data_filename, features_and_percentages)

    s = getHeader() + """
import numpy as np
import scikitplot as skplt

features_and_percentages = deserialize("{0}")
features_and_percentages.sort(key=lambda row: row[1], reverse=True) # truncate top ten
features_and_percentages = features_and_percentages[:10]
features_and_percentages.sort(key=lambda row: row[1], reverse=False) # plotting needs ascending order

xs = [x[0] for x in features_and_percentages]
ys = [y[1] for y in features_and_percentages]
yerr = [[min(y[1], y[2]) for y in features_and_percentages], [y[2] for y in features_and_percentages]]

plt.title(None)
fig, ax = plt.subplots()
ax.barh(xs, ys, xerr=yerr)
ax.set_ylabel('Feature name', fontsize=14)
ax.set_xlabel('Feature importance', fontsize=14)
ax.tick_params(labelsize=14)
ax.grid(axis='x')
plt.tight_layout()

plt.savefig('{1}', format='png')
plt.savefig('{1}'.replace('.png', '.eps'), format='eps')
print("Written {1}/eps")
""".format(data_filename, plot_filename)

    if os.path.isfile(PLOT_DIR + script_filename):
        print("Not overwriting", PLOT_DIR +script_filename, "but using existing one...")
    else:
        with open(PLOT_DIR +script_filename, "w") as f:
            f.write(s)

    os.system("cd "+PLOT_DIR+" && python3 "+script_filename)