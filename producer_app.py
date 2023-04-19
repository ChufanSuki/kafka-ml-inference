#!/usr/bin/env python

import base64
import os
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from io import BytesIO
from glob import glob
import sys

import h5py
import numpy as np
from confluent_kafka import Producer
from PIL import Image
import concurrent.futures
import time
from utils import *

from middleware import numpy_to_base64_image
from producer_config import config as producer_config


class ProducerThread:
    def __init__(self, config) -> None:
        self.producer: Producer = Producer(config)

    def write_to_kafka(self, topic_name, items):
        count = 0
        for message, key in items:
            self.producer.produce(
                topic=topic_name, 
                value=message, 
                timestamp=count,
                on_delivery=delivery_report,
                headers={
                        "file_name": key
                }
            )
            count += 1
        self.producer.flush()
        print("Wrote {0} messages into topic: {1}".format(count, topic_name))
        
    def produce_from_mat(self, topic, filename='CIFAR11_dataset.mat'):
        f = h5py.File(filename,'r')
        x_train = np.array(f.get('Xtrain'))
        x_test = np.array(f.get('Xtest'))
    
        self.write_to_kafka(topic, zip(numpy_to_base64_image(x_train, rescale=255), numpy_to_base64_image(x_test, rescale=255)))

    def produce_from_folder(self, topic, directory_path='train'):
        key = []
        img_arrs = []
        largest_size = 0
        count = 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
            # Check if the file is an image
                if filename.endswith(('jpg', 'jpeg', 'png', 'bmp', 'gif')):
                    # Read the image file
                    image_path = os.path.join(dirpath, filename)
                    with Image.open(image_path) as img:
                        # Convert the image to a NumPy array
                        img_arr = np.array(img)
                        b_string = base64.b64decode(numpy_to_base64_image(img_arr).encode('utf-8'))
                        count += 1
                        print(f"encoded {count} images to base64.")
                        byte_size = sys.getsizeof(b_string)
                        if byte_size > largest_size:
                            largest_size = byte_size
                        img_arrs.append(b_string)
                        key.append(filename)
        print("Largest byte size of the string:", largest_size)
        self.write_to_kafka(topic, zip(img_arrs, key))
    
    def publishFrame(self, video_path):
        video = cv2.VideoCapture(video_path)
        video_name = os.path.basename(video_path).split(".")[0]
        frame_no = 1
        while video.isOpened():
            _, frame = video.read()
            # pushing every 3rd frame
            if frame_no % 3 == 0:
                frame_bytes = serializeImg(frame)
                self.producer.produce(
                    topic="multi-video-stream", 
                    value=frame_bytes, 
                    on_delivery=delivery_report,
                    timestamp=frame_no,
                    headers={
                        "video_name": str.encode(video_name)
                    }
                )
                self.producer.poll(0)
            time.sleep(0.1)
            frame_no += 1
        video.release()
        return
        
    def start(self, vid_paths):
        # runs until the processes in all the threads are finished
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.publishFrame, vid_paths)

        self.producer.flush() # push all the remaining messages in the queue
        print("Finished...")


if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('--topic', default='image_classification_topic_01')
    parser.add_argument('--directory')
    args = parser.parse_args()


    # Produce data by selecting random values from these lists.
    topic = args.topic
    directory = args.directory
    paths = glob(directory + '*.jpg')
    producer_thread = ProducerThread(producer_config)
    # produce_from_mat(producer, topic)
    producer_thread.produce_from_folder(topic, directory)
    