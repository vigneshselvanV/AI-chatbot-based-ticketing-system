import asyncio
import io
import sys
from playwright.async_api import async_playwright

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        page = await context.new_page()
        
        # MAS to CSTM on a future date to avoid "past date" errors
        # Date format: DD-MMM-YY e.g., 01-Jun-24
        # But erail works without date too (shows today/tomorrow)
        url = "https://erail.in/trains-between-stations/chennai-central-MAS/mumbai-central-MMCT"
        print(f"Navigating to {url}...")
        
        # Use domcontentloaded
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        
        # We can extract the table
        trains = await page.evaluate("""
            () => {
                const rows = Array.from(document.querySelectorAll('#divTrainsList table tr'));
                // sometimes it's #divTrainsListHeader or just '.TrainList'
                const fallback = Array.from(document.querySelectorAll('table tr'));
                
                return fallback.map(row => {
                    const cols = row.querySelectorAll('td');
                    if (cols.length >= 6) {
                        return Array.from(cols).map(c => c.innerText.trim()).join(' | ');
                    }
                    return null;
                }).filter(Boolean).slice(0, 15);
            }
        """)
        
        if trains:
            print(f"Found {len(trains)} trains.")
            for t in trains:
                print(t)
        else:
            print("No trains found. Dumping some text.")
            text = await page.evaluate("document.body.innerText.substring(0, 1000)")
            print(text)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
