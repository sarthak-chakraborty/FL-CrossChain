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
	"time"
	"strconv"
	"path/filepath"
	"encoding/json"
	"sort"
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
Node 		   string `json:"node"`
Weights		   string `json:"weights"`
Hyperparam     Hyperparams `json:"hyperparams"`
Gradients	   [][]float64 `json:"gradients"`
Dataset        Dataset `json:"dataset"`
Metric         Metrics `json:"metrics"`
}

type Asset_Full struct {
	ID             string `json:"ID"`
	Round_No       int    `json:"round_no"`
	Node 		   string `json:"node"`
	Weights		   [][][][][]float64 `json:"weights"`
	Hyperparam     Hyperparams `json:"hyperparams"`
	Gradients	   [][]float64 `json:"gradients"`
	Dataset        Dataset  `json:dataset`
	Metric         Metrics  `json:metrics`
}

type Asset_Pointer struct {
	ID          string
	Round_No    int
}


//////////////////////////////////////////////////////////////

func split(buf []byte, lim int) [][]byte {
	var chunk []byte
	chunks := make([][]byte, 0, len(buf)/lim+1)
	for len(buf) >= lim {
		chunk, buf = buf[:lim], buf[lim:]
		chunks = append(chunks, chunk)
	}
	if len(buf) > 0 {
		chunks = append(chunks, buf[:len(buf)])
	}
	return chunks
}


func join(chunks [][]byte) []byte {
	var result []byte
	for i:= 0; i < len(chunks); i++ {
		for j := 0; j < len(chunks[i]); j++{
			result = append(result, chunks[i][j])
		}
	}
	return result
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
		"test-network-1",
		"organizations",
		"peerOrganizations",
		"org1-net1.example.com",
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


	// ENTER ASSET Handler
	http.HandleFunc( "/enterAsset", func(w http.ResponseWriter, r *http.Request) {
		log.Println(r.Body)

		decoder := json.NewDecoder(r.Body)
	    var recv_asset Asset_Full
	    err := decoder.Decode(&recv_asset)
	    if err != nil {
	        panic(err)
	    }

	    log.Println("--> Submit Transaction: CreateAsset, creates new asset with ID, weights, hyperparams, and gradients arguments")
	    start1 := time.Now()

	    byte_weight, _ :=  json.Marshal(recv_asset.Weights)
		chunks := split(byte_weight, 800*1024)

		for j := 0; j < len(chunks); j++ {
			start2 := time.Now()
			frag_no := j

			asset := Asset{
				ID: recv_asset.ID + "_" + strconv.Itoa(frag_no),
				Round_No: recv_asset.Round_No,
				Fragment_No: frag_no,
				Node: recv_asset.Node,
				Weights: string(chunks[j]),
				Hyperparam: recv_asset.Hyperparam,
				Gradients: recv_asset.Gradients,
				Dataset: recv_asset.Dataset,
				Metric: recv_asset.Metric,
			}

			bytes, _ := json.Marshal(asset)
			fmt.Println("Sending asset")
			_, err := contract.SubmitTransaction("CreateAsset", asset.ID, string(bytes))
			if err != nil {
				log.Fatalf("Failed to Submit transaction: %v", err)
			}
			log.Println("Asset Entered with ID: ", asset.ID)
			duration2 := time.Since(start2)
			// frag_time = append(frag_time, duration2.Milliseconds())
			fmt.Println("Time: ", duration2.Milliseconds())
		}
		duration1 := time.Since(start1)
		// asset_time = append(asset_time, duration1.Milliseconds())
		fmt.Println("Asset Time: ", duration1.Milliseconds())
	},)



	// MAKE REQUEST handler
	http.HandleFunc( "/makeRequest", func(w http.ResponseWriter, r *http.Request) {
		resp, err := http.PostForm("http://127.0.0.1:8050/fetchData", url.Values{"key": {"Value"}, "id": {"123"}})
		if err != nil {
			panic(err)
		}
		defer resp.Body.Close()
		fmt.Println("Response status:", resp.Status)
	
		bodyBytes, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			panic(err)
		}
		var asset Asset_Full
		err = json.Unmarshal(bodyBytes, &asset)
		if err != nil {
			panic(err)
		}
		
		file,_ := json.Marshal(asset)
		_ = ioutil.WriteFile("/home/sarthak/KGP-Documents/MTP/Code/FL/received_asset-cifar.json", file, 0644)
		
		fmt.Println("Asset with ID = ", asset.ID, " received")
		
	},)



	// FETCH DATA handler
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

		sort.Slice(asset_result, func(i, j int) bool {
			return asset_result[i].Round_No > asset_result[j].Round_No
		})

		// Find the asset ID having the largest round_no (entered most recently)
		last_entered := asset_result[0]
		fmt.Println(last_entered.ID)

		count := 0
		for _, elem := range asset_result {
			if elem.Round_No == last_entered.Round_No {
				count = count + 1
			}
		}

		// Get Each fragment and append to get the full weight
		start := time.Now()
		var chunks [][]byte
		var asset_full Asset_Full
		log.Println("--> Evaluate Transaction: ReadAsset, function returns the asset based with the passed ID on the ledger")
		for i := 0; i < count; i++ {
			fmt.Println("server_round_"+strconv.Itoa(last_entered.Round_No)+"_"+strconv.Itoa(i))
			result, err = contract.EvaluateTransaction("ReadAsset", "server_round_"+strconv.Itoa(last_entered.Round_No)+"_"+strconv.Itoa(i))
			fmt.Println(err)
			if err != nil {
				log.Fatalf("Failed to evaluate transaction: %v", err)
			}
			var asset_result Asset
			_ = json.Unmarshal([]byte(string(result)), &asset_result)
			
			if i == 0 {
				asset_full.ID = "server_round_" + strconv.Itoa(last_entered.Round_No)
				asset_full.Round_No = asset_result.Round_No
				asset_full.Node = asset_result.Node
				asset_result.Gradients = asset_result.Gradients
				asset_full.Hyperparam = asset_result.Hyperparam
				asset_full.Dataset = asset_result.Dataset
				asset_full.Metric = asset_result.Metric
			}

			chunks = append(chunks, []byte(asset_result.Weights))
		}
		joined_weights := join(chunks)
		_ = json.Unmarshal(joined_weights, &asset_full.Weights)
		duration := time.Since(start)

		fmt.Println("Asset Retrieval Time: ", duration.Milliseconds())

		bytes, _ := json.Marshal(asset_full)
		w.Write(bytes)
	},)



	fmt.Println("============ Listening at 127.0.0.1:8050 ============")

	http.ListenAndServe("127.0.0.1:8050", nil)
}


func populateWallet(wallet *gateway.Wallet) error {
	log.Println("============ Populating wallet ============")
	credPath := filepath.Join(
		"..",
		"..",
		"test-network-1",
		"organizations",
		"peerOrganizations",
		"org1-net1.example.com",
		"users",
		"User1@org1-net1.example.com",
		"msp",
	)

	certPath := filepath.Join(credPath, "signcerts", "User1@org1-net1.example.com-cert.pem")
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
