# QUIC + non-QUIC capture via Firefox or Chrome

## Prerequisites

- Dumpcap 2.6.10
- Firefox 79.0
- Chrome
- Python 3.6
- Pip 9.0
- psutil
- Selenium 3.141.0 (`pip3 install selenium`)
- webdriver-manager

## Capturing

### Dummy capture

**Note: Traffic from other apps will be mixed-in.** This is to test the process. See below for the real setup.

1. Change your interface in `automate-capture.sh`. Line to be changed is `CAPTURE_INTERFACE=`

2. Modify the PROFILE variable to set the kind of experiment you want in `automate-capture.sh:22-32`

3. Run `./capture-url.sh INTERFACE URL PROFILE OUTPUT_PATH`. You should see the title of the webpage being printed on stdout.

For instance `./capture-url.sh veth1 blog.cloudflare.com firefox-quic-default dataset`

It will create:

```
dataset
└── firefox-quic-default
    ├── geckodriver.log
    ├── capture.pcap
    ├── python_log.txt
    └── sslkeys.txt
```

### Isolated capture using Network Namespaces

#### One time setup

1. To silence Firefox, add the contents `setup/hosts` to `/etc/hosts`.

```
sudo cat setup/hosts >> /etc/hosts
```

2. To prevent Firefox auto-update queries, add the `setup/policies` files in `/opt/firefox/distribution/` or where Firefox is installed. Add a symlink `policies.json` -> `policies` (which one is read depends on the plateform).

3. Setup a network namespace named `netns1` with an interface `veth1` with IP `10.1.1.1`.
See [setup/setup-ns.sh](setup/setup-ns.sh) for how to do this.

#### Run a capture

1. If you deployed this script in a VPS accessible through SSH, work in `screen` or `tmux`.

2. **Ensure you are in the network namespace:** Run `ip link`, if you don't see `veth1`, run `# ip netns exec netns1 bash` to enter the network namespace as `root`.

3. Run `./automate-capture.sh`. It runs the script `./capture-url.sh` in a loop, iterating over the contents of `urls`.
