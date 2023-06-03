from build_dns_fingerprints import *
from build_trace_fingerprints import *
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import random
import argparse

def match_secondary_ips(candidates, trace_ips, ip_entropy_dict, primary):

	candidate_entropy_dict = {}

	if primary:
		secondary_trace_ips = trace_ips[1:]
	else:
		secondary_trace_ips = trace_ips

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


def process_tps(fname, url_file):

	with open(url_file) as f:
		lines = f.readlines()
	urls = [x.strip() for x in lines]

	with open(fname) as f:
		lines = f.readlines()
		truths = [x.split("|")[0].strip() for x in lines]
		truths = [urls[int(x)] for x in truths]

	return truths


def choose_data(trace_ip_list, i, url_file, tp_folder):

	trace_list = []
		
	fname = tp_folder + "/tp_" + str(i)
	truths = process_tps(fname, url_file)
	truth_counts = Counter(truths)
	
	for truth, count in truth_counts.items():
		rel_traces = []
		for item in trace_ip_list:
			if item[0] == truth:
				rel_traces.append(item)
		try:
			chosen = random.sample(rel_traces, count)
			trace_list += chosen
		except Exception as e:
			print(e, count, rel_traces)

	return trace_list


def pipeline(dns_folder, trace_file, url_file, tp_folder, primary):

	ip_entropy_dict, ip_fingerprint = get_dns_fingerprint_info(dns_folder)
	trace_ip_list = process_trace_data(trace_file, url_file)

	for i in range(0, 10):

		chosen = choose_data(trace_ip_list, i, url_file, tp_folder)
		print("Chose:", i, len(chosen))
		truths = []
		preds = []
		failures = 0

		for traces in chosen:
			try:
				true_domain = traces[0]
				trace_ips = traces[1]

				if primary:
					candidates = get_candidates(ip_fingerprint, trace_ips)
					if len(candidates.keys()) == 0:
						candidates = ip_fingerprint
				else:
					candidates = ip_fingerprint
				predicted_domain = match_secondary_ips(candidates, trace_ips, ip_entropy_dict, primary)
				truths.append(true_domain)
				preds.append(predicted_domain)
			except Exception as e:
				#print(e)
				truths.append(true_domain)
				preds.append("Failed")
				failures += 1
				#continue

		print("Accuracy:", accuracy_score(truths, preds))
		print("Failures:", failures/len(trace_ip_list))

		with open("overall_results", "a") as f:
			f.write("\n")
			f.write(" Accuracy: " + str(accuracy_score(truths, preds)))
			f.write("\n")
			f.write(" F1-score: " + str(f1_score(truths, preds, average='macro')))
			f.write("\n")
			f.write(" P-score: " + str(precision_score(truths, preds, average='macro')))
			f.write("\n")
			f.write(" R-score: " + str(recall_score(truths, preds, average='macro')))
			f.write("\n")
			f.write("Failures: " + str(failures/len(trace_ip_list)))
			f.write("\n")		

		with open("tp_results_" + str(i), "w") as f:
			for j in range(0, len(truths)):
				f.write(truths[j] + " | " + preds[j] + "\n")

def main(program, args):

    # Create argument parser and arguments
    parser = argparse.ArgumentParser(prog=program, description="Run comparison between website fingerprinting and IP fingerprintng.")
    parser.add_argument(
        "--dnsdata",
        type=str,
        help="Folder path containing DNS data.",
        default="dns_data/"
    )
    parser.add_argument(
        "--tracefile",
        type=str,
        help="File path containing trace data.",
        default="summary_quic_tls_split.npy"
    )
    parser.add_argument(
        "--urls",
        type=str,
        help="File path list of sites.",
        default="urls"
    )
    parser.add_argument(
        "--tpfolder",
        type=str,
        help="Folder containing truths/predictions files.",
        default="tp_folder/"
    )
    parser.add_argument(
        "--primary",
        type=bool,
        help="Consider primary IP.",
        default=False
    )

    ns = parser.parse_args(args)
    pipeline(ns.dnsdata, ns.tracefile, ns.urls, ns.tpfolder, ns.primary)


if __name__ == "__main__":

    main(sys.argv[0], sys.argv[1:])

