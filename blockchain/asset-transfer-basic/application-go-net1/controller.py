import json
import requests
import struct

url = "http://127.0.0.1:8050/enterAsset"

arr = [[1.5, 3.34, 43.22], [12.6, 7.98, 35.44]]

obj = {"ID": "server_round_3",
	   "Round_No": 6,
	   "Node": "server",
	   "Weights": arr,
	   "hyperparams":{
	   				  "Epoch":50,
	   				  "Batch_Size":16,
	   				  "Loss_Func":"cross-entropy"
	   				  },
	   	"Gradients": [[1.0, 3.0], [12.6, 7.98]],
	   	"Dataset": {
	   				 "Dataset_ID": 0,
	   				 "Dataset_Name": "cifar10",
	   				 "Train_Samples": 50000,
	   				 "Test_Samples": 10000,
	   				 "Val_Split": 0.0
	   				},
	   	"Metric": {
	   				"Train_Loss": 2.14,
	   				"Train_Acc": 0.98,
	   				"Test_Loss": 2.32,
	   				"Test_Acc": 0.96
	   			  }
	   	}

r = requests.post(url, json=obj)

print(r)