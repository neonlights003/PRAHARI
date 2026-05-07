import urllib.request, json

data = json.dumps({"admin_id": "admin", "password": "admin123"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/admin/login",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    r = urllib.request.urlopen(req)
    resp = json.loads(r.read().decode())
    print("Full response:", resp)
    print("Token present:", "token" in resp)
    print("Token value:", resp.get("token", "MISSING"))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, json.loads(e.read().decode()))
