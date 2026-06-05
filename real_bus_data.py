import re
from datetime import datetime, timedelta
import asyncio
from playwright.async_api import async_playwright

# ════════════════════════════════════════════════════════════
# Cache implementation
# ════════════════════════════════════════════════════════════
CACHE = {}
CACHE_TTL = timedelta(minutes=15)

def get_cached(cache_key):
    if cache_key in CACHE:
        timestamp, data = CACHE[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return data
    return None

def set_cache(cache_key, data):
    CACHE[cache_key] = (datetime.now(), data)

# ════════════════════════════════════════════════════════════
# Data Normalizer
# ════════════════════════════════════════════════════════════
def parse_price_value(price_str):
    if not price_str:
        return 0
    clean = re.sub(r'[^\d]', '', str(price_str))
    return int(clean) if clean else 0

def clean_time(time_str):
    if not time_str:
        return "--:--"
    time_str = time_str.upper().strip()
    match = re.search(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', time_str)
    if not match:
        return time_str
    
    h = int(match.group(1))
    m = int(match.group(2) or 0)
    ampm = match.group(3)
    
    if ampm == 'PM' and h < 12:
        h += 12
    if ampm == 'AM' and h == 12:
        h = 0
        
    return f"{h:02d}:{m:02d}"

def clean_duration(dur_str):
    if not dur_str:
        return "--"
    dur_str = str(dur_str).lower()
    
    h_match = re.search(r'(\d+)\s*(?:h|hrs|hours)', dur_str)
    m_match = re.search(r'(\d+)\s*(?:m|mins|minutes)', dur_str)
    
    if "mins" in dur_str and not h_match and not "h" in dur_str:
        mins = int(re.search(r'(\d+)', dur_str).group(1))
        h = mins // 60
        m = mins % 60
        return f"{h}h {m}m"
        
    h = h_match.group(1) if h_match else "0"
    m = m_match.group(1) if m_match else "0"
    
    if ":" in dur_str and not h_match:
        parts = dur_str.split(":")
        h = parts[0]
        m = parts[1]
        
    return f"{h}h {m}m"

def normalize_bus(b):
    price_val = parse_price_value(b.get('price'))
    dep = clean_time(b.get('departure'))
    operator = b.get('operator', 'Unknown')
    
    # Generate stable ID
    bus_id = f"{b.get('source', 'unknown')}_{operator.replace(' ', '')}_{dep}".lower()
    
    return {
        "id": bus_id,
        "operator": operator,
        "bus_type": b.get("bus_type", "Standard"),
        "departure": dep,
        "arrival": clean_time(b.get("arrival")),
        "arrival_next_day": b.get("arrival_next_day", False),
        "duration": clean_duration(b.get("duration")),
        "price": price_val,
        "currency": "INR",
        "seats_available": int(b.get("seats_available", 0) or 0),
        "rating": float(b.get("rating", 0.0) or 0.0),
        "boarding_point": b.get("boarding_point", "Main Boarding"),
        "dropping_point": b.get("dropping_point", "Main Dropping"),
        "amenities": b.get("amenities", ["WiFi"]),
        "cancellation": b.get("cancellation", False),
        "live_tracking": b.get("live_tracking", False),
        "source": b.get("source", "playwright"),
        "booking_url": b.get("booking_url", "")
    }

# ════════════════════════════════════════════════════════════
# RedBus city slug map
# RedBus uses specific URL slugs that don't always match city names.
# Keys = lowercase aliases users might type; Values = exact RedBus slug
# ════════════════════════════════════════════════════════════
CITY_SLUG_MAP = {
    # Tamil Nadu
    "chennai": "chennai",
    "madras": "chennai",
    "madurai": "madurai",
    "coimbatore": "coimbatore",
    "trichy": "tiruchirappalli",
    "trichy-tiruchirappalli": "tiruchirappalli",
    "tiruchirappalli": "tiruchirappalli",
    "tiruchirapalli": "tiruchirappalli",
    "tiruchy": "tiruchirappalli",
    "salem": "salem",
    "erode": "erode",
    "tirunelveli": "tirunelveli",
    "nellai": "tirunelveli",
    "thoothukudi": "thoothukudi",
    "tuticorin": "thoothukudi",
    "vellore": "vellore",
    "kanchipuram": "kanchipuram",
    "kumbakonam": "kumbakonam",
    "thanjavur": "thanjavur",
    "tanjore": "thanjavur",
    "rameswaram": "rameswaram",
    "rameshwaram": "rameswaram",
    "kodaikanal": "kodaikanal",
    "kodai": "kodaikanal",
    "ooty": "ooty",
    "udagamandalam": "ooty",
    "udhagamandalam": "ooty",
    "theni": "theni",
    "dindigul": "dindigul",
    "nagercoil": "nagercoil",
    "nagarcoil": "nagercoil",
    "kanyakumari": "kanyakumari",
    "cape comorin": "kanyakumari",
    "pondicherry": "pondicherry",
    "puducherry": "pondicherry",
    "pudukkottai": "pudukkottai",
    "namakkal": "namakkal",
    "dharmapuri": "dharmapuri",
    "krishnagiri": "krishnagiri",
    "cuddalore": "cuddalore",
    "nagapattinam": "nagapattinam",
    "sivaganga": "sivaganga",
    "ramanathapuram": "ramanathapuram",
    "virudhunagar": "virudhunagar",
    "tiruppur": "tiruppur",
    "karur": "karur",
    "perambalur": "perambalur",
    "ariyalur": "ariyalur",
    "chidambaram": "chidambaram",
    "villupuram": "villupuram",
    "tindivanam": "tindivanam",
    "hosur": "hosur",
    "ambur": "ambur",
    "vellore": "vellore",
    "ranipet": "ranipet",
    "tiruvannamalai": "tiruvannamalai",
    "tiruvannamalai": "tiruvannamalai",
    "kallakurichi": "kallakurichi",
    "tenkasi": "tenkasi",
    "sattur": "sattur",
    "sivakasi": "sivakasi",
    "paramakudi": "paramakudi",
    "karaikudi": "karaikudi",
    "musiri": "musiri",
    "palani": "palani",
    "pollachi": "pollachi",
    "valparai": "valparai",
    "mettupalayam": "mettupalayam",
    "gudalur": "gudalur",
    "coonoor": "coonoor",
    "yercaud": "yercaud",
    "kotagiri": "kotagiri",
    "tambaram": "tambaram",
    "avadi": "avadi",
    "ambattur": "ambattur",
    "tiruvallur": "tiruvallur",
    "mahabalipuram": "mahabalipuram",
    "mamallapuram": "mahabalipuram",
    "velankanni": "velankanni",
    "pattukottai": "pattukottai",

    # Karnataka
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "bengalore": "bengaluru",
    "mysore": "mysuru",
    "mysuru": "mysuru",
    "hubli": "hubballi",
    "hubballi": "hubballi",
    "dharwad": "dharwad",
    "mangalore": "mangaluru",
    "mangaluru": "mangaluru",
    "shimoga": "shivamogga",
    "shivamogga": "shivamogga",
    "belgaum": "belagavi",
    "belagavi": "belagavi",
    "bellary": "ballari",
    "ballari": "ballari",
    "tumkur": "tumakuru",
    "tumakuru": "tumakuru",
    "hassan": "hassan",
    "mandya": "mandya",
    "chikmagalur": "chikkamagaluru",
    "chikkamagaluru": "chikkamagaluru",
    "udupi": "udupi",
    "gulbarga": "kalaburagi",
    "kalaburagi": "kalaburagi",
    "bidar": "bidar",
    "hospet": "hospet",
    "hampi": "hampi",
    "bagalkot": "bagalkot",
    "bijapur": "vijayapura",
    "vijayapura": "vijayapura",
    "raichur": "raichur",
    "koppal": "koppal",
    "gadag": "gadag",
    "haveri": "haveri",
    "davanagere": "davanagere",
    "davangere": "davanagere",
    "chitradurga": "chitradurga",
    "kolar": "kolar",
    "bangalore airport": "bengaluru",
    "yelahanka": "bengaluru",

    # Kerala
    "thiruvananthapuram": "thiruvananthapuram",
    "trivandrum": "thiruvananthapuram",
    "kochi": "kochi",
    "cochin": "kochi",
    "ernakulam": "kochi",
    "kozhikode": "kozhikode",
    "calicut": "kozhikode",
    "thrissur": "thrissur",
    "trichur": "thrissur",
    "kollam": "kollam",
    "quilon": "kollam",
    "kottayam": "kottayam",
    "palakkad": "palakkad",
    "palghat": "palakkad",
    "alappuzha": "alappuzha",
    "alleppey": "alappuzha",
    "kannur": "kannur",
    "cannanore": "kannur",
    "malappuram": "malappuram",
    "kasaragod": "kasaragod",
    "idukki": "idukki",
    "munnar": "munnar",
    "thekkady": "thekkady",
    "periyar": "thekkady",
    "wayanad": "wayanad",
    "varkala": "varkala",
    "kovalam": "thiruvananthapuram",

    # Andhra Pradesh & Telangana
    "hyderabad": "hyderabad",
    "secunderabad": "hyderabad",
    "vijayawada": "vijayawada",
    "visakhapatnam": "visakhapatnam",
    "vizag": "visakhapatnam",
    "tirupati": "tirupati",
    "guntur": "guntur",
    "nellore": "nellore",
    "warangal": "warangal",
    "karimnagar": "karimnagar",
    "rajahmundry": "rajahmundry",
    "kakinada": "kakinada",
    "kurnool": "kurnool",
    "ongole": "ongole",
    "anantapur": "anantapur",
    "kadapa": "kadapa",
    "cuddapah": "kadapa",
    "nizamabad": "nizamabad",
    "khammam": "khammam",
    "nalgonda": "nalgonda",

    # Other major cities
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "pune": "pune",
    "nagpur": "nagpur",
    "delhi": "delhi",
    "new delhi": "delhi",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "ahmedabad": "ahmedabad",
    "surat": "surat",
    "jaipur": "jaipur",
    "lucknow": "lucknow",
    "kanpur": "kanpur",
    "bhopal": "bhopal",
    "indore": "indore",
    "patna": "patna",
    "guwahati": "guwahati",
    "bhubaneswar": "bhubaneswar",
    "raipur": "raipur",
    "chandigarh": "chandigarh",
    "dehradun": "dehradun",
    "shimla": "shimla",
    "goa": "goa",
    "panaji": "goa",
    "madgaon": "goa",
    "margao": "goa",
    "coorg": "madikeri",
    "madikeri": "madikeri",
}

def get_redbus_slug(city: str) -> str:
    """Convert any city name/alias to the correct RedBus URL slug."""
    city_lower = city.lower().strip()
    # Direct lookup
    if city_lower in CITY_SLUG_MAP:
        return CITY_SLUG_MAP[city_lower]
    # Partial match — find if any key is contained in city_lower
    for key, slug in CITY_SLUG_MAP.items():
        if key in city_lower or city_lower in key:
            return slug
    # Fallback: use the city name itself (lowercase, spaces replaced with hyphens)
    return city_lower.replace(" ", "-")


# ════════════════════════════════════════════════════════════
# Scrapers
# ════════════════════════════════════════════════════════════


async def strategyB_RedBus(from_city: str, to_city: str, date: str) -> list:
    from_slug = get_redbus_slug(from_city)
    to_slug = get_redbus_slug(to_city)
    url = f"https://www.redbus.in/bus-tickets/{from_slug}-to-{to_slug}?doj={date}"
    results = []
    print(f"[REDBUS] Navigating to: {url}")
    
    captured_data = None
    
    import os
    scraper_key = os.getenv("SCRAPERAPI_KEY")
    proxy = {"server": "http://proxy-server.scraperapi.com:8001", "username": "scraperapi", "password": scraper_key} if scraper_key else None
    
    async with async_playwright() as pw:
        # headless=True is required for Render. ScraperAPI proxy bypasses the bot detection.
        browser = await pw.chromium.launch(
            headless=True, 
            proxy=proxy,
            args=['--disable-http2', '--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        async def handle_response(response):
            nonlocal captured_data
            if "searchResults" in response.url and "api" in response.url:
                try:
                    data = await response.json()
                    if "data" in data and "inventories" in data["data"]:
                        captured_data = data
                except:
                    pass

        page.on("response", handle_response)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait a few seconds for API response
            import asyncio
            for _ in range(10):
                if captured_data:
                    break
                await asyncio.sleep(1)
            
            if captured_data and "data" in captured_data and "inventories" in captured_data["data"]:
                inv = captured_data["data"]["inventories"]
                for b in inv:
                    departure = b.get("departureTime", "2026-06-04 20:00:00").split(" ")[1][:5] if b.get("departureTime") else "20:00"
                    arrival = b.get("arrivalTime", "2026-06-05 06:00:00").split(" ")[1][:5] if b.get("arrivalTime") else "06:00"
                    dur_min = b.get("journeyDurationMin", 600)
                    duration = f"{dur_min // 60}h {dur_min % 60}m"
                    price = b.get("fareList", [800])[0] if b.get("fareList") else 800
                    
                    results.append({
                        "operator": b.get("travelsName", "Unknown Operator"),
                        "bus_type": b.get("busType", "AC Sleeper"),
                        "departure": departure,
                        "arrival": arrival,
                        "duration": duration,
                        "price": str(price),
                        "seats_available": b.get("availableSeats", 15),
                        "rating": float(b.get("totalRatings", 0.0) or 0.0),
                        "source": "redbus"
                    })
            
            print(f"[REDBUS] Success! Scraped {len(results)} buses directly via API.")
            
        except Exception as e:
            print(f"[REDBUS] Error: {e}")
        finally:
            await browser.close()
            
    return results

async def strategyC_AbhiBus(from_city: str, to_city: str, date: str) -> list:
    from_slug = from_city.lower().replace(" ", "-")
    to_slug = to_city.lower().replace(" ", "-")
    
    # Date mapping: DD-MM-YYYY
    parts = date.split('-')
    if len(parts) == 3 and len(parts[0]) == 4: # YYYY-MM-DD
        date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
    else:
        date_str = date

    url = f"https://www.abhibus.com/bus/{from_slug}-to-{to_slug}/{date_str}"
    
    print(f"[ABHIBUS] Navigating to: {url}")
    results = []
    
    import os
    scraper_key = os.getenv("SCRAPERAPI_KEY")
    proxy = {"server": "http://proxy-server.scraperapi.com:8001", "username": "scraperapi", "password": scraper_key} if scraper_key else None
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True, 
            proxy=proxy,
            args=['--disable-http2', '--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            try:
                await page.wait_for_selector(".search-result-item, .bus-card, .card", timeout=15000)
            except:
                pass
                
            buses = await page.evaluate('''() => {
                const items = document.querySelectorAll('.search-result-item, .bus-card-item, .card');
                return Array.from(items).map(item => {
                    const getText = sel => item.querySelector(sel)?.innerText?.trim() || '';
                    return {
                        operator: getText('.operator-name, .bus-operator, .travels-name, h5'),
                        bus_type: getText('.bus-type, .coach-type, .bus-info p'),
                        departure: getText('.departure-time, .dep-time, .time-info span:first-child'),
                        arrival: getText('.arrival-time, .arr-time, .time-info span:last-child'),
                        duration: getText('.journey-duration, .duration'),
                        price: getText('.seat-fare, .price-val, .fare, h4'),
                        seats_available: parseInt(getText('.available-seats, .seats-left')) || 15,
                        rating: parseFloat(getText('.rating-value, .rating')) || 4.0,
                        cancellation: true,
                        live_tracking: false,
                        source: "abhibus"
                    };
                });
            }''')
            
            for b in buses:
                if b.get('operator') and b.get('price'):
                    results.append(b)
                    
        except Exception as e:
            print(f"[ABHIBUS] Error: {e}")
        finally:
            await browser.close()
            
    return results

async def strategyD_MakeMyTrip(from_city: str, to_city: str, date: str) -> list:
    return []

async def strategyE_GoIbibo(from_city: str, to_city: str, date: str) -> list:
    return []

async def strategyF_Paytm(from_city: str, to_city: str, date: str) -> list:
    return []

async def scrape_bus(from_city: str, to_city: str, date: str) -> list | dict:
    cache_key = f"{from_city}_{to_city}_{date}"
    cached_data = get_cached(cache_key)
    if cached_data:
        print("[CACHE] Returning cached results.")
        return cached_data

    strategies = [
        ("B", strategyB_RedBus),
        ("C", strategyC_AbhiBus)
    ]
    
    all_results = []
    
    for name, strategy in strategies:
        print(f"[STRATEGY {name}] Starting...")
        try:
            res = await strategy(from_city, to_city, date)
            if res and len(res) > 0:
                print(f"[STRATEGY {name}] Success: {len(res)} results.")
                all_results.extend(res)
                break  # Stop at first successful strategy as per instructions
        except Exception as e:
            print(f"[STRATEGY {name}] Failed: {e}")
            
    if not all_results:
        return {"is_fallback": True}
        
    # Deduplicate based on operator + departure
    seen = set()
    unique = []
    for b in all_results:
        key = f"{b.get('operator')}_{b.get('departure')}"
        if key not in seen:
            seen.add(key)
            unique.append(b)
            
    normalized = [normalize_bus(b) for b in unique]
    
    # Store in cache
    set_cache(cache_key, normalized)
    
    return normalized
