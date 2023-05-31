from build_dns_fingerprints import *
from build_trace_fingerprints import *
from sklearn.metrics import accuracy_score

def match_secondary_ips(candidates, trace_ips, ip_entropy_dict):

	candidate_entropy_dict = {}

	secondary_trace_ips = trace_ips[1:]

	for ti in secondary_trace_ips:
		for domain, ip_info in candidates.items():
			secondary_ips = ip_info[1]
			if ti in secondary_ips:
				if domain not in candidate_entropy_dict:
					candidate_entropy_dict[domain] = 0
				candidate_entropy_dict[domain] += ip_entropy_dict[ti]

	predicted_domain = max(candidate_entropy_dict, key=candidate_entropy_dict.get)

	return predicted_domain

def get_candidates(ip_fingerprint, trace_ips):

	primary_ip = trace_ips[0]
	candidates = {}

	for domain, ip_info in ip_fingerprint.items():
		primary_ip_candidates = ip_info[0]
		for pi in primary_ip_candidates:
			if pi == primary_ip:
				candidates[domain] = ip_info

	return candidates

def pipeline(dns_folder, trace_file, url_file):

	ip_entropy_dict, ip_fingerprint = get_dns_fingerprint_info(dns_folder)
	trace_ip_list = process_trace_data(trace_file, url_file)

	truths = []
	preds = []
	failures = 0

	for traces in trace_ip_list:
		try:
			#print(traces)
			true_domain = traces[0]
			trace_ips = traces[1]
			
			candidates = get_candidates(ip_fingerprint, trace_ips)
			#print(candidates)
			predicted_domain = match_secondary_ips(candidates, trace_ips, ip_entropy_dict)
			#print(predicted_domain)
			truths.append(true_domain)
			preds.append(predicted_domain)
		except Exception as e:
			#print(traces, e)
			failures += 1
			continue

		#break

	print("Accuracy:", accuracy_score(truths, preds))
	print("Failures:", failures/len(trace_ip_list))

	correct = []
	wrong = []

	for i in range(0, len(truths)):
		if truths[i] == preds[i]:
			correct.append(truths[i])
		else:
			wrong.append(truths[i])

	correct = set(correct)
	wrong = set(wrong)

	with open("correct", "w") as f:
		for item in correct:
			f.write(item + "\n")

	with open("wrong", "w") as f:
		for item in wrong:
			f.write(item + "\n")


if __name__ == "__main__":

	DNS_FOLDER = "dns_data/"
	TRACE_FILE = "/Users/siby/Downloads/summary_quic_tls_split.npy"
	URL_FILE = "urls"

	pipeline(DNS_FOLDER, TRACE_FILE, URL_FILE)

