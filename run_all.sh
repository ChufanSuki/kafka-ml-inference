# producer
./producer.py getting_started.ini --directory ../dataset/val_dataset/pre_val_image --topic image_segmentation_topic
./producer.py getting_started.ini --directory ../car_dataset/testing_images --topic object_detection_topic
./producer.py getting_started.ini --directory dataset --topic image_classification_topic
./producer.py getting_started.ini --directory ../dataset/sar_dataset --topic sar_object_detection_topic
./producer.py getting_started.ini --directory ../dataset/boat_dataset --topic boat_object_detection_topic
# consumer
./consumer.py getting_started.ini --topic image_segmentation_topic
./consumer.py getting_started.ini --topic object_detection_topic
./consumer.py getting_started.ini --topic image_classification_topic
./consumer.py getting_started.ini --topic sar_object_detection_topic
./consumer.py getting_started.ini --topic boat_object_detection_topic