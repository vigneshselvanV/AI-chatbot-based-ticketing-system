import asyncio
from real_bus_data import scrape_bus
from datetime import datetime, timedelta

async def test():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    print(f"Scraping buses for {tomorrow}...")
    result = await scrape_bus("Coimbatore", "Chennai", tomorrow)
    print("Result:")
    for b in result:
        print(b['operator'], b['price'], b['departure'])

asyncio.run(test())
