# Integration Test with Model
import h5py
import numpy as np
from middleware import send_service, numpy_to_base64_image
import base64
from PIL import Image

f = h5py.File('CIFAR11_dataset.mat','r')
data = f.get('Xtrain')
data = np.array(data)
image_array = data[-2]

with open('test_image.jpg', 'rb') as image_file:
    encoded_bytes = base64.b64encode(image_file.read())

base64_str = numpy_to_base64_image(image_array, resize=(128, 128))
classification_response = send_service("http://10.14.42.236:32032/imageClassification", base64_str)

encoded_string = encoded_bytes.decode(('utf-8'))
detection_response = send_service("http://10.14.42.236:30495/objectDetect", encoded_string)
detection_response = send_service("http://10.14.42.236:30495/objectDetect", base64_str)
