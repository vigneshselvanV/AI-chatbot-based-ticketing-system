import asyncio
import io
import sys
from playwright.async_api import async_playwright
from scrapers import _create_stealth_page

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser, page = await _create_stealth_page(p)
        
        url = "https://www.makemytrip.com/railways/listing?isSeo=true&classCode=&date=20260526&destCity=Madurai&destStn=MDU&srcCity=Coimbatore&srcStn=CBE&trainNumber="
        
        print(f"Navigating to: {url}")
        
        # Intercept network to see if there's a JSON API we can use
        async def handle_response(response):
            if "railways/listing" in response.url or "api" in response.url:
                try:
                    if response.status == 200 and "json" in response.headers.get("content-type", ""):
                        print(f"Captured API: {response.url}")
                except:
                    pass
        
        page.on("response", handle_response)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(10000)
            
            # Save screenshot to debug if blocked
            await page.screenshot(path="debug_mmt.png")
            
            # Check for train cards
            trains = await page.evaluate("""
                () => {
                    const cards = Array.from(document.querySelectorAll('.train-name, .train-depart-time, .train-arrival-time, .ticket-price'));
                    return cards.length;
                }
            """)
            print(f"Found {trains} elements matching train data.")
            
            html = await page.content()
            with open("debug_mmt.html", "w", encoding="utf-8") as f:
                f.write(html)
                
            print("Done evaluating.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
