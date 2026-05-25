import asyncio
from scrapers import scrape_flight, scrape_bus, scrape_train
from datetime import datetime, timedelta

async def test_all():
    # Use a date 10 days from today
    test_date = (datetime.now() + timedelta(days=10)).strftime("%d%m%Y")
    test_date_dash = (datetime.now() + timedelta(days=10)).strftime("%d-%m-%Y")
    
    print(f"Testing flight DEL to BOM on {test_date}")
    flight_data = await scrape_flight("DEL", "BOM", test_date)
    print("Flight Data:", flight_data)
    print("-" * 50)
    
    print(f"Testing bus DEL to JAI on {test_date_dash}")
    bus_data = await scrape_bus("delhi", "jaipur", test_date_dash)
    print("Bus Data:", bus_data)
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_all())
