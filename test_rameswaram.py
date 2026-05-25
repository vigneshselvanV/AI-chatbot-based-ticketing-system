import asyncio
import httpx
import sys
import io

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_api():
    url = "http://localhost:8000/search"
    query = "check trains from rameswaram to coimbatore Tomorrow"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        print(f"--- Testing Query: '{query}' ---")
        try:
            response = await client.post(url, json={"query": query})
            data = response.json()
            
            results = data.get("data", [])
            print(f"Found {len(results)} total results!")
            print(f"Data source: {data.get('data_source')}")
            
            if results:
                print("First Result:")
                print(results[0])
            else:
                print("No results returned!")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
