import requests
import json

url = "http://10.14.42.236:32492/imageClassification"
data = {"data": "5.0,3.4,1.5,0.2"}

def send_service(url, data):
    # define the headers and data for the request
    headers = {"Content-Type": "application/json"}

    # convert the data dictionary to a JSON string
    data_json = json.dumps(data)

    # send the post request
    response = requests.post(url, headers=headers, data=data_json)
    
    print(response.status_code) # Should print 200 if successful
    print(response.json()) # Should print the response data from the server

    return response

response = send_service(url, data)

