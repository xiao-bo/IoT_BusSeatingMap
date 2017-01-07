import requests
import json

test = {"seat": [1,2,3,4,5,5,6]}
myurl = "http://localhost:3000/"
response = requests.post(myurl, json=test)
print response.json()
