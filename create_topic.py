from confluent_kafka.admin import AdminClient, NewTopic

n_repicas = 1
n_partitions = 3

admin_client = AdminClient({
    "bootstrap.servers": "localhost:9092"
})

topic_list = []
topic_list.append(NewTopic("object_detection_test04_min_test_006_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("object_detection_test04_min_test_tv_city_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("object_detection_test04_min_test_follow_vehicle_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("object_detection_sar_jpg_images_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("object_detection_boat_boat_dataset_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("image_segmentation_val_image_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("image_classification_test01_flight_data_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("image_classification_test01_flight_data1_topic", n_partitions, n_repicas))
topic_list.append(NewTopic("image_classification_test01_flight_data2_topic", n_partitions, n_repicas))
fs = admin_client.create_topics(topic_list)

for topic, f in fs.items():
    try:
        f.result()  # The result itself is None
        print("Topic {} created".format(topic))
    except Exception as e:
        print("Failed to create topic {}: {}".format(topic, e))