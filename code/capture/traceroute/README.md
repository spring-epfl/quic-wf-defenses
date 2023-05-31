# Traceroute experiments



This folder contains resources required for the traceroute analysis. 

To run a normal traceroute, please use the script:

```
./loop-tr.sh N
```

where N is the number of times you want to run a traceroute for a URL. URLs are read from a file "urls" in the same directory. 

We use another tool **trAIxroute** . Advantages of using this:

1. It can run both normal traceroute and Paris-traceoute, so we can compare the results.
2. It can provide results on IXPs in the route (useful for the IXP adversary).

### Using trAIxroute

Use the [latest version](https://github.com/gnomikos/traIXroute) from GitHub, installation via pip throws an error (tested on MacOS 10.14 with Python 3.7).  Once installed, run as follows:

```
sudo ./traIXroute/bin/traixroute -thread probe -t -dest google.ch
```

Replace `-t` with `-sc ` to run Paris traceroute.

Note: we can also get ASN information with `-asn` flag.