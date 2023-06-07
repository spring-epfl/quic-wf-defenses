from prettytable import PrettyTable
import json
import os

def print_table(data_dict, col1, col2, tag):

    """
    Function to print nice AS tables.
    """

    t = PrettyTable([col1, col2])
    for k, v in data_dict.items():
        if tag == "PercSite":
            t.add_row([k, v])
        else:
            t.add_row([k, str(v['mean']) + " +- " + str(v['std'])])
            
    print(t)


def get_as_hops(filename, dirname, traceroute_dir):

    """
    Function to get AS hop info from traceroute files.
    """

    full_name = os.path.join(traceroute_dir, dirname, filename)
    with open(full_name) as f:
        data = json.loads(f.read())

    asn_list = []
    result = data[0]['result']

    for item in result:
        hop_result = item['result'][0]
        asn = hop_result['asn']
        asn_list.append(asn)

    return asn_list

def read_har_file(dirname, har_dir):

    """
    Function to read HAR files.
    """

    full_name = os.path.join(har_dir, dirname + ".json")
    with open(full_name) as f:
        data = json.loads(f.read())

    return data

def get_quic_info(data, host):

    """
    Function to get quic info from HAR files.
    """

    for entry in data:
        if entry['host'] == host:
            return entry['uses_quic']

    return 'N/A'