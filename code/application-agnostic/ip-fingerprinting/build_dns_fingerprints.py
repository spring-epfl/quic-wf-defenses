import json
import os
import math
import numpy as np
from collections import Counter

def get_ip_entropy(ip_domain_map, domain_entropy_dict):

	ip_entropy_dict = {}

	for ip, domain_list in ip_domain_map.items():
		if len(domain_list) == 1:
			ip_entropy_dict[ip] = domain_entropy_dict[domain_list[0]]
		else:
			entropies = []
			for domain in domain_list:
				entropies.append(domain_entropy_dict[domain])

			ip_entropy_dict[ip] = np.mean(entropies)

	return ip_entropy_dict

def get_domain_entropy(subdomain_list):

	domain_entropy_dict = {}

	counts = Counter(subdomain_list)
	for subdomain, count in counts.items():
		prob_d = count/len(subdomain_list)
		entropy = -math.log2(prob_d)
		domain_entropy_dict[subdomain] = entropy

	return domain_entropy_dict

def get_subdomains(data):

	all_subdomains = []

	for domain, domain_info in data.items():
		for subdomain, iplist in domain_info.items():
			all_subdomains.append(subdomain)

	return all_subdomains

def build_ip_domain_map(data):

	ip_domain_map = {}

	for domain, domain_info in data.items():
		for subdomain, iplist in domain_info.items():
			for ip in iplist:
				if ip not in ip_domain_map:
					ip_domain_map[ip] = []

				if subdomain not in ip_domain_map[ip]:
					ip_domain_map[ip].append(subdomain)

	return ip_domain_map


def build_ip_fingerprint(data):

	ip_fingerprint = {}

	for domain, domain_info in data.items():
		if domain not in ip_fingerprint:
			ip_fingerprint[domain] = {0 : [], 1: []}

		for subdomain, iplist in domain_info.items():
			if subdomain == domain:
				ip_fingerprint[domain][0] += iplist
			else:
				ip_fingerprint[domain][1] += iplist

	return ip_fingerprint


def read_file(dns_file):

	data = {}
	with open(dns_file) as f:
		data = json.loads(f.read())

	return data

def get_dns_fingerprint_info(dns_folder):

	fnames = os.listdir(dns_folder)
	ip_fingerprint_all = {}
	ip_domain_map_all = {}
	subdomain_list_all = []

	for fname in fnames:
		
		filepath = os.path.join(dns_folder, fname)
		data = read_file(filepath)

		ip_fingerprint = build_ip_fingerprint(data)
		ip_domain_map = build_ip_domain_map(data)
		subdomain_list = get_subdomains(data)
		
		for k, v in ip_fingerprint.items():
			if k not in ip_fingerprint_all:
				ip_fingerprint_all[k] = {0 : [], 1 : []}
			ip_fingerprint_all[k][0] += v[0]
			ip_fingerprint_all[k][1] += v[1]

			ip_fingerprint_all[k][0] = list(set(ip_fingerprint_all[k][0]))
			ip_fingerprint_all[k][1] = list(set(ip_fingerprint_all[k][1]))

		for k, v in ip_domain_map.items():
			if k not in ip_domain_map_all:
				ip_domain_map_all[k] = []
			ip_domain_map_all[k] += v
			ip_domain_map_all[k] = list(set(ip_domain_map_all[k]))

		subdomain_list_all += subdomain_list

	domain_entropy_dict = get_domain_entropy(subdomain_list_all)
	ip_entropy_dict = get_ip_entropy(ip_domain_map_all, domain_entropy_dict)

	return ip_entropy_dict, ip_fingerprint_all


if __name__ == "__main__":

	DNS_FOLDER = "dns_data/"
	ip_entropy_dict, ip_fingerprint = get_dns_fingerprint_info(DNS_FOLDER)

	with open("ip_entropy.json", "w") as f:
		f.write(json.dumps(ip_entropy_dict, indent=4))

	with open("ip_fingerprint.json", "w") as f:
		f.write(json.dumps(ip_fingerprint, indent=4))
