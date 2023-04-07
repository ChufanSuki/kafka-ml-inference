#!/usr/bin/env python

import sys
import pickle
from argparse import ArgumentParser, FileType
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser

import numpy as np
from confluent_kafka import OFFSET_BEGINNING, Consumer

from middleware import send_service
from result import ImageClassificationResult, ObjectDetectionResult

url = "http://10.14.42.236:32492/imageClassification"

icr_list = []

# Define the function to process a Kafka message
def process_message(msg):
    frame_byted = msg.value()
    numpy_array = np.frombuffer(frame_byted)
    result = send_service(url, numpy_array).json()
    icr = ImageClassificationResult(numpy_array, result["name"], result["score"])
    icr_list.append(icr)
    print("Processed message with result:", result)

# Define the function to consume messages from Kafka
def consume_messages():
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                executor.submit(process_message, msg)

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
        consume_messages()
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()
    # open a file, where you want to store the data
    with open(filename, 'wb') as file:
        pickle.dump(icr_list, file)
