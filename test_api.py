import asyncio
import httpx
import time
import sys
import io

# Force UTF-8 output on Windows to prevent charmap encoding errors
if sys.platform == "win32" and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


async def test_api():
    url = "http://localhost:8000/search"
    queries = [
        "bus from Chennai to Madurai tomorrow",
        "flight from Delhi to Mumbai tomorrow",
        "train from Coimbatore to Chennai tomorrow",
        "compare all transport modes from Coimbatore to Chennai tomorrow"
    ]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for q in queries:
            print(f"\n--- Testing Query: '{q}' ---")
            start = time.time()
            try:
                response = await client.post(url, json={"query": q})
                data = response.json()
                
                results = data.get("data", [])
                print(f"Time taken: {time.time() - start:.2f} seconds")
                print(f"Found {len(results)} total results!")
                
                if results:
                    modes = [r.get("mode") for r in results]
                    print(f"Modes Breakdown: Flights={modes.count('flight')}, Trains={modes.count('train')}, Buses={modes.count('bus')}")
                    print("Sample Result:")
                    print(results[0])
                    
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
