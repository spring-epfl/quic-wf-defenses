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

1. Run the code in **capture/quic-nquic** to obtain network trace files. You obtain a folder of .pcap files at the end of this process.
2. Run the code in **process-capture/parse_pcaps_into_npys.py** to process the folder of .pcap files and obtain packet-sepcific information. You obtain a folder of .npy files at the end of this process.
3. Run the code in **app-agnostic-attacks/wf-unconstrained/build_features.py** to extract features from the .npy folder. This results in a .npy feature file. 
3. Run the code in **app-agnostic-attacks/wf-unconstrained/attack.py** to perform 10-fold cross-validation on the feature file. This results in a .json file with the results. 


All the other scripts are for scenarios that are variations of this main scenario. Adjust the pipeline based on the scenario you want to analyze. 