import os
class ServerConfig:
	"""
	Mention any server configurations here
	"""
	model = "default"

	hparams = {
		"num_epochs": 2,
		"batch_size": 8
	}

	stopping_criteria = {"version": 5000}


	# Synchronous Setting Parameters
	selector_threshold = 2
	aggregator_threshold = 2


class DatabaseConfig:
	"""
	Database Configuration
	
	Class for now, will pass as environment later on
	"""
	host = "mongodb://db" or os.environ["MDB_HOST"]
	port = 27017 or os.environ["MDB_PORT"]
	database = 'fldb'
