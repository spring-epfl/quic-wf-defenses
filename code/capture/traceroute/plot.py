import glob
import sys
import pydot

def read_file(file):
    with open(file, "r") as f:
        lines = f.readlines()
        lines = lines[1:]
        lines = [l.strip() for l in lines]
        lines = [l.split(' ') for l in lines]
        path = [l[2] for l in lines]
        return path

logfiles = glob.glob('logs/*.log')
paths = [read_file(l) for l in logfiles]


labels = set()
for p in paths:
    for node in p:
        if node != "*":
            labels.add(node)

nodes = dict()
nodes["localhost"] = dict(count=0, children={})
for l in labels:
    nodes[l] = dict(count=0, children={})

edges=dict()

for p in paths:
    current = 'localhost'
    for child in p:
        if child != "*":

            if not (current, child) in edges:
                edges[(current, child)] = 0

            edges[(current, child)] += 1
            current = child



graph = pydot.Dot(graph_type='graph')

pynodes = dict()
pynodes["localhost"] = pydot.Node("localhost")
for l in labels:
    pynodes[l] = pydot.Node(l)

for n in pynodes:
    graph.add_node(pynodes[n])

for e in edges:
    print(e)
    graph.add_edge(pydot.Edge(pynodes[e[0]], pynodes[e[1]], label=edges[e]))

graph.write_png('plots/topology.png')
