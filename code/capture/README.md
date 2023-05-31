# Traffic capture

This folder contains the code for various traffic-capture scenarios in the paper. The sub-folders each deal with a capture setup and are as follows:

1. ***quic-nquic/*** : Main capture setup (used in Section 4 experiments). This is used to capture QUIC (or non-QUIC) traffic for a list of websites. 

2. ***quic-percentage/*** : Capture setup to calculate the amount of QUIC traffic for each website. Run this before the main capture to obtain a list of websites that primarily contain QUIC traffic.

3. ***har/*** : Capture HAR files of different websites (used in Section 5 analysis).

4. ***links/*** : Obtain links of sub-pages for a list of websites (used in Section 4 heterogeneous-world experiment).


Each folder contains a README with information on how to run the code. 
