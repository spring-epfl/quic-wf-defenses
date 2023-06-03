# randomforests-netflows

This folder contains code to run the WF attack using random forests for the constrained adversary who uses sampled netflows. It is used in Section 4.2.2 of the paper. 

Before running this code, you should have gathered PCAP files using the code in **capture/** and processed them to obtain .npy files using **process-capture/parse_pcaps_into_netflows.py** and **process-captrue/parse_netflows_into_npys.py**. 

The scripts in this folder take in the processed .npy files, extracts features from them and writes them to .npy files, and runs the WF attack. 

The code consists of the following scripts:

1. **build_features.py** reads in the .npy processed traces and outputs a .npy feature file. Note that, by default, it generates features for undefended traces. You can generate features for defended traces by adding the defense into the function call. You can also change the amount of padding for the defense. Check lines 24-33 for examples.
2. **constants.py** contains the parameters used in the WF attack (such as number of trees, number of classes, test percentage, etc.). 
2. **attack.py** is the default attack file. It runs a 10-fold cross validation of the attack. Place all the .npy featrue files you want to run the attack on inside a directoy and run the script (edit path in line 9). It generates the results in a JSON file. 

The directory **src/** contains helper files for performing feature extraction and classification. The file **utils.py** contains some helper functions. 