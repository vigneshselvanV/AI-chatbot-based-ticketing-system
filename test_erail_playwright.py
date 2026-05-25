import asyncio
import io
import sys
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = "https://erail.in/trains-between-stations/mas/cstm"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Extract train names
        trains = await page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('#divTrainsListHeader table tr'));
                return rows.slice(1, 6).map(row => {
                    const cols = row.querySelectorAll('td');
                    if (cols.length >= 6) {
                        return cols[1].innerText + " " + cols[3].innerText + "-" + cols[4].innerText;
                    }
                    return row.innerText;
                });
            }
        """)
        print(f"Found {len(trains)} trains.")
        for t in trains:
            print(t)
            
        # If that didn't work, just dump some text
        if not trains:
            text = await page.evaluate("document.body.innerText.substring(0, 1000)")
            print(text)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
