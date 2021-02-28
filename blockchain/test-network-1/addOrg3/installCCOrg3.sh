#!/bin/bash

function chaincode-go() {
    cd "$PWD/../asset-transfer-basic/chaincode-go"
}

function test-network() {
    cd "$HOME/KGP-Documents/MTP/Code/Hyperledger/fabric-samples/test-network-1"
}

echo -e "\n\n======== Configuring Leader Election ============"

cd "../"

export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org3MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org3-net1.example.com/peers/peer0.org3-net1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org3-net1.example.com/users/Admin@org3-net1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7061

export CORE_PEER_GOSSIP_USELEADERELECTION=false
export CORE_PEER_GOSSIP_ORGLEADER=true


echo -e "\n\n======== Install and Approve Chaincode ============"

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/

chaincode_version=$1

chaincode-go
GO111MODULE=on go mod vendor
test-network

peer lifecycle chaincode package basic_${chaincode_version}.tar.gz --path ../asset-transfer-basic/chaincode-go/ --lang golang --label basic_${chaincode_version}.0
peer lifecycle chaincode install basic_${chaincode_version}.tar.gz

peer lifecycle chaincode queryinstalled --output json > chaincode_package_id.json
INDEX="$((${chaincode_version} - 1))"
PACKAGE_ID=`jq -r '.installed_chaincodes['${INDEX}'].package_id' chaincode_package_id.json`
export CC_PACKAGE_ID=$PACKAGE_ID
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --channelID mychannel --name basic --version ${chaincode_version}.0 --package-id $CC_PACKAGE_ID --sequence ${chaincode_version}


# echo -e "\n\n======== Include Org3 Anchor Peer ============"