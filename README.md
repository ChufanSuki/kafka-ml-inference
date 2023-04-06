```bash
pip install confluent-kafka

docker compose up -d

docker compose exec broker \
  kafka-topics --create \
    --topic my_image_topic \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1

chmod u+x producer.py

./producer.py getting_started.ini

chmod u+x consumer.py

./consumer.py getting_started.ini
```

```
Produced event to topic my_image_topic: key = 0           
Produced event to topic my_image_topic: key = 1           
Produced event to topic my_image_topic: key = 2   
```

```
Waiting...
Consumed event from topic my_image_topic: key = 0           
Consumed event from topic my_image_topic: key = 1           
Consumed event from topic my_image_topic: key = 2 
Waiting...
```


```bash
pip install flask

python app.py
```