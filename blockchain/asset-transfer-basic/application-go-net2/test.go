package main

import (
	"fmt"
	"encoding/json"
	"io/ioutil"
)


type Weight struct {
	Iter_ID			string
	Weight			[]float64
}



func main() {
	fmt.Println("Hello World")

	arr := []float64{1.0, 2.1, 5.4}

	weight := Weight{
		Iter_ID: "123",
		Weight: arr,
	}

	file,_ := json.Marshal(weight)
 
	_ = ioutil.WriteFile("test.json", file, 0644)
}