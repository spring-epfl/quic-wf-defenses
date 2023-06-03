# app-aware-attacks

This folder contains the code to run application-aware WF attacks (Section 5). Before running this code, ensure that you have collected HAR files of the websites using the code in **capture/** (abut 40 samples per site). Also run the code in **process-capture/create_har_npy.py** to obtain the processed .npy file. 

The code consists of the following notebooks:

1. **attack_by_parties.ipynb** runs the attacks on traces filtered by first-party, third-party, and Google resources (Section 5.2.2).
2. **defense-pad.ipynb** runs the attacks on a defense that pads local sizes (Section 5.2.3 local).  
3. **defense-padtotal.ipynb** runs the attacks on a defense that pads global sizes (Section 5.2.3 global).  
4. **defense-dummies.ipynb** runs the attacks on a defense that adds dummies (Section 5.2.3 dummies).  

The notebooks also plot the F1-score and the cost of adding various defenses. 
