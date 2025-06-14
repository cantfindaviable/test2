import requests
import sys

try:
    res = requests.get("http://0.0.0.0:8000/api/v2/heartbeat")
    if res.status_code == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)