import asyncio
from datetime import datetime, timedelta
import real_bus_data

async def test():
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    routes = [
        ("Coimbatore", "Chennai"),
        ("Bangalore", "Mumbai"),
        ("Chennai", "Madurai")
    ]
    
    for src, dst in routes:
        print(f"\\n--- Testing {src} -> {dst} ---")
        results = await real_bus_data.scrape_bus(src, dst, tomorrow)
        if isinstance(results, dict) and results.get("is_fallback"):
            print("0 results (Fallback triggered)")
        else:
            print(f"Count: {len(results)}")
            for i, b in enumerate(results[:2]):
                print(f"  {b.get('operator')} | {b.get('price')} INR | {b.get('departure')} -> {b.get('arrival')}")

if __name__ == "__main__":
    asyncio.run(test())
