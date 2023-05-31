import json
import os
import numpy as np
from matplotlib import pyplot as plt

def read_url_file(fname):

    with open(fname) as f:
        urls = f.readlines()
        urls = [x.strip() for x in urls]

    return urls


def process_json(data):

    hop_list = []
    result = data[0]['result']
    num_hops = len(result)
    num_asterisks = 0
    for item in result:
        hop_num = item['hop']
        hop_result = item['result'][0]
        ip = hop_result['from']
        if ip == '*':
            num_asterisks += 1
        hop_list.append(ip)

    return num_hops, num_asterisks, hop_list

def get_hop_differences(hop_list_all_runs):

    n = len(hop_list_all_runs)
    list_len = [len(x) for x in hop_list_all_runs]
    print(list_len)
    max_hops = max(list_len)
    num_ips_at_hop = []
    
    for i in range(0, max_hops):
        ip_at_hop = []
        for item in hop_list_all_runs:
            if len(item) > i:
                ip_at_hop.append(item[i])
        num_ips = len(set(ip_at_hop))
        if (num_ips == 1) & ('*' in ip_at_hop):
            num_ips = -1
        num_ips_at_hop.append(num_ips)
    return num_ips_at_hop

def process_file(output_dir, tag, num_runs=5):

    num_hops_list = []
    perc_asterisk_list = []
    hop_list_all_runs = []

    for ct in range(1, num_runs+1):
        fname = tag + str(ct) + ".json"
        fname = os.path.join(output_dir, fname)
        with open(fname) as f:
            try:
                data = json.loads(f.read())
                num_hops, num_asterisks, hop_list = process_json(data)
                num_hops_list.append(num_hops)
                perc_asterisk_list.append(num_asterisks/num_hops * 100)
                hop_list_all_runs.append(hop_list)
            except Exception as e:
                print(e)
    num_ips_at_hop = get_hop_differences(hop_list_all_runs)

    return num_hops_list, perc_asterisk_list, num_ips_at_hop

def plot_data(all_hops, all_perc_asterisk, all_ip_at_hop, urls):

    hops_mean = [np.mean(x) for x in all_hops]
    hops_std = [np.std(x) for x in all_hops]
    ind = np.arange(len(urls))
    
    plt.bar(ind, hops_mean, yerr=hops_std)
    plt.xticks(ind, urls, rotation='vertical')
    plt.ylabel("Number of hops")
    plt.show()


    ast_mean = [np.mean(x) for x in all_perc_asterisk]
    ast_std = [np.std(x) for x in all_perc_asterisk]
    plt.bar(ind, ast_mean, yerr=ast_std)
    plt.xticks(ind, urls, rotation='vertical')
    plt.ylabel("% asterisks in route")
    plt.show()

    for i in range(0, len(urls)):
        x_data = range(0, len(all_ip_at_hop[i]))
        plt.plot(x_data, all_ip_at_hop[i], 'o-', label=urls[i])
    plt.ylabel("Number of IPs seen")
    plt.xlabel("Hop")
    plt.legend()
    plt.show()

    for i in range(0, len(urls)):
        x_data = range(0, len(all_ip_at_hop[i]))
        x_data = [(x+1)/len(all_ip_at_hop[i]) * 100 for x in x_data]
        plt.plot(x_data, all_ip_at_hop[i], 'o-', label=urls[i])
    plt.legend()
    plt.ylabel("Number of IPs seen")
    plt.xlabel("Hop as a % of total route")
    plt.show()

def process_files(output_dir, url_file, num_runs=5):

    urls = read_url_file(url_file)[:5]
    filenames = os.listdir(output_dir)

    all_hops = []
    all_perc_asterisk = []
    all_ip_at_hop = []

    for i in range(0, len(urls)):
        tag = "out" + str(i) + "_"
        num_hops_list, perc_asterisk_list, num_ips_at_hop = process_file(output_dir, tag)
        all_hops.append(num_hops_list)
        all_perc_asterisk.append(perc_asterisk_list)
        all_ip_at_hop.append(num_ips_at_hop)

    plot_data(all_hops, all_perc_asterisk, all_ip_at_hop, urls)


if __name__ == "__main__":

    OUTPUT_DIR = "../outputsc"
    URL_FILE = "../urls_test"
    NUM_RUNS = 5
    process_files(OUTPUT_DIR, URL_FILE, NUM_RUNS)