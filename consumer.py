#!/usr/bin/env python

import sys
import pickle
from argparse import ArgumentParser, FileType
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from configparser import ConfigParser
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from confluent_kafka import OFFSET_BEGINNING
from confluent_kafka import Consumer as KafkaConsumer
import random
from middleware import send_service, numpy_to_base64_image, Service, ServicePool
from result import ImageClassificationResult, ObjectDetectionResult, Position, ImageSegmentationResult
from typing import List
from threading import Thread


image_classification_url = "http://10.14.42.236:32032/imageClassification"
object_detection_url = "http://10.14.42.236:32079/objectDetect"
image_segmentation_url = "http://10.14.42.236:30260/imageSegmentation"
class ObjectDetectionService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)
        
class ImageClassificationService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)
        
class ImageSegmentationService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)

image_classification_service = ImageClassificationService(image_classification_url)
object_detection_service = ObjectDetectionService(object_detection_url)
image_segmentation_service = ImageSegmentationService(image_classification_url)
image_classification_pool = ServicePool()
object_detection_pool = ServicePool()
image_classification_pool.add(image_classification_service)
object_detection_pool.add(object_detection_service)
service_pool = [image_classification_service, object_detection_service]
service_pools = [image_classification_pool, object_detection_pool]

class Consumer:
    def __init__(self, config, reset, topic) -> None:
        self.consumer: KafkaConsumer = KafkaConsumer(config)
        self.reset = reset
        self.topic = topic
        # Subscribe to topic
        self.consumer.subscribe([topic], on_assign=self.reset_offset)
        if topic == "image_classification":
            self.service = ImageClassificationService("http://10.14.42.236:32032/imageClassification")
        elif topic == "object_detection":
            self.service = ObjectDetectionService("http://10.14.42.236:32079/objectDetect")
        elif topic == "image_segmentation":
            self.service = ImageSegmentationService("http://10.14.42.236:30260/imageSegmentation")
        
    # Set up a callback to handle the '--reset' flag.
    def reset_offset(self, partitions):
        if self.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            self.consumer.assign(partitions)
            
    # Define the function to process a Kafka message
    def process_message(self, msg):
        base64_str = base64.b64encode(msg.value()).decode('utf-8')
        result = send_service(self.service.url, base64_str)
        result = result["result"]
        if isinstance(self.service, ImageClassificationService):
            icr = ImageClassificationResult(base64_str, result[0]["classfication"], result[0]["score"])
            self.service.result_list.append(icr)
        elif isinstance(self.service, ObjectDetectionService):
            num = len(result)
            odr = ObjectDetectionResult(num, base64_str)
            for i in range(num):
                odr.add_to_result(
                    result[i]['class_name'], result[i]['score'], 
                    Position(result[i]['position']['left'], result[i]['position']['top'], result[i]['position']['width'], result[i]['position']['height'])
                )
            odr.draw_rectangle_on_image()
            self.service.result_list.append(odr)
        elif isinstance(self.service, ImageSegmentationService):
            isr = ImageSegmentationResult(result["segementation_list_path"][0])
            self.service.result_list.append(isr)
        print(f"Use {self.service.get_service_name()} Processed message with result:{result}")

    def run(self):
        # Poll for new messages from Kafka and print them.
        try:
            # consume_messages(service_pool)
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    print("Waiting...")
                elif msg.error():
                    print("ERROR: %s".format(msg.error()))
                else:
                    self.process_message(msg, self.service)
        except KeyboardInterrupt:
            print(f"exsiting now...")
        finally:
            # Leave group and commit final offsets
            self.consumer.close()



# Define the function to consume messages from Kafka
def consume_messages(service):
    with ThreadPoolExecutor(max_workers=16) as executor:
        while True:
            msg = consumer.consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                executor.submit(process_message, msg, service)

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--topic-list', nargs='+', default='segment_topic classification_topic object_detection_topic')
    parser.add_argument('--filename', default='results')
    args = parser.parse_args()
    
    filename = args.filename
    topic_list = args.topic_list

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])

    consumer_list = []
    # Create Consumer instance
    for topic in topic_list:
        consumer_list.append(Consumer(config, args.reset, topic))

    # Create a thread for each consumer and start all the threads
    threads = []
    for consumer in consumer_list:
        thread = Thread(target=consumer)
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    # open a file, where you want to store the data
    # write every N times
    for consumer in consumer_list:
        consumer.service.dump(filename+"-"+consumer.service.get_service_name())
