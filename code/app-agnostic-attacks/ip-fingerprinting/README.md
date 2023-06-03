# IP fingerprinting

This folder contains code to run the IP fingerprinting attack by [Hoang et al.](https://homepage.np-tokumei.net/publication/publication_2021_popets/). It is used in Section 4.1.1 of the paper. 

Before running this code, you need to build a dataset of IP fingerprints by constantly running DNS queries over the list of websites. 

In order to do that, first run a HAR capture (**capture/har-capture** directory) to obtain HAR files for the websites. Then run the script to fetch DNS information for each resource mentioned in the HAR file (**capture/har-capture/fetch_dns_info.py**). Perform this step multiple times (over several days to obtain varied fingerprints). 

Run the script **compare_fingerprints.py**. This script takes in the following:

1. Folder containing the DNS information (which you created in the previous step).
2. NPY file containing trace information (from the processed PCAPS you collected).
3. List of websites used in the experiment.
4. Folder containing the truths and predictions of 10-fold cross validation from the WF attack.
5. A flag indicating whether to consider the primary (first) IP in the attack or not. 

The script first builds IP fingerprints from the DNS information. It then processes trace file to obtain IP fingerprints of the traces. It reads the WF attack files to obtain the same list of websites for 10 iterations of the IP fingerprinting attack. It matched the trace file IPs against the DNS information IPs to guess the website. It writes the output to files, and calculates accuracy metrics. 