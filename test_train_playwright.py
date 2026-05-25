import asyncio
import io
import sys
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def scrape_ixigo_train():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # Test ixigo train page
        url = "https://www.ixigo.com/trains/Chennai-to-Mumbai"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(10000)
        
        body = await page.evaluate("document.body.innerText")
        with open("debug_ixigo_train.txt", "w", encoding="utf-8") as f:
            f.write(body)
            
        print("Done. Saved to debug_ixigo_train.txt")
        print("Preview:")
        print(body[:1000])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ixigo_train())
