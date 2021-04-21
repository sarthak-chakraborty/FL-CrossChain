import os
class ServerConfig:
	"""
	Mention any server configurations here
	"""
	model = "cnn"

	hparams = {
		"num_epochs": 2,
		"batch_size": 16
	}

	stopping_criteria = {"version": 5000}
	
	weights = './received_asset_cifar_2.json

	# Synchronous Setting Parameters
	selector_threshold = 40
	aggregator_threshold = 40


class DatabaseConfig:
	"""
	Database Configuration
	
	Class for now, will pass as environment later on
	"""
	host = "mongodb://db" or os.environ["MDB_HOST"]
	port = 27017 or os.environ["MDB_PORT"]
	database = 'fldb'
