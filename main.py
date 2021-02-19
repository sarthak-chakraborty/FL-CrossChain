import sys

from federated.nodes.server.components.coordinator import Coordinator
from federated.nodes.server.components.aggregator import Aggregator
from federated.nodes.server.components.deliverator import Deliverator
from federated.nodes.server.components.connector import Connector
from federated.nodes.server.components.registrar import Registrar
from federated.nodes.server.components.selector import Selector
from federated.nodes.client import Client


def usage():
    return "Usage: python {} (server|client)".format(sys.argv[0])


testing = False

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print(usage())
        exit(1)

    if sys.argv[1] == 'server':
        # Run Server
        if testing:
            Coordinator(1).test()
        else:
            Coordinator(1).run()
    elif sys.argv[1] == 'client':
        # Check if client id has been provided
        if len(sys.argv) != 3:
            print(usage())
            exit(1)
        # Run Client
        # print("Starting Client {}..".format(sys.argv[2]))
        if testing:
            Client('Mischievous Client').test()
        else:
            Client('Good Client').run()
    elif sys.argv[1] == 'registrar':
        Registrar(1, 1).run()
    elif sys.argv[1] == 'aggregator':
        Aggregator(1, 1).run()
    elif sys.argv[1] == 'deliverator':
        Deliverator(1).run()
    elif sys.argv[1] == 'connector':
        Connector(1).run()
    elif sys.argv[1] == 'selector':
        Selector(1, 1).run()
    else:
        print(usage())
