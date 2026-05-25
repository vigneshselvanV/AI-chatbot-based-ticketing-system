import asyncio
import io
import sys
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        async def on_response(response):
            if "json" in response.headers.get("content-type", ""):
                if "railways" in response.url.lower() or "train" in response.url.lower() or "search" in response.url.lower():
                    print(f"API Intercepted: {response.url}")
                    try:
                        data = await response.json()
                        # simple heuristic to see if it has train data
                        str_data = json.dumps(data).lower()
                        if "train" in str_data and "departure" in str_data:
                            print("==> FOUND TRAIN DATA API!")
                            with open("debug_redbus_train_api.json", "w", encoding="utf-8") as f:
                                json.dump(data, f)
                    except Exception as e:
                        pass
                        
        page.on("response", on_response)
        
        # We need a proper date in the URL for Redbus maybe?
        # RedBus Train URLs are usually: https://www.redbus.in/railways/search?src=MAS&dst=CSTM&doj=20260601
        # Let's try the regular page first:
        url = "https://www.redbus.in/railways/trains-between-stations/Chennai-to-Mumbai"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
