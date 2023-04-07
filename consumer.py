#!/usr/bin/env python

import sys
import pickle
from argparse import ArgumentParser, FileType
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from confluent_kafka import OFFSET_BEGINNING, Consumer

from middleware import send_service, numpy_to_base64_image
from result import ImageClassificationResult, ObjectDetectionResult, Location

image_classification_url = "http://10.14.42.236:32492/imageClassification"
object_detection_url = "http://10.14.42.236:30495/objectDetect"
icr_list = []

# Define the function to process a Kafka message
def process_message(msg, url):
    # base64_bytes = msg.value().decode('utf-8').encode('utf-8')
    # base64_str = base64.b64encode(base64_bytes).decode('utf-8')
    base64_str = base64.b64encode(msg.value()).decode('utf-8')
    # img = Image.open(BytesIO(msg.value()))
    # img.save("my_image_consumer.jpg")
    result = send_service(url, base64_str)
    result = result["result"]
    if url == image_classification_url:
        icr = ImageClassificationResult(base64_str, result[0]["name"], result[0]["score"])
    else: # url == object_detection_url
        
        icr = ObjectDetectionResult(base64_str, result["name"], result["score"], Location(result["left"], result["top"], result["height"], result["weight"]))
    icr_list.append(icr)
    print("Processed message with result:", result)

# Define the function to consume messages from Kafka
def consume_messages(url):
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                executor.submit(process_message, msg, url)

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--topic', default='my_image_demo')
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
        # consume_messages(object_detection_url)
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                process_message(msg, object_detection_url)
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()
    # open a file, where you want to store the data
    with open(filename, 'wb') as file:
        pickle.dump(icr_list, file)
