#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser

import h5py
import numpy as np
from confluent_kafka import Producer

if __name__ == '__main__':
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    args = parser.parse_args()

    # Parse the configuration.
    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser['default'])

    # Create Producer instance
    producer = Producer(config)

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print('ERROR: Message failed delivery: {}'.format(err))
        else:
            print("Produced event to topic {topic}: key = {key:12}".format(
                topic=msg.topic(), key=msg.key().decode('utf-8')))

    # Produce data by selecting random values from these lists.
    topic = "my_image_topic"

    count = 0
    
    
    f = h5py.File('CIFAR11_dataset.mat','r')
    data = f.get('Xtrain')
    data = np.array(data)
    data = ["sin", "cos", "tan"]
    
    while count < 3:
        message = data[count]
        producer.produce(topic, key=str(count), value=message, callback=delivery_callback)
        count += 1
        

    # Block until the messages are sent.
    producer.poll(10000)
    producer.flush()