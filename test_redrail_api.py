import asyncio
import io
import sys
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        async def capture(response):
            if 'json' in response.headers.get('content-type', ''):
                url = response.url
                if 'redbus' in url and ('api' in url or 'search' in url or 'train' in url):
                    print(f"Intercepted API: {url}")
                    try:
                        text = await response.text()
                        print(f"Data snippet: {text[:200]}")
                    except:
                        pass

        page.on('response', capture)
        
        url = "https://www.redbus.in/railways/trains-between-stations/Chennai-to-Mumbai"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
