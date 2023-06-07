# QUIC website-fingerprinting defenses

Artifact release for the paper "Evaluating practical QUIC website fingerprinting defenses for the masses" (PETS 2023).

### Code Organization

The code is organized in the following folders:

*capture* provides all the scripts necessary to perform different kinds of data capture used in the paper (network traffic, HAR files, traceroutes).

*process-capture* provides the scripts necessary to process the captures into formats used for classification. It also contains scripts to convert network captures into netflows. 

*app-agnostic-attacks* contains scripts for the various application-agnostic WF attacks and defenses (Section 4 of the paper).

*app-aware-attacks* contains scripts for the various application-aware WF attacks and defenses (Section 5 of the paper).

*lib* contains some helper files used by the other scripts.

Each folder contains READMEs that describe how to run the code.

### Setup 

We provide a Docker setup with all the required dependencies. First, install Docker. After cloning the repo, build the image using the following command: 

```
$ cd quic-wf-defenses
$ docker build -t quic-wf-defenses .

```

Start the container and execute a shell as follows:

```
$ docker run --rm --detach --interactive --name quic-wf-container quic-wf-defenses
$ docker exec -it quic-wf-container /bin/bash

```

### Datasets

We provide datasets on [SWITCHDrive](https://drive.switch.ch/index.php/s/NDGjfJqrePU0G77) which can be used to as tests to run the attacks (instead of performing captures from scratch). If you want to perform your own captures, please follow the instructions in **code/capture/**.

The README has an overview of the datasets. 


### Paper

**Evaluating practical QUIC website fingerprinting defenses for the masses**
*Sandra Siby, Ludovic Barman, Christopher A. Wood, Marwan Fayed, Nick Sullivan, Carmela Troncoso* 
PETS 2023

Abstract -- Website fingerprinting (WF) is a well-known threat to users’ web privacy. New Internet standards, such as QUIC, include padding to support defenses against WF. Previous work on QUIC WF only analyzes the effectiveness of defenses when users are behind a VPN. Yet, this is not how most users browse the Internet. In this paper, we provide a comprehensive evaluation of QUIC-padding-based defenses against WF when users directly browse the web, i.e., without VPNs, HTTPS proxies, or other tunneling protocols. We confirm previous claims that application-agnostic transport-layer padding cannot provide effective protection against powerful adversaries capable of observing all traffic traces. We further demonstrate that such padding is ineffective even against adversaries with constraints on traffic visibility and processing power. At the  pplication layer, we show that defenses need to be deployed by both first and third parties, and that they can only thwart traffic analysis in limited situations. We identify challenges to deploy effective WF defenses and provide recommendations to address them.

[Link to full paper, coming soon!]

### Citation

If you use the code/data in your research, please cite our work as follows:

```
@inproceedings{Siby23QUICWF,
  title     = {Evaluating practical QUIC website fingerprinting defenses for the masses},
  author    = {Sandra Siby, Ludovic Barman, Christopher A. Wood, Marwan Fayed, Nick Sullivan, Carmela Troncoso},
  booktitle = {PETS},
  year      = {2023}
}
```