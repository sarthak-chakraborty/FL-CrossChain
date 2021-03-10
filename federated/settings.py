
class Settings:
    """
    Settings for the system

    NOTE: All these settings are necessary. They are used at many places.
    """

    # Mention all server components in this list
    server_components = [
        'Aggregator',
        'Connector',
        'Deliverator',
        'Registrar',
        'Selector'
    ]

    # Mention all the (normal) endpoints in this dict
    endpoint = {
        'Aggregator': 'aggregator-server',
        'Connector': 'connector-server',
        'Deliverator': 'deliverator-server',
        'Registrar': 'registration-server',
        'Selector': 'selector-server',
        'Coordinator': 'coordinator-server'
    }

    # Mention all the trigger endpoints in this dict
    trigger = {
        'Aggregator': 'aggregator-server-trigger',
        'Connector': 'connector-server-trigger',
        'Deliverator': 'deliverator-server-trigger',
        'Registrar': 'registration-server-trigger',
        'Selector': 'selector-server-trigger',
        'Coordinator': 'coordinator-server-trigger'
    }

    # Mention the messaging infrastructure being used
    messaging_infra = "Kafka"
    
    # Enable Cross-Chain Communication and Asset entry
    enable_crosschain = True
    
    # Dataset and partition strategy
    dataset_id = 0
    dataset = 'cifar-10'
    input_shape = (32, 32, 3)
    partition = 'iid'
    test_batch_size = 100
    num_classes = 10

    # Cityscapes Dataset
    # dataset = 'cityscapes'
    # input_shape = (256, 256, 3)
    # partition = 'noniid'
    # test_batch_size = 32
    # num_classes = 29

    # Shakespeare
    # dataset = 'shakespeare'
    # input_length = 80
    # num_classes = 70

    #delay =  8 * [10] + 16 * [40] +  26 * [70] + 26 * [100] + 16 * [130] + 8 * [160]
    #delay =  8 * [40] + 16 * [160] +  26 * [280] + 26 * [400] + 16 * [520] + 8 * [640]
    #delay =  4 * [40] + 8 * [160] + 16 * [280] + 16 * [400] + 8 * [520] + 4 * [640]
    #delay =  4 * [2.5] + 8 * [5] + 18 * [10] + 18 * [20] + 8 * [30] + 4 * [40]
    #delay =  4 * [10] + 8 * [40] + 18 * [70] + 18 * [100] + 8 * [130] + 4 * [160]
    delay =  5 * [2]

    



