## Start Kafka
```bash
pip install confluent-kafka

docker compose up -d

docker compose exec broker \
  kafka-topics --create \
    --topic my_image_topic \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 1
```

If you failed to create docker containers, and `docker conatiner logs id` shows that `Unable to create data directory /var/lib/zookeeper/log/version-2`. This may be caused by full disk (`docker system df`), run`docker builder prune` to clear build cache.

### Produce 

```bash
chmod u+x producer.py

./producer.py getting_started.ini
```

```bash
Produced event to topic my_image_topic: key = 0           
Produced event to topic my_image_topic: key = 1           
Produced event to topic my_image_topic: key = 2   
```

### Consume

```bash
chmod u+x consumer.py

./consumer.py getting_started.ini
```

```bash
Waiting...
Consumed event from topic my_image_topic: key = 0           
Consumed event from topic my_image_topic: key = 1           
Consumed event from topic my_image_topic: key = 2 
Waiting...
```

## Start Flask

```bash
pip install flask

python app.py
```

```bash
curl -H "Content-type: application/json" -X POST 127.0.0.1:8000/get_img -o result.json
```

### API Endpoint for image classification

The API endpoint is located at `http://localhost/get_classified_img`.
Request Format

The API accepts POST requests in JSON format with the following fields:

- `plane_id: will not be used.`

Example Request:

```json
{
    "plane_id": "1"
}
```

Response Format

The API returns a JSON object with the following fields:
- `success: Boolean value indicating if the request was successful.`
- `class_name: Class name of the classified image.`
- `service: Name of the service.`
- `base64_str: Base64 string of the classified image.`
- `score: The score of the classification.`
- `message: A message describing the result of the request.`

Example Response:

```json
{
    "success": true,
    "class_name": "Cat",
    "service": "Image Classification",
    "base64_str": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABmklEQV",
    "score": 0.99,
    "message": "Object successfully classified."
}
```

Error Responses

The API returns an error response if the request is malformed or if an error occurs during processing. The error response will contain a message describing the error.

Example Error Response:

```json
{
    "success": false,
    "message": "Malformed request data. Please provide a valid plane ID."
}
```

### API Endpoint for object detection

The API endpoint is located at http://localhost/get_img.
Request Format

The API accepts POST requests in JSON format with the following fields:

- `plane_id: A unique identifier for the rendering job with plane id.`

Example Request:

```json
{
    "plane_id": "1"
}
```

Response Format

The API returns a JSON object with the following fields:
- `success: Boolean value indicating if the request was successful.`
- `service: Name of the service.`
- `base64_str: Base64 string of the image with detected objects.`
- `class_name: A list of class names of the detected objects.`
- `location: A list of coordinates representing the location of the object in the image.`
- `message: A message describing the result of the request.`

Example Response:

```json
{
    "success": true,
    "service": "Object Detection",
    "base64_str": "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABmklEQV",
    "class_name": ["person", "person", "car", "car"],
    "score": [1.0, 1.0, 1.0, 1.0],
    "position": [{"left": 315.0, "top": 268.0, "height": 324.0, "width": 336.0}, {"left": 270.0, "top": 254.0, "height": 321.0, "width": 291.0}, {"left": 647.0, "top": 247.0, "height": 279.0, "width": 679.0}, {"left": 437.0, "top": 282.0, "height": 311.0, "width": 472.0}, {"left": 250.0, "top": 254.0, "height": 320.0, "width": 272.0}],
    "message": "Object successfully classified."
}
```

Error Responses

The API returns an error response if the request is malformed or if an error occurs during processing. The error response will contain a message describing the error.

Example Error Response:

```json
{
    "success": false,
    "message": "Malformed request data. Please provide a valid plane ID."
}
```
