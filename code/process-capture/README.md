# process-capture

This folder contains code to process the files obtained from various capture setups in **capture/**. Before running this code, ensure that you have run the code in **/capture**.

The scripts in this folder take in the processed .npy files, extracts features from them and writes them to .npy files, and runs the WF attack. 

The code consists of the following scripts:

1. **parse_pcaps_into_npys.py** is the script used for most of the experiments. It takes in a directory of .pcap files processes them into a directory of .npy files. The processing consists of extracting the size, directionality, and timing of packets in the trace. The script creates individual .npy files for each trace, and combined .npy files (starting with the tag **summary_*) containing all the traces' information. The .npy files are used for feature extraction and classification. Run the script with the path to the pcap files as input. 
2. **parse_pcaps_into_netflows.py** converts .pcap files into sampled netflows (for attacks in Section 4.2.2). It generates netflows at 4 sampling rates (1%, 10%, 100%, 1000%). Run the script with the path to the pcap files as input. 
**NOTE**: This script requires that [nfdump](https://github.com/phaag/nfdump) is installed. Install nfdump from the provided link as it also has **nfpcapd** (that the script requires).
3. **parse_netflows_into_npys.py** converts the netflows from parse_pcaps_into_netflows.py to .npy files. Run the script with the path to the netflow files as input. 
4. **create_google_view.py** creates the Google view of network traces (used in Section 4.2.3). It requires traceroutes from **capture/**, as the traceroutes are used to determine which resources pass through the Google AS. Run the script with the path to the pcap and traceroute files as input. 
3. **parse_hars_into_npy.py** converts the directory of .har files and processes them to a single .npy file. Modify lines 96-98 with appropriate paths and run the script.

The file **pcap_sizes.py** is a helper script to check sizes of pcaps.