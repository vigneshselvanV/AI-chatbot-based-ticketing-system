"""Quick test of RedBus trains URL."""
import asyncio
import sys
import io
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        urls = [
            ("RedBus trains search", "https://www.redbus.in/railways"),
            ("RedBus train route 1", "https://www.redbus.in/railways/trains-between-stations/Chennai-to-Mumbai"),
            ("RedBus train route 2", "https://www.redbus.in/railways/Chennai-to-Mumbai"),
            ("RailYatri", "https://www.railyatri.in/trains-between-stations?from_station_code=MAS&to_station_code=CSTM&journey_date=01-06-2026&src=Chennai+Central&dstn=Mumbai+CSMT"),
        ]

        for name, url in urls:
            print(f"\n{'='*50}")
            print(f"Testing: {name}")
            print(f"URL: {url}")
            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(10000)
                title = await page.title()
                body = await page.evaluate("() => document.body.innerText")
                print(f"Title: {title}")
                print(f"Body length: {len(body)} chars")
                
                # Save text
                safe_name = name.replace(" ", "_").replace("/", "_")
                with open(f"debug_train_{safe_name}.txt", "w", encoding="utf-8") as f:
                    f.write(body)
                
                # Check for train content
                has_express = 'Express' in body or 'Rajdhani' in body or 'Superfast' in body
                has_error = 'oops' in body.lower() or '404' in body.lower() or 'not found' in body.lower()
                print(f"Has train names: {has_express}")
                print(f"Has error: {has_error}")
                
                if has_express and not has_error:
                    print("*** WORKS! ***")
                    # Print first 2000 chars
                    print(f"\nFirst 2000 chars:\n{body[:2000]}")
                    await page.screenshot(path=f"debug_train_{safe_name}.png", full_page=False)
                    break
                else:
                    print(f"Preview: {body[:300]}")
                    
            except Exception as e:
                print(f"Error: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
