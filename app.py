from flask import Flask, jsonify, request


app = Flask(__name__)

# Define your routes here
@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/getimg')
def get_image():
    plane_id = request.args.get('planeid')
    # Do something with plane_id (e.g., retrieve the corresponding image)

    # Return the image file to the client
    filename = 'path/to/image/file.jpg'
    return send_file(filename, mimetype='image/jpeg')


# Start the server
if __name__ == '__main__':
    app.run(debug=True)
