from pprint import pformat
import pickle
import logging
import json
import sys

from confluent_kafka import Producer
from confluent_kafka import Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic, NewPartitions, ConfigResource, ConfigSource
from confluent_kafka import KafkaException
import sys
import threading
import logging


from federated.messaging.messages import AbstractMessage, MessageList

class Sender:

    p = Producer({
            'bootstrap.servers': 'kafka:29092',
            'message.max.bytes': 1000000000
        })


    @classmethod
    def send(cls, message):
        """
        Send message to its assigned topic
        :param message: Instance of Subclass of Message
        :return: None
        """

        """
        Assert that message is sendable
        """
        assert isinstance(message, AbstractMessage)

        # Asynchronously produce a message, the delivery report callback
        # will be triggered from poll() above, or flush() below, when the message has
        # been successfully delivered or failed permanently.

        def delivery_report(err, msg):
            """ Called once for each message produced to indicate delivery result.
                Triggered by poll() or flush(). """
            if err is not None:
                print('[Kafka] Message delivery failed: {}'.format(err))
            else:
                print('[Kafka] Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
	print(message.endpoint)
        cls.p.produce(message.endpoint, message.serialize(), callback=delivery_report)

        cls.p.poll(0)
        # Wait for any outstanding messages to be delivered and delivery report
        # callbacks to be triggered.
        cls.p.flush()


def recv(message_class, count=1, endpoint=None, timeout=20, groupid='mygroup'):
    """
    :param message_class: Message Class
    :param count: Integer (-1 for infinite)
    :return: List of received Instances of size count
    """

    """
    Assert that message is receivable
    """
    assert issubclass(message_class, AbstractMessage)

    c = Consumer({
        'bootstrap.servers': 'kafka:29092',
        'group.id': str(groupid),
        'message.max.bytes': 1000000000,
        'max.partition.fetch.bytes': 1000000000,
        'auto.offset.reset': 'earliest'
    })

    def print_assignment(consumer, partitions):
        pass
        # print('[Kafka] Assignment:', partitions)

    """ If endpoint is not specified use message class 
        endpoint. """
    if not endpoint:
        topic = message_class.endpoint
    else:
        topic = endpoint
    create_topics([topic])
    c.subscribe([topic], on_assign=print_assignment)
    # Read messages from Kafka, append to result
    results = MessageList()

    if count == -1:
        num_messages = 100
        msgs = c.consume(num_messages=num_messages, timeout=timeout)
        for msg in msgs:
            if msg is not None:
                if msg.error():
                    print("Consumer error: {}".format(msg.error()))
                    continue

                results.append(message_class.deserialize(msg.value()))
                try:
                    print(results[-1].client_endpoint())
                except:
                    print("Client Endpoint not found for "),
                    print(message_class)

    else:
        while count > 0:
            msg = c.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            else:
                # sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                #                  (msg.topic(), msg.partition(), msg.offset(),
                #                   str(msg.key())))
                count -= 1
                results.append(message_class.deserialize(msg.value()))
                try:
                    print(results[-1].client_endpoint())
                except:
                    print("Client Endpoint not found for "),
                    print(message_class)


    c.close()
    return results


def create_topics(topics):
    """ Create topics """

    a = AdminClient({'bootstrap.servers': 'kafka:29092'})

    new_topics = [NewTopic(topic, num_partitions=3, replication_factor=1) for topic in topics]
    # Call create_topics to asynchronously create topics, a dict
    # of <topic,future> is returned.
    fs = a.create_topics(new_topics)

    # Wait for operation to finish.
    # Timeouts are preferably controlled by passing request_timeout=15.0
    # to the create_topics() call.
    # All futures will finish at the same time.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))


def info(args):
    """ list topics and cluster metadata """

    a = AdminClient({'bootstrap.servers': 'kafka:29092'})

    if len(args) == 0:
        what = "all"
    else:
        what = args[0]

    md = a.list_topics(timeout=10)

    print("Cluster {} metadata (response from broker {}):".format(md.cluster_id, md.orig_broker_name))

    if what in ("all", "brokers"):
        print(" {} brokers:".format(len(md.brokers)))
        for b in iter(md.brokers.values()):
            if b.id == md.controller_id:
                print("  {}  (controller)".format(b))
            else:
                print("  {}".format(b))

    if what not in ("all", "topics"):
        return

    print(" {} topics:".format(len(md.topics)))
    for t in iter(md.topics.values()):
        if t.error is not None:
            errstr = ": {}".format(t.error)
        else:
            errstr = ""

        print("  \"{}\" with {} partition(s){}".format(t, len(t.partitions), errstr))

        for p in iter(t.partitions.values()):
            if p.error is not None:
                errstr = ": {}".format(p.error)
            else:
                errstr = ""

            print("partition {} leader: {}, replicas: {},"
                  " isrs: {} errstr: {}".format(p.id, p.leader, p.replicas,
                                                p.isrs, errstr))


def delete_topics(topics):
    """ delete topics """


    # Call delete_topics to asynchronously delete topics, a future is returned.
    # By default this operation on the broker returns immediately while
    # topics are deleted in the background. But here we give it some time (30s)
    # to propagate in the cluster before returning.
    #
    # Returns a dict of <topic,future>.

    a = AdminClient({'bootstrap.servers': 'kafka:29092'})

    fs = a.delete_topics(topics, operation_timeout=30)

    # Wait for operation to finish.
    for topic, f in fs.items():
        try:
            f.result()  # The result itself is None
            print("Topic {} deleted".format(topic))
        except Exception as e:
            print("Failed to delete topic {}: {}".format(topic, e))
