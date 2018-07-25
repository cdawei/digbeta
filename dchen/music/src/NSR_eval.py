import os
import sys
import gzip
import numpy as np
import pickle as pkl
from scipy.sparse import issparse
from sklearn.metrics.pairwise import cosine_similarity
from tools import calc_metrics

TOPs = [5, 10, 20, 30, 50, 100, 200, 300, 500, 1000]

if len(sys.argv) != 4:
    print('Usage:', sys.argv[0], 'WORK_DIR  DATASET  MODEL_FILE.pkl.gz')
    sys.exit(0)

work_dir = sys.argv[1]
dataset = sys.argv[2]
fmodel = sys.argv[3]

assert fmodel.endswith('pkl.gz')
assert os.path.exists(fmodel)

data_dir = os.path.join(work_dir, 'data/%s/coldstart/setting1' % dataset)
fperf = os.path.join(data_dir, 'perf-nsr.pkl')
X_test = pkl.load(gzip.open(os.path.join(data_dir, 'X_test.pkl.gz'), 'rb'))
X_test = np.hstack([np.ones((X_test.shape[0], 1)), X_test])
Y_test = pkl.load(gzip.open(os.path.join(data_dir, 'Y_test.pkl.gz'), 'rb'))
song2pop = pkl.load(gzip.open(os.path.join(data_dir, 'song2pop.pkl.gz'), 'rb'))
songs = pkl.load(gzip.open(os.path.join(data_dir, 'songs_train_dev_test_s1.pkl.gz'), 'rb'))
test_songs = [sid for sid, _ in songs['test_song_set']]
index2song = {ix: sid for ix, sid in enumerate(test_songs)}

assert issparse(Y_test)
clf = pkl.load(gzip.open(fmodel, 'rb'))
assert clf.trained is True

rps = []
hitrates = {top: [] for top in TOPs}
aucs = []
novelty_dict = dict()
diversities = []
for j in range(Y_test.shape[1]):
    if (j+1) % 100 == 0:
        sys.stdout.write('\r%d / %d' % (j+1, Y_test.shape[1]))
        sys.stdout.flush()
    y_true = Y_test[:, j].toarray().reshape(-1)
    npos = y_true.sum()
    if npos < 1:
        continue
    u = clf.pl2u[j]
    wk = clf.V[u, :] + clf.W[j, :] + clf.mu
    y_pred = np.dot(X_test, wk)
    rp, hr_dict, auc = calc_metrics(y_true, y_pred, tops=TOPs)
    rps.append(rp)
    for top in TOPs:
        hitrates[top].append(hr_dict[top])
    aucs.append(auc)

    # compute novelty@100
    sortix = np.argsort(-y_pred)
    nov = np.mean([-np.log2(song2pop[index2song[ix]]) for ix in sortix[:100]])
    try:
        novelty_dict[u].append(nov)
    except KeyError:
        novelty_dict[u] = [nov]

    # compute diversity@100
    csd = 1. / cosine_similarity(X_test[sortix[:100], :])
    diversities.append((csd.sum() - np.trace(csd)) / (100 * 99))

print('\n%d, %d' % (len(rps), Y_test.shape[1]))
nsr_perf = {dataset: {'Test': {'R-Precision': np.mean(rps),
                               'Hit-Rate': {top: np.mean(hitrates[top]) for top in TOPs},
                               'AUC': np.mean(aucs),
                               'Novelty': np.mean([np.mean(novelty_dict[u]) for u in novelty_dict]),
                               'Diveristy': np.mean(diversities)},
                      'Test_All': {'R-Precision': rps,
                                   'Hit-Rate': {top: hitrates[top] for top in TOPs},
                                   'AUC': aucs,
                                   'Novelty': novelty_dict,
                                   'Diversity': diversities}}}
pkl.dump(nsr_perf, open(fperf, 'wb'))
print(nsr_perf[dataset]['Test'])
