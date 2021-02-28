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

////////////////////////////////////////////////
// Structures for Reading Data from file
type Weight struct {
	Iter_ID			string
	Weight			[][][][][]float64
}

// type Client_List struct {
// 	Client_ID		string
// 	Params			[]Weight
// }
/////////////////////////////////////////////////


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



	path := "/home/sarthak/KGP-Documents/MTP/Code/Hyperledger/fed-learn/Server/VGG-Compressed-Cifar10/"
	
	files, err := ioutil.ReadDir(path)
    if err != nil {
        log.Fatalf("%v", err)
    }

    // READ SERVER DATA
    var server_wt []Weight

    for _, file := range files {
    	if file.Name() == "metrics" {
    		continue
    	}
        fmt.Println(file.Name())
        f2, err := os.Open(path + file.Name())
		if err != nil {
	        log.Fatalf("File Not Opened: %v", err)
		}
		dec := json.NewDecoder(f2)
	    var wt Weight
	    err = dec.Decode(&wt)
	    if err != nil {
	        log.Fatalf("Failed to Read JSON: %v", err)
	    }
		f2.Close()
		server_wt = append(server_wt, wt)
    }


    // READ METRICS
    path = path + "metrics/"
    files, err = ioutil.ReadDir(path)
    if err != nil {
        log.Fatalf("%v", err)
    }

    var dataset Dataset
    var hyperparam []Hyperparams
    var metric []Metrics
    for _, file := range files {
    	fmt.Println(file.Name())
        f2, err := os.Open(path + file.Name())
		if err != nil {
	        log.Fatalf("File Not Opened: %v", err)
		}
		dec := json.NewDecoder(f2)

		if file.Name() == "dataset.json" {
			err = dec.Decode(&dataset)
		    if err != nil {
		        log.Fatalf("Failed to Read JSON: %v", err)
		    }
			f2.Close()
		} else if file.Name() == "hyperparams.json" {
			err = dec.Decode(&hyperparam)
		    if err != nil {
		        log.Fatalf("Failed to Read JSON: %v", err)
		    }
			f2.Close()
		} else if file.Name() == "metrics.json" {
			err = dec.Decode(&metric)
		    if err != nil {
		        log.Fatalf("Failed to Read JSON: %v", err)
		    }
			f2.Close()
		}
	    
    }


	// // READ ALL CLIENT DATA
	// for i := 0; i < TOT_CLIENTS; i++ {
	// 	fmt.Println(i)
	// 	f2, err = os.Open(path + "Client/client_weights_" + strconv.Itoa(i) + "_json.json")
	// 	if err != nil {
	// 		log.Fatalf("File Not Opened: %v", err)
	// 	}
	// 	dec = json.NewDecoder(f2)
	// 	var client_wt Client_List
	// 	err = dec.Decode(&client_wt)
	// 	if err != nil {
	// 		log.Fatalf("Failed to Read JSON: %v", err)
	// 	}
	// 	f2.Close()
	// 	all_client_wt = append(all_client_wt, client_wt)
	// }


	//////////////////////////////////////////////////////////////////
	// log.Println("--> Evaluate Transaction: GetAllAssets, function returns all the current assets on the ledger")
	// result, err := contract.EvaluateTransaction("GetAllAssets")
	// if err != nil {
	// 	log.Fatalf("Failed to evaluate transaction: %v", err)
	// }
	// log.Println(string(result))
	/////////////////////////////////////////////////////////////////
	
	

	grad := [][]float64 {{12.0,32.4},{554.8,33.2}}

	var asset_time []int64
	var frag_time []int64

	log.Println("--> Submit Transaction: CreateAsset, creates new asset with ID, weights, hyperparams, and gradients arguments")
	for i := 0; i < len(server_wt); i++ {
		fmt.Println(i)
		start1 := time.Now()
		// for j := 0; j < TOT_CLIENTS; j++{

		// 	weight := all_client_wt[j].Params[i].Weight
		// 	round_no, err := strconv.Atoi(all_client_wt[j].Params[i].Iter_ID)
		// 	asset := Asset{
		// 		ID: "client_" + all_client_wt[j].Client_ID + "_round_" + strconv.Itoa(round_no),
		// 		Round_No: round_no,
		// 		Node: "client",
		// 		Weights: weight,
		// 		Hyperparam: hyperparam,
		// 		Gradients: grad,
		// 		Dataset: dataset,
		// 		Metric: metric,
		// 	}
		// 	bytes, err := json.Marshal(asset)

		// 	result, err = contract.SubmitTransaction("CreateAsset", asset.ID, string(bytes))
		// 	if err != nil {
		// 		log.Fatalf("Failed to Submit transaction: %v", err)
		// 	}
		// 	log.Println("Asset Entered with ID: ", asset.ID)
		// }

		weight := server_wt[i].Weight
		round_no, _ := strconv.Atoi(server_wt[i].Iter_ID)

		byte_weight, _ :=  json.Marshal(weight)
		chunks := split(byte_weight, 800*1024)

		if round_no < 400 {
			continue;
		}

		for j := 0; j < len(chunks); j++ {
			start2 := time.Now()
			frag_no := j

			asset := Asset{
				ID: "server_round_" + strconv.Itoa(round_no) + "_" + strconv.Itoa(frag_no),
				Round_No: round_no,
				Fragment_No: frag_no,
				Node: "server",
				Weights: string(chunks[j]),
				Hyperparam: hyperparam[i],
				Gradients: grad,
				Dataset: dataset,
				Metric: metric[i],
			}

			if (asset.ID == "server_round_500_0"){
				fmt.Printf("%T\n", asset.Weights)
			}
			bytes, _ := json.Marshal(asset)
			fmt.Println("Sending asset")
			_, err := contract.SubmitTransaction("CreateAsset", asset.ID, string(bytes))
			if err != nil {
				log.Fatalf("Failed to Submit transaction: %v", err)
			}
			log.Println("Asset Entered with ID: ", asset.ID)
			duration2 := time.Since(start2)
			frag_time = append(frag_time, duration2.Milliseconds())
			fmt.Println("Time: ", duration2.Milliseconds())
		}
		duration1 := time.Since(start1)
		asset_time = append(asset_time, duration1.Milliseconds())
		fmt.Println("Asset Time: ", duration1.Milliseconds())
	}

	// PRINT TIME STATISTICS
	var sum int64
	sum = 0
	for i := 0; i < len(asset_time); i++ { 
        sum += (asset_time[i]) 
    } 
    avg := (float64(sum)) / (float64(len(asset_time))) 
    fmt.Println("Average Asset Entering Time: ", avg)

    sum = 0
	for i := 0; i < len(frag_time); i++ { 
        sum += (frag_time[i]) 
    } 
    avg = (float64(sum)) / (float64(len(frag_time))) 
    fmt.Println("Average Asset Entering Time: ", avg)


	log.Println("============ application-golang ends ============")
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
