import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def dump_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        await page.goto("https://www.ixigo.com/search/result/flight/DEL/BOM/18052026/1/0/0/e", timeout=45000, wait_until="domcontentloaded")
        try:
            await page.locator("text=₹").first.wait_for(timeout=30000)
            html = await page.content()
            with open("ixigo_flight.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Successfully dumped HTML")
        except Exception as e:
            print("Failed:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_html())
