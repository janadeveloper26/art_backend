import urllib.request
import urllib.error
import json

url = "https://api.gloriousartcreations.com/api/v1/auth/firebase/login"
data = json.dumps({
    "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijc5OTRiNGYzMTU2MzJiMjk3NzAwNmQ5M2U5NGIyYWNiZTMwNWZlNDYiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiRXJpYyBTaGVsZG9uIFJTIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0tzQ2E1VF9EYnZmZDNJMFFkSnQwMmxEaEdLYlJmYkV6dC1HdUhvZkJSREJXYWJzSzNWPXM5Ni1jIiwiaXNzIjoiaHR0cHM6Ly9zZWN1cmV0b2tlbi5nb29nbGUuY29tL2dsb3VyaW91c2FydC05NDY5OSIsImF1ZCI6Imdsb3VyaW91c2FydC05NDY5OSIsImF1dGhfdGltZSI6MTc4MTQzMTg4MCwidXNlcl9pZCI6InNzZVBhZVg4cUhNMTVNTkNmUUFXbjd3ZUxvRjMiLCJzdWIiOiJzc2VQYWVYOHFITTE1TU5DZlFBV243d2VMb0YzIiwiaWF0IjoxNzgxNDMxODgxLCJleHAiOjE3ODE0MzU0ODEsImVtYWlsIjoiZXJpY3NoZWxkb24wNEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMTAxMTkyNjM2OTI0OTg2MDQ3MiJdLCJlbWFpbCI6WyJlcmljc2hlbGRvbjA0QGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.cPyeAgjtLip4Pxs_JldieiwcDrOEXCIEVQVUTRWkGv6UiTfwV8CNVm35DrggCBF-A-5Hx_56fL5pllZ33XyM2OVZy9a_lrmufAliDbkbywZ__g6BFJPO13JVVs6E69itQTf",
    "name": "Eric Sheldon RS",
    "device": {
        "device_id": "test_id",
        "device_name": "test_name",
        "manufacturer": "test",
        "brand": "test",
        "android_version": "34",
        "platform": "android"
    }
}).encode('utf-8')

headers = {
    "Content-Type": "application/json"
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
