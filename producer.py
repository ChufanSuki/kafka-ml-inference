#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser

import h5py
import numpy as np
from confluent_kafka import Producer

def write_to_kafka(producer, topic_name, items):
    count=0
    for message, key in items:
        producer.produce(topic, key=str(count), value=message, callback=delivery_callback)
        count+=1
    producer.flush()
    print("Wrote {0} messages into topic: {1}".format(count, topic_name))

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
    
    f = h5py.File('CIFAR11_dataset.mat','r')
    x_train = np.array(f.get('Xtrain'))
    x_test = np.array(f.get('Xtest'))
    
    write_to_kafka(producer, topic, zip(x_train, x_test))
