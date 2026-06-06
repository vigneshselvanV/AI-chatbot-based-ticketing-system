import asyncio, os, sys
sys.path.insert(0, r'd:\-----projects-----\AI chat bot based ticketing system\one last time - Copy (2)(real data)')
from scrapers import scrape_bus
import dotenv; dotenv.load_dotenv()
async def test():
    buses = await scrape_bus('Rameswaram', 'Chennai', '07-06-2026')
    if isinstance(buses, dict):
        print("Fallback:", buses)
    else:
        for b in buses:
            print(f"{b['operator']} | {b['price']}")
asyncio.run(test())
