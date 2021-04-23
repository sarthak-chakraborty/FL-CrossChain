from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np 
import flask
import json
from flask import Flask, request, jsonify
import os

app = Flask(__name__, static_url_path='')

@app.route('/store/', methods=['POST'])
def store_weights():

	message = request.form.get("message")
	file_name = request.form.get("name")

	f = open(file_name, 'w')
	json.dump(message, f)
	f.close()

	return jsonify({"Success": True})

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8050)
