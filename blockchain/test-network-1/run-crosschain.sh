#!/bin/bash

function chaincode-go() {
    cd "$PWD/../asset-transfer-basic/chaincode-go"
}

function test-network() {
    cd "$HOME/KGP-Documents/MTP/Code/FL/fabric-samples/test-network-1"
}

function application-go() {
    cd "$PWD/../asset-transfer-basic/application-go-net1"
}

# Destroy the network and then create a fresh one
echo -e "\n\n======== Destorying Old Network ============"
test-network
./network.sh down

echo -e "\n\n======== Creating New Network ============"
./network.sh up createChannel

echo -e "\n\n======== Packaging Chaincode ============="
chaincode-go
GO111MODULE=on go mod vendor
test-network

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/

peer lifecycle chaincode package basic.tar.gz --path ../asset-transfer-basic/chaincode-go/ --lang golang --label basic_1.0


echo -e "\n\n======== Installing Chaincode and approving on Org1 ==========="
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1-net1.example.com/peers/peer0.org1-net1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1-net1.example.com/users/Admin@org1-net1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode install basic.tar.gz

ID=`peer lifecycle chaincode queryinstalled`
PACKAGE_ID=${ID:42:74}
export CC_PACKAGE_ID=$PACKAGE_ID
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version 1.0 --package-id $CC_PACKAGE_ID --sequence 1 --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem


echo -e "\n\n======== Installing Chaincode and approving on Org2 ==========="
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2-net1.example.com/users/Admin@org2-net1.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install basic.tar.gz
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version 1.0 --package-id $CC_PACKAGE_ID --sequence 1 --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem


echo -e "\n\n======== Committing Chaincode ==========="
peer lifecycle chaincode checkcommitreadiness --channelID mychannel --name basic --version 1.0 --sequence 1 --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --output json
peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version 1.0 --sequence 1 --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --peerAddresses localhost:7051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1-net1.example.com/peers/peer0.org1-net1.example.com/tls/ca.crt --peerAddresses localhost:9051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt



echo -e "\n\n========= Remove previous Wallet ========"
application-go

rm -f $PWD/wallet/appUser.id
