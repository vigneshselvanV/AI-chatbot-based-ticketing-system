import urllib.request
import json

payload = {
    'query': 'what maduari is famaus for', 
    'context': {'from_city': None, 'to_city': 'rameswaram', 'date': None, 'passengers': 1},
    'history': []
}
req = urllib.request.Request(
    'http://localhost:8000/search',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    resp = urllib.request.urlopen(req).read().decode('utf-8')
    print('Response:', resp)
except Exception as e:
    print('Error:', e)
