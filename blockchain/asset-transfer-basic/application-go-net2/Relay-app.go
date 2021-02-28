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
	Fragment_No    int    `json:"fragment_no"`
	Node           string  `json:"node"`
	Weights		   [][][][]float64 `json:"weights"`
	Hyperparam     Hyperparams `json:"hyperparams"`
	Gradients	   [][]float64 `json:"gradients"`
	Dataset        Dataset  `json:dataset`
	Metric         Metrics  `json:metrics`
}

type Asset_Pointer struct {
	ID          string
	Round_No    int
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
		file,_ := json.Marshal(asset)
		_ = ioutil.WriteFile("/home/sarthak/KGP-Documents/MTP/Code/Hyperledger/fed-learn/Server/received_asset.json", file, 0644)

		fmt.Println("Asset with ID = ", asset.ID, " received")
	},)


	http.HandleFunc( "/fetchData", func(w http.ResponseWriter, r *http.Request) {
		r.ParseForm()
		x := r.PostForm.Get("id")
		fmt.Println(x)

		log.Println("--> Evaluate Transaction: CountTransferableAssets, function returns the transferable current asset pointers on the ledger")
		result, err := contract.EvaluateTransaction("CountTransferableAssets")
		if err != nil {
			log.Fatalf("Failed to evaluate transaction: %v", err)
		}
		
		var asset_result []Asset_Pointer
		err = json.Unmarshal([]byte(string(result)), &asset_result)

		fmt.Println(len(asset_result))
		sort.Slice(asset_result, func(i, j int) bool {
			return asset_result[i].Round_No > asset_result[j].Round_No
		})

		// Find the asset ID having the largest round_no (enterer most recently)
		last_entered := asset_result[0]
		fmt.Println(last_entered.ID)

		log.Println("--> Evaluate Transaction: ReadAsset, function returns the asset based with the passed ID on the ledger")
		result, err = contract.EvaluateTransaction("ReadAsset", last_entered.ID)
		if err != nil {
			log.Fatalf("Failed to evaluate transaction: %v", err)
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
