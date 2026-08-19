# JSON FORMATS
## *Important*:
*'//' next to the json attribute is a comment here*

## NODE 1

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
    //NIL
}

### node1/outputs/p2pn1n2Output.json
{   "from": "node1", //sender
    "to": "node2", //reciever
    "sysus": //data from the systemInfo.json (written by the vision.py)
    {
        "nodeid": 1, //Which node are we working with
        "cpu": 5.0, //util% for all parameters
        "gpu": 0,
        "ram": 73.7,
        "disk": 66.2
    },
    "objects": //top 3 highest confidence objects to be listed
    {
        "obj1": "rock", //first object name
        "conf1": 0.95, 
        "obj2": "rock", //second object name
        "conf2": 0.92, //confidence of the second object
        "obj3": "something", //third object name
        "conf3": 0.72, //confidence of the third objec
    }  
}

### node1/outputs/p2pn1n3Output.json
{
    //NIL
}

## NODE 2

### node2/dataset/systemInfo.json
{
    "nodeid": 2, //Which node are we working with
    "cpu": 5.0, //util% for all parameters
    "gpu": 0,
    "ram": 73.7,
    "disk": 66.2
}

### node2/inputs/p2pn1n2Input.json
{
    "from": "node1", //sender
    "to": "node2", //reciever
    "sysus": //data from the systemInfo.json (written by the vision.py)
    {
        "nodeid": 1, //Which node are we working with
        "cpu": 5.0, //util% for all parameters
        "gpu": 0,
        "ram": 73.7,
        "disk": 66.2
    },
    "objects": //top 3 highest confidence objects to be listed
    {
        "obj1": "rock", //first object name
        "conf1": 0.95, 
        "obj2": "rock", //second object name
        "conf2": 0.92, //confidence of the second object
        "obj3": "something", //third object name
        "conf3": 0.72, //confidence of the third objec
    }  
}

### node2/inputs/p2pn2n3Input.json
{
    "from": "node3", //sender
    "to": "node2", //reciever
    "duststorm": 0, //values can be 0 (or) 1
    "sandtrap": 0, //values can be 0 (or) 1
    "earthuplink": 0 //values can be 0 (or) 1
}

### node2/outputs/p2pn1n2Output.json
{
    "from": "node2", //sender
    "to": "node1", //reciever
    "model": "light", //model can be "light" (or) "medium"
    "img": "1" //which image to process from node1/dataset/img__.jpg
}

### node2/outputs/p2pn2n3Output.json
{
    "from": "node2", //sender
    "to": "node3", //reciever
    "sysus": //data from the systemInfo.json (written by the main.py)
    {
        "node1": { ... }, //Node 1 hardware info
        "node2": { ... }  //Node 2 hardware info
    },
    "model": "light", //written by main.py complexity engine
    "kt": //kinematic telemetry written by main.py from CSV
    {
        "wheelslip0": 10, //current wheel slip percentage
        "torque0": 50, //current torque percentage
        "wheelslip1": 20, //-1 frame wheel slip percentage
        "torque1": 50, //-1 frame wheel torque percentage
        ... //up to wheelslip9/torque9
    },
    "sensor": //raw CSV row from mars_rover_sensor_data.csv
    {
        "timestamp": 5.3, //CSV timestamp in seconds
        "image_num": 53, //corresponding image number
        "wheel_slip": 5.87, //wheel slip %
        "torque": 10.38, //motor torque %
        "solar": 93.21, //solar battery %
        "segment": "NORMAL" //"NORMAL", "DUST_STORM", or "SAND_TRAP"
    },
    "classifying": //fusion brain output from main.py classifying engine
    {
        "vision_classification": "Nominal", //"Nominal", "Moderate Terrain", "Loose Surface", "Loose Sand", "Reduced Visibility"
        "telemetry_classification": "Normal Torque", //"Normal Torque", "Elevated Torque", "High Torque", "Erratic Torque", "Solar Degraded"
        "fusion_output": "NOMINAL — No Fusion Conflict", //fusion decision string
        "fusion_confidence": 0.85, //0.0 to 1.0
        "rover_command": "NOMINAL" //"NOMINAL", "SLOW", "HALT", "SAFE_MODE"
    }
}

## NODE 3

### node3/inputs/p2pn1n3Input.json
{
    //NIL
}

### node3/inputs/p2pn2n3Input.json
{
    "from": "node2", //sender
    "to": "node3", //reciever
    "sysus": //data from the systemInfo.json (written by the main.py)
    {
        "nodeid": 2, //Which node are we working with
        "cpu": 5.0, //util% for all parameters
        "gpu": 0,
        "ram": 73.7,
        "disk": 66.2
    },
    "model": "light", //model can be "light" (or) "medium"
    "kt": //kinematic telemetry written by main.py
    {
        "wheelslip0": 10, //current wheel slip percentage
        "torque0": 50, //current torque percentage
        "wheelslip1": 20, //-1 frame wheel slip percentage
        "torque1": 50, //-1 frame wheel torque percentage
        "wheelslip2": 20, //-2 frame wheel slip percentage
        "torque2": 50, //-2 frame wheel torque percentage
        "wheelslip3": 20, //-3 frame wheel slip percentage
        "torque3": 50, //-3 frame wheel torque percentage
        "wheelslip4": 20, //-4 frame wheel slip percentage
        "torque4": 50, //-4 frame wheel torque percentage
        "wheelslip5": 20, //-5 frame wheel slip percentage
        "torque5": 50, //-5 frame wheel torque percentage
        "wheelslip6": 20, //-6 frame wheel slip percentage
        "torque6": 50, //-6 frame wheel torque percentage
        "wheelslip7": 20, //-7 frame wheel slip percentage
        "torque7": 50, //-7 frame wheel torque percentage
        "wheelslip8": 20, //-8 frame wheel slip percentage
        "torque8": 50, //-8 frame wheel torque percentage
        "wheelslip9": 20, //-9 frame wheel slip percentage
        "torque9": 50, //-9 frame wheel torque percentage
    },
}

### node3/outputs/p2pn2n3Output.json
{
    "from": "node3", //sender
    "to": "node2", //reciever
    "duststorm": 0, //values can be 0 (or) 1
    "sandtrap": 0, //values can be 0 (or) 1
    "earthuplink": 0 //values can be 0 (or) 1
}

### node3/outputs/p2pn1n3Output.json
{
    //NIL
}