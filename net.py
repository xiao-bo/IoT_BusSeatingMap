import requests
import json

test = {"seat": [1, 0, 0, 0, 1, 0, 0, 0]}
myurl = "http://localhost:3000/"
response = requests.post(myurl, json=test)
print response.json()
