from flask import Flask, jsonify, request, send_file

import requests
import json
import pickle
from result import ImageClassificationResult, ObjectDetectionResult, Position

app = Flask(__name__)

filename = 'results'
with open(filename, 'rb') as file:
    result_list = pickle.load(file)
    
count = 0

class ResultEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImageClassificationResult):
            return {"success": True, "base64_str": obj.base64_str, "class_name": obj.class_name, "score": obj.score, "message": "Image Classification Result"}
        elif isinstance(obj, ObjectDetectionResult):
            return {
                "success": True,
                "base64_str": obj.base64_str,
                "class_name": obj.class_name,
                "score": obj.score,
                "position": json.dumps(obj.position, cls=ResultEncoder)
            }
        elif isinstance(obj, Position):
            return {
                "left": obj.left,
                "top": obj.top,
                "height": obj.height,
                "width": obj.width
            }
        return super().default(obj)

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

@app.route('/get_img', methods=['POST'])
def get_image():
    # plane_id = request.args.get('planeid')
    global count
    count = count + 1
    print(f"return the {count-1}-th result.")
    data_json = json.dumps(result_list[count-1],cls=ResultEncoder)
    print(data_json)
    return json.dumps(result_list[count-1],cls=ResultEncoder)

@app.route('/get_classified_img')
def get_classified_img():
    plane_id = request.args.get('planeid')
    global count
    print(count)
    count = count + 1
    print(f"return the {count-1}-th result.")
    return jsonify(result_list[count-1])

# Start the server
if __name__ == '__main__':
    app.run(debug=True)
