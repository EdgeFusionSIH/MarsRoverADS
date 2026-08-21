## for mac and windows:
import json

FILE = "node1/inputs/p2pn1n2Input.json"

with open(FILE, "r") as file:
    data = json.load(file)

print(data)

