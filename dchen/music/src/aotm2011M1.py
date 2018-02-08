import os
import sys
import gzip
import time
import numpy as np
import pickle as pkl

if len(sys.argv) != 7:
    print('Usage: python', sys.argv[0], 'WORK_DIR  C1  C2  C3  P  N_EPOCH')
    sys.exit(0)
else:
    work_dir = sys.argv[1]
    C1 = float(sys.argv[2])
    C2 = float(sys.argv[3])
    C3 = float(sys.argv[4])
    p = float(sys.argv[5])
    n_epochs = int(sys.argv[6])

data_dir = os.path.join(work_dir, 'data')
src_dir = os.path.join(work_dir, 'src')
sys.path.append(src_dir)

from PCMLC import PCMLC as PClassificationMLC

pkl_data_dir = os.path.join(data_dir, 'aotm-2011/setting1')
fxtrain = os.path.join(pkl_data_dir, 'X_train.pkl.gz')
fytrain = os.path.join(pkl_data_dir, 'Y_train.pkl.gz')
fadjmat = os.path.join(pkl_data_dir, 'adjacency_mat.pkl.gz')

X_train = pkl.load(gzip.open(fxtrain, 'rb'))
Y_train = pkl.load(gzip.open(fytrain, 'rb'))
same_user_mat = pkl.load(gzip.open(fadjmat, 'rb'))
userwiseReg = False

print('C: %g, %g, %g, p: %g' % (C1, C2, C3, p))

print(time.strftime('%Y-%m-%d %H:%M:%S'))
clf = PClassificationMLC(C1=C1, C2=C2, C3=C3, p=p, weighting='both', similarMat=same_user_mat, userwiseReg=userwiseReg)
clf.fit_minibatch(X_train, Y_train, batch_size=1024, n_epochs=n_epochs, learning_rate=0.1, verbose=1)

if clf.trained is True:
    fmodel = os.path.join(pkl_data_dir, 'mlr-aotm2011-C-%g-%g-%g-p-%g.pkl' % (C1, C2, C3, p))
    pkl.dump(clf, open(fmodel, 'wb'))

