from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np 
import flask
import json
from flask import Flask, request, jsonify
from subprocess import Popen, PIPE
from bls.scheme import *
import os
import multiprocessing
from petlib.bn import Bn
from bplib.bp import G1Elem

app = Flask(__name__, static_url_path='')


def signature(client_id, path, message, params, bin_signs):
	PATH = os.path.join(path, 'priv_sk_{}'.format(client_id))
	f = open(PATH, 'rb')
	bin_sk = f.read()
	f.close()
	sk = Bn.from_binary(bin_sk)

	signat = sign(params, sk, message)
	bin_signs[client_id] = signat.export()


# class Client(multiprocessing.Process):
# 	def __init__(self, id, path):
# 		super(Process, self).__init__()
# 		self.id = id
# 		self.path = path
	
# 	def run(message, params, signs):
# 		PATH = os.path.join(self.path, 'priv_sk_{}'.format(self.id))
# 		f = open(PATH, 'rb')
# 		bin_sk = f.read()
# 		sk = Bn.from_binary(bin_sk)

# 		sign = sign(params, sk, message)
# 		signs[self.id] = sign



def gen_keys(num):
	PATH = '../'
	folder_name = 'artifacts'
	FOLDER_PATH = os.path.join(PATH, folder_name)

	if not os.path.exists(FOLDER_PATH):
		os.mkdir(FOLDER_PATH)

	PRIVATE_KEY_PATH = os.path.join(FOLDER_PATH, "priv")
	PUBLIC_KEY_PATH = os.path.join(FOLDER_PATH, "publ")
	if not os.path.exists(PRIVATE_KEY_PATH):
		os.mkdir(PRIVATE_KEY_PATH)
	if not os.path.exists(PUBLIC_KEY_PATH):
		os.mkdir(PUBLIC_KEY_PATH)

	params = setup()
	(priv_sk, publ_vk) = ttp_keygen(params, num, num)

	bin_priv_sk = [sk.binary() for sk in priv_sk]
	bin_publ_vk = [vk.export() for vk in publ_vk]

	for i in range(num):
		f = open(os.path.join(PRIVATE_KEY_PATH, 'priv_sk_{}'.format(i)), 'wb')
		f.write(bin_priv_sk[i])
		f.close()

		f = open(os.path.join(PUBLIC_KEY_PATH, 'publ_vk_{}'.format(i)), 'wb')
		f.write(bin_publ_vk[i])
		f.close()

	return params, FOLDER_PATH, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
	

def read_keys(path, params):
	(G, o, g1, g2, e) = params
	keys = {}
	for file in os.listdir(path):
		f = open(os.path.join(path, file), 'rb')
		bin_vk = f.read()
		f.close()

		client_id = int(file[8:])
		keys[client_id] = G2Elem.from_bytes(bin_vk, G)

	return keys.values()


def read_sigma(path, params):
	(G, o, g1, g2, e) = params
	f = open(path, 'rb')
	bin_sigma = f.read()
	f.close()

	return G1Elem.from_bytes(bin_sigma, G)
	


@app.route('/signMessage/', methods=['POST'])
def signMessage():
	"""
	Sign the received message using BLS signature
	"""
	message = request.form.get("message")
	num_clients = int(request.form.get("num"))

	# Generate Keys and store them
	params, path, priv_path, publ_path = gen_keys(num_clients)

	manager = multiprocessing.Manager()
	bin_signs = manager.dict()
	jobs = []
	for i in range(num_clients):
		p = multiprocessing.Process(target=signature, args=(i, priv_path, message, params, bin_signs))
		jobs.append(p)
		p.start()
	for proc in jobs:
		proc.join()

	signs = [G1Elem.from_bytes(s, params[0]) for s in bin_signs.values()]

	# Aggregate the signatures
	sigma = aggregate_sigma(params, signs, threshold=False)

	# Convert signature and params into binary format
	bin_sigma = sigma.export()
	SIGMA_PATH = os.path.join(path, "Sigma")
	if not os.path.exists(SIGMA_PATH):
		os.mkdir(SIGMA_PATH)

	f = open(os.path.join(SIGMA_PATH, "sigma"), 'wb')
	f.write(bin_sigma)
	f.close()

	return jsonify({
		"Path": publ_path,
		"Sigma": os.path.join(SIGMA_PATH, "sigma")
		})



@app.route('/verifyMessage/', methods=['POST'])
def verifyMessage():
	"""
	Verify the received message for BLS signature
	"""

	message = request.form.get("message")
	path = request.form.get("key_path")
	sigma_path = request.form.get("sigma")
	
	params = setup()
	vk = read_keys(path, params)
	aggr_vk = aggregate_vk(params, vk, threshold=False)
	sigma = read_sigma(sigma_path, params)

	# Verify
	success = verify(params, aggr_vk, sigma, message)

	return jsonify({"Success":success})
	

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8051)
