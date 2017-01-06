import urllib
myurl = "http://localhost:3000/"
response = urllib.urlopen(myurl)
data = response.read()
