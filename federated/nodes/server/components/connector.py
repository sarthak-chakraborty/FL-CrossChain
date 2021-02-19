import datetime 

import tensorflow as tf

from federated.models import Update, ClientUpdateMetric, KerasModel
from federated.messaging import UpdateMessage
from federated.nodes.server.base_server import BaseServer


class Connector(BaseServer):
    """
    The Connector is what links the client updates to the
    server database

    NOTE: The connector must be independent of the algorithm
    Read: https://docs.confluent.io/current/connect/index.html
    """

    name = "Connector"

    def __init__(self, id):
        """
        :param id: Connector ID (Not used right now)
        """
        super(Connector, self).__init__(id)
        self.count = 0

    def run(self):
        # Receive start signal
        print('Waiting for start signal...')
        self.recv_start_signal()
        print('Received start signal')
        print('Waiting for updates...')

        while True:
            tf.keras.backend.clear_session()
            # Receive update and save them
            update_msgs = self.recv_msg_all(UpdateMessage).list
            for update_msg in update_msgs:
                # Get update instance from update_message
                update = Update.from_update_msg(update_msg, self.count)
                update_metric = ClientUpdateMetric.from_update(update, KerasModel.get_latest_version(update.kmodel.id).version)

                # Increment update count
                self.count += 1

                print("Received update from {}".format(update.client_endpoint))

                # Save the update
                print("Saving update...")
                update.commit()
                update_metric.commit()
                print("Update saved")
