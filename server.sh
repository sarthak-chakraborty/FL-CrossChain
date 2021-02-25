#!/bin/bash
function home() {
    cd "$HOME/KGP-Documents/MTP/Code/FL/"
}

rm -rf data
rm -rf /tmp/*
rm -rf updates
rm -rf models
rm nohup.out
mkdir updates
mkdir models
docker rm --force $(docker ps -aq)
docker image prune -f
docker volume prune -f
export NETWORK=$1
docker-compose -f docker-compose-kafka.yml up --build -d
source fabric-samples/test-network-1/run-crosschain.sh
nohup go run cross-chain-application.go > cross-chain.out
nohup python peerApplication/sign.py > sign.out
nohup python peerApplication/verify.py > verify.out

home
docker-compose -f docker-compose-server.yml up --build
# sleep 1
# tail -f nohup.out
