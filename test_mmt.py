import asyncio
import httpx
import re
import json

async def test_api():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    # 1. Try MakeMyTrip
    try:
        url = 'https://www.makemytrip.com/bus/search/Coimbatore/Chennai/04-06-2026'
        print(f"Fetching MMT: {url}")
        async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            print("MMT Status:", resp.status_code)
            if resp.status_code == 200:
                print("MMT HTML length:", len(resp.text))
                # check if there's any state
                if 'window.__INITIAL_STATE__' in resp.text:
                    print("Found MMT initial state!")
    except Exception as e:
        print("MMT Error:", e)

    # 2. Try AbhiBus
    try:
        # Abhibus correct URL might be different? Let's check a standard API
        print("Fetching Abhibus API...")
    except Exception as e:
        pass

asyncio.run(test_api())
