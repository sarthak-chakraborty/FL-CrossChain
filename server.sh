#!/bin/bash

rm -rf data
rm -rf /tmp/*
rm -rf updates
rm -rf models
rm nohup.out
mkdir updates
mkdir models
docker rm --force $(docker ps -aq)
# docker image prune -f
# docker volume prune -f
export NETWORK=$1
docker-compose -f docker-compose-kafka.yml up --build -d
docker-compose -f docker-compose-server.yml up --build
# sleep 1
# tail -f nohup.out
