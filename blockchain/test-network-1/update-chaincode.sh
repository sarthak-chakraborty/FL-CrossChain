#!/bin/bash

function chaincode-go() {
    cd "$PWD/../asset-transfer-basic/chaincode-go"
}

function test-network() {
    cd "$HOME/KGP-Documents/MTP/Code/Hyperledger/fabric-samples/test-network-1"
}

chaincode_version=$1

echo -e "\n\n======== Packaging Chaincode ============="
chaincode-go
GO111MODULE=on go mod vendor
test-network

export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=$PWD/../config/
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1-net1.example.com/users/Admin@org1-net1.example.com/msp

peer lifecycle chaincode package basic_${chaincode_version}.tar.gz --path ../asset-transfer-basic/chaincode-go/ --lang golang --label basic_${chaincode_version}.0


echo -e "\n\n======== Installing Chaincode and approving on Org1 ==========="
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1-net1.example.com/peers/peer0.org1-net1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1-net1.example.com/users/Admin@org1-net1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode install basic_${chaincode_version}.tar.gz

peer lifecycle chaincode queryinstalled --output json > chaincode_package_id.json
INDEX="$((${chaincode_version} - 1))"
PACKAGE_ID=`jq -r '.installed_chaincodes['${INDEX}'].package_id' chaincode_package_id.json`
export NEW_CC_PACKAGE_ID=$PACKAGE_ID
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version ${chaincode_version}.0 --package-id $NEW_CC_PACKAGE_ID --sequence ${chaincode_version} --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem


echo -e "\n\n======== Installing Chaincode and approving on Org2 ==========="
export CORE_PEER_LOCALMSPID="Org2MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2-net1.example.com/users/Admin@org2-net1.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install basic_${chaincode_version}.tar.gz
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version ${chaincode_version}.0 --package-id $NEW_CC_PACKAGE_ID --sequence ${chaincode_version} --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem


echo -e "\n\n======== Committing Chaincode ==========="
peer lifecycle chaincode checkcommitreadiness --channelID mychannel --name basic --version ${chaincode_version}.0 --sequence ${chaincode_version} --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --output json
peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer-net1.example.com --channelID mychannel --name basic --version ${chaincode_version}.0 --sequence ${chaincode_version} --tls --cafile ${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer-net1.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --peerAddresses localhost:7051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org1-net1.example.com/peers/peer0.org1-net1.example.com/tls/ca.crt --peerAddresses localhost:9051 --tlsRootCertFiles ${PWD}/organizations/peerOrganizations/org2-net1.example.com/peers/peer0.org2-net1.example.com/tls/ca.crt
