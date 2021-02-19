#!/bin/bash

rm -rf /tmp/*
docker rm --force $(docker ps -aq)
export NETWORK=$1 
docker run -dit --name alpine --network $1 alpine
docker-compose -f docker-compose-client.yml up --build -d --scale client=$2 

# tail -f nohup.out