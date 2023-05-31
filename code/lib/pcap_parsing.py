
import sys
import os
import glob
import subprocess
import shlex
from operator import itemgetter

DIRECTION_INCOMING = -1
DIRECTION_OUTGOING = 1
SOURCE_IP = '10.1.1.1'


def parse_list_of_numbers(val):
    if val.strip() == '':
        return []
    return [int(l) for l in val.split(',')]


# runs tshark on a .pcap, extracts TLS & QUIC packets, outputs: [Time in sec, Source IP, [List of TLS lengths], QUIC length], last two fields are potentially empty
TSHARK_FILTER = '(tls or quic) and !(_ws.expert.severity == error) and !(_ws.malformed) and !(_ws.expert.message ~ \\"Ignored unknown record\\")'
TSHARK_COMMAND = 'tshark -r {{0}} -Y "{0}" -e _ws.col.Time -e ip.src -e tls.record.length -e quic.packet_length -Tfields'.format(
    TSHARK_FILTER)


def parse_tshark_line(l):
    parts = l.split('\t')

    time_sec = float(parts[0])
    source_ip = str(parts[1])

    lengths_tls = []
    lengths_quic = []

    if len(parts) >= 3:
        lengths_tls = parse_list_of_numbers(parts[2])
    if len(parts) == 4:
        lengths_quic = parse_list_of_numbers(parts[3])

    return time_sec, source_ip, lengths_tls,  lengths_quic


def text_to_timestamp_sizes(txt):
    lines = txt.split('\n')
    lines = [l.strip() for l in lines]

    res = []

    time0 = None

    for l in lines:
        if l.strip() == "":
            continue

        time_sec, source_ip, lengths_tls, lengths_quic = parse_tshark_line(l)

        if time0 is None:
            time0 = time_sec

        direction = DIRECTION_INCOMING
        if source_ip == SOURCE_IP:
            direction = DIRECTION_OUTGOING

        # add all TLS packet in this record, if any
        for l in lengths_tls:
            res.append([time_sec-time0, direction*l])

        # add all QUIC packet in this record, if any
        for l in lengths_quic:
            res.append([time_sec-time0, direction*l])

    res.sort(key=itemgetter(0))

    return res


def text_to_timestamp_sizes_separate_quic_tls_traffic(txt):
    lines = txt.split('\n')
    lines = [l.strip() for l in lines]

    quic = []
    tls = []

    time0 = None

    for l in lines:
        if l.strip() == "":
            continue

        time_sec, source_ip, lengths_tls, lengths_quic = parse_tshark_line(l)

        if time0 is None:
            time0 = time_sec

        direction = DIRECTION_INCOMING
        if source_ip == SOURCE_IP:
            direction = DIRECTION_OUTGOING

        # add all TLS packet in this record, if any
        for l in lengths_tls:
            tls.append([time_sec-time0, direction*l])

        # add all QUIC packet in this record, if any
        for l in lengths_quic:
            quic.append([time_sec-time0, direction*l])

    quic.sort(key=itemgetter(0))
    tls.sort(key=itemgetter(0))

    return quic, tls


def pcap_to_txt(pcap_file):
    cmd = shlex.split(TSHARK_COMMAND.format(pcap_file))
    tshark = subprocess.run(cmd, stdout=subprocess.PIPE)
    raw_trace = tshark.stdout.decode('utf8').strip()
    return raw_trace


def pcap_to_timestamp_sizes(pcap_file):
    raw_trace = pcap_to_txt(pcap_file)
    return text_to_timestamp_sizes(raw_trace)


def pcap_get_number_records(pcap_file):
    tls_records = 0
    quic_records = 0

    txt = pcap_to_txt(pcap_file)
    lines = txt.split('\n')
    lines = [l.strip() for l in lines]

    for l in lines:
        if l.strip() == "":
            continue

        _, _, lengths_tls, lengths_quic = parse_tshark_line(l)
        tls_records += len(lengths_tls)
        quic_records += len(lengths_quic)

    return tls_records, quic_records
