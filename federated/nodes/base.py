from federated.messaging.Kafka.kafka import recv, Sender
from federated.messaging.messages import AbstractMessage
from federated.messaging.messages import StartSignalMessage


class Node:
    """
    AbstractNode

    Imagine a node to be a thread,
    A thread with an endpoint for communtication

    For example:
        In socket programming an endpoint could be:
            process_id, thread_id, ip, port

        In kafka, endpoint abstraction is 'topic'
        In zeroMq, endpoint will look like 'tcp://10.4.17.22:5000'
    """

    @property
    def endpoint(self):
        """
        endpoint, This will be used by the message module
        :return: The endpoint at which this node listens for messages
        """
        raise NotImplementedError

    def recv_msg(self, message_type, count=1):
        """
        Each node will have it's own receive message, I could not think
        of a way around this.
        :param message_type: Message class
        :param count: No. of messages to receive
        :return: Instance of MessageList (see federated.models.MessageList)
        """
        assert issubclass(message_type, AbstractMessage)

        return recv(message_type, count=count, endpoint=self.endpoint)

    def recv_msg_all(self, message_type, timeout=20, groupid='mygroup'):
        """
        Receives all messages meant for this node
        Each node will have it's own receive message all
        :param message_type: Message class
        :param count: No. of messages to receive
        :return: Instance of MessageList (see federated.models.MessageList)
        """
        assert issubclass(message_type, AbstractMessage)

        return recv(message_type, count=-1, endpoint=self.endpoint, timeout=timeout, groupid=groupid)
