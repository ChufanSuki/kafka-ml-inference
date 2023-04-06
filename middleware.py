import requests
import json

url = "http://10.14.42.236:32492/imageClassification"

# define the headers and data for the request
headers = {"Content-Type": "application/json"}
data = {"data": "5.0,3.4,1.5,0.2"}

# convert the data dictionary to a JSON string
data_json = json.dumps(data)

# send the post request
response = requests.post(url, headers=headers, data=data_json)


print(response.status_code) # Should print 200 if successful
print(response.json()) # Should print the response data from the server