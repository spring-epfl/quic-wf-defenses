# app-agnostic-attacks

This folder contains the code to run application-agnostic WF attacks (Section 4). Before running this code, ensure that you have collected trace files of the websites using the code in **capture/**. Also run the code in **process-capture/** to obtain the processed .npy files. 

The code consists of the following folders (each folder has a README file describing the code in it):

1. **wf-unconstrained/** runs the WF attacks for the unconstrained adversary (Section 4.1).
2. **ip-fingerprinting/** runs the IP fingerprinting attack by Hoang et al. (Section 4.1.1).
3. **wf-constrained/** runs the WF attacks for the constrained adversary (Section 4.2).  
