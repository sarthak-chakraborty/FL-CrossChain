package chaincode

import (
	"encoding/json"
	"fmt"
  "strconv"
  "strings"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing an Asset
type SmartContract struct {
  contractapi.Contract
}

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
  Weights		     string `json:"weights" metadata:",optional"`
  Hyperparam     Hyperparams `json:"hyperparams"`
  Gradients		   [][]float64 `json:"gradients"`
  Dataset        Dataset  `json:dataset`
  Metric         Metrics  `json:metrics`
}

type Asset_Pointer struct {
  ID          string
  Round_No    int
}

const index = "node~name"
// const index2 = "round_no~fragment_no"

// InitLedger adds a base set of assets to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
  assets := []Asset{
  }

  for _, asset := range assets {
    assetJSON, err := json.Marshal(asset)
    if err != nil {
        return err
    }

    err = ctx.GetStub().PutState(asset.ID, assetJSON)
    if err != nil {
        return fmt.Errorf("failed to put to world state. %v", err)
    }
  }

  return nil
}


// CreateAsset issues a new asset to the world state with given details.
func (s *SmartContract) CreateAsset(ctx contractapi.TransactionContextInterface, id string, assetString string) error {
  var asset Asset
  fmt.Println("Converting to asset")
  err := json.Unmarshal([]byte(assetString), &asset)
  if err != nil {
    return err
  }
  fmt.Println("Converted...")

  exists, err := s.AssetExists(ctx, id)
  if err != nil {
    return err
  }
  if exists {
    return fmt.Errorf("the asset %s already exists", id)
  }

  fmt.Println("Marshalling JSON")
  assetJSON, err := json.Marshal(asset)
  if err != nil {
    return err
  }
  fmt.Println("Adding it to the ledger")
  err = ctx.GetStub().PutState(id, assetJSON)
  if err != nil {
	return err
  }
  fmt.Println("Added..")

  node_index_key, err := ctx.GetStub().CreateCompositeKey(index, []string{asset.Node, id})
  if err != nil {
	return err
  }
  //  Save index entry to world state. Only the key name is needed, no need to store a duplicate copy of the asset.
  //  Note - passing a 'nil' value will effectively delete the key from state, therefore we pass null character as value
  value := []byte{0x00}
  fmt.Println("Creating Composite Key \n")
  return ctx.GetStub().PutState(node_index_key, value)

  // node_index_key, err = ctx.GetStub().CreateCompositeKey(index2, []string{strconv.Itoa(round_no), strconv.Itoa(asset.Fragment_No)})
  // if err != nil {
  // return err
  // }
  // //  Save index entry to world state. Only the key name is needed, no need to store a duplicate copy of the asset.
  // //  Note - passing a 'nil' value will effectively delete the key from state, therefore we pass null character as value
  // fmt.Println("Creating Composite Key 2")
  // return ctx.GetStub().PutState(node_index_key, value)
}



// ReadAsset returns the asset stored in the world state with given id.
func (s *SmartContract) ReadAsset(ctx contractapi.TransactionContextInterface, id string) (*Asset, error) {
  fmt.Println("\nRead Asset")
  fmt.Println(id)
  assetJSON, err := ctx.GetStub().GetState(id)
  fmt.Println("GetState(), err: %v", err)
  if err != nil {
    return nil, fmt.Errorf("failed to read from world state: %v", err)
  }
  if assetJSON == nil {
    return nil, fmt.Errorf("the asset %s does not exist", id)
  }

  var asset Asset
  err = json.Unmarshal(assetJSON, &asset)
  fmt.Printf("%T\n",asset.Weights)
  if err != nil {
    return nil, err
  }

  return &asset, nil
}

// UpdateAsset updates an existing asset in the world state with provided parameters.
func (s *SmartContract) UpdateAsset(ctx contractapi.TransactionContextInterface, id string, assetString string) error {
  exists, err := s.AssetExists(ctx, id)
  if err != nil {
    return err
  }
  if !exists {
    return fmt.Errorf("the asset %s does not exist", id)
  }

  var asset Asset
  err = json.Unmarshal([]byte(assetString), &asset)
  if err != nil {
    return err
  }

  assetJSON, err := json.Marshal(asset)
  if err != nil {
    return err
  }

  return ctx.GetStub().PutState(id, assetJSON)
}


// DeleteAsset deletes an given asset from the world state.
func (s *SmartContract) DeleteAsset(ctx contractapi.TransactionContextInterface, id string) error {
  exists, err := s.AssetExists(ctx, id)
  if err != nil {
    return err
  }
  if !exists {
    return fmt.Errorf("the asset %s does not exist", id)
  }

  return ctx.GetStub().DelState(id)
}


// AssetExists returns true when asset with given ID exists in world state
func (s *SmartContract) AssetExists(ctx contractapi.TransactionContextInterface, id string) (bool, error) {
  assetJSON, err := ctx.GetStub().GetState(id)
  if err != nil {
    return false, fmt.Errorf("failed to read from world state: %v", err)
  }

  return assetJSON != nil, nil
}



// GetAllAssets returns all assets found in world state
func (s *SmartContract) GetAllAssets(ctx contractapi.TransactionContextInterface) ([]*Asset, error) {
  // range query with empty string for startKey and endKey does an
  // open-ended query of all assets in the chaincode namespace.
  resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
  if err != nil {
    return nil, err
  }
  defer resultsIterator.Close()

  var assets []*Asset
  for resultsIterator.HasNext() {
    queryResponse, err := resultsIterator.Next()
    if err != nil {
      return nil, err
    }

    var asset Asset
    err = json.Unmarshal(queryResponse.Value, &asset)
    if err != nil {
      return nil, err
    }
    assets = append(assets, &asset)
  }

  return assets, nil
}


// GetTransferableAssets returns all assets found in world state having Node="server"
func (s *SmartContract) GetTransferableAssets(ctx contractapi.TransactionContextInterface) ([]*Asset, error) {

	resultsIterator, err := ctx.GetStub().GetStateByPartialCompositeKey(index, []string{"server"})
  fmt.Println("resultIterator ran with error: %v", err)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var assets []*Asset
	for resultsIterator.HasNext() {
	    responseRange, err := resultsIterator.Next()
      fmt.Println("resultIterator.Next(), err: %v", err)
	    if err != nil {
	      return nil, err
	    }

	    _, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(responseRange.Key)
      fmt.Println(compositeKeyParts)
		if err != nil {
			return nil, err
		}

		if len(compositeKeyParts) > 1 {
			returnedAssetID := compositeKeyParts[1]
      fmt.Println(returnedAssetID)
			asset, err := s.ReadAsset(ctx, returnedAssetID)
			if err != nil {
				return nil, err
			}
		    assets = append(assets, asset)
		}
	}

  fmt.Println(len(assets))
	return assets, nil
}


// CountTransferableAssets returns IDs of all assets found in world state having Node="server"
func (s *SmartContract) CountTransferableAssets(ctx contractapi.TransactionContextInterface) ([]*Asset_Pointer, error) {

  resultsIterator, err := ctx.GetStub().GetStateByPartialCompositeKey(index, []string{"server"})
  fmt.Println("resultIterator ran with error: %v", err)
  if err != nil {
    return nil, err
  }
  defer resultsIterator.Close()

  var assets []*Asset_Pointer
  for resultsIterator.HasNext() {
      responseRange, err := resultsIterator.Next()
      fmt.Println("resultIterator.Next(), err: %v", err)
      if err != nil {
        return nil, err
      }

      _, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(responseRange.Key)
      fmt.Println(compositeKeyParts)
    if err != nil {
      return nil, err
    }

    if len(compositeKeyParts) > 1 {
      returnedAssetID := compositeKeyParts[1]
      res := strings.Split(returnedAssetID, "_")
      round_no, _ := strconv.Atoi(res[2])
      fmt.Println(returnedAssetID)

      asset_p := Asset_Pointer {
        ID: returnedAssetID,
        Round_No: round_no,
      }
      assets = append(assets, &asset_p)
    }
  }

  fmt.Println(len(assets))
  return assets, nil
}


// // CountFragments returns IDs of all assets found in world state having Node="server" and round_no="R"
// func (s *SmartContract) CountFragments(ctx contractapi.TransactionContextInterface, round_no int) ([]*Asset_Pointer, error) {

//   resultsIterator, err := ctx.GetStub().GetStateByPartialCompositeKey(index, []string{strconv.Itoa(round_no)})
//   fmt.Println("resultIterator ran with error: %v", err)
//   if err != nil {
//     return nil, err
//   }
//   defer resultsIterator.Close()

//   var assets []*Asset_Pointer
//   for resultsIterator.HasNext() {
//       responseRange, err := resultsIterator.Next()
//       fmt.Println("resultIterator.Next(), err: %v", err)
//       if err != nil {
//         return nil, err
//       }

//       _, compositeKeyParts, err := ctx.GetStub().SplitCompositeKey(responseRange.Key)
//       fmt.Println(compositeKeyParts)
//     if err != nil {
//       return nil, err
//     }

//     if len(compositeKeyParts) > 1 {
//       returnedAssetID := compositeKeyParts[2]
//       fmt.Println(returnedAssetID)

//       asset_p := Asset_Pointer {
//         ID: returnedAssetID,
//         Round_No: strconv.Atoi(round_no),
//       }
//       assets = append(assets, &asset_p)
//     }
//   }

//   fmt.Println(len(assets))
//   return assets, nil
// }