import asyncio
import io
import sys
import json
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def on_response(response):
            if "json" in response.headers.get("content-type", ""):
                if "train" in response.url.lower() or "search" in response.url.lower():
                    print(f"API Intercepted: {response.url}")
                    try:
                        data = await response.json()
                        with open("debug_ixigo_api.json", "w", encoding="utf-8") as f:
                            json.dump(data, f)
                    except Exception as e:
                        print(f"Error parsing json from {response.url}: {e}")
                        
        page.on("response", on_response)
        
        # Test ixigo train page
        url = "https://www.ixigo.com/search/result/train/MAS/CSTM/01062026//1/0/0/0/ALL"
        # Or just the home page and we can see if there is an API? The ixigo URL format is:
        url = "https://www.ixigo.com/trains/Chennai-to-Mumbai"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(15000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
