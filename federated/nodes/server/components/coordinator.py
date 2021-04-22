import tensorflow as tf
import time
import json
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from classification_models.tfkeras import Classifiers
from federated.messaging.Kafka.kafka import Sender
from federated.models import KerasModel, Update, RemoteClient, ClientUpdateMetric, ServerEvalMetric, ClientMessageMetric
from federated.messaging.messages import StartSignalMessage, ReadyMessage, CoordinatorRequestMessage
from federated.nodes.server.base_server import BaseServer

from federated.keras_models.mobilenet import MobileNet
from federated.keras_models.simple_cnn import SimpleCNN
from federated.keras_models.simple_cnn_transfer import SimpleCNN as CNNTransfer
from federated.keras_models.VGG11 import VGG
from federated.keras_models.VGG11_transfer import VGG as VGGTransfer

from federated.nodes.server.config import ServerConfig
from federated.settings import Settings



class Coordinator(BaseServer):
	"""
	Coordinator
	Initializes and Starts other components
	"""

	name = 'Coordinator'

	def __init__(self, id, model_id=1):
		super(Coordinator, self).__init__(id)
		self.model_id = model_id


	@staticmethod
	def get_default_model():
		model = tf.keras.Sequential([
			tf.keras.layers.Flatten(input_shape=Settings.input_shape),
			tf.keras.layers.Dense(128, activation='relu'),
			tf.keras.layers.Dense(Settings.num_classes)
		])
		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics


	@staticmethod
	def get_cnn_model():
		model = SimpleCNN(Settings.input_shape, Settings.num_classes)

		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics


	@staticmethod
	def get_cnn_transfer_model():
		model = CNNTransfer(Settings.input_shape, Settings.num_classes)

		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics


	@staticmethod
	def get_mobilenet_model():
		model = MobileNet(Settings.input_shape, Settings.num_classes)		
		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics
	
		
	@staticmethod
	def get_resnet_model():
		ResNet18, _ = Classifiers.get('resnet18')
		model = ResNet18(Settings.input_shape, weights=None, classes=Settings.num_classes)
		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy()
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics
		
		
	@staticmethod
	def get_vgg_model():
		model = VGG(Settings.input_shape, Settings.num_classes, size=128)		
		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics

	@staticmethod
	def get_vgg_model():
		model = VGGTransfer(Settings.input_shape, Settings.num_classes, size=128)		
		optimizer = 'adam'
		loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
		metrics = ['accuracy']
		return model, optimizer, loss_fn, metrics


	@staticmethod
	def get_initial_model():
		model = ServerConfig.model
		if model == "default":
			return Coordinator.get_default_model()
		elif model == "cnn":
			return Coordinator.get_cnn_model()
		elif model == "cnn-transfer":
			return Coordinator.get_cnn_transfer_model()
		elif model == "mobilenet-v2":
			return Coordinator.get_mobilenet_model()
		elif model == "vgg11":
			return Coordinator.get_vgg_model()
		elif model == "vgg11-transfer":
			return Coordinator.get_vgg_transfer_model()
		elif model == "resnet":
			return Coordinator.get_resnet_model()
	
	@staticmethod
	def set_weights(model):
		if ServerConfig.weights == None:
			return model
		else:	
			w = None
			try:
			    f_open = open(ServerConfig.weights,)
			    data = json.load(f_open)
			    print(data.keys())

			    w = np.array(data['weights'])
			    for i in range(len(w)):
			        w[i] = np.array(w[i])
			        if w[i].shape[1] == 1:
			            w[i] = w[i].reshape(w[i].shape[0])
			except:
			    w = None

			if w == None:
				return model
			else:
				print(w.shape)
				num = len(w) - int(ServerConfig.last_weight_index)
				w = w[:num]
				model_weights = np.array(model.get_weights())
				print(len(model_weights))

				for i in range(num, len(model_weights)):
					w = np.vstack((w, model_weights[i]))

				model.set_weights(w)
				return model
				

	@staticmethod
	def init_db():
		Update.destroy_db()
		KerasModel.destroy_db()
		RemoteClient.destroy_db()
		ClientUpdateMetric.destroy_db()
		ClientMessageMetric.destroy_db()
		ServerEvalMetric.destroy_db()
		
		model, optimizer, loss_fn, metrics = Coordinator.get_initial_model()
		model = Coordinator.set_weights(model)
		print(model.summary())
		kmodel = KerasModel(
			id=1,
			name='cnn',
			version=0,
			architecuture=model.to_json(),
			weights=model.get_weights(),
			optimizer=optimizer,
			loss=loss_fn,
			metrics=metrics
		)
		kmodel.commit()


	def run(self):
		print("Starting...")
		print("Initializing DB...")
		Coordinator.init_db()

		print("Starting Registrar...")
		Sender.send(StartSignalMessage('Registrar'))
		print("Starting Connector...")
		Sender.send(StartSignalMessage('Connector'))
		print("Starting Aggregator...")
		Sender.send(StartSignalMessage('Aggregator'))
		print("Starting Deliverator...")
		Sender.send(StartSignalMessage('Deliverator'))

		print("Strategy : Plain Synchronous")
		self.plain_synchronous()

		print("Coordinator exiting...")


	def plain_synchronous(self):
		round_no = 0

		while True:
			print("Round {}".format(round_no))

			"""
			print("Starting Selector...")
			Sender.send(StartSignalMessage('Selector'))
			"""

			print("Waiting for CoordinatorRequestMessage...")
			cflags = self.recv_msg(CoordinatorRequestMessage, count=1).first().control_flags

			control = cflags.get("continue")
			if not control:
				print("Coordinator Exiting...")
				break

			# Comment the two lines if Ready Message implemented. Also check Registrar and Selector
			time.sleep(3)
			print("Starting Selector...")
			Sender.send(StartSignalMessage('Selector'))

			print("Round {} complete".format(round_no))
			round_no += 1

