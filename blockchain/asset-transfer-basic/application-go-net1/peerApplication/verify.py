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
from bplib.bp import G1Elem, G2Elem

app = Flask(__name__, static_url_path='')


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
	app.run(host="127.0.0.1", port=12001)