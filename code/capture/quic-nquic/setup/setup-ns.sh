#!/bin/sh

ip netns add netns1
ip netns exec netns1 ip link list
ip netns exec netns1 ip link set dev lo up
echo 'Test loopback in network namespace.'
ip netns exec netns1 ping -c 1 127.0.0.1

ip link add veth0 type veth peer name veth1
ip link set veth1 netns netns1

ip netns exec netns1 ip addr add 10.1.1.1/24 dev veth1
ip netns exec netns1 ip link set dev veth1 up

ip addr add 10.1.1.2/24 dev veth0
ip link set dev veth0 up

sysctl net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE # maybe change interface !

ip netns exec netns1 ip ro add default via 10.1.1.2

echo 'Test connectivity via in network namespace.'
ip netns exec netns1 ping -c 1 1.1.1.1

# References:
# https://github.com/Lekensteyn/netns
# http://sgros.blogspot.com/2017/04/how-to-run-firefox-in-separate-network.html
# https://lwn.net/Articles/580893/
