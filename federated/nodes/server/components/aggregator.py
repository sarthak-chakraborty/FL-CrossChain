import time
######logging######
from pymongo import MongoClient
import datetime
####################
from threading import Thread
import tensorflow as tf
import numpy as np
import requests


from federated.models import KerasModel, Update, RemoteClient, ServerEvalMetric
from federated.nodes.server.algorithm.federated_averaging import FederatedAveraging

from federated.messaging.Kafka.kafka import Sender
from federated.messaging.messages import DeliveratorRequestMessage, StartSignalMessage, CoordinatorRequestMessage
from federated.nodes.server.base_server import BaseServer
from federated.messaging.messages import TrainingRequest
from federated.nodes.server.config import ServerConfig
from federated.settings import Settings
from federated.dataset.loader import Cifar10, Cifar100


class Aggregator(BaseServer):
	"""
	Aggregator
	For aggregating updates from clients
	"""

	name = "Aggregator"

	def __init__(self, id, model_id):
		"""
		:param id: Aggregator ID (Maybe we could have more of these folks)
		:param model_id: The model this is responsible for (Can it be a list ?)
		"""
		super(Aggregator, self).__init__(id)
		self.model_id = model_id
		self.url = "http://127.0.0.1:8050/enterAsset"
		self.threshold = ServerConfig.aggregator_threshold
		self.data_loader = Aggregator.load_test_dataset()


	def run(self):
		print('Waiting for start signal...')
		self.recv_start_signal()
		print('Received start signal')
		print('Starting...')
		print('Will look for updates every 10s')

		
		self.plain_synchronous()

	# Sequence for plain synchronous fl
	def plain_synchronous(self):
		while True:
			tf.keras.backend.clear_session()
			kmodel_new = []
			data_count = []
			valid_updates = []
			while True:
				updates = Update.query(handled=False)

				if updates.count() == 0:
					time.sleep(5)
					continue

				kmodel_global = KerasModel.get_latest_version(self.id)
				global_version = kmodel_global.version

				for update in updates.list:
					if update.kmodel.version == global_version:
						valid_updates.append(update)
						kmodel_new.append(update.kmodel)
						data_count.append(update.data_count)

					Update.handle(update)
					# update.handled = True
					# update.commit()

				if len(valid_updates) >= self.threshold:
					break
			
			print("Found {} new updates...".format(len(valid_updates)))
			print("Applying aggregation strategy...")

			# Aggregate models
			print("Aggregating global_model (version {})..."
					.format(kmodel_global.version))

			kmodel_global = FederatedAveraging.fit(
								kmodel_global,
								kmodel_new,
								data_count)


			kmodel_global.version += 1
			print("Global Model {} updated to version {}".format(kmodel_global.id, kmodel_global.version))
			print("Evaluating new global model...")
			
			# Evaluate model on test set 
			# Thread(target=Aggregator.evaluate, args=(kmodel_global, self.data_loader, self.id)).start()
			test_loss, test_acc = Aggregator.evaluate(kmodel_global, self.data_loader, self.id)

			# Save aggregate model
			print("Saving new global model...")
			kmodel_global.commit()
			
			new_weights = []
			server_weights = kmodel_global.weights
			
			print("INFOS")
			print(len(server_weights))
			
			for index in range(len(server_weights)):
				feature_weight = server_weights[index]
				print(len(feature_weight.shape))
				if len(feature_weight.shape) == 1:
					new_weights.append(feature_weight.reshape(feature_weight.shape[0], 1, 1, 1).tolist())
				elif len(feature_weight.shape) == 2:
					new_weights.append(feature_weight.reshape(feature_weight.shape[0], feature_weight.shape[1], 1, 1).tolist())
				elif len(feature_weight.shape) == 3:
					new_weights.append(feature_weight.reshape(feature_weight.shape[0], feature_weight.shape[1], feature_weight.shape[2], 1).tolist())
				else:
					new_weights.append(feature_weight.tolist())

			obj = {"ID": "server_round_"+str(kmodel_global.version),
				   "Round_No": kmodel_global.version,
				   "Node": "server",
				   "Weights": new_weights,
				   "hyperparams":{
				   				  "Epoch": ServerConfig.hparams["num_epochs"],
				   				  "Batch_Size": ServerConfig.hparams["batch_size"],
				   				  "Loss_Func":"cross-entropy"
				   				  },
				   	"Gradients": [[1.0, 3.0], [12.6, 7.98]],
				   	"Dataset": {
				   				 "Dataset_ID": Settings.dataset_id,
				   				 "Dataset_Name": Settings.dataset,
				   				 "Train_Samples": 50000,
				   				 "Test_Samples": self.data_loader.num_data,
				   				 "Val_Split": 0.1
				   				},
				   	"Metric": {
				   				"Train_Loss": 2.14,
				   				"Train_Acc": 0.98,
				   				"Test_Loss": test_loss,
				   				"Test_Acc": test_acc
				   			  }
				   	}
			if Settings.enable_crosschain:
				r = requests.post(self.url, json=obj)
				print(r)

			# Check if stopping criteria reached
			if Aggregator.can_stop(ServerConfig.stopping_criteria, kmodel_global.version):
				"""
				Stopping criteria has reached
				Notify the clients
				
				TODO: Notify the coordinator that everything is done
				"""
				print("Stopping criteria has reached")
				Aggregator.stop_all_active_clients()

				print("Asking the coordinator to stop...")
				Sender.send(CoordinatorRequestMessage({"continue": False}))
				print("Exiting...")
				return
			else:
				"""
				Notify the coordinator to start the next round 
				"""
				print("Notifying Coordinator...")
				Sender.send(CoordinatorRequestMessage({"continue": True}))


	
	@staticmethod
	def load_test_dataset():
		dataset = Settings.dataset

		if dataset == 'cifar-10':
			return Cifar10(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					batch_size=Settings.test_batch_size
					)

		elif dataset == 'cifar-100':
			return Cifar100(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					batch_size=Settings.test_batch_size
					)

		elif dataset == 'cityscapes':
			return Cityscapes(
					batch_size=Settings.test_batch_size
					)


	@staticmethod
	def evaluate(kmodel_global, data_loader, id):
		print("Evaluating new global model...")
		"""
		'''
		Evaluate model

		Only for fashion mnist
		'''

		fmnist = FashionMnist()
		test_loss, test_acc = kmodel_global.get_model().evaluate(
			fmnist.test_data,
			verbose=2
		)
		print("Test Loss: {}, Test Accuracy: {}".format(test_loss, test_acc))
		"""

		test_loss, test_acc = kmodel_global.get_model().evaluate(data_loader.test_dataset)
		print("Test Loss: {}, Test Accuracy: {}".format(test_loss, test_acc))
		server_metric = ServerEvalMetric(kmodel_global.id, kmodel_global.version, test_loss, test_acc)
		server_metric.commit()
		return test_loss, test_acc


	@staticmethod
	def can_stop(stop_criteria, global_version):
		"""
		Check stopping criteria
		"""
		if "version" in stop_criteria and global_version >= stop_criteria["version"]:
			return True

		return False


	@staticmethod
	def stop_all_active_clients():
		print("Asking all clients to stop immediately...")

		cflags = {"stop": True}
		active_clients = RemoteClient.query(is_reg=True, status='active')

		client_endpoints = []
		for active_client in active_clients.list:
			active_client.is_reg = False
			client_endpoints.append(active_client.client_endpoint)

		print("Sending 'Stop' DRM...")
		Sender.send(DeliveratorRequestMessage(
			client_endpoints,
			control_flags=cflags,
			train_request=None)
		)


	def __repr__(self):
		return "<Aggregator: {}>".format(self.id)
