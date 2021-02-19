#!/bin/bash

export NETWORK=federated
docker-compose -f docker-compose-client.yml up --build --scale client=$1