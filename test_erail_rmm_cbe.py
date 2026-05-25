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
        
        urls = [
            "https://erail.in/trains-between-stations/rmm/cbe",
            "https://erail.in/trains-between-stations/rameswaram-RMM/coimbatore-jn-CBE",
            "https://erail.in/trains-between-stations/rameswaram-RMM/coimbatore-main-jn-CBE"
        ]
        
        for url in urls:
            print(f"\\nTesting URL: {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            
            trains = await page.evaluate("""
                () => {
                    const fallback = Array.from(document.querySelectorAll('table tr'));
                    return fallback.map(row => {
                        const cols = row.querySelectorAll('td');
                        if (cols.length >= 6) {
                            return Array.from(cols).map(c => c.innerText.trim()).join(' | ');
                        }
                        return null;
                    }).filter(Boolean).slice(0, 3);
                }
            """)
            
            if trains:
                for t in trains:
                    print(t)
            else:
                print("No trains found.")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
