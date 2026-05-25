"""
Intercept the actual API calls that travel websites make internally.
This script will open each site, capture XHR/fetch responses, and print the raw data.
"""
import asyncio
import sys
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def intercept_flight_api():
    """Intercept Ixigo's internal flight search API to understand the real data format."""
    print("\n" + "="*60)
    print("INTERCEPTING IXIGO FLIGHT API CALLS...")
    print("="*60)
    
    captured_responses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Capture all network responses
        async def handle_response(response):
            url = response.url
            # Look for API calls that contain flight data
            if any(kw in url.lower() for kw in ['search', 'flight', 'result', 'fare', 'srp']):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type or 'javascript' in content_type:
                        body = await response.text()
                        if len(body) > 100:  # Skip tiny responses
                            print(f"\n[API CAPTURED] {response.status} {url[:120]}")
                            print(f"  Content-Type: {content_type}")
                            print(f"  Body length: {len(body)} chars")
                            # Try to parse as JSON
                            try:
                                data = json.loads(body)
                                print(f"  JSON keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                                captured_responses.append({'url': url, 'data': data})
                            except:
                                print(f"  First 200 chars: {body[:200]}")
                except Exception as e:
                    pass
        
        page.on('response', handle_response)
        
        url = "https://www.ixigo.com/search/result/flight/DEL/BOM/20260601/1/0/0/e/0/CHEAPEST"
        print(f"\nNavigating to: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(25000)
        
        print(f"\n\nTotal API responses captured: {len(captured_responses)}")
        
        # Also try to extract from the DOM after JS renders
        print("\n--- DOM EXTRACTION ATTEMPT ---")
        dom_text = await page.evaluate("""
            () => {
                const body = document.body.innerText;
                return body.substring(0, 3000);
            }
        """)
        print(f"Body text (first 3000 chars):\n{dom_text}")
        
        await page.screenshot(path="debug_intercept_flight.png", full_page=False)
        await browser.close()
    
    return captured_responses


async def intercept_redbus_api():
    """Intercept RedBus API calls."""
    print("\n" + "="*60)
    print("INTERCEPTING REDBUS API CALLS...")
    print("="*60)
    
    captured_responses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        async def handle_response(response):
            url = response.url
            if any(kw in url.lower() for kw in ['search', 'bus', 'result', 'route', 'inventory']):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.text()
                        if len(body) > 100:
                            print(f"\n[API CAPTURED] {response.status} {url[:120]}")
                            print(f"  Body length: {len(body)} chars")
                            try:
                                data = json.loads(body)
                                print(f"  JSON keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                                captured_responses.append({'url': url, 'data': data})
                            except:
                                print(f"  First 200 chars: {body[:200]}")
                except:
                    pass
        
        page.on('response', handle_response)
        
        url = "https://www.redbus.in/bus-tickets/chennai-to-madurai?fromCityName=Chennai&toCityName=Madurai&onward=1-Jun-2026"
        print(f"\nNavigating to: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(15000)
        
        print(f"\n\nTotal RedBus API responses captured: {len(captured_responses)}")
        
        # DOM extraction
        print("\n--- DOM EXTRACTION ---")
        aria_results = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('li[aria-label*="Departs"]');
                return Array.from(cards).slice(0, 3).map(c => c.getAttribute('aria-label'));
            }
        """)
        print(f"Aria-label cards found: {len(aria_results)}")
        for i, label in enumerate(aria_results):
            print(f"  Card {i+1}: {label}")
        
        await page.screenshot(path="debug_intercept_bus.png", full_page=False)
        await browser.close()
    
    return captured_responses


async def intercept_train_api():
    """Intercept Ixigo train API calls."""
    print("\n" + "="*60)
    print("INTERCEPTING IXIGO TRAIN API CALLS...")
    print("="*60)
    
    captured_responses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        async def handle_response(response):
            url = response.url
            if any(kw in url.lower() for kw in ['search', 'train', 'result', 'route', 'rail', 'schedule']):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.text()
                        if len(body) > 100:
                            print(f"\n[API CAPTURED] {response.status} {url[:120]}")
                            print(f"  Body length: {len(body)} chars")
                            try:
                                data = json.loads(body)
                                print(f"  JSON keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                                captured_responses.append({'url': url, 'data': data})
                            except:
                                print(f"  First 200 chars: {body[:200]}")
                except:
                    pass
        
        page.on('response', handle_response)
        
        url = "https://www.ixigo.com/search/result/train/Chennai/Mumbai/20260601/1/0/0/0/ALL"
        print(f"\nNavigating to: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(20000)
        
        print(f"\n\nTotal Train API responses captured: {len(captured_responses)}")
        
        # DOM extraction
        print("\n--- DOM EXTRACTION ---")
        dom_text = await page.evaluate("""
            () => document.body.innerText.substring(0, 3000)
        """)
        print(f"Body text (first 3000 chars):\n{dom_text}")
        
        await page.screenshot(path="debug_intercept_train.png", full_page=False)
        await browser.close()
    
    return captured_responses


async def main():
    print("Starting API interception for all 3 travel modes...")
    print("This will open browser windows to capture real API responses.\n")
    
    # Run one at a time to avoid overwhelming the system
    flight_data = await intercept_flight_api()
    bus_data = await intercept_redbus_api()
    train_data = await intercept_train_api()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Flight APIs captured: {len(flight_data)}")
    print(f"Bus APIs captured: {len(bus_data)}")
    print(f"Train APIs captured: {len(train_data)}")
    
    # Save captured data for analysis
    all_data = {
        'flight': [{'url': r['url'], 'keys': list(r['data'].keys()) if isinstance(r['data'], dict) else 'array'} for r in flight_data],
        'bus': [{'url': r['url'], 'keys': list(r['data'].keys()) if isinstance(r['data'], dict) else 'array'} for r in bus_data],
        'train': [{'url': r['url'], 'keys': list(r['data'].keys()) if isinstance(r['data'], dict) else 'array'} for r in train_data],
    }
    
    with open('captured_apis.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    print("\nSaved API summary to captured_apis.json")
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
