import os
import pymongo
from pymongo import MongoClient
import pickle
import datetime
import tensorflow as tf
from tensorflow.keras import layers
from pathlib import Path
import string
import secrets
import json

from federated.generic import List
from federated.nodes.server.config import DatabaseConfig


# TODO: Seperate file for each model


class ModelList(List):
    """
    List of Models
    """

    def __init__(self):
        super(ModelList, self).__init__()

    def append(self, model):
        assert isinstance(model, AbstractModel)

        self.list.append(model)


class AbstractModel:
    """
    Abstract Model Class
    """

    @property
    def collection(self):
        """
        Collection to which this model must be saved
        :return:
        """
        raise NotImplementedError

    def commit(self):
        """
        Saves a model in the database
        Update, if primary key exists
        """
        # print("Connection to Mongo...")
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        # print("mongo-client: {}".format(client))
        db = client[DatabaseConfig.database]
        records = db[self.collection]
        # print(kmodels)
        records.save(self.to_dict())
        client.close()

    @classmethod
    def query(cls, **kwargs):
        """
        Generic querying

        Examples:
            >> RemoteClient.find(_id=1, is_reg=True)
            >> RemoteClient.find(_id=1)

            >> for client in Client.find():
            >>      do_something(client)

        Returns a list of instances satisfying the query
        If arg=None, all instances are returned
        """
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]
        records = db[cls.collection].find(kwargs)

        result = ModelList()
        for record in records:
            result.append(cls.from_dict(record))
        client.close()
        return result

    @classmethod
    def destroy_db(cls):
        """
        Drops a collection

        Example:
            Client.destroy()
        """
        print("Destroying {}...".format(cls.collection))
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]
        records = db[cls.collection]
        print(records)
        records.drop()

    def to_dict(self):
        """
        Returns a dictionary representation of database model
        Used while saving model
        """
        raise NotImplementedError

    @classmethod
    def from_dict(cls, obj):
        """
        Converts a dict to instance

        Used while querying
        """
        raise NotImplementedError


class KerasModel(AbstractModel):
    """
    Tensorflow Model
    """

    collection = 'keras_models'

    def __init__(self, id, name, version, architecuture, weights, optimizer, loss, metrics):
        """
        :param _id: Keras Model ID (primary Key) (Update: No longer the primary key)
        :param name: Keras Model Name (Eg. CNN)
        :param version: Version of Model
        :param architecuture: json architecture plan
        :param weights: weights of model, numpy array
        :param loss: loss type eg. 'categorical_crossentropy' or instance of tf.keras.losses.Loss
        :param metrics: eg: ['accuracy']
        :param optimizer: eg: 'adam' or instance of tf.keras.optimizers.Optimizer
        """
        self.id = id
        self.name = name
        self.architecture = architecuture
        self.weights = weights
        self.optimizer = optimizer
        self.loss = loss
        self.metrics = metrics
        self.version = version
        
    def get_model(self):
        model = tf.keras.models.model_from_json(self.architecture)
        model.set_weights(self.weights)
        model.compile(optimizer=self.optimizer, loss=self.loss, metrics=self.metrics)

        assert isinstance(model, tf.keras.models.Model)
        return model

    def set_model(self, model):
        """
        Sets a model, i.e. saves the architecture and weights
        :param model: instance of tf.keras.models.Model
        """
        assert isinstance(model, tf.keras.models.Model)

        self.architecture = model.to_json()
        self.weights = model.get_weights()

    def set_weights(self, weights):
        """
        Sets weights of KerasModel instance
        :param weights: numpy array, (model.get_weights())
        :return: None
        """
        self.weights = weights

    def get_weights(self):
        """
        Returns weights of the instance
        """
        return self.weights

    @classmethod
    def get_latest_version(cls, id):
        """
        Get Latest Version
        :param id: integer, model_id
        :return: Instance of KerasModel class for latest model
        """
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]
        records = db[cls.collection].find({'id': id}).sort("version", pymongo.DESCENDING).limit(1)

        for record in records:
            kmodel = cls.from_dict(record)
            
        model = tf.keras.models.model_from_json(kmodel.architecture)
        model.load_weights("models/" + str(kmodel.version) + ".h5")
        kmodel.set_model(model)
        return kmodel

    def to_dict(self):
        return dict({
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'architecture': self.architecture,
            'weights': pickle.dumps(self.weights),
            'optimizer': pickle.dumps(self.optimizer),
            'loss': pickle.dumps(self.loss),
            'metrics': pickle.dumps(self.metrics)
        })

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["id"],
            name=obj["name"],
            version=obj["version"],
            architecuture=obj["architecture"],
            weights=obj["weights"] if type(obj["weights"]) is str else pickle.loads(obj["weights"]),
            optimizer=pickle.loads(obj["optimizer"]),
            loss=pickle.loads(obj["loss"]),
            metrics=pickle.loads(obj["metrics"])
        )
    
    def commit(self):
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]
        records = db[self.collection]
        record = self.to_dict()
        record["weights"] = "models/" + str(self.version) + ".h5"
        self.get_model().save_weights("models/" + str(self.version) + ".h5")
        records.save(record)

    def __repr__(self):
        return "<KerasModel <ID : {}, Version : {}>".format(self.id, self.version)


class RemoteClient(AbstractModel):
    """
    Remote clients
    """

    collection = 'clients'

    def __init__(self, id, client_endpoint, desc='', is_reg=False, status='active', reg_timestamp=None):
        """
        :param _id: Client ID (primary key)
        :param desc: Client Description (Eg. Powerful, Slow etc. <May be useless>)
        :param is_reg: Client Registration Status
        :param reg_timestamp: Time of Registration
        """
        self._id = id
        self.desc = desc
        self.is_reg = is_reg
        self.status = status
        self.client_endpoint = client_endpoint
        self.reg_timestamp = reg_timestamp or datetime.datetime.utcnow()

    @property
    def id(self):
        return self._id

    def to_dict(self):
        return dict({
            '_id': self.id,
            'desc': self.desc,
            'is_reg': self.is_reg,
            'status': self.status,
            'client_endpoint': self.client_endpoint,
            'reg_timestamp': self.reg_timestamp
        })

    @classmethod
    def from_dict(cls, obj):
        return cls(
            id=obj["_id"],
            desc=obj["desc"],
            is_reg=obj["is_reg"],
            status=obj["status"],
            client_endpoint=obj["client_endpoint"],
            reg_timestamp=obj["reg_timestamp"])

    @classmethod
    def from_reg_msg(cls, reg_msg, client_id):
        """
        Registers a client from a RegistrationMessage (See federated.messaging.RegistrationMessage)
        :param reg_msg: Instance of RegistrationMessage
        :return: Instance of RemoteClient
        """

        description = reg_msg.description
        client_endpoint = reg_msg.client_endpoint
        """
            If client is found in database return from database
            else save to database and return client instance
        """
        if cls.query(client_endpoint=client_endpoint).count() > 0:
            return cls.query(client_endpoint=client_endpoint).first()
        else:
            rclient = cls(client_id, client_endpoint=client_endpoint, desc=description, is_reg=False)
            rclient.commit()
            return rclient

    def __repr__(self):
        return "<{}>".format(self.client_endpoint)


class Update(AbstractModel):
    """
    Update (sent by client) Model
    """
    collection = 'update'

    def __init__(self, _id, client_endpoint, client_id, kmodel, history, data_count, server_sent_ts, client_recv_ts, client_sent_ts, server_recv_ts, handled=False):
        """
        :param client_id: Client which sends the update
        :param kmodel: Instance of keras.models.Model (Eg. Sequential())
        :param timestamp: Time at which the update Arrived
        """
        assert isinstance(kmodel, KerasModel)

        self._id = _id
        self.client_endpoint = client_endpoint
        self.client_id = client_id
        self.kmodel = kmodel
        self.history = history
        self.server_sent_ts = server_sent_ts
        self.client_recv_ts = client_recv_ts
        self.client_sent_ts = client_sent_ts
        self.server_recv_ts = server_recv_ts
        self.data_count = data_count
        self.handled = handled

    def to_dict(self):
        return dict({
            '_id': self._id,
            'client_endpoint': self.client_endpoint,
            'client_id': self.client_id,
            'kmodel': self.kmodel.to_dict(),
            'history': self.history,
            'handled': self.handled,
            "server_sent_ts": self.server_sent_ts,
            "client_recv_ts": self.client_recv_ts,
            "client_sent_ts": self.client_sent_ts,
            "server_recv_ts": self.server_recv_ts,
            'data_count': self.data_count,
        })

    @classmethod
    def query(cls, **kwargs):
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]

        records = db[cls.collection].find(kwargs)
        result = ModelList()

        for record in records:
            update = cls.from_dict(record)
            model = tf.keras.models.model_from_json(update.kmodel.architecture)
            fname = "updates/" + str(update.kmodel.version) + "_" + str(update.client_id) + ".h5"
            print("fname: {}".format(fname))

            model.load_weights(fname)
            update.kmodel.set_model(model)
            result.append(update)
            os.remove(fname)
            print("Deleted: {}".format(fname))

        client.close()  
        return result

    @classmethod
    def handle(cls, update):
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]

        db[cls.collection].update_one({"_id": update._id}, {"$set" : {"handled": True}})


    @classmethod
    def from_dict(cls, obj):
        return cls(
            _id=obj["_id"],
            client_endpoint=obj["client_endpoint"],
            client_id = obj["client_id"],
            kmodel=KerasModel.from_dict(obj["kmodel"]),
            history=obj["history"],
            data_count=obj["data_count"],
            handled=obj["handled"],
            server_sent_ts=obj["server_sent_ts"],
            client_recv_ts=obj["client_recv_ts"],
            client_sent_ts=obj["client_sent_ts"],
            server_recv_ts=obj["server_recv_ts"]
        )

    @classmethod
    def from_update_msg(cls, update_msg, id):
        """
        :param update_msg: UpdateMessage Instance (See federated.messaging.UpdateMessage)
        :return: Instance of Update
        """
        return cls(
            _id=id,
            client_endpoint=update_msg.client_endpoint,
            client_id = update_msg.client_id,
            kmodel=update_msg.kmodel,
            data_count=update_msg.data_count,
            history=update_msg.history,
            handled=False,
            server_sent_ts=update_msg.server_sent_ts,
            client_recv_ts=update_msg.client_recv_ts,
            client_sent_ts=update_msg.client_sent_ts,
            server_recv_ts=datetime.datetime.utcnow()
        )
    
    def commit(self):
        client = MongoClient(DatabaseConfig.host, DatabaseConfig.port)
        db = client[DatabaseConfig.database]
        records = db[self.collection]
        record = self.to_dict()
        record["kmodel"]["weights"] = "updates/" + str(self.kmodel.version) + "_" + str(self.client_id) + ".h5"
        self.kmodel.get_model().save_weights("updates/" + str(self.kmodel.version) + "_" + str(self.client_id) + ".h5")
        records.save(record)
        client.close()

    def __repr__(self):
        return "<Update: <Client: {}, Model: {}, Time: {}>>".format(self.client_endpoint, self.kmodel.id, self.server_recv_ts)


class ClientUpdateMetric(AbstractModel):
    """
    Metric for Analytics Purposes
    """

    collection = 'client_metrics'

    def __init__(self, client_id, model_id, history, train_version, global_version, server_sent_ts, client_recv_ts, client_sent_ts, server_recv_ts, timestamp=None):
        """
        :param client_id: Client which sent the metrics
        :param epoch_no: Epoch No during training
        :param model_id: Model ID
        :param timestamp: Time at which the metric arrived
        """
        self.client_id = client_id
        self.model_id = model_id
        self.train_loss = history["loss"][-1]
        self.test_loss = history["val_loss"][-1]
        self.train_acc = history["accuracy"][-1]
        self.test_acc = history["val_accuracy"][-1]
        self.train_version = train_version
        self.global_version = global_version
        self.server_sent_ts = server_sent_ts
        self.client_recv_ts = client_recv_ts
        self.client_sent_ts = client_sent_ts
        self.server_recv_ts = server_recv_ts

    def to_dict(self):
        return dict({
            "client_id": self.client_id,
            "model_id": self.model_id,
            "train_version": self.train_version,
            "global_version": self.global_version,
            "train_loss": self.train_loss,
            "test_loss": self.test_loss,
            "train_acc":self.train_acc,
            "test_acc": self.test_acc,
            "server_sent_ts": self.server_sent_ts,
            "client_recv_ts": self.client_recv_ts,
            "client_sent_ts": self.client_sent_ts,
            "server_recv_ts": self.server_recv_ts
        })

    @classmethod
    def from_dict(cls, obj):
        return cls(
            obj["client_id"],
            obj["model_id"],
            obj["train_version"],
            obj["global_version"],
            obj["train_loss"],
            obj["test_loss"],
            obj["train_acc"],
            obj["test_acc"],            
            obj["server_sent_ts"],
            obj["client_recv_ts"],
            obj["client_sent_ts"],
            obj["server_recv_ts"]
        )
    
    @classmethod
    def from_update(cls, update, global_version):
        """
        :param update: UpdateInstance (See federated.messaging.UpdateMessage)
        :return: Instance of ClientUpdateMetric
        """
        return cls(
            update.client_id,
            update.kmodel.id,
            update.history,
            update.kmodel.version,
            global_version,
            update.server_sent_ts[0][0], # somehow becomes an array
            update.client_recv_ts[0][0],
            update.client_sent_ts,
            update.server_recv_ts
        )


class ServerEvalMetric(AbstractModel):
    """
    Metric for Analytics Purposes
    """

    collection = 'server_metrics'

    def __init__(self, model_id, version, test_loss, test_acc, timestamp=None):
        """
        :param client_id: Client which sent the metrics
        :param epoch_no: Epoch No during training
        :param model_id: Model ID
        :param timestamp: Time at which the metric arrived
        """
        self.model_id = model_id
        self.version = version
        self.test_loss = test_loss
        self.test_acc = test_acc
        self.timestamp = timestamp or datetime.datetime.utcnow()

    def to_dict(self):
        return dict({
            "model_id": self.model_id,
            "version": self.version,
            "test_loss": self.test_loss,
            "test_acc": self.test_acc,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_dict(cls, obj):
        return cls(
            obj["model_id"],
            obj["version"],
            obj["test_loss"],
            obj["test_acc"],
            obj["timestamp"]
        )

class ClientMessageMetric(AbstractModel):
    """
    Metric for Analytics Purposes
    """

    collection = 'client_messages'

    def __init__(self, client_id, version, timestamp=None):
        """
        :param client_id: Client to send to
        :param version: Version sent
        :param timestamp: Time at which the metric arrived
        """
        self.client_id = client_id
        self.version = version
        self.timestamp = timestamp or datetime.datetime.utcnow()

    def to_dict(self):
        return dict({
            "client_id": self.client_id,
            "version": self.version,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_dict(cls, obj):
        return cls(
            obj["client_id"],
            obj["version"],
            obj["timestamp"]
        )
