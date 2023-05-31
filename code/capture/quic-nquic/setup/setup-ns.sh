#!/bin/sh

# NOTE: it is best to run the commands one by one, some of them are blocking anyway

sudo ip netns add netns1
sudo ip netns exec netns1 ip link list
sudo ip netns exec netns1 ip link set dev lo up
sudo ip netns exec netns1 ping 127.0.0.1 # test

sudo ip link add veth0 type veth peer name veth1
sudo ip link set veth1 netns netns1

sudo ip netns exec netns1 ip addr add 10.1.1.1/24 dev veth1
sudo ip netns exec netns1 ip link set dev veth1 up

sudo ip addr add 10.1.1.2/24 dev veth0
sudo ip link set dev veth0 up

ping 10.1.1.1 # test
sudo ip netns exec netns1 ping 10.1.1.2 # test

sudo sysctl net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE # maybe change interface !
sudo iptables -t nat -A POSTROUTING -o ens3 -j MASQUERADE # maybe change interface !

sudo ip netns exec netns1 ip ro add default via 10.1.1.2
sudo ip netns exec netns1 ping 1.1.1.1 # test

# References:
# https://github.com/Lekensteyn/netns
# http://sgros.blogspot.com/2017/04/how-to-run-firefox-in-separate-network.html
# https://lwn.net/Articles/580893/