import os
import json
from random import sample
import numpy as np
import socket
from scapy.all import *
from scapy.layers.tls.all import *
from utils import *

def process_pcap(pcap, ip_list, ip_uses_quic, resource_list, output_dir):

    """
    Function to process a single pcap file using Scapy.
    Args:
        pcap: Input file
        ip_list: List of IPs corresponding to the resources seen by the AS. Used to filter traffic.
        ip_uses_quic: List of indicators whether IP uses quic (not used currently).
        resource_list: List of resource domain names.
        output_dir: Output directory where output pcap should be placed.
    The output is a pcap with partial trace in the output directory.
    """

    try:
        # We first do a simple IP comparison. If the destination IP of a packet is in the
        # IP list, we keep that packet. We also log this IP.
        seen_ips = []
        new_pkts = []
        pkts = rdpcap(pcap)
        for pkt in pkts:
            if pkt.haslayer(IP):
                src = pkt[IP].src
                dst = pkt[IP].dst
                if dst in ip_list:
                    new_pkts.append(pkt)
                    seen_ips.append(dst)
                elif src in ip_list:
                    new_pkts.append(pkt)
                    seen_ips.append(src)

        # Our resource-IP mapping might not be perfect. IPs could have changed.
        # For example A.com might now correspond to 1.2.3.5 instead of 1.2.3.4.
        # We do the next step to handle this case.
        # We look at the SNI in the ClientHellos to see if the host name corresponds to the resource.
        # If it does, we log that IP, and also keep the packet corresponding to the IP.

        missed_ips = set(ip_list) - set(seen_ips)
        ips_to_keep = []

        if len(missed_ips) > 0:
            for pkt in pkts:
                if pkt.haslayer(TLS_Ext_ServerName):
                    if pkt.haslayer(ServerName):
                        servername = pkt[ServerName].servername.decode()
                        if servername in resource_list:
                            dst = pkt[IP].dst
                            if dst not in seen_ips:
                                ips_to_keep.append(dst)

            for pkt in pkts:
                if pkt.haslayer(IP):
                    dst = pkt[IP].dst
                    src = pkt[IP].src
                    if dst in ips_to_keep:
                        new_pkts.append(pkt)
                    elif src in ips_to_keep:
                        new_pkts.append(pkt)

        # We sort the selected packets by timestamp.
        sorted_new_pkts = sorted(new_pkts, key=lambda ts: ts.time)
        # We write the packets to output.
        wrpcap(os.path.join(output_dir, "capture.pcap"), sorted_new_pkts)

    except Exception as e:
        print("Error processing pcap:", pcap, e)


def transform_traces(asn_process_dict, pcaps_dir, output_dir, tag="quic"):

    """
    Function to create traces for the partial adversary given full traces.
    Args:
        asn_process_dict: Dictionary of resources seen by the adversary (from get_as_routes())
        pcaps_dir: Directory of pcap files for full traces
        output_dir: Output directory where new traces should be placed
        tag: Tag indicating whether dataset is quic or not 
    The output is a set of pcaps written to the output_dir (file structure is the same as input directory)
    """

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    for k, v in asn_process_dict.items():

        try:
            site_dir = os.path.join(pcaps_dir, k)
            sample_dirs = os.listdir(site_dir)
            

            for sample_dir in sample_dirs:

                ip_list = []
                ip_uses_quic = []
                filename = os.path.join(site_dir, sample_dir, tag, "capture.pcap")
                full_output_dir = os.path.join(output_dir, k, sample_dir, tag)
                os.makedirs(full_output_dir, exist_ok=True)
                for i in range(0, len(v['resources'])):
                    resource = v['resources'][i]
                    try:
                        ip = socket.gethostbyname(resource)
                        ip_list.append(ip)
                        ip_uses_quic.append(v['uses_quic'][i])
                    except Exception as e:
                        print("Error with IP mapping:", e, resource)

                process_pcap(filename, ip_list, ip_uses_quic, v['resources'], full_output_dir)

        except Exception as e:
            print("Error transforming traces:", e)

def process_traceroute_files(traceroute_dir):

    """
    Function to process traceroutes to get ASN/route information.
    Used by print_as_info().
    Args:
        directory of traceroutes
    Returns:
        seen_dict: Dictionary { Site : { ASN : % routes seen }}
        asn_dict: Dictionary { Traceroute filename : Set of valid ASes in route}
        total_sites: Number of sites with successful traceroutes.
    """

    seen_dict = {}
    asn_dict = {}

    dirnames = os.listdir(traceroute_dir)
    print("Total number of successful traceroute sites:", len(dirnames))
    total_sites = len(dirnames)

    for dirname in dirnames:

        seen_persite_dict = {}
        persite_routes = 0
        seen_dict[dirname] = {}

        filenames = os.listdir(os.path.join(traceroute_dir, dirname))
        if len(filenames) == 0:
            print("No traceroute for:", dirname)
            continue

        persite_routes += len(filenames)

        for filename in filenames:

            asn_list = get_as_hops(filename, dirname, traceroute_dir)
            good_asn_list = [x for x in asn_list if x != '*']

            full_name = os.path.join(traceroute_dir, dirname, filename)
            asn_dict[full_name] = set(good_asn_list)

            for item in set(good_asn_list):
                if item not in seen_persite_dict:
                    seen_persite_dict[item] = 0
                seen_persite_dict[item] += 1

        for k, v in seen_persite_dict.items():
            perc_seen = v/persite_routes * 100
            seen_dict[dirname][k] = perc_seen

    return seen_dict, asn_dict, total_sites

def get_as_routes(ASN, traceroute_dir, har_dir):

    """
    Function that takes in an AS number and returns the resources seen by the AS.
    This is used to create the partial traces.
    Args:
        ASN: The adversary AS number.
        traceroute_dir: Directory of traceroutes.
        har_dir: Directory of har files.
    Returns:
        asn_resources_dict: Dictionary { Site1 : { 'resources' : [List of resource domains],
                                                   'uses_quic' : [List of whether each domain uses quic]
                                                   },
                                        Site2: ...}
    """

    asn_resources_dict = {}
    ASN = str(ASN)

    seen_dict, good_asn_dict, total_sites = process_traceroute_files(traceroute_dir)

    dirnames = os.listdir(traceroute_dir)

    for dirname in dirnames:

        asn_resources_dict[dirname] = { 'resources' : [], 'uses_quic' : [] }
        har_data = read_har_file(dirname, har_dir)

        filenames = os.listdir(os.path.join(traceroute_dir, dirname))
        if len(filenames) == 0:
            print("No traceroute for:", dirname)
            continue

        for filename in filenames:

            full_name = os.path.join(traceroute_dir, dirname, filename)
            good_asns = good_asn_dict[full_name]
            
            if ASN in good_asns:
                asn_resources_dict[dirname]['resources'].append(filename[:-5])
                uses_quic = get_quic_info(har_data, filename[:-5])
                asn_resources_dict[dirname]['uses_quic'].append(uses_quic)

    return asn_resources_dict



def print_as_info(traceroute_dir):

    """
    Function to print information about routes seen by each AS in the dataset.
    Use this to decide which AS to pick as adversary.
    Args:
        directory of traceroutes
    Prints:
        Table 1: ASN and % of sites that it sees.
        Table 2: ASN and mean/std % of routes per site that it sees. 

    """

    asn_seen_percroute = {}
    asn_seen_percsite = {}

    seen_dict, asn_dict, total_sites  = process_traceroute_files(traceroute_dir)
   
    for k, v in seen_dict.items():
        perc_seen = []
        for k1, v1 in v.items():
            perc_seen.append(v1) 

        for k1, v1 in v.items():
            if k1 not in asn_seen_percroute:
                asn_seen_percroute[k1] = []
            if k1 not in asn_seen_percsite:
                asn_seen_percsite[k1] = 0
            asn_seen_percsite[k1] += 1
            asn_seen_percroute[k1].append(v1)

    asn_seen_percroute_processed = {}
    for k, v in asn_seen_percroute.items():
        asn_seen_percroute_processed[k] = {'mean' : np.mean(v), 'std' : np.std(v)}

    asn_seen_percroute_processed = {k: v for k, v in sorted(asn_seen_percroute_processed.items(), key=lambda item: item[1]['mean'], reverse=True)}  
    
    asn_seen_percsite_processed = {}
    for k, v in asn_seen_percsite.items():
        asn_seen_percsite_processed[k] = v/total_sites * 100

    asn_seen_percsite_processed = {k: v for k, v in sorted(asn_seen_percsite_processed.items(), key=lambda item: item[1], reverse=True)}  
    
    print_table(asn_seen_percsite_processed, 'ASN', '% of sites seen', "PercSite")
    print_table(asn_seen_percroute_processed, 'ASN', '% of routes seen per site', "PercRoute")
    

def main():


    TRACEROUTE_DIR = "../traceroutehar/output_lb_100p_150/" #Traceroute directory # traIXrouteVPS/outputquic150
    HAR_DIR = "../outputhar_lb_quic-100p-150/all/" #HAR file directory
    ASN = 15169 #Chosen ASN adversary
    PCAP_DIR = "/home/jwhite/d/git/quic-fingerprinting/cf-clusters-datasets/cluster-203-2/pcaps" #Input pcaps
    OUTPUT_DIR = "/home/jwhite/d/git/quic-fingerprinting/cf-clusters-datasets/cluster-203-2-AS-view/pcaps" #Output directory for processed pcaps


    print_as_info(TRACEROUTE_DIR)
    asn_process_dict = get_as_routes(ASN, TRACEROUTE_DIR, HAR_DIR)
    #transform_traces(asn_process_dict, PCAP_DIR, OUTPUT_DIR)

if __name__ == "__main__":

    main()