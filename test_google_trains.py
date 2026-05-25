import asyncio
import io
import sys
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            has_touch=False
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = "https://www.google.com/search?q=trains+from+Chennai+to+Mumbai+on+1+June+2026&hl=en"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        body = await page.evaluate("document.body.innerText")
        with open("debug_google_trains.txt", "w", encoding="utf-8") as f:
            f.write(body)
            
        print("Done. Saved to debug_google_trains.txt")
        print("First 1000 chars:")
        print(body[:1000])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
