import os
import pickle
import shutil
import sys

import numpy as np
from PIL import Image



def cifar_iid(dataset, num_clients):
    """
    Sample I.I.D. client data from CIFAR10 dataset
    :param dataset:
    :param num_clients:
    :return: dict of image index
    """

    data, label = np.array(dataset['data']), np.array(dataset['label'])
    num_items = len(data) // num_clients

    data_split = np.random.choice(len(data), (num_clients, num_items), replace=False)
    user_data = {i: data[data_split[i]] for i in range(num_clients)}
    user_label = {i: label[data_split[i]] for i in range(num_clients)}
    dict_users = {'data': user_data, 'label': user_label}
    return dict_users


def cifar_noniid(overlapping_classes, dataset, num_clients, num_classes):
    """
    Sample Non I.I.D. client data from CIFAR10 dataset
    :param dataset:
    :param num_clients:
    :return: dict of image index
    """

    data, label = dataset['data'], dataset['label']

    num_items = int(len(data))
    dict_users = {}
    idx = {}

    for i in range(num_classes):
        idx[i] = np.where(label == i)[0]

    # if(num_clients<=5):
    #     k = int(10/num_users)
    #     for i in range(num_users):
    #         a = 0
    #         for j in range(i*k,(i+1)*k):
    #             a += j
    #             if(j==i*k):
    #                 dict_users[i] = list(idx[j])
    #             else:
    #                 dict_users[i] = np.append(dict_users[i],idx[j])
    #         print(a)
    #     return dict_users
    # if k = 4, a particular user can have samples only from at max 4 classes

    k = overlapping_classes

    num_examples = int(num_items / (k * num_clients))

    user_data, user_label = {}, {}
    for i in range(num_clients):
        t = 0
        while (t != k):
            j = np.random.randint(0, num_classes)
            if (len(idx[(i + j) % num_classes]) >= num_examples):
                data_index = set(np.random.choice(idx[(i + j) % num_classes], num_examples, replace=False))

                if (t == 0):
                    user_data[i] = [data[index] for index in data_index]
                    user_label[i] = [label[index] for index in data_index]
                else:
                    user_data[i].extend([data[index] for index in data_index])
                    user_label[i].extend([label[index] for index in data_index])

                idx[(i + j) % num_classes] = list(set(idx[(i + j) % num_classes]) - data_index)
                t += 1

        user_label[i] = np.array(user_label[i])

    dict_users = {'data': user_data, 'label': user_label}
    return dict_users


def divide_data(datadir, type, dict_users):
    c = 0  # Show progress
    for i in range(0, num_clients):
        clientdir = datadir + "/" + type + "/client_" + str(i) + "/"  # client directory
        clientdata = dict_users['data'][i]
        clientlabel = dict_users['label'][i]

        for j in range(num_classes):
            labeldir = clientdir + str(j)
            os.makedirs(labeldir)

        for j in range(clientdata.shape[0]):
            savefile = clientdir + str(clientlabel[j]) + "/" + str(j) + ".jpg"
            im = Image.fromarray(clientdata[j])
            im.save(savefile)
            c += 1
            if c % 100 == 0:
                print(c, end='\r')


if __name__ == '__main__':
    dataset_name = sys.argv[1]

    with open('../datasets/{}/data.pkl'.format(dataset_name), 'rb') as f:
        dataset = pickle.load(f, encoding='latin1')
    num_classes = len(np.unique(dataset['label']))
    overlapping_classes = 40

    num_clients = int(sys.argv[2])
    print(num_clients)

    datadir = "../datasets/" + dataset_name + "/dataclient"
    # delete old partitioning
    try:
        shutil.rmtree(datadir)
    except OSError as e:
        print("No old data")

    np.random.seed(0)

    if num_clients >= 20:
        dict_users = cifar_noniid(overlapping_classes, dataset, num_clients, num_classes)
        divide_data(datadir, 'noniid', dict_users)

    dict_users = cifar_iid(dataset, num_clients)
    divide_data(datadir, 'iid', dict_users)

    # Load test data
    with open('../datasets/{}/testdata.pkl'.format(dataset_name), 'rb') as f:
        dataset = pickle.load(f, encoding='latin1')

    datadir = "../datasets/" + dataset_name + "/testdata/"
    try:
        shutil.rmtree(datadir)
    except OSError as e:
        print("No old test data")

    data = np.array(dataset['data'])
    label = np.array(dataset['label'])
    for j in range(num_classes):
        labeldir = datadir + str(j)
        os.makedirs(labeldir)

    c = 0
    for j in range(data.shape[0]):
        savefile = datadir + str(label[j]) + "/" + str(j) + ".jpg"
        im = Image.fromarray(data[j])
        im.save(savefile)
        c += 1
        if c % 100 == 0:
            print(c, end='\r')

