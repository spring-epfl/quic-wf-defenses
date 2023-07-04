# Traffic capture

## Overview

This folder contains the code for various traffic-capture scenarios in the paper. The sub-folders each deal with a capture setup and are as follows:

1. ***quic-percentage/*** : Capture setup to calculate the amount of QUIC traffic for each website. Run this before the main capture to obtain a list of websites that primarily contain QUIC traffic.

2. ***quic-nquic/*** : Main capture setup (used in Section 4 experiments). This is used to capture QUIC (or non-QUIC) traffic for a list of websites.

3. ***hars/*** : Capture HAR files of different websites (used in Section 5 analysis).

4. ***traceroutes/*** : Capture traceroutes (used in Section 4 constrained adversary).

5. ***links/*** : Obtain links of sub-pages for a list of websites (used in Section 4 heterogeneous-world experiment).

6. ***screenshots/*** : Takes screenshots of the page (used for debugging purposes).


## Network setup

Firefox uses some auto-update features which might hinder our data collection. To silence them, add the contents `setup/hosts` to `/etc/hosts`.

```
$ cd /quic-wf-defenses/capture
$ sudo cat setup/hosts >> /etc/hosts
```

To disable Firefox auto-update, we provide a configuration that you can add in `/opt/firefox/distribution/` (or in the `distribution` directory at the location where Firefox is installed).

```
$ sudo cp setup/opt_firefox_distribution_policies /opt/firefox/distribution/policies
$ sudo ln -s policies /opt/firefox/distribution/policies.json
```

To avoid other traffic getting mixed, we need to setup a network namespace named `netns1` with an interface `veth1` with IP `10.1.1.1` which we will use to capture data.
As this operation can be a bit complex, we provide a script `setup-ns.sh` to do this network setup.

```
$ sudo bash setup/setup-ns.sh
```

We can then execute a shell in the virtual network environment and drop priviledges to run the captures as a normal user.

```
$ sudo ip netns exec netns1 bash
# su quicuser
```

To enure that you are using the correct network, you can check that you have a `veth1` interface.

```
$ ip link
...
x: veth1: ...
...
```

## Evaluating which Websites to Capture

As QUIC is not yet widely deployed, it is important to select a subset of website which are already using QUIC.
We evaluate if a website should be included in that subset by measuring the percentage of QUIC request a browser make to other hostnames while visiting that website.
We wrote scripts to automate this process.

To reproduce our data set, assuming we are using a Docker container set up as proposed in the README at the root of this repository, we first call a shell script to retrieve data from websites and extract HAR data from them.

```
$ cd /quic-wf-defenses/capture/quic-percentage
$ bash automate-capture.sh /data/urls.txt "/data/$(date +%Y%m%d)"
```

Then we parse pare the collected HAR files to evaluate which website is doing the highest percentage of external QUIC connections. Then order them by percentage and extract the first 200 websites by this criteria.

```
$ python3 parse_har.py /data/urls.txt "/data/$(date +%Y%m%d)/percentage" "/data/$(date +%Y%m%d)/percentage.csv" -n 200
```

## Capture Traffic from Website subset

To test that the capture is working, you can run a single capture of one website, for example to capture `blog.cloudflare.com` by using the Firefox browser:

```
$ cd /quic-wf-defenses/capture/quic-nquic
$ bash capture-url.sh veth1 blog.cloudflare.com firefox-quic-default /tmp/foo
```

You should see the title of the webpage being printed on stdout, and the script should create the following files:

```
/tmp/foo
└── firefox-quic-default
    ├── geckodriver.log
    ├── capture.pcap
    ├── python_log.txt
    └── sslkeys.txt
```

If everything is good, we can run a real capture, but first, depending of the kind of experiment we are running, we might want to modify the PROFILE variable in `automate-capture.sh:22-32` to set it to the profile we want to use with our favourite editor, and possibly change the list of URLs we want to capture in `automate-capture.sh:18`.

```
$ nano automate-capture.sh
```

Finally, we can run the script`./automate-capture.sh` which will runs the script `./capture-url.sh` in a loop, iterating over the URLs.

```
$ bash automate-capture.sh
```

## Capture HAR Files of Websites

We provided a script to extract HAR data from scrapped websites.

```
$ cd /quic-wf-defenses/capture/hars
$ bash automate-capure.sh /data/good_urls.txt "/data/$(date +%Y%m%d)/hars"
```

## Scrap Links of Sub-pages

We provide a script to do a simple links extraction from a website.

```
$ cd /quic-wf-defenses/capture/links
$ python3 links-capture.py /data/good_urls.txt "/data/$(date +%Y%m%d)/links"
```

## Traceroute Experiments

We wrote a script to run a normal traceroute N times for a list of URLs:

```
$ cd /quic-wf-defenses/capture/traceroutes
$ bash loop-tr.sh URLS OUTPUT_DIR N
```

where URLS is a file containing the URLs you want to traceroute, OUTPUT_DIR is the output directory, and N is the number of times you want to run a traceroute for a URL.

### Using trAIxroute

We use another tool **trAIxroute** . Advantages of using this:

1. It can run both normal traceroute and Paris-traceoute, so we can compare the results.
2. It can provide results on IXPs in the route (useful if we consider an IXP adversary).

```
$ python3 -m traixroute -thread probe -t -dest google.ch
```

Replace `-t` with `-sc ` to run Paris traceroute.

**Note:** we can also get ASN information with `-asn` flag.

We wrote a script to run a trAIxroute traceroute N times for a list of URLs:

```
$ bash run-traixroute.sh URLS OUTPUT_DIR N
```

where URLS is a file containing the URLs you want to traceroute, OUTPUT_DIR is the output directory, and N is the number of times you want to run a traceroute for a URL.

### Creating different views from traceroutes

In our Section 4 (constrained adversary) experiments, we have to create different 'views' of the traffic based on the AS they pass through. In order to do this, we have to know which resource network traffic passes through which AS, and create partial traces for them. We can do this using the following steps:

1. Run a HAR capture in **capture/har-capture**.
2. Run **parse-hars.py** to create a directory of URLs for each website visit.
3. Run **run-traixroute-har.sh** on the directory of URLS to obtain traceroutes.
4. Use the scripts in **processing-scripts** to create partial traces. The scripts take in full PCAPS, traceroutes, HAR files, and specified AS, and outputs PCAPS with only traffic passing through that AS.
