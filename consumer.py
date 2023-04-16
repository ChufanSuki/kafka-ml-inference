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
from middleware import send_service, numpy_to_base64_image, Service, ServicePool
from result import ImageClassificationResult, ObjectDetectionResult, Position, ImageSegmentationResult
from typing import List


image_classification_url = "http://10.14.42.236:31120/imageClassification"
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
image_segmentation_service = ImageSegmentationService(image_segmentation_url)
image_classification_pool = ServicePool()
object_detection_pool = ServicePool()
image_classification_pool.add(image_classification_service)
object_detection_pool.add(object_detection_service)
service_pool = [image_classification_service, object_detection_service]
service_pools = [image_classification_pool, object_detection_pool]

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
    def __init__(self, config, topic, db):
        self.config = config
        self.topic = topic
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
                    process_message(msg, service)

                    # bulk process
                    msg_count += 1
                    self.img_map = reset_map(self.img_map)
                    if msg_count % self.batch_size == 0:
                        # predict on batch
                        img_array = np.asarray(msg_array)
                        img_array = preprocess_input(img_array)
                        predictions = self.model.predict(img_array)
                        labels = decode_predictions(predictions)

                        self.videos_map = reset_map(self.videos_map)
                        for metadata, label in zip(metadata_array, labels):
                            top_label = label[0][1]
                            confidence = label[0][2]
                            confidence = confidence.item()
                            frame_no, video_name = metadata
                            doc = {
                                "frame": frame_no,
                                "label": top_label,
                                "confidence": confidence
                            }
                            self.videos_map[video_name].append(doc)

                        # insert bulk results into mongodb
                        insert_data_unique(self.db, self.videos_map)

                        # commit synchronously
                        consumer.commit(asynchronous=False)
                        # reset the parameters
                        msg_count = 0
                        metadata_array = []
                        msg_array = []

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

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    parser.add_argument('--topic', default='image_segmentation_topic')
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

    if topic == "object_detection_topic":
        service = object_detection_service
    elif topic == "image_classification_topic":
        service = image_classification_service
    elif topic == "image_segmentation_topic":
        service = image_segmentation_service
    
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
                process_message(msg, service)
    except KeyboardInterrupt:
        print(f"exsiting now...")
    finally:
        # Leave group and commit final offsets
        consumer.close()
    # open a file, where you want to store the data
    # write every N times
    service.dump(filename+"-"+topic)
