import pickle
import numpy as np 
import os

IN_PATH = '../cifar-10-python/cifar-10-batches-py/'
OUT_PATH = '../cifar-10-python/'

im = []
im_label = []
for file in os.listdir(IN_PATH):
	if file.startswith("data_batch"):
		with open(os.path.join(IN_PATH, file), 'rb') as fo:
			d = pickle.load(fo, encoding='bytes')

		im.append(d[b'data'])
		im_label.append(d[b'labels'])

im = np.array(im)
im_label = np.array(im_label)

print(im.shape)
im = im.reshape(im.shape[0]*im.shape[1], -1)
im_label = im_label.reshape(-1)

new_im = []
print(im.shape)
for i in range(len(im)):
	a_r = im[i][:1024]
	a_g = im[i][1024:2048]
	a_b = im[i][2048:]

	x = list(zip(a_r, a_g, a_b))
	x = np.array(x)
	x = x.reshape(32,32,3)

	new_im.append(x)
new_im = np.array(new_im)

data = {'data': new_im, 'label':im_label}

pickle.dump(data, open(os.path.join(OUT_PATH, 'testdata.pkl'), 'wb'))
