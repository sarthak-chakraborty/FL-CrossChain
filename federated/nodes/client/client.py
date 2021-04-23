import time
import datetime
import random
import socket

#######
from pymongo import MongoClient
db = MongoClient('db', 27017).fldb
#######
import numpy as np

from federated.nodes.client.algorithm.sgd import SGD
from federated.models import Update
from federated.messaging.Kafka.kafka import Sender
from federated.messaging.messages import ClientMessage, UpdateMessage, RegistrationMessage, ReadyMessage
from federated.nodes.base import Node
from federated.settings import Settings
from federated.dataset.loader import Cifar10, Cifar100, MNIST



class Client(Node):
	"""
	This is the Client...

	It will receive models and hyperparameters from the server
	and act according the installed strategy

	NOTE: Client code should be completely generic and
	independent of the strategy used by the server. Wise use of control flags
	should do that.
	"""

	def __init__(self, id, description='', endpoint=None):
		"""
		:param id: identifier for client (Used in remote client) (Used to fetch client endpoint)
		:param description: Client description (Not used)
		"""

		self.id = random.randint(0, 1000000)
		self.description = description

		self.wait = False
		self.stop = False

		self.model = None
		self.latest_kmodel = None
		self.latest_hparams = None
		self.load_data = False
		self.load_model = False

		# Set the server ip_address
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('10.255.255.255', 1))
		ip_address = s.getsockname()[0]
		s.close()

		self.ip_address = endpoint or ip_address 

	@property
	def endpoint(self):
		"""
		:return: Endpoint for messaging client
		"""
		return self.ip_address

	def register(self):
		"""
		Send registration message to server, and set ID and flags (if any)
		"""
		# Register
		print("[{}] Registering...".format(self.endpoint))
		Sender.send(RegistrationMessage(self.id, self.description, self.endpoint))

		# Process Response
		reg_response = self.recv_msg(ClientMessage).first()
		cflags = reg_response.control_flags

		# Check for set_id flag
		if cflags is not None:
			if cflags.get("set_id")!=None:
				print("[{}] Setting ID to {}".format(self.endpoint, cflags["set_id"]))
				self.id = cflags["set_id"]

			if cflags.get("wait"):
				if cflags["wait"]:
					print("[{}] Wait flag initiated".format(self.endpoint))
					self.wait = True
				else:
					self.wait = False

			if cflags.get("resume"):
				print("[{}] Resume flag initiated".format(self.endpoint))
				self.wait = False
		else:
			print("[{}] No ID received. Quitting...")

	def send_ready(self):
		"""
		Sends ready message to server
		"""
		# Send ReadyMessage
		print("[{}] Sending ReadyMessage...".format(self.endpoint))
		Sender.send(ReadyMessage(client_endpoint=self.endpoint, metadata=''))

		# Selector Response
		print("[{}] Waiting for Selector Response...".format(self.endpoint))
		selector_res = self.recv_msg(ClientMessage).last()

		if selector_res.control_flags is not None:
			if selector_res.control_flags["selected"]:
				print("[{}] Selected for Training".format(self.endpoint))
				return True
			else:
				print("[{}] Rejected, Trying again after few seconds".format(self.endpoint))
				return False

	def receive_model(self):
		"""
		Look for LAST Train Request
		"""
		print("[{}] Looking for Training Request...".format(self.endpoint))
		cm_list = self.recv_msg_all(ClientMessage, timeout=50, groupid=str(self.id))
		return cm_list.last() if cm_list.count() > 0 else None

	def set_flags(self, cflags):
		"""
		Set flags if received in train request
		:param cflags: control flags received as cm.cflags from server
		"""
		if cflags is not None:
			if cflags.get("set_id"):
				print("[{}] Setting ID to {}".format(self.endpoint, cflags["set_id"]))
				self.id = cflags["set_id"]

			if cflags.get("wait"):
				if cflags["wait"]:
					print("[{}] Wait flag initiated".format(self.endpoint))
					self.wait = True
				else:
					self.wait = False

			if cflags.get("resume"):
				print("[{}] Resume flag initiated".format(self.endpoint))
				self.wait = False
			
			if cflags.get("stop"):
				print("Client with ID {} [{}] is stopping...".format(self.id, self.endpoint))
				print("No more computation and no updates to be sent henceforth!!")
				self.stop = True

	def set_model(self, cm):
		"""
		Set the received model/weights for training
		:param cm: Client message with train request
		:return kmodel: KerasModel if model found, None otherwise
		"""
		if cm.train_request is not None:
			print("[{}] Found Training Request {}".format(self.endpoint, cm.train_request))
			train_req = cm.train_request
			print("[{}] Training on: {}".format(self.endpoint, train_req.kmodel))
			# Retrieve KerasModel and hparams
			kmodel = train_req.kmodel
			if not self.load_model:
				self.model = kmodel.get_model() #first model copied
				self.load_model = True
			else:
				self.model.set_weights(kmodel.weights) #only weights copied for further models
			self.hparams = train_req.hparams
			print("Received Model Version: {}".format(kmodel.version))
			return kmodel
		else:
			print("[{}] Train Request Missing.".format(self.endpoint))
			if self.wait:
				print("Wait signal intialized. Trying again after few seconds...")
			return None

	def train_model(self, data, kmodel):
		"""
		Training the model with set hyperparams
		:param data: Client dataset from train - validation
		:param kmodel: KerasModel received
		:return kmodel: KerasModel created
		:return newmodel: tf.keras model trained
		:return history: train metrics object
		"""
		print("Will Start Training")
		new_model, history = SGD.update(self.model, data, self.hparams["num_epochs"])
		kmodel.set_model(new_model)
		return kmodel, new_model, history

	def send_update(self, kmodel, data, history, server_sent_ts, client_recv_ts):
		"""
		Sends update to server
		:param kmodel:  Keras model with trained model
		:param data: Client training data
		:param history: Train metrics object
		:param server_sent_ts: Timestamp of server sending
		:param client_recv_td: Timestamp of client receiving
		"""
		print("[{}] Sending Update...".format(self.endpoint))
		update_msg = UpdateMessage(client_id = self.id, 
									client_endpoint=self.endpoint, 
									kmodel=kmodel, 
									data_count=data.num_data, 
									history=history, 
									server_sent_ts=server_sent_ts, 
									client_recv_ts=client_recv_ts)	
		Sender.send(update_msg)

	def run(self):
		print('[{}] Started...'.format(self.endpoint))

		self.register()
		#time.sleep(random.randint(0, 120))
		while True:
			# Uncomment for ready request implementation
			# is_ready = self.send_ready()
			# if not is_ready:
			#     continue	

			cm = self.receive_model()
			if cm is None:
				continue

			cflags = cm.control_flags
			server_sent_ts = cm.timestamp
			client_recv_ts = datetime.datetime.utcnow()

			self.set_flags(cflags)
			if self.stop:
				break

			kmodel = self.set_model(cm)
			if kmodel is None:
				continue		

			# Get data
			if not self.load_data:
				data = Client.load_dataset(self.id, self.hparams["batch_size"])
				print("Dataset loaded")
				print("Loading test dataset")
				test_data = Client.load_testdataset(self.hparams["batch_size"])
				self.load_data = True

			###############
			print("Will start pretests")
			preval_loss, preval_acc = self.model.evaluate(data.val_dataset)
			print("Done pretests")
			if test_data:
				pretest_loss, pretest_acc = self.model.evaluate(test_data.test_dataset)
			else:
				pretest_loss, pretest_acc = 0, 1
			###############

			weights = kmodel.get_weights()
			# print("[{}, Client_{}] {}, {}".format(self.endpoint, self.id, weights[0][0][0][0], weights[0][0][0][1]))
			kmodel, new_model, history = self.train_model(data, kmodel)

			################
			if test_data:
				posttest_loss, posttest_acc = new_model.evaluate(test_data.test_dataset)
			else:
				posttest_loss, posttest_acc = 0, 1
			postval_loss, postval_acc = new_model.evaluate(data.val_dataset)
			db.pretrain_logs.insert_one({
											"client_id":self.id, 
											"recv_version":kmodel.version, 
											"pretest_loss":pretest_loss, 
											"pretest_acc":pretest_acc,
											"posttest_loss":posttest_loss, 
											"posttest_acc":posttest_acc,
											"preval_loss":preval_loss, 
											"preval_acc":preval_acc,
											"postval_loss":postval_loss, 
											"postval_acc":postval_acc,
											"server_sent_ts":server_sent_ts,
											"lambda":Settings.delay[self.id]							
										})
			###############

			time.sleep(int(np.random.poisson(Settings.delay[self.id])))

			# Send update
			weights = kmodel.get_weights()
			# print("[{}, Client_{}] {}, {}".format(self.endpoint, self.id, weights[0][0][0][0], weights[0][0][0][1]))
			self.send_update(kmodel, data, history, server_sent_ts, client_recv_ts)


	@staticmethod
	def load_dataset(id, batch_size):
		dataset = Settings.dataset

		if dataset == 'cifar-10':
			return Cifar10(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					partition=Settings.partition,
					batch_size=batch_size,
					validation_split=0.1,
					client_id=id
					)
		
		elif dataset == 'cifar-100':
			return Cifar100(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					partition=Settings.partition,
					batch_size=batch_size,
					validation_split=0.1,
					client_id=id
					)
		
		elif dataset == 'mnist':
			return MNIST(
					batch_size=batch_size,
					client_id=id
					)
		
					
	@staticmethod
	def load_testdataset(batch_size):
		dataset = Settings.dataset

		if dataset == 'cifar-10':
			return Cifar10(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					partition=Settings.partition,
					batch_size=batch_size,
					validation_split=0.1,
					)
		
		elif dataset == 'cifar-100':
			return Cifar100(
					target_height=Settings.input_shape[0],
					target_width=Settings.input_shape[1],
					partition=Settings.partition,
					batch_size=batch_size,
					validation_split=0.1,
					)

		elif dataset == 'mnist':
			return MNIST(
					batch_size=batch_size,
					)
					

	def strategy(self):
		pass
