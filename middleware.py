import requests

url = 'http://example.com/api/users'
data = {
    'username': 'john.doe',
    'email': 'john.doe@example.com',
    'password': 'mysecretpassword'
}

response = requests.post(url, json=data)


print(response.status_code) # Should print 200 if successful
print(response.json()) # Should print the response data from the server