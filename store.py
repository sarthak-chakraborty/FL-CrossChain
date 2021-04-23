import json
import os
import requests

url = "http://:8050/store/"
name = 'received_asset-cifar-25.json'

f = open(name, 'r')
data = json.load(f)

obj = {"name": name, "message": data}

r = requests.post(url, json=obj)

print(r)