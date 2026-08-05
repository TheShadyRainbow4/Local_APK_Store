import concurrent.futures
import json
import time
import urllib.request
import urllib.error
import sys

SERVER_URL = "http://127.0.0.1:8552"

def post_json(endpoint, data=None, raw_body=None, timeout=5):
    url = f"{SERVER_URL}{endpoint}"
    if raw_body is not None:
        body_bytes = raw_body.encode('utf-8') if isinstance(raw_body, str) else raw_body
    elif data is not None:
        body_bytes = json.dumps(data).encode('utf-8')
    else:
        body_bytes = b""
    
    req = urllib.request.Request(url, data=body_bytes, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode('utf-8')
            return response.status, res_body
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8')
        return e.code, res_body
    except Exception as e:
        return 500, f"Exception: {type(e).__name__} - {e}"

def test_single_request():
    print("Testing single POST request to /api/heartbeat...")
    status, resp = post_json("/api/heartbeat", data={"client_id": "test_1", "device_name": "Test Device"})
    print(f"Single request result: status={status}, resp={resp}")

if __name__ == "__main__":
    test_single_request()
