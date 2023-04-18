from flask import Flask, jsonify, request
from pymongo import MongoClient, DESCENDING
from bson.json_util import dumps
from pymongo.errors import InvalidName
app = Flask(__name__)

# Set up a connection to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['ai_studio_demo']
doc_counters = {}
# Define a route to retrieve documents in order of insertion
@app.route('/get_document', methods=['GET'])
def get_document():
    global doc_counters
    collection_name = request.args.get("collection")  # get the collection name from the query parameter
    try:
        collection = db[collection_name]  # try to get the collection with the given name
    except InvalidName:
        return jsonify({"error": "Invalid collection name."}), 400  # return an error response if the collection name is invalid
    # Get the number of documents in the collection
    print(collection_name)
    num_docs = collection.count_documents({})
    print(num_docs)
    doc_counter = doc_counters.get(collection_name, 0)
    document = collection.find().limit(1).skip(doc_counter).next()
    doc_counter = (doc_counter + 1) % num_docs
    doc_counters[collection_name] = doc_counter 
    print(document)
    return jsonify(dumps(document))

if __name__ == '__main__':
    app.run(debug=True)
