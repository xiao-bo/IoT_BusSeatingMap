import requests
import json

test = {"key1": "value1", "key2": "value2"}
test2 = {"key1": [1,2,3,4,5,6,7]}
myurl = "http://localhost:3000/"
response = requests.post(myurl, json=test2)
