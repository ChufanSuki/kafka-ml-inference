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


```bash
pip install flask

python app.py
```