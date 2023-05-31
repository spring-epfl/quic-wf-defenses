import numpy as np

def read_file(trace_file):

	data = np.load(trace_file, allow_pickle=True).item()
	return data

def site_map(url_file):

	with open(url_file) as f:
		lines = f.readlines()
	urls = [x.strip() for x in lines]

	return urls

def process_trace_data(trace_file, url_file):

	data = read_file(trace_file)
	src_ip = '10.1.1.1'
	trace_ip_list = []

	urls = site_map(url_file)

	for site, site_data in data.items():
		site_name = urls[int(site)]
		site_ips = []
		quic = site_data['quic']
		for sample, sample_data in quic.items():
			ip_data = sample_data['tls']
			sample_ips = []
			for ipd in ip_data:
				if (ipd[3] != src_ip) and (ipd[3] not in sample_ips):
					sample_ips.append(ipd[3])
			trace_ip_list.append((site_name, sample_ips))

	return trace_ip_list

			
if __name__ == "__main__":

	FNAME = "/Users/siby/Documents/summary_quic_tls_split.npy"
	URL_FNAME = "urls"
	trace_ip_list = process_trace_data(FNAME, URL_FNAME)

	print(trace_ip_list[:5])

