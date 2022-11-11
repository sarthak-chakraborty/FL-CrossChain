#!/bin/bash
function home() {
    cd "$HOME/FL-CrossChain/"
}

sudo rm -rf data
sudo rm -rf /tmp/*
rm -rf updates
rm -rf models
rm nohup.out
mkdir updates
mkdir models
docker rm --force $(docker ps -aq)
docker image prune -f
docker volume prune -f
export NETWORK=$1
docker network create -d overlay --attachable $1
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.2.0 1.4.8
source blockchain/test-network-1/run-crosschain.sh
nohup go run cross-chain-application.go > cross-chain.out &
nohup python3 peerApplication/sign.py > sign.out &

sudo apt install -y net-tools
sudo ifconfig lo:0 10.254.254.254

home
docker-compose -f docker-compose-kafka.yml up --build -d
# nohup python peerApplication/sign.py > sign.out
# nohup python peerApplication/verify.py > verify.out

docker-compose -f docker-compose-server.yml up --build
# sleep 1
# tail -f nohup.out
