import asyncio
import io
import sys
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.railyatri.in/trains-between-stations?from_station_code=MAS&to_station_code=CSTM&journey_date=01-06-2026&src=Chennai+Central&dstn=Mumbai+Central"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        text = await page.evaluate("document.body.innerText")
        with open("debug_ry.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Done. Check debug_ry.txt")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
