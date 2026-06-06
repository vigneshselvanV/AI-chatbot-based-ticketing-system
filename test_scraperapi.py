"""Quick end-to-end test of the new ScraperAPI scraper."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['SCRAPERAPI_KEY'] = '01ac6fb3a652d4473de473ec4bf256f0'

from scrapers import scrape_bus

async def main():
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    print(f"Testing: Coimbatore -> Chennai on {tomorrow}")
    buses = await scrape_bus("Coimbatore", "Chennai", tomorrow)
    if isinstance(buses, dict):
        print("Got fallback dict:", buses.get('is_fallback'))
        print(buses.get('message'))
    else:
        print(f"\n✅ Got {len(buses)} buses!\n")
        for i, b in enumerate(buses[:5], 1):
            print(f"[{i}] {b['operator']}")
            print(f"     Type: {b['bus_type']}")
            print(f"     {b['departure']} → {b['arrival']} ({b['duration']})")
            print(f"     Price: {b['price']}  Seats: {b['seats_available']}")
            print()
    return buses

asyncio.run(main())
