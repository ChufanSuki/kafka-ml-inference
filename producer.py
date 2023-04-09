#!/usr/bin/env python

import base64
import os
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from io import BytesIO

import h5py
import numpy as np
from confluent_kafka import Producer as KafkaProducer
from PIL import Image

from middleware import numpy_to_base64_image


class Producer:
    def __init__(self, config) -> None:
        self.producer: KafkaProducer = KafkaProducer(config)
    
    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(self, err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12} message = {message:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8'), message=base64.b64encode(msg.value()).decode('utf-8')[-12:]))

    def write_to_kafka(self, topic_name, items):
        count = 0
        for message, key in items:
            self.producer.produce(topic, key=str(count), value=message, callback=self.delivery_callback)
            count+=1
        self.producer.flush()
        print("Wrote {0} messages into topic: {1}".format(count, topic_name))
        
    def produce_from_mat(self, topic, filename='CIFAR11_dataset.mat'):
        f = h5py.File(filename,'r')
        x_train = np.array(f.get('Xtrain'))
        x_test = np.array(f.get('Xtest'))
    
        self.write_to_kafka(topic, zip(numpy_to_base64_image(x_train, rescale=255), numpy_to_base64_image(x_test, rescale=255)))

    def produce_from_folder(self, topic, directory_path='train', test=False):
        # List all the files in the directory
        image_files = [f for f in os.listdir(directory_path) if f.endswith(".jpg")]
        key = []
        img_arrs = []
        num = 0
        # Loop through each file and convert to base64
        for file_name in image_files:
            if test:
                if num == 100:
                    break
            file_path = os.path.join(directory_path, file_name)
            img = Image.open(file_path)
            # Convert the image to a NumPy array
            img_arr = np.array(img)
            b_string = base64.b64decode(numpy_to_base64_image(img_arr).encode('utf-8'))
            img_arrs.append(b_string)
            if test and num == 0:
                img_bytes = img_arrs[0]

                # read the bytes as an image using PIL (Python Imaging Library)
                img = Image.open(BytesIO(img_bytes))

                # save the image as a JPEG file
                img.save("my_image.jpg")
            key.append(num)
            num = num + 1
        
        self.write_to_kafka(topic, zip(img_arrs, key))


if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--topic', default='my_image_topic')
    parser.add_argument('--directory-path')
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    # Produce data by selecting random values from these lists.
    topic = args.topic
    directory_path = args.directory_path
    producer = Producer(config)
    # produce_from_mat(producer, topic)
    producer.produce_from_folder(topic, directory_path, test=True)
    