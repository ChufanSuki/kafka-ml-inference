# Integration Test with Model
import h5py
import numpy as np
from middleware import send_service, numpy_to_base64_image

f = h5py.File('CIFAR11_dataset.mat','r')
data = f.get('Xtrain')
data = np.array(data)
image_array = data[-2]

base64_str = numpy_to_base64_image(image_array)
classification_response = send_service("http://10.14.42.236:32032/imageClassification", base64_str)
detection_response = send_service("http://10.14.42.236:30495/objectDetect", base64_str)
