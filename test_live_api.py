import httpx, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("Testing LIVE /search endpoint (allow 130s for ScraperAPI)...")
try:
    r = httpx.post(
        'http://localhost:8000/search',
        json={'query': 'bus from Coimbatore to Chennai tomorrow', 'context': {}, 'history': []},
        timeout=130
    )
    d = r.json()
    print('HTTP Status:', r.status_code)
    print('Type:', d.get('type'))
    data = d.get('data', [])
    print('Bus count:', len(data))
    if data:
        print('\nFirst 3 buses:')
        for b in data[:3]:
            print(f"  {b.get('operator','?')} | {b.get('price','?')} | Dep:{b.get('departure','?')}")
    else:
        print('No data returned.')
        print('Full response:')
        print(json.dumps(d, indent=2, ensure_ascii=False)[:2000])
except httpx.ReadTimeout:
    print("TIMEOUT - API did not respond within 130s")
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
