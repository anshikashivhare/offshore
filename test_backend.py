import requests
try:
    r = requests.get('http://localhost:8000/api/v1/icebergs/')
    print(r.status_code)
except Exception as e:
    print(e)
