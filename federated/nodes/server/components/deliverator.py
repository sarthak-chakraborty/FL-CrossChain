from confluent_kafka.admin import AdminClient, NewPartitions
from federated.messaging.Kafka.kafka import Sender
from federated.models import KerasModel
from federated.messaging.messages import TrainingRequest
from federated.nodes.server.config import ServerConfig
from federated.messaging.messages import DeliveratorRequestMessage, ClientMessage
from federated.nodes.server.base_server import BaseServer

##############
from pymongo import MongoClient
import datetime
#########

class Deliverator(BaseServer):
	"""
	The Deliverator belongs to an elite order, a hallowed subcategory.
	https://en.wikipedia.org/wiki/Snow_Crash

	It is the sole delivery guy for all clients.

	NOTE: No other node should be sending any kind of data to clients
		  They must toss it to the deliverator,
		  It will do the rest...

	NOTE: Do not put any algorithm specific code in this module
	"""

	name = 'Deliverator'

	def __init__(self, id):
		"""
		:param id: Deliverator ID (Not used anywhere, currently)
		"""
		super(Deliverator, self).__init__(id)

	def run(self):
		# Wait for start signal from coordinator
		print('Waiting for start signal...')
		self.recv_start_signal()
		print('Received start signal')
		print('Waiting for DRMs...')

		######################
		db = MongoClient('db', 27017).fldb
		######################

		while True:
			# Receive delivery request message
			print("Waiting for drms...")
			drms = self.recv_msg_all(DeliveratorRequestMessage, timeout=10).list
			for drm in drms:
				print("Received DRM for {}".format(drm.client_endpoints))

				##########################
				# lp = LineProfiler()
				# lp_wrapper = lp(self.sending)
				# lp_wrapper(drm, db)
				# lp.print_stats()
				###########################

				# Get the train_request and flags
				trq = drm.train_request
				cflags = drm.control_flags
				print(cflags)
				##################
				if trq is not None:  
				    db.server_times.update_one({"version" : trq.kmodel.version}, {"$set" : {"del_send_ts" : datetime.datetime.utcnow()}})
				###################
				# Send the model to appropriate clients
				for client_endpoint in drm.client_endpoints:
				    Sender.send(ClientMessage(client_endpoint=client_endpoint, control_flags=cflags, train_request=trq))
				    print("Message sent to {}".format(client_endpoint))


	def sending(self, drm, db):
		# Get the train_request and flags
		trq = drm.train_request
		cflags = drm.control_flags
		##################
		if trq is not None:  
			db.server_times.update_one({"version" : trq.kmodel.version}, {"$set" : {"del_send_ts" : datetime.datetime.utcnow()}})
		###################

		print(len(drm.client_endpoints))
		# Send the model to appropriate clients
		for client_endpoint in drm.client_endpoints:
			cm = ClientMessage(client_endpoint=client_endpoint, control_flags=cflags, train_request=trq)
			Sender.send(cm)
			print("Message sent to {}".format(client_endpoint))


	def __repr__(self):
		return '<Deliverator Node : {}>'.format(self.id)
