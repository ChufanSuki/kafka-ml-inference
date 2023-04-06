from flask import Flask, jsonify, request, send_file

import requests
import json

app = Flask(__name__)

# Define your routes here
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/genimg')
def gen_image():
    # get generate number
    data = request.args.get('data')

    url = "http://10.14.42.236:32492/imageClassification"

    # define the headers and data for the request   
    headers = {"Content-Type": "application/json"}

    # convert the data dictionary to a JSON string
    data_json = json.dumps(data)

    # send the post request
    response = requests.post(url, headers=headers, data=data_json)

    # Return the image file to the client
    filename = 'path/to/image/file.jpg'
    return send_file(filename, mimetype='image/jpeg')

@app.route('/getimg')
def get_image():
    plane_id = request.args.get('planeid')
    # Do something with plane_id (e.g., retrieve the corresponding image)

    # Return the image file to the client
    filename = 'path/to/image/file.jpg'
    return send_file(filename, mimetype='image/jpeg')


# Start the server
if __name__ == '__main__':
    app.run(debug=True)
