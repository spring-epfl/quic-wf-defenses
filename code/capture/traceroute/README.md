# Traceroute experiments

This folder contains resources required for the traceroute analysis. 

To run a normal traceroute, first create a file called **urls** where each line is a URL that you want to run traceroute on, and run the script:

```
./loop-tr.sh N
```

where N is the number of times you want to run a traceroute for a URL. 

### Using trAIxroute

We use another tool **trAIxroute** . Advantages of using this:

1. It can run both normal traceroute and Paris-traceoute, so we can compare the results.
2. It can provide results on IXPs in the route (useful if we consider an IXP adversary).

Use the [latest version](https://github.com/gnomikos/traIXroute) from GitHub, installation via pip throws an error (tested on MacOS 10.14 with Python 3.7).  Once installed, run as follows:

```
sudo ./traIXroute/bin/traixroute -thread probe -t -dest google.ch
```

Replace `-t` with `-sc ` to run Paris traceroute.

Note: we can also get ASN information with `-asn` flag.

We have the following script using trAIxroute:

**run-traixroute.sh** runs traIXroute on a list of URLs sepcified in a file **urls**. Change lines 14 and 16 depending on the type of traceroute you want to run. 

### Creating different views from traceroutes 

In our Section 4 (constrained adversary) experiments, we have to create different 'views' of the traffic based on the AS they pass through. In order to do this, we have to know which resource network traffic passes through which AS, and create partial traces for them. We can do this using the following steps:

1. Run a HAR capture in **capture/har-capture**.
2. Run **parse-hars.py** to create a directory of URLs for each website visit.
3. Run **run-traixroute-har.sh** on the directory of URLS to obtain traceroutes.
4. Use the scripts in **processing-scripts** to create partial traces. The scripts take in full PCAPS, traceroutes, HAR files, and specified AS, and outputs PCAPS with only traffic passing through that AS. 