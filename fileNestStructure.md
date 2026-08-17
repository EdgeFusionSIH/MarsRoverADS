- Readme.md

- node1 {Taman's Laptop}
	- dataset
		- systemInfo.json
		- img1.jpg
		- img2.jpg ...
	- inputs 
		- p2pn1n2Input.json {Image number, Model to be used}
		- p2pn1n3Input.json {NIL}
	- vision.py //{running the yolo multi-server}
	- sysUs.py //{running find system usage finder}
	- p2pn1n3.py {websocket between node1 and node 3, sending lastFrame.jpg}
	- p2pn1n2.py {websocket between node1 and node 2, sending p2pn1n2Output.json, recieving p2pn1n2Input.json}
	- outputs
		- p2pn1n3Output.json {NIL}
		- p2pn1n3Output.json {System usage and contains obj name, confidence%}
		- currentFrame.jpg
		- lastFrame.jpg

- node2 {Aarav's Mac}
	- dataset
		- telemetry.csv {include timestamps and also img.jpg acc. to the timestamps}
		- systemInfo.json
	- inputs 
		- p2pn1n2Input.json //{Sys info and object detection info}
		- p2pn2n3Input.json //{Chaos Bench}
	- checker.py //{running the csv file interpretation server}
	- forest.py
	- sysUs.py //{Runs to find system usage}
	- p2pn2n3.py //{Websocket for the node1 and node 2, sending p2pn1n2Output.json, p2pn1n2Input.json}
	- p2pn1n2.py
	- Outputs
		- p2pn1n2Output.json //{Image number, Model to be used}
		- p2pn2n3Output.json //{Node sys info, Models Used, wheelslip, torque, wheelslipHistory, torqueHistory, Fusion Brain}

- node3 {Bhavika's Laptop}
	

