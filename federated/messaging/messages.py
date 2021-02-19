import pickle
import datetime

from federated.models import KerasModel, Update
from federated.settings import Settings
from federated.generic import List
from federated.settings import Settings
from federated.generic import List


# TODO: Seperate file for each Message


class MessageList(List):
    """
    List of Messages
    """

    def __init__(self):
        super(MessageList, self).__init__()

    def append(self, message):
        assert isinstance(message, AbstractMessage)

        self.list.append(message)


class AbstractMessage(object):
    """
    A Message is anything that will be sent to the messaging system/framework.

    This class defines the properties to be present
    in a Message
    These properties will be used by the Messaging Framework
    """

    """
    Messages MUST implement the following functions
    They will used while using send and recv apis in Messaging (See federated.messaging.Kafka.kafka)
    """

    @property
    def endpoint(self):
        """
        The endpoint to which the message should be sent
        :return: topic string

        They are called topics in kafka. May be an api endpoint in some other framework.
        """
        raise NotImplementedError

    def serialize(self):
        """
        Serializes an instance
        :return: serialized instance
        """
        raise NotImplementedError

    @classmethod
    def deserialize(cls, data):
        """
        Deserializes a serialized instance of the class
        :param data: serialized instance of the class
        :return: Deserialized instance
        """
        raise NotImplementedError


class RegistrationMessage(AbstractMessage):
    """
    RegistrationMessage is sent by the client to the server
    """
    endpoint = Settings.endpoint["Registrar"]

    def __init__(self, client_id, description, client_endpoint):
        self.client_id = client_id
        self.description = description
        self.client_endpoint = client_endpoint

    def serialize(self):
        return pickle.dumps(dict({
            "client_id": self.client_id,
            "description": self.description,
            "client_endpoint": self.client_endpoint
        }))

    @classmethod
    def deserialize(cls, data):
        obj = pickle.loads(data)
        return cls(
            client_id=obj["client_id"],
            description=obj["description"],
            client_endpoint=obj["client_endpoint"]
        )

    def __repr__(self):
        return "<RegistrationMessage: <client_id : {}>>".format(self.client_id)


class DeliveratorRequestMessage(AbstractMessage):
    """
    DeliveratorRequestMessage

    Sent from aggregator to deliverator

    Upon receipt the deliverator will send messages
    to the specified clients
    """

    endpoint = Settings.endpoint["Deliverator"]

    def __init__(self, client_endpoints, control_flags, train_request):
        assert isinstance(client_endpoints, list)

        self.client_endpoints = client_endpoints

        if control_flags is not None:
            assert isinstance(control_flags, dict)

        if train_request is not None:
            assert isinstance(train_request, TrainingRequest)

        self.control_flags = control_flags
        self.train_request = train_request

    def serialize(self):
        return pickle.dumps(dict({
            "client_endpoints": self.client_endpoints,
            "control_flags": self.control_flags,
            "train_request": pickle.dumps(self.train_request),
        }))

    @classmethod
    def deserialize(cls, data):
        obj = pickle.loads(data)
        return cls(
            client_endpoints=obj["client_endpoints"],
            control_flags=obj["control_flags"],
            train_request=pickle.loads(obj["train_request"]),
        )

    def __repr__(self):
        return "<DeliveratorRequestMessage>"


class UpdateMessage(AbstractMessage):
    """
    UpdateMessage

    Sent from client to server, after training completion

    This will carry an Update Model within.
    See federated.models.Update
    """
    endpoint = Settings.endpoint["Connector"]

    def __init__(self, client_id, client_endpoint, kmodel, history, data_count, server_sent_ts, client_recv_ts, client_sent_ts=None):
        """
        :param update: Instance of Update Model
        """

        assert isinstance(kmodel, KerasModel)
        self.client_id = client_id
        self.client_endpoint = client_endpoint
        self.history = history
        self.data_count = data_count
        self.kmodel = kmodel
        self.server_sent_ts = server_sent_ts,
        self.client_recv_ts = client_recv_ts,
        self.client_sent_ts = client_sent_ts or datetime.datetime.utcnow()

    def serialize(self):
        return pickle.dumps(dict({
            "client_id": self.client_id,
            "client_endpoint": self.client_endpoint,
            "kmodel": self.kmodel.to_dict(),
            "data_count": self.data_count,
            "history": self.history,
            "server_sent_ts": self.server_sent_ts,
            "client_recv_ts": self.client_recv_ts,
            "client_sent_ts": self.client_sent_ts
        }))

    @classmethod
    def deserialize(cls, data):
        obj = pickle.loads(data)
        return cls(
            client_id=obj["client_id"],
            client_endpoint=obj["client_endpoint"],
            kmodel=KerasModel.from_dict(obj["kmodel"]),
            data_count=obj["data_count"],
            history=obj["history"],
            server_sent_ts=obj["server_sent_ts"],
            client_recv_ts=obj["client_recv_ts"],
            client_sent_ts=obj["client_sent_ts"]
        )

    def __repr__(self):
        return "<UpdateMessage: {}>".format(self.client_endpoint)


class ReadyMessage(AbstractMessage):
    """
    Sent from clients to Selector after successful
    registration
    """

    endpoint = Settings.endpoint["Selector"]

    def __init__(self, client_endpoint, metadata=None):
        self.client_endpoint = client_endpoint
        self.metadata = metadata

    def serialize(self):
        return pickle.dumps(dict({
            "client_endpoint": self.client_endpoint,
            "metadata": self.metadata
        }))

    @classmethod
    def deserialize(cls, data):
        obj = pickle.loads(data)
        return cls(
            client_endpoint=obj["client_endpoint"],
            metadata=obj["metadata"]
        )

    def __repr__(self):
        return '<ReadyMessage: <{}>>'.format(self.client_endpoint)


#
# class MetricMessage(AbstractMessage):
#     """
#     Metric Message
#     Carries an instance of Metric Model within
#     """
#     endpoint = Config.endpoint[""]
#
#     def __init__(self, metric):
#         """
#         :param metric: An instance of Metric class (See federated.models.Metric)
#         """
#         self.metric = metric
#
#     def serialize(self):
#         return pickle.dumps(self.metric.to_dict())
#
#     @classmethod
#     def deserialize(cls, data):
#         return cls(Metric.from_dict(pickle.loads(data)))


class StartSignalMessage(AbstractMessage):
    """
    Sent by coordinator to other components
    """

    def __init__(self, component_name):
        """
        :param component: eg. 'Aggregator', 'Connector'
        """
        assert component_name in Settings.server_components

        self.component_name = component_name

    @property
    def endpoint(self):
        return Settings.trigger[self.component_name]

    def serialize(self):
        return pickle.dumps(self.component_name)

    @classmethod
    def deserialize(cls, data):
        return cls(pickle.loads(data))


class TrainingRequest:
    """
    TrainingRequeust

    Sent from server to client
    Includes model and hyperparams
    """

    def __init__(self, kmodel, hparams):
        """
        :param client_id: unique identifier of client, RemoteClient->id
        :param kmodel: Instance of KerasModel (See federated.models.KerasModel)
        :param hparams: Dictionary of Hyperparameters
        """
        assert isinstance(kmodel, KerasModel)

        self.kmodel = kmodel
        self.hparams = hparams

    def __repr__(self):
        return '<TrainingRequest: <Model {}, Version {}>>'.format(self.kmodel.id, self.kmodel.version)


class ClientMessage(AbstractMessage):
    """
    Client Message
    To be sent from server to client
    """

    def __init__(self, client_endpoint, control_flags, train_request=None, timestamp=None):
        """
        :param client_id: ID of client
        :param flags: Flags to be sent (A dictionary)
        :param trq: TrainRequestMessage
        """
        self.client_endpoint = client_endpoint

        if control_flags is not None:
            assert isinstance(control_flags, dict)

        if train_request is not None:
            assert isinstance(train_request, TrainingRequest)

        self.control_flags = control_flags
        self.train_request = train_request
        self.timestamp = timestamp or datetime.datetime.utcnow()

    @property
    def endpoint(self):
        return self.client_endpoint

    def serialize(self):
        return pickle.dumps(dict({
            "client_endpoint": self.client_endpoint,
            "control_flags": self.control_flags,
            "train_request": pickle.dumps(self.train_request),
            "timestamp": self.timestamp
        }))

    @classmethod
    def deserialize(cls, data):
        obj = pickle.loads(data)
        return cls(
            client_endpoint=obj["client_endpoint"],
            control_flags=obj["control_flags"],
            train_request=pickle.loads(obj["train_request"]),
            timestamp=obj["timestamp"]
        )


class CoordinatorRequestMessage(AbstractMessage):
    endpoint = Settings.endpoint['Coordinator']

    def __init__(self, control_flags):
        self.control_flags = control_flags

    def serialize(self):
        return pickle.dumps(self.control_flags)

    @classmethod
    def deserialize(cls, data):
        return cls(pickle.loads(data))
