import random

import tensorflow as tf

from federated.models.models import Update, RemoteClient
from federated.messaging import UpdateMessage
from federated.messaging.messages import ReadyMessage, DeliveratorRequestMessage, TrainingRequest
from federated.models.models import KerasModel, ClientMessageMetric
from federated.nodes.server.base_server import BaseServer
from federated.nodes.server.config import ServerConfig
from federated.messaging.Kafka.kafka import Sender
from federated.settings import Settings


class Selector(BaseServer):
	"""
	The Connector is what links the client updates to the
	server database
	"""
	name = "Selector"

	def __init__(self, id, model_id):
		"""
		:param id: Connector ID (Not used right now)
		"""
		super(Selector, self).__init__(id)
		self.threshold = ServerConfig.selector_threshold
		self.count = 0
		self.round = 0
		self.model_id = model_id

	def run(self):
		self.plain_synchronous()

	def plain_synchronous(self):
		while True:
			print('Waiting for start signal...')

			# First start signal would be from coordinator
			# Rest will be from aggregator
			self.recv_start_signal()
			print('Received start signal')
			tf.keras.backend.clear_session()
			# Initialize variables
			ready_count = 0
			client_endpoints = []

			print('Round {} started'.format(self.round))

			# Bradcast New Model to ALL Clients
			active_clients = RemoteClient.query(is_reg=True, status='active')

			client_endpoints = []
			for active_client in active_clients.list:
				client_endpoints.append(active_client.client_endpoint)

			assert (len(client_endpoints) >= self.threshold)

			# Uncomment if Ready Message based Client selection needs to be enabled
			"""
			while ready_count < self.threshold:
				'''
				Keep looking for clients until the threshold is reached,
				In McMahan et al. they select a random subset of ready clients

				TODO: Collect all the ready messages in a list and send selection confirmation
				together
				'''
				print("Waiting for Ready Message, {}/{}".format(ready_count, self.threshold))
				ready_msg = self.recv_msg(message_type=ReadyMessage, count=1).first()
				print("Received Ready Message from {}".format(ready_msg.client_endpoint))

				
				# Do something with metadata
				

				# Append client endpoint
				client_endpoints.append(ready_msg.client_endpoint)

				# Tell client that it was selected
				print("Sending selection DRM for {}...".format(ready_msg.client_endpoint))
				drm = DeliveratorRequestMessage(
					client_endpoints=[ready_msg.client_endpoint],
					control_flags={"selected": True},
					train_request=None
				)
				Sender.send(drm)

				# Increment count
				ready_count += 1
			"""

			# Fetch latest model and send to the endpoints
			kmodel = KerasModel.get_latest_version(self.model_id)
			trq = TrainingRequest(kmodel=kmodel, hparams=ServerConfig.hparams)
			print("Sending DRM for all selected clients...")
			drm = DeliveratorRequestMessage(
				client_endpoints=client_endpoints,
				control_flags={"start_train": True},
				train_request=trq
			)

			# Send to the deliverator
			Sender.send(drm)
			for active_client in active_clients.list:
				ClientMessageMetric(active_client.id, kmodel.version).commit()
			# Move to next round
			self.round += 1


