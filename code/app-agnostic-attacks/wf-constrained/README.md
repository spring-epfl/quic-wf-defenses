# wf-constrained

This folder contains code to run the WF attack using random forests for the constrained adversary. It is used in Section 4.2 of the paper. 

Before running this code, you should have gathered PCAP files using the code in **capture/** and processed them to obtain .npy files using the code in **process-capture/**. 

The scripts in this folder take in the processed .npy files, extracts features from them and writes them to .npy files, and runs the WF attack. 

The code consists of the following scripts:

1. **build_features_netflows.py** reads in the .npy processed NetFlow traces and outputs a .npy feature file. Note that, by default, it generates features for undefended traces. You can generate features for defended traces by adding the defense into the function call. You can also change the amount of padding for the defense. Check lines 24-33 for examples.
2. **constants.py** contains the parameters used in the WF attack (such as number of trees, number of classes, test percentage, etc.). 
3. **attack_netflows.py** is the attack file. It runs a 10-fold cross validation of the attack. Place all the .npy feature files you want to run the attack on inside a directoy and run the script (edit path in line 9). It generates the results in a JSON file. 
4. **build_features_google.py** reads in the .npy processed traces with Google view and outputs a .npy feature file. 
5. **attack_google.py** is the attack file. It runs a 10-fold cross validation of the attack. Place all the .npy feature files you want to run the attack on inside a directoy and run the script (edit path in line 9). It generates the results in a JSON file. 
6. **build_features_google_timings.py** reads in the .npy processed Google ClientHello traces and outputs a .npy feature file. 
7. **attack_google_timings.py** is the attack file. It runs a 10-fold cross validation of the attack. Place all the .npy feature files you want to run the attack on inside a directoy and run the script (edit path in line 9). It generates the results in a JSON file. 

The directory **src/** contains helper files for performing feature extraction and classification. 
