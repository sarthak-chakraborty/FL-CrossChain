from federated.nodes.base import Node
from federated.messaging.messages import StartSignalMessage
from federated.messaging.Kafka.kafka import recv
from federated.settings import Settings


class BaseServer(Node):
    """
    Abstract class for server
    Mentions required functionalities
    """

    def __init__(self, id):
        self.id = id

    @property
    def name(self):
        """
        :return: Name of the component, eg. 'Aggregator', Must be installed in settings.
        """
        raise NotImplementedError

    @property
    def endpoint(self):
        """
        :return: Normal Endpoint For the component
        """
        return Settings.endpoint[self.name]

    @property
    def trigger(self):
        """
        :return: This is where the container should get triggers from coordinator
        """
        return Settings.trigger[self.name]

    def recv_start_signal(self):
        """
        Receives start signal
        """
        return recv(StartSignalMessage, count=1, endpoint=self.trigger)
