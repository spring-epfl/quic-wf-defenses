# randomforests

This folder contains code to run the WF attack using random forests for the unconstrained adversary. It is used in Section 4.1 of the paper. 

Before running this code, you should have gathered PCAP files using the code in **capture/** and processed them to obtain .npy files using the code in **process-capture/parse_pcaps_into_npys.py**. 

The scripts in this folder take in the processed .npy files, extracts features from them and writes them to .npy files, and runs the WF attack. 

The code consists of the following scripts:

1. **build_features.py** reads in the .npy processed traces and outputs a .npy featrue file. Note that, by default, it generates features for undefended traces. You can generate features for defended traces by providing the type of defense you want as an arg to the script (none, nosize, nototalsize, notiming, nosizetiming).
2. **constants.py** contains the parameters used in the WF attack (such as number of trees, number of classes, test percentage, etc.). 
2. **attack.py** is the default attack file. It runs a 10-fold cross validation of the attack. Place all the .npy featrue files you want to run the attack on inside a directoy and run the script (edit path in line 9). It generates the results in a JSON file. 
3. **attack_cross.py** runs the cross-classification used in the client and time experiments. Provide the list of .npys you want to run the cross-attack on (line 12) and run. It generates JSON files depending on the number of permutations. 
4. **attack_het.py** is the same as attack.py but is used in the heteroeneous experiment (where the sub-pages are different). Provide the input directory (line 10) and run the script. 

The directory **src/** contains helper files for performing feature extraction and classification. 