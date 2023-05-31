import glob
import sys
import numpy as np
import overheads


for isquic in ['quic/', 'non-quic/']:
    base_path = '../datasets-npy/dataset-40x1035-25-08-2020/' + isquic
    sources1 = glob.glob(base_path + "*.npy")
    sources1.sort()

    for defense in ['frontglue', 'padme', 'wtfpad']:
        defended_path = '../datasets-npy/dataset-40x1035-25-08-2020-' + defense + "/" + isquic

        sources2 = glob.glob(defended_path + "*.npy")
        sources2.sort()
        pairs = list(zip(sources1, sources2))

        overhead_overall_pairs = []
        for pair in pairs:
            Xs1, _ = np.load(pair[0], allow_pickle=True)
            Xs2, _ = np.load(pair[1], allow_pickle=True)

            overhead_pairs = []

            i = min(len(Xs1), len(Xs2))-1
            while i >= 0:
                print(pair[0], i, end="\r")
                o = overheads.get_overhead_for_defense(Xs1[i], Xs2[i])
                overhead_pairs.append(dict(bw=o[0], lat=o[1]))
                overhead_overall_pairs.append(dict(bw=o[0], lat=o[1]))
                i -= 1
            res = overheads.summarise_overhead_for_defense(overhead_pairs)

        print()
        res = overheads.summarise_overhead_for_defense(overhead_overall_pairs)
        print(defense, isquic, res)
