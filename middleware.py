import requests
import json
import numpy as np 
import base64
import io
from PIL import Image
from io import BytesIO

url = "https://62a03266-fc4f-4a06-aab9-89e4e0ad3145.mock.pstmn.io/imageClassification"
data = {"data": "5.0,3.4,1.5,0.2"}

def send_service(url, data):
    # define the headers and data for the request
    headers = {"Content-Type": "application/json"}

    # convert the data dictionary to a JSON string
    data_json = json.dumps(data)

    # send the post request
    response = requests.post(url, headers=headers, data=data_json)
    
    print(response.status_code) # Should print 200 if successful
    try:
        json_data = json.loads(response.text)
        print(json_data)
    except json.decoder.JSONDecodeError:
        # handle the case where the response body could not be decoded as JSON
        print("Failed to decode response body as JSON")

    

    return response

def numpy_to_base64_image(arr):
    # Reshape the 1D array to a 3D array of shape (32, 32, 3)
    arr = np.uint8(arr * 255)
    img_arr = arr.reshape((3, 32, 32)).transpose([1, 2, 0]) 
    # Convert the NumPy array to a PIL Image object
    img = Image.fromarray(img_arr)
    # Create a BytesIO object to hold the image data
    img_bytes = io.BytesIO()
    # Save the image to the BytesIO object in PNG format
    img.save(img_bytes, format='PNG')
    # Encode the image data in base64
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    # Return the base64-encoded image string
    return img_base64

# send_service("http://10.14.42.236:32032/imageClassification", )