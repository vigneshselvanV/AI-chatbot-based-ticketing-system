import asyncio
from datetime import datetime, timedelta
from scrapers import scrape_bus

async def main():
    test_date = (datetime.now() + timedelta(days=5)).strftime("%d-%m-%Y")
    source = "Coimbatore"
    destination = "Chennai"
    
    attempts = 1
    while True:
        print(f"\n{'='*50}")
        print(f"--- Attempt {attempts} ---")
        print(f"Scraping buses from {source} to {destination} on {test_date}...")
        results = await scrape_bus(source, destination, test_date)
        
        if isinstance(results, list) and len(results) > 0:
            print(f"\n✅ SUCCESS! Found {len(results)} real buses.")
            print("="*50)
            for i, b in enumerate(results[:5], 1):
                print(f"  [{i}] {b.get('operator', 'Unknown')} | {b.get('bus_type', 'Unknown')} | {b.get('price', '--')}")
                print(f"       {b.get('departure', '--')} → {b.get('arrival', '--')}  ({b.get('duration', '--')})")
            break
        elif isinstance(results, dict) and results.get("is_fallback"):
            print("⚠️ Received static fallback due to blocks. Retrying in 5 seconds...")
        else:
            print("❌ No real results or empty. Retrying in 5 seconds...")
            
        attempts += 1
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
