import urllib.request
import urllib.error
import json

url = "https://api.gloriousartcreations.com/api/v1/videos/signed-url"
data = json.dumps({"file_name": "test.mp4"}).encode('utf-8')
headers = {
    "Content-Type": "application/json",
    # We don't have a valid token, but we should at least see if it's 401 or 400
    "Authorization": "Bearer invalidtoken123"
}

req = urllib.request.Request(url, data=data, headers=headers, method="POST")

try:
    response = urllib.request.urlopen(req)
    print("Status:", response.status)
    print("Body:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Error Body:", e.read().decode())
except Exception as e:
    print("Exception:", e)
