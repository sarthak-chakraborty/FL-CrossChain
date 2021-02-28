/*
Copyright 2020 IBM All Rights Reserved.

SPDX-License-Identifier: Apache-2.0
*/

package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"encoding/json"
	"net/http"
	"net/url"

	"github.com/hyperledger/fabric-sdk-go/pkg/core/config"
	"github.com/hyperledger/fabric-sdk-go/pkg/gateway"
	// "github.com/go-martini/martini"
)

type Asset struct {
	ID             string `json:"ID"`
	Color          string `json:"color"`
	Size           int    `json:"size"`
	Owner          string `json:"owner"`
	AppraisedValue int    `json:"appraisedValue"`
}

func main() {
	log.Println("============ application-golang starts ============")

	err := os.Setenv("DISCOVERY_AS_LOCALHOST", "true")
	if err != nil {
		log.Fatalf("Error setting DISCOVERY_AS_LOCALHOST environemnt variable: %v", err)
	}

	wallet, err := gateway.NewFileSystemWallet("wallet")
	if err != nil {
		log.Fatalf("Failed to create wallet: %v", err)
	}

	if !wallet.Exists("appUser") {
		err = populateWallet(wallet)
		if err != nil {
			log.Fatalf("Failed to populate wallet contents: %v", err)
		}
	}

	ccpPath := filepath.Join(
		"..",
		"..",
		"test-network-2",
		"organizations",
		"peerOrganizations",
		"org1-net2.example.com",
		"connection-org1.yaml",
	)
	

	gw, err := gateway.Connect(
		gateway.WithConfig(config.FromFile(filepath.Clean(ccpPath))),
		gateway.WithIdentity(wallet, "appUser"),
	)
	if err != nil {
		log.Fatalf("Failed to connect to gateway: %v", err)
	}
	defer gw.Close()
	

	network, err := gw.GetNetwork("mychannel")
	if err != nil {
		log.Fatalf("Failed to get network: %v", err)
	}
	contract := network.GetContract("basic")


	http.HandleFunc( "/makeRequest", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("Make Request called")

		resp, err := http.PostForm("http://127.0.0.1:8000/fetchData", url.Values{"key": {"Value"}, "id": {"123"}})
		if err != nil {
			panic(err)
		}
		defer resp.Body.Close()
		fmt.Println("Response status:", resp.Status)
	
		bodyBytes, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			panic(err)
		}
		var asset Asset
		err = json.Unmarshal(bodyBytes, &asset)
		if err != nil {
			panic(err)
		}
		fmt.Println(asset)
	},)


	http.HandleFunc( "/fetchData", func(w http.ResponseWriter, r *http.Request) {
		r.ParseForm()
		x := r.PostForm.Get("id")
		fmt.Println(x)

		log.Println("--> Evaluate Transaction: GetAllAssets, function returns all the current assets on the ledger")
		result, err := contract.EvaluateTransaction("GetAllAssets")
		if err != nil {
			log.Fatalf("Failed to evaluate transaction: %v", err)
		}
		
		var asset_result []Asset
		err = json.Unmarshal([]byte(string(result)), &asset_result)

		last_entered := asset_result[len(asset_result) - 1]
		bytes, err := json.Marshal(last_entered)
		if err != nil {
			panic(err)
		}
		w.Write(bytes)
	},)

	fmt.Println("============ Listening at 127.0.0.1:9000 ============")

	http.ListenAndServe(":9000", nil)

}

func populateWallet(wallet *gateway.Wallet) error {
	log.Println("============ Populating wallet ============")
	credPath := filepath.Join(
		"..",
		"..",
		"test-network-2",
		"organizations",
		"peerOrganizations",
		"org1-net2.example.com",
		"users",
		"User1@org1-net2.example.com",
		"msp",
	)

	certPath := filepath.Join(credPath, "signcerts", "User1@org1-net2.example.com-cert.pem")
	// read the certificate pem
	cert, err := ioutil.ReadFile(filepath.Clean(certPath))
	if err != nil {
		return err
	}

	keyDir := filepath.Join(credPath, "keystore")
	// there's a single file in this dir containing the private key
	files, err := ioutil.ReadDir(keyDir)
	if err != nil {
		return err
	}
	if len(files) != 1 {
		return fmt.Errorf("keystore folder should have contain one file")
	}
	keyPath := filepath.Join(keyDir, files[0].Name())
	key, err := ioutil.ReadFile(filepath.Clean(keyPath))
	if err != nil {
		return err
	}

	identity := gateway.NewX509Identity("Org1MSP", string(cert), string(key))

	return wallet.Put("appUser", identity)
}
