import pickle
import numpy as np 
import os

IN_PATH = '../cifar-100-python/'
OUT_PATH = '../cifar-100-python/'

def unpickle(file):
    with open(file, 'rb') as fo:
        myDict = pickle.load(fo, encoding='latin1')
    return myDict

trainData = unpickle(os.path.join(IN_PATH, 'train'))
testData = unpickle(os.path.join(IN_PATH, 'test'))

im_train = trainData['data']
im_train_label = trainData['coarse_labels']

im_test = testData['data']
im_test_label = testData['coarse_labels']


X_train = im_train.reshape(len(im_train),3,32,32).transpose(0,2,3,1)
X_test = im_test.reshape(len(im_test),3,32,32).transpose(0,2,3,1)

data_train = {'data': X_train, 'label':im_train_label}
data_test = {'data': X_test, 'label':im_test_label}

pickle.dump(data_train, open(os.path.join(OUT_PATH, 'data.pkl'), 'wb'))
pickle.dump(data_test, open(os.path.join(OUT_PATH, 'testdata.pkl'), 'wb'))
