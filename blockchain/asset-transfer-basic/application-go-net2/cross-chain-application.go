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
	"strconv"
	"path/filepath"
	"encoding/json"

	"github.com/hyperledger/fabric-sdk-go/pkg/core/config"
	"github.com/hyperledger/fabric-sdk-go/pkg/gateway"
)


type Dataset struct {
	Dataset_ID      int 
	Dataset_Name    string
	Train_Samples   int
	Test_Samples    int
	Val_Split       float64
  }
  
  type Hyperparams struct {
	Epoch         int
	Batch_Size    int
	Loss_Func     string
  }
  
  type Metrics struct {
	Train_Loss    float64
	Train_Acc     float64
	Test_Loss     float64
	Test_Acc      float64
  }
  
  // Asset describes basic details of what makes up a simple asset
  type Asset struct {
	ID             string `json:"ID"`
	Round_No       int    `json:"round_no"`
	Weights		   [][][]float64 `json:"weights"`
	Hyperparam     Hyperparams `json:"hyperparams"`
	Gradients	   [][]float64 `json:"gradients"`
	Dataset        Dataset  `json:dataset`
	Metric         Metrics  `json:metrics`
  }

type Weight struct {
	Iter_ID			string
	Weight			[][][]float64
}

type Client_List struct {
	Client_ID		string
	Params			[]Weight
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
	
	log.Println("============ Connection to be established ============")

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


	// Open the file and load the object back!
    f2, err := os.Open("/home/sarthak/KGP-Documents/MTP/Code/Hyperledger/fed-learn/Client/client_weights_0_json.json")
    dec := json.NewDecoder(f2)
    var client_wt Client_List
    err = dec.Decode(&client_wt)
    if err != nil {
        log.Fatalf("Failed to Read JSON: %v", err)
    }
	f2.Close()
	
	

	// log.Println("--> Submit Transaction: InitLedger, function creates the initial set of assets on the ledger")
	// result, err := contract.SubmitTransaction("InitLedger")
	// if err != nil {
	// 	log.Fatalf("Failed to Submit transaction: %v", err)
	// }
	// log.Println(string(result))


	//////////////////////////////////////////////////////////////////
	log.Println("--> Evaluate Transaction: GetAllAssets, function returns all the current assets on the ledger")
	result, err := contract.EvaluateTransaction("GetAllAssets")
	if err != nil {
		log.Fatalf("Failed to evaluate transaction: %v", err)
	}
	log.Println(string(result))
	/////////////////////////////////////////////////////////////////


	////////////////////////////////////////////////////////////////
	weight := client_wt.Params[0].Weight
	grad := [][]float64 {{12.0,32.4},{554.8,33.2}}
	dataset := Dataset {
		Dataset_ID: 0,
		Dataset_Name: "foobar",
		Train_Samples: 100,
		Test_Samples:  30,
		Val_Split:   0,
	}
	hyperparam := Hyperparams {
		Epoch: 1,
		Batch_Size: 32,
		Loss_Func: "CategoricalEntropy",
	}
	metric := Metrics {
		Train_Loss: 0.1,
		Train_Acc: 0.99,
		Test_Loss: 0.1,
		Test_Acc: 0.99,
	}
	round_no, err := strconv.Atoi(client_wt.Params[0].Iter_ID)
	asset := Asset{
		ID: "client_" + client_wt.Client_ID + "_round_" + round_no,
		Round_No: round_no,
		Weights: weight,
		Hyperparam: hyperparam,
		Gradients: grad,
		Dataset: dataset,
		Metric: metric,
	}

	bytes, err := json.Marshal(asset)
	log.Println("--> Submit Transaction: CreateAsset, creates new asset with ID, weights, hyperparams, and gradients arguments")
	result, err = contract.SubmitTransaction("CreateAsset", asset.ID, string(bytes))
	if err != nil {
		log.Fatalf("Failed to Submit transaction: %v", err)
	}
	log.Println("Asset Entered with Client ID: ", asset.ID)
	// log.Println(string(result))
	/////////////////////////////////////////////////////////////////


	/////////////////////////////////////////////////////////////////
	weight = client_wt.Params[1].Weight
	grad = [][]float64 {{12.0,32.4},{554.8,33.2}}
	round_no, err = strconv.Atoi(client_wt.Params[1].Iter_ID)
	asset = Asset{
		ID: "client_" + client_wt.Client_ID + "_round_" + round_no,
		Round_No: round_no,
		Weights: weight,
		Hyperparam: hyperparam,
		Gradients: grad,
		Dataset: dataset,
		Metric: metric,
	}

	bytes, err = json.Marshal(asset)
	log.Println("--> Submit Transaction: CreateAsset, creates new asset with ID, weights, hyperparams, and gradients arguments")
	result, err = contract.SubmitTransaction("CreateAsset", asset.ID, string(bytes))
	if err != nil {
		log.Fatalf("Failed to Submit transaction: %v", err)
	}
	log.Println("Asset Entered with Client ID: ", asset.ID)
	// log.Println(string(result))
	/////////////////////////////////////////////////////////////////


	////////////////////////////////////////////////////////////////
	log.Println("--> Evaluate Transaction: GetAllAssets, function returns all the current assets on the ledger")
	result, err = contract.EvaluateTransaction("GetAllAssets")
	if err != nil {
		log.Fatalf("Failed to evaluate transaction: %v", err)
	}
	// log.Println(string(result))
	/////////////////////////////////////////////////////////////////


	/////////////////////////////////////////////////////////////////
	// log.Println("--> Evaluate Transaction: ReadAsset, function returns an asset with a given assetID")
	// result, err = contract.EvaluateTransaction("ReadAsset", "client1")
	// if err != nil {
	// 	log.Fatalf("Failed to evaluate transaction: %v\n", err)
	// }
	// log.Println(string(result))
	/////////////////////////////////////////////////////////////////



	// log.Println("--> Evaluate Transaction: AssetExists, function returns 'true' if an asset with given assetID exist")
	// result, err = contract.EvaluateTransaction("AssetExists", "client1")
	// if err != nil {
	// 	log.Fatalf("Failed to evaluate transaction: %v\n", err)
	// }
	// log.Println(string(result))

	// log.Println("--> Evaluate Transaction: ReadAsset, function returns 'asset1' attributes")
	// result, err = contract.EvaluateTransaction("ReadAsset", "client1")
	// if err != nil {
	// 	log.Fatalf("Failed to evaluate transaction: %v", err)
	// }
	// log.Println(string(result))
	log.Println("============ application-golang ends ============")
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
