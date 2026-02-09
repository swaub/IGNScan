import requests
import json

url = "https://api.mojang.com/profiles/minecraft"
# "Notch" is taken, "dhkjfhskjdfhksd" is likely free
payload = ["Notch", "dhkjfhskjdfhksd"]
try:
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text}")
except Exception as e:
    print(e)
