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
from confluent_kafka import OFFSET_BEGINNING, Consumer
import random
from middleware import send_service, numpy_to_base64_image, Service
from result import ImageClassificationResult, ObjectDetectionResult, Position
from typing import List


image_classification_url = "http://10.14.42.236:32032/imageClassification"
object_detection_url = "http://10.14.42.236:32079/objectDetect"

icr_list = []

class ObjectDetectionService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)
        
class ImageClassificationService(Service):
    def __init__(self, url) -> None:
        super().__init__(url)

image_classification_service = ImageClassificationService(image_classification_url)
object_detection_service = ObjectDetectionService(object_detection_url)
service_pool = [image_classification_service, object_detection_service]

# Define the function to process a Kafka message
def process_message(msg, service_pool: List[Service]):
    # base64_bytes = msg.value().decode('utf-8').encode('utf-8')
    # base64_str = base64.b64encode(base64_bytes).decode('utf-8')
    base64_str = base64.b64encode(msg.value()).decode('utf-8')
    # img = Image.open(BytesIO(msg.value()))
    # img.save("my_image_consumer.jpg")
    service = service_pool[random.randint(0, len(service_pool)-1)]
    result = send_service(service.url, base64_str)
    result = result["result"]
    if isinstance(service, ImageClassificationService):
        icr = ImageClassificationResult(base64_str, result[0]["classfication"], result[0]["score"])
    elif isinstance(service, ObjectDetectionService):
        num = len(result)
        icr = ObjectDetectionResult(num, base64_str)
        for i in range(num):
            icr.add_to_result(
                result[i]['class_name'], result[i]['score'], 
                Position(result[i]['position']['left'], result[i]['position']['top'], result[i]['position']['width'], result[i]['position']['height'])
                )
        icr.draw_rectangle_on_image()
    icr_list.append(icr)
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

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--topic', default='my_image_topic')
    parser.add_argument('--filename', default='results')
    args = parser.parse_args()
    
    filename = args.filename
    topic = args.topic

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])

    # Create Consumer instance
    consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

    # Subscribe to topic
    consumer.subscribe([topic], on_assign=reset_offset)

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
                process_message(msg, service_pool)
    except KeyboardInterrupt:
        print(f"exsiting now... processed {len(icr_list)} messages.")
    finally:
        # Leave group and commit final offsets
        consumer.close()
    # open a file, where you want to store the data
    # write every N times
    with open(filename, 'wb') as file:
        pickle.dump(icr_list, file)
