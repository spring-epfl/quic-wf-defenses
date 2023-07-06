### Code Organization

The code is organized in the following folders:

*capture* provides all the scripts necessary to perform different kinds of data capture used in the paper (network traffic, HAR files, traceroutes).

*process-capture* provides the scripts necessary to process the captures into formats used for classification. It also contains scripts to convert network captures into netflows. 

*app-agnostic-attacks* contains scripts for the various application-agnostic WF attacks and defenses (Section 4 of the paper).

*app-aware-attacks* contains scripts for the various application-aware WF attacks and defenses (Section 5 of the paper).

*lib* contains some helper files used by the other scripts.

Each folder contains READMEs that describe how to run the code.


### Main pipeline

To run the main pipeline of experiments (assuming you have a list of URLs to analyze), please run as follows:

1. Run the code in **capture/quic-nquic** to obtain network trace files. You obtain a folder of .pcap files at the end of this process. Detailed instructions in README of **capture/**. Modify automate-capture.sh to take in your list of URLs as input.

```
$ bash automate-capture.sh
```

2. Run the code in **process-capture/parse_pcaps_into_npys.py** to process the folder of .pcap files and obtain packet-sepcific information. You obtain a folder of .npy files at the end of this process. Details in README of **process-capture/**.

```
$ cd process-capture/
$ python3 parse_pcaps_into_npys.py /data/pcaps/
```

The above snippet will create a new folder with .npy files in /data/npys.

3. Run the code in **app-agnostic-attacks/wf-unconstrained/build_features.py** to extract features from the .npy folder. This results in a .npy feature file. Details in README of **app-agnostic-attacks**.

```
$ cd app-agnostic-attacks/wf-unconstrained/
$ python3 build_features.py --input /data/ --output features.npy --defense none
```

The above snippet will create a features.npy file in the current folder.

4. Run the code in **app-agnostic-attacks/wf-unconstrained/attack.py** to perform 10-fold cross-validation on the feature file. This results in a .json file with the results. Note that you need to create a directory to put your feature file in and then modify attack.py to input the path to the directory before running it.

```
$ mkdir /data/features
$ mv features.npy /data/features
$ python3 attack.py
```

The output .json file of the script above will contain the metrics of the classifier that can be compared against results in the paper. The output .json provides the number of classes, number of samples used, the accuracy/precision/recall/f1-score, and the features and their importances.

Sample output:

```
{
  "score": {
    "n_classes": [
      150,
      0
    ],
    "min_n_samples": [
      40,
      0
    ],
    "max_n_samples": [
      40,
      0
    ],
    "accuracy": [
      0.9576874999999999,
      0.003649640868937959
    ],
    "precision": [
      0.9589748018676456,
      0.0038197502044932945
    ],
    "recall": [
      0.9576874999999999,
      0.003649640868937959
    ],
    "f1score": [
      0.9573383071883479,
      0.003813301379661153
    ]
  },
  "features": [
    [
      "hist_1003",
      0.04022462678877165,
      0.0021000236270692224
    ],
    [
      "hist_1337",
      0.028745123751845597,
      0.00114796525987474
    ],
    .
    .
    .
    .
}
```

All the other scripts in the different folders are for scenarios that are variations of this main scenario. Adjust the pipeline based on the scenario you want to analyze. 


