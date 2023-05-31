# Datasets & Fingerprinting

Pre-requisites: Install `requirements.txt` with pip

This repo contains the attacks and defenses to perform website fingerprinting.

Datasets:

- `datasets-pcaps` is the source of everything; see `/capture` on how to generate it.
- `datasets-taowang` is the old, text-based processed dataset
- `datasets-npy` is the new, binary-based dataset

Attacks and defenses:

- `../old/fingerprinting/fingerprinting-attacks` is an all-in-one set of scripts that does both attacks and defenses and prints a nice table, *extremely slowly*. It was fine with small datasets. It uses notably the text-based datasets, and recomputes defenses and attacks on the fly.
- `fingerprinting-defenses` just builds the defenses using NPYs. Once they are built, you don't need to rebuild them to tune the attacks/plots.
- `kfingerprinting` is a faster implementation of just kFingerprinting that looks at npys.

To summarize, there are two ways to look at this folder:

1) `datasets-pcap` -> `../old/fingerprinting/datasets-taowang` -> `../old/fingerprinting/fingerprinting-attack` (all inclusive, slow, doesn't run unless your machine has infinite memory)
2) `datasets-pcap` -> `datasets-npy` -> `defenses` -> `kfingerprinting` (much faster)
