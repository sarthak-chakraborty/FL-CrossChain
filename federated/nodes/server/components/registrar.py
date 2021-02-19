from federated.messaging.Kafka.kafka import Sender
from federated.models import KerasModel, RemoteClient
from federated.messaging import RegistrationMessage
from federated.messaging.messages import DeliveratorRequestMessage, TrainingRequest, CoordinatorRequestMessage
from federated.messaging.messages import StartSignalMessage
from federated.nodes.server.config import ServerConfig
from federated.settings import Settings
from federated.nodes.server.base_server import BaseServer


class Registrar(BaseServer):
	"""
	Registrar Server
	For handling client registry
	"""
	name = 'Registrar'

	def __init__(self, id, model_id):
		super(Registrar, self).__init__(id)
		self.model_id = model_id
		self.register_count = 0

	def run(self):
		print('Waiting for start signal...')
		self.recv_start_signal()
		print("Received start signal")

		while True:
			# Receive registration message
			print('Waiting for registrations..., Current count: {}'.format(self.register_count))
			reg_msgs = self.recv_msg_all(RegistrationMessage, timeout=5).list


			for reg_msg in reg_msgs:
				# register_count is passed to set the client_id
				rclient = RemoteClient.from_reg_msg(reg_msg, self.register_count)
				print("Received request from {}".format(rclient))


				# wait signal in both strategy
				wait = True

				# If client has not registered before, send the client_id
				if not rclient.is_reg:
					rclient.is_reg = True
					rclient.commit()	
					cflags = {"set_id": self.register_count, "wait": wait}
					print("Assigning ID {} to {}".format(self.register_count, rclient))

					# Increment registration count
					self.register_count += 1
					
				else:
					cflags = {"set_id": rclient._id, "wait": wait}
					print("Passing ID {} to already registered {}".format(rclient._id, rclient))

				print("Sending DRM for {}...".format(rclient))

				# Toss response to the deliverator
				Sender.send(DeliveratorRequestMessage(
					client_endpoints=[rclient.client_endpoint],
					control_flags=cflags,
					train_request=None))

				""" 
				Sending latest model to the registering client. Comment the block if Ready Signal is implemented.
				It will be taken care by Selector. Need to uncomment blocks in Selector and Corrdinator
				"""

				# If a threshold number of clients registered, send the model to them, else wait for the threshold
				if self.register_count >= ServerConfig.selector_threshold:
					print("Threshold number of clients registered...")
					print("Notifying Coordinator...")
					Sender.send(CoordinatorRequestMessage({"continue": True}))



	def __repr__(self):
		return '<Registrar: {}>'.format(self.id)
