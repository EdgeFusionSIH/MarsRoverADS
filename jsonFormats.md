# JSON FORMATS
## *Important*:
*'//' next to the json attribute is a comment here*

## Node 2

### node1/dataset/systemInfo.json
{
    "nodeid": 1, //Which node are we working with
    "cpu": 5.0, //util% for all parameters
    "gpu": 0,
    "ram": 73.7,
    "disk": 66.2
}

### node1/inputs/p2pn1n2Input.json

{
    "from": "node2", //sender
    "to": "node1", //reciever
    "model": "light", //model can be "light" (or) "medium"
    "img": "1" //which image to process from node1/dataset/img__.jpg
}

### node1/inputs/p2pn1n3Input.json
{

}

### node1/outputs/p2pn1n2Output.json
{

}

### node1/outputs/p2pn1n3Output.json
{

}

## Node 2

### node1/dataset/systemInfo.json
{
    "nodeid": 2, //Which node are we working with
    "cpu": 5.0, //util% for all parameters
    "gpu": 0,
    "ram": 73.7,
    "disk": 66.2
}

### node1/inputs/p2pn1n2Input.json

{

}

### node1/inputs/p2pn1n3Input.json
{

}

### node1/outputs/p2pn1n2Output.json
{
    "from": "node2", //sender
    "to": "node1", //reciever
    "model": "light", //model can be "light" (or) "medium"
    "img": "1" //which image to process from node1/dataset/img__.jpg
}

### node1/outputs/p2pn1n3Output.json
{

}
