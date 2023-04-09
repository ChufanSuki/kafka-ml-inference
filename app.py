from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
import json
import pickle
from result import ImageClassificationResult, ObjectDetectionResult, Position
import random

app = Flask(__name__)
CORS(app)

filename = 'results'
with open(filename, 'rb') as file:
    result_list = pickle.load(file)
    
count = 0

def write_json(result):
    data = json.dumps(result, cls=ResultEncoder)

    # load as dict
    json_dict = json.loads(data)
    json_dict_position = json.loads(json_dict["position"])
    del json_dict['position']
    json_dict['position'] = json_dict_position

    # write pretty JSON to file
    # with open('formatted.json','w') as formatted_file: 
    #     json.dump(json_dict, formatted_file, indent=4)  
    return json_dict

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

@app.route('/get_img', methods=['GET'])
def get_image():
    # plane_id = request.args.get('planeid')
    global count
    count = count + 1
    idx = count - 1
    if count >= len(result_list):
        idx = random.randint(0, len(result_list) - 1)
    print(f"return the {idx}-th result.")
    json_dict = write_json(result_list[idx])
    return json.dumps(json_dict)

@app.route('/get_classified_img')
def get_classified_img():
    plane_id = request.args.get('planeid')
    global count
    print(count)
    count = count + 1
    print(f"return the {count-1}-th result.")
    json_dict = write_json(result_list[count-1])
    data = json.dumps(result_list[count-1], cls=ResultEncoder)
    return json.dumps(json_dict)

# Start the server
if __name__ == '__main__':
    app.run(debug=True, port=8000)
