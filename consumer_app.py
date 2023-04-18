#!/usr/bin/env python

import sys
import pickle
from argparse import ArgumentParser, FileType
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from configparser import ConfigParser
import base64
import threading
import numpy as np
from PIL import Image
from io import BytesIO
from confluent_kafka import OFFSET_BEGINNING, Consumer, KafkaError, KafkaException
import random
from middleware import send_service, numpy_to_base64_image, Service, ServicePool
from result import ImageClassificationResult, ObjectDetectionResult, Position, ImageSegmentationResult
from typing import List

from pymongo import MongoClient
from utils import *
import time
import cv2
from consumer_config import config as consumer_config


image_classification_test01_url = "http://10.14.42.236:31409/imageClassification"
object_detection_test04_url = "http://10.14.42.236:31541/objectDetect"
# image_segmentation_url = "http://10.14.42.236:30260/imageSegmentation"
# sar_object_detection_url = "http://10.14.42.236:32423/objectDetect"
# boat_object_detection_url = "http://10.14.42.236:30455/objectDetect"


class ObjectDetectionService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)
        
class ImageClassificationService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)
        
class ImageSegmentationService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)

image_classification_test01_service = ImageClassificationService(image_classification_test01_url)
object_detection_test04_service = ObjectDetectionService(object_detection_test04_url)
# sar_object_detection_service = ObjectDetectionService(sar_object_detection_url)
# boat_object_detection_service = ObjectDetectionService(boat_object_detection_url)
# image_segmentation_service = ImageSegmentationService(image_segmentation_url)
# image_classification_pool = ServicePool()
# object_detection_pool = ServicePool()
# image_classification_pool.add(image_classification_service)
# object_detection_pool.add(object_detection_service)
# service_pool = [image_classification_service, object_detection_service]
# service_pools = [image_classification_pool, object_detection_pool]

# Define the function to process a Kafka message
def process_message(msg, service):
    base64_str = base64.b64encode(msg.value()).decode('utf-8')
    result = send_service(service.url, base64_str)
    result = result["result"]
    if isinstance(service, ImageClassificationService):
        icr = ImageClassificationResult(base64_str, result[0]["classfication"], result[0]["score"])
        service.result_list.append(icr)
    elif isinstance(service, ObjectDetectionService):
        num = len(result)
        odr = ObjectDetectionResult(num, base64_str)
        for i in range(num):
            odr.add_to_result(
                result[i]['class_name'], result[i]['score'], 
                Position(result[i]['position']['left'], result[i]['position']['top'], result[i]['position']['width'], result[i]['position']['height'])
                )
        if num != 0:
            odr.draw_rectangle_on_image()
        service.result_list.append(odr)
    elif isinstance(service, ImageSegmentationService):
            isr = ImageSegmentationResult(result["segmentation_list_path"][0])
            service.result_list.append(isr)
    print(f"Use {service.get_service_name()} Processed message with result:{result}")

# Define the function to consume messages from Kafka
def consume_messages(service_pool):
    with ThreadPoolExecutor(max_workers=16) as executor:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                executor.submit(process_message, msg, service_pool)
                
class ConsumerThread:
    def __init__(self, config, topic, batch_size, service, db):
        self.config = config
        self.topic = topic
        self.batch_size = batch_size
        self.service = service
        self.db = db

    def read_data(self):
        consumer = Consumer(self.config)
        consumer.subscribe(self.topic)
        self.run(consumer, 0, [], [])

    def run(self, consumer, msg_count, msg_array, metadata_array):
        try:
            while True:
                msg = consumer.poll(0.5)
                if msg == None:
                    continue
                elif msg.error() == None:
                    
                    base64_str = base64.b64encode(msg.value()).decode('utf-8')

                    # convert image bytes data to numpy array of dtype uint8
                    # nparr = np.frombuffer(msg.value(), np.uint8)

                    # decode image
                    # img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    # img = cv2.resize(img, (224, 224))

                    # get metadata
                    frame_no = msg.timestamp()[1]
                    file_name = msg.headers()[0][1].decode("utf-8")

                    metadata_array.append((frame_no, file_name))
                    msg_count += 1
                    result_list = send_service(self.service.url, base64_str)["result"]
                    if isinstance(service, ObjectDetectionService):
                        num = len(result_list)
                        odr = ObjectDetectionResult(num, base64_str)
                        for i in range(num):
                            odr.add_to_result(
                                result_list[i]['class_name'], result_list[i]['score'], 
                                Position(result_list[i]['position']['left'], result_list[i]['position']['top'], result_list[i]['position']['width'], result_list[i]['position']['height'])
                            )
                        if num != 0:
                            odr.draw_rectangle_on_image()
                        base64_str = odr.base64_str    
                    result = {
                        "base64_str": base64_str,
                        "result_list": result_list
                    }
                    self.db[self.topic[0]].insert_one(result)
                    # commit synchronously
                    consumer.commit(asynchronous=False)
                    # reset the parameters
                    metadata_array = []
                    result = {}
                    result_list = []
                    print(f"Proceed {msg_count}-th message in threading {threading.get_ident()}")

                elif msg.error().code() == KafkaError._PARTITION_EOF:
                    print('End of partition reached {0}/{1}'
                        .format(msg.topic(), msg.partition()))
                else:
                    print('Error occured: {0}'.format(msg.error().str()))

        except KeyboardInterrupt:
            print("Detected Keyboard Interrupt. Quitting...")
            pass

        finally:
            consumer.close()

    def start(self, numThreads):
        # Note that number of consumers in a group shouldn't exceed the number of partitions in the topic
        for _ in range(numThreads):
            t = threading.Thread(target=self.read_data)
            t.daemon = True
            t.start()
            while True: 
                time.sleep(10)



if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    # parser.add_argument('--reset', action='store_true')
    parser.add_argument('--topic', default='image_segmentation_topic')
    parser.add_argument('--filename', default='results')
    args = parser.parse_args()
    
    filename = args.filename
    topic = [args.topic]
    
    # connect to mongodb
    client = MongoClient('mongodb://localhost:27017')
    db = client["ai_studio_demo"]
    

    # video_names = ["MOT20-02-raw", "MOT20-03-raw", "MOT20-05-raw"]
    # videos_map = create_collections_unique(db, video_names)
    service = None
    import re

    object_detection_pattern = r'^object_detection_test04_.*_topic$'
    image_classification_pattern = r'^image_classification_test01_.*_topic$'
    if re.match(object_detection_pattern, topic[0]):
        service = object_detection_test04_service
    elif re.match(image_classification_pattern, topic[0]):
        service = image_classification_test01_service
    
    consumer_thread = ConsumerThread(consumer_config, topic, 1, service, db)
    consumer_thread.start(3)


    # # Set up a callback to handle the '--reset' flag.
    # def reset_offset(consumer, partitions):
    #     if args.reset:
    #         for p in partitions:
    #             p.offset = OFFSET_BEGINNING
    #         consumer.assign(partitions)
