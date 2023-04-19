import requests
import json
import numpy as np 
import base64
import io
from io import BytesIO
from PIL import Image, ImageDraw
import pickle

# See test_model.py for example usage

class Service:
    def __init__(self, url) -> None:
        self.url = url
        self.result_list = []
    
    def get_service_name(self):
        self.name = self.url.split("/")[-1]
        return self.name
    
    def dump(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.result_list, file)

class ServicePool:
    def __init__(self) -> None:
        self.pool = []
        self.idx = 0
    
    def add(self, service):
        self.pool.append(service)

def get_image_base64(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
    except:
        pass
    return None

def send_service(url, data):
    # define the headers and data for the request
    headers = {"Content-Type": "application/json"}

    data = {"image": data}
    import time

    start_time = time.time()
    # send the post request
    response = requests.post(url, headers=headers, json=data)
    end_time = time.time()
    time_taken = end_time - start_time
    print("Time taken:", time_taken, "seconds")

    try:
        json_data = json.loads(response.text)
        return json_data
    except json.decoder.JSONDecodeError:
        # handle the case where the response body could not be decoded as JSON
        print("Failed to decode response body as JSON")
    
def numpy_to_base64_image(arr, resize=None, rescale=None):
    if rescale:
        arr = np.uint8(arr * rescale)
    if len(arr.shape) == 1:
        # Reshape the 1D array to a 3D array of shape (32, 32, 3)
        img_arr = arr.reshape((3, 32, 32)).transpose([1, 2, 0]) 
    else:
        img_arr = arr
    if resize:
        img = Image.fromarray(img_arr)
        resized_img_pil = img.resize((resize))
        img_arr = np.array(resized_img_pil)
    # Convert the NumPy array to a PIL Image object
    img = Image.fromarray(img_arr)
    # Create a BytesIO object to hold the image data
    img_bytes = io.BytesIO()
    # Save the image to the BytesIO object in PNG format
    img.save(img_bytes, format='PNG')
    # Encode the image datahttps://github.com/ChufanSuki/kafka-ml-inference.git in base64
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    # Return the base64-encoded image string
    return img_base64

def draw_rectangle_on_image(base64_str, position_obj, color='red', width=2):
    # decode the base64 string into a bytes object
    img_bytes = base64.b64decode(base64_str)
    
    # create a PIL image object from the bytes object
    img = Image.open(BytesIO(img_bytes))

    # create a drawing object
    draw = ImageDraw.Draw(img)

    # define the coordinates of the rectangle
    top = position_obj.top
    left = position_obj.left
    bottom = top + position_obj.height
    right = left + position_obj.width

    # draw the rectangle
    draw.rectangle((left, top, right, bottom), outline=color, width=width)

    # encode the image as a base64 string and return it
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def tif_to_jpg(input_folder, output_folder):

    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.tif'):
            # Open the TIF image file
            tif_image = Image.open(os.path.join(input_folder, file_name))

            # Construct the output file name
            output_file_name = os.path.splitext(file_name)[0] + ".jpg"
