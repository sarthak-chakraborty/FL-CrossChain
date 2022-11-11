# Proof of Federated Training

This is the repository corresponding to the paper titled "Proof of Federated Training: Accountable Cross-Network Model Training and Inference" ([link](https://ieeexplore.ieee.org/document/9805548)) accepted to 2022 IEEE International Conference on Blockchain and Cryptocurrency (ICBC '22). 

***Please cite our paper in any published work that uses any of these resources***

> @INPROCEEDINGS{9805548,  
  author={Chakraborty, Sarthak and Chakraborty, Sandip},   
  booktitle={2022 IEEE International Conference on Blockchain and Cryptocurrency (ICBC)},  
  title={Proof of Federated Training: Accountable Cross-Network Model Training and Inference},  
  year={2022}, 
  volume={},  
  number={},  
  pages={1-9},  
  doi={10.1109/ICBC54727.2022.9805548}}  


## Abstract

Blockchain has widely been adopted to design accountable federated learning frameworks; however, the existing frameworks do not scale for distributed model training over multiple independent blockchain networks. For storing the pre-trained models over blockchain, current approaches primarily embed a model using its structural properties that are neither scalable for cross-chain exchange nor suitable for cross-chain verification. This paper proposes an architectural framework for cross-chain verifiable model training using federated learning, called Proof of Federated Training (PoFT), the first of its kind that enables a federated training procedure span across the clients over multiple blockchain networks. Instead of structural embedding, PoFT uses model parameters to embed the model over a blockchain and then applies a verifiable model exchange between two blockchain networks for cross-network model training. We implement and test PoFT over a large-scale setup using Amazon EC2 instances and observe that cross-chain training can significantly boosts up the model efficacy. In contrast, PoFT incurs marginal overhead for inter-chain model exchanges.


## Running PoFT

### Starting Federated and Blockchain Network

	1. sh server.sh federated
	2. sh client-int.sh / sh client-ext.sh federated $num

The first script needs to be run in the AWS instance that will act as a server. It will first clear all docker containers, create an overlay network for docker swarm, start the blockchain network and the applications, start the Kafka containers and then start the server containers.

The second script needs to be run at every instance that will host a client. If the user wants to run the federated server and the clients in the same machine, he should run the script `client-int.sh`. Or else, if the clients are hosted in separate instances, then the docker swarm needs to be activated and hence the clients should run `client-ext.sh`. The number of dockerised clients that will run on a single instance is denoted by `$num`.

The two scripts together will run a single federated network with blockchain and its relay service. It will act as a sender network. To run a receiver network, the same steps need to be followed on a different group of instances.


### Activating Weights transfer

To start the process of transferring the weights, run `go run blockchain/asset-transfer-basic/application-go-net1/Controller.go`

For simplicity, we have currently modelled the system such that there is only 1 federated network and the network itself requests for a weight from its own blockchain network. However, cloning the codes and changing the endpoints to the network of a second federated network will establish the connection and the transfer request between the two separate federated networks.

