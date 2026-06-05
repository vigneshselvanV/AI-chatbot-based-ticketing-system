import asyncio
from playwright.async_api import async_playwright
import sys

async def test():
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True)
        page = await browser.new_page()
        try:
            url = 'https://tickets.paytm.com/bus/search/Coimbatore/Chennai/2026-06-04/1'
            print('Navigating to:', url)
            await page.goto(url, timeout=20000)
            
            await asyncio.sleep(5)
            
            html = await page.content()
            if 'Rs' in html or '₹' in html or 'bus' in html.lower():
                print('Found potential buses in HTML!')
            
            buses = await page.evaluate('''() => {
                const items = document.querySelectorAll('.bus-card-wrapper, .card, [class*="BusCard"], .bus-item');
                return Array.from(items).map(item => item.innerText);
            }''')
            print(f'Found {len(buses)} buses')
            if buses:
                print('Sample:', buses[0][:100])
        except Exception as e:
            print('Error:', e)
        await browser.close()

asyncio.run(test())
