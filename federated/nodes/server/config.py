import os
class ServerConfig:
	"""
	Mention any server configurations here
	"""
	model = "cnn-transfer"

	hparams = {
		"num_epochs": 2,
		"batch_size": 32
	}

	stopping_criteria = {"version": 5000}
	
	weights = '/app/cnn_40/received_asset-cifar_25.json'
	last_weight_index = 4

	# Synchronous Setting Parameters
	selector_threshold = 10
	aggregator_threshold = 10


class DatabaseConfig:
	"""
	Database Configuration
	
	Class for now, will pass as environment later on
	"""
	host = "mongodb://db" or os.environ["MDB_HOST"]
	port = 27017 or os.environ["MDB_PORT"]
	database = 'fldb'
