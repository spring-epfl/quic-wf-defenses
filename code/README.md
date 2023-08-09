### Code Organization

The code is organized in the following folders:

*capture* provides all the scripts necessary to perform different kinds of data capture used in the paper (network traffic, HAR files, traceroutes).

*process-capture* provides the scripts necessary to process the captures into formats used for classification. It also contains scripts to convert network captures into netflows. 

*app-agnostic-attacks* contains scripts for the various application-agnostic WF attacks and defenses (Section 4 of the paper).

*app-aware-attacks* contains scripts for the various application-aware WF attacks and defenses (Section 5 of the paper).

*lib* contains some helper files used by the other scripts.

Each folder contains READMEs that describe how to run the code.


### Main pipeline

The main pipeline does the following: 

1. Conducts a capture of network traffic to obtain a set of .pcap files. 
2. Processes this set of .pcap files to obtain packet-sepcific information (size, time, directionality of each QUIC packet) in a .npy format. 
3. Extracts features from the .npy files (either with or without a particular defense applied).
4. Runs the WF attack on the extracts features (10-fold cross-validation).

The output of the pipeline is a file that shows the performance of the attack in undefended or defended scenarios. 

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

### Other pipelines

There are variations of the main pipeline, we describe these and how to run the code below:

#### Limited-visibility adversary 

This adversary performs the WF attack on partial network traces. The adversary is assumed to be an AS (autonomous system) that observes only the network traces that passes through the AS. We simulate this adversary as follows: 

1. Collect HAR files for each website on the list. The HAR files show which resources are fetched when visiting a site. The end of this process gives us the set of resources fetched for all websites in our list.
2. Run traceroute for every resource. The traceroute shows the IPs and ASes that were present in the path for each resource fetch. 
3. Run a script that takes in the network traces, the HAR files, the traceroutes, and a required AS (which is the adversary we want to simulate). The script filters the network traces to only have traffic that passes through the required AS. 

To simulate this limited adversary, run the code as follows:

1. Obtain .pcap traces from a list of websites by following Step 1 of the main pipeline above. 

2. Collect HAR files:

```
$ cd capture/hars
$ mkdir "/data/$(date +%Y%m%d)/hars"
$ bash automate-capture.sh /data/urls_subset.txt "/data/$(date +%Y%m%d)/hars"
```

3. Parse the HAR files:

```
$ cd capture/traceroutes
$ python3 parse-hars.py /data/$(date +%Y%m%d)/hars /data/$(date +%Y%m%d)/processed-hars
```

4. Run traceroutes:

Follow instructions in capture/ README ([here](https://github.com/spring-epfl/quic-wf-defenses/tree/main/code/capture#traceroute-experiments)) to set up a virtual environment and run the capture. Use the output from Step 2 as input for the traceroutes.

5. Obtain filtered traces: 

First, modify capture/traceroutes/processing-scripts/create_partial_traces.py (Lines 303-310, 328) with paths to the .pcap traces, HAR files, traceroutes, and ASN you want. Then, run the script:

```
$ cd capture/traceroutes/processing-scripts
$ python3 create_partial_traces.py
```

You will obtain a set of .pcap files with filtered traces. After this, run Steps 2-4 of the main pipeline to run the attack.

Note on Google experiments: Section 4.2.3 of the paper uses limited-visibility adversary with Google as the adversary. To run this, use Google's AS (15169) as the input when running create_partial_traces.py. There is another attack that only uses ClientHello timings to Google, to run this, complete Steps 1-5, then run (modify line 52 to path of filtered Google traces):

```
$ python3 create_google_handshakes.py
```
This results in a set of Google traces containing only ClientHello packets. Perform the rest of the attack by running Steps 2-4 of the main pipeline.

#### Limited-processing adversary

This adversary performs the WF attack on sampled NetFlow traces instead of full traces. The adversary is assumed to be an AS that has only the processing/storage capability to run the attack on flows instead of packets. We simulate this adversary as follows:

1. Obtain .pcap traces from a list of websites by following Step 1 of the main pipeline above. 

2. Convert the pcaps into NetFlows (note that it generates 4 sets of flows at sampling rates of 0.1%, 1%, 10%, 100%):

```
$ cd process-capture
$ python3 parse_pcaps_into_netflows.py /data/pcaps/
```
3. The previous step generates a folder of NetFlows in /data/netflows/. Convert the NetFLows into .npy files:

```
$ python3 parse_netflows_into_npys.py /data/netflows/
```

4. Extract features by running wf-constrained/build_features_netflows.py. Change lines 21 and 22 to put the paths of the input and output files. Lines 24-35 indicate how to run the attack under different sampling and defense conditions, uncomment as desired. 

```
$ cd wf-constrained/
$ python3 build_features_netflows.py
```

5. Run the attack. Note that you need to create a directory to put your feature file in and then modify attack_netflows.py (Line 9) to input the path to the directory before running it.
 
```
$ mkdir /data/features
$ mv features.npy /data/features
$ python3 attack_netflows.py
```

#### Application-aware defender

So far, we conducted the attacks using an application-agnostic defender. We also conduct attacks on an application-aware defender (Section 5 of the paper). These attacks work on HAR traces instead of network files because the defenses work directly on application data instead of network-layer data. 

Please run the following pipeline:

1. Run the code in capture/ to obtain the HAR files (follow the instructions [here](https://github.com/spring-epfl/quic-wf-defenses/tree/main/code/capture#capture-har-files-of-websites)). 

2. Process the HAR files by running process-capture/parse_hars_into_npy.py. Modify lines 96-98 to provide paths to the HAR directory, URL list, and your desired output path. 

```
$ cd process-capture/
$ python3 parse_hars_into_npy.py
```

The output of this step will be a single .npy file which you can use as input in future steps.

3. We provide three notebooks showing how various attacks and defenses can be run on the processed HAR data. These notebooks are in app-aware-attacks/, run the steps as indicated in the notebooks:

a. [attack_by_parties.ipynb](https://github.com/spring-epfl/quic-wf-defenses/blob/main/code/app-aware-attacks/attack_by_parties.ipynb): runs the attacks on traces filtered by first-party, third-party, and Google resources (Section 5.2.2 of the paper).

b. [defense-pad.ipynb](https://github.com/spring-epfl/quic-wf-defenses/blob/main/code/app-aware-attacks/defense-pad.ipynb): runs the attacks on a defense that pads local sizes (Section 5.2.3 local of the paper).  

c. [defense-padtotal.ipynb](https://github.com/spring-epfl/quic-wf-defenses/blob/main/code/app-aware-attacks/defense-padtotal.ipynb): runs the attacks on a defense that pads global sizes (Section 5.2.3 global of the paper).

d. [defense-dummies.ipynb](https://github.com/spring-epfl/quic-wf-defenses/blob/main/code/app-aware-attacks/defense-dummies.ipynb): runs the attacks on a defense that adds dummies (Section 5.2.3 dummies of the paper).

