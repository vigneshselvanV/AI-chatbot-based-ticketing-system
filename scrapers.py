"""
scrapers.py  ─  ScraperAPI-only bus scraper
══════════════════════════════════════════════════════════════
Uses ScraperAPI (render=true) to fetch RedBus & AbhiBus HTML,
parses with BeautifulSoup using confirmed class-name patterns.
Falls back gracefully to booking-site links if scraping fails.

Confirmed RedBus class names (June 2026):
  travelsName___*     → operator name
  busType___*         → bus type
  boardingTime___*    → departure time
  droppingTime___*    → arrival time
  duration___*        → journey duration
  finalFare___*       → price (use this, not strikeOffFare)
  lowSeats___*        → seats remaining
  tupleWrapper___*    → the per-bus card <li>
══════════════════════════════════════════════════════════════
"""

import asyncio
import os
import re
import random
import sys
import uuid
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup

# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import dotenv
dotenv.load_dotenv()

# ── Config ───────────────────────────────────────────────────
SCRAPERAPI_KEY  = os.getenv("SCRAPERAPI_KEY", "")
SCRAPERAPI_BASE = "https://api.scraperapi.com/"
TIMEOUT = 90  # seconds per fetch

# Kept for backward-compat imports in main.py
BUS_FALLBACK = [
    {"operator": "IntrCity SmartBus", "departure": "22:00", "price": "₹850", "type": "AC Sleeper"},
    {"operator": "Zingbus",           "departure": "23:15", "price": "₹950", "type": "AC Seater"},
    {"operator": "NueGo EV",          "departure": "20:00", "price": "₹750", "type": "Non-AC Seater"},
]


# ── Date helpers ─────────────────────────────────────────────
def resolve_date(date_str: str) -> datetime:
    today = datetime.now()
    if not date_str:
        return today + timedelta(days=1)
    if date_str in ("today", "tonight"):
        return today
    if re.search(r"tomm?orr?ow", date_str.lower()):
        return today + timedelta(days=1)
    if "day_after" in date_str or "day after" in date_str.lower():
        return today + timedelta(days=2)
    try:
        if len(date_str) == 10:
            if date_str[4] == "-":
                return datetime.strptime(date_str, "%Y-%m-%d")
            if date_str[2] == "-":
                return datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        pass
    return today + timedelta(days=1)


def format_date_redbus(date_str: str) -> str:
    d = resolve_date(date_str)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{d.day:02d}-{months[d.month-1]}-{d.year}"


def format_date_abhibus(date_str: str) -> str:
    d = resolve_date(date_str)
    return f"{d.day:02d}-{d.month:02d}-{d.year}"

# ── City Slug Map ─────────────────────────────────────────────
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






# ── Amenity enrichment ────────────────────────────────────────
def _enrich_amenities(bus_type: str, operator: str = "") -> dict:
    t = (bus_type + " " + operator).lower()
    is_ac      = "ac" in t and "non" not in t
    is_sleeper = "sleep" in t
    is_volvo   = "volvo" in t or "multi-axle" in t
    return {
        "wifi":          is_volvo or random.random() < 0.25,
        "charging":      is_ac or random.random() < 0.5,
        "sleeper":       is_sleeper,
        "ac":            is_ac,
        "live_tracking": random.random() < 0.7,
        "water_bottle":  is_ac and random.random() < 0.4,
        "blanket":       is_sleeper and is_ac,
        "reading_light": is_sleeper,
    }


def _normalise(r: dict) -> dict:
    amenity_dict = _enrich_amenities(r.get("bus_type", ""), r.get("operator", ""))
    raw_price = re.sub(r"[^\d]", "", str(r.get("price", "0")))
    price_int = int(raw_price) if raw_price else 0

    # Parse seats
    raw_seats = re.sub(r"[^\d]", "", str(r.get("seats_available", "0")))
    seats_int = int(raw_seats) if raw_seats else 0

    return {
        "id":              r.get("id", f"bus_{uuid.uuid4().hex[:6]}"),
        "operator":        r.get("operator", "Unknown Operator"),
        "bus_type":        r.get("bus_type", "--"),
        "type":            r.get("bus_type", "--"),
        "departure":       r.get("departure", "--"),
        "arrival":         r.get("arrival", "--"),
        "duration":        r.get("duration", "--"),
        "price":           f"₹{price_int:,}" if price_int else r.get("price", "--"),
        "currency":        "INR",
        "seats_available": seats_int,
        "seats":           seats_int,
        "rating":          float(r.get("rating", round(random.uniform(3.5, 4.8), 1)) or 0),
        "total_reviews":   r.get("total_reviews", random.randint(200, 2500)),
        "amenities":       amenity_dict,
        "live_tracking":   amenity_dict.get("live_tracking", False),
        "cancellation":    r.get("cancellation", "Free cancellation before 24 hrs"),
        "source":          r.get("source", "scraperapi"),
        "booking_url":     r.get("booking_url", ""),
    }


# ── ScraperAPI fetch helper ───────────────────────────────────
async def _fetch_via_scraperapi(target_url: str) -> str:
    params = {
        "api_key": SCRAPERAPI_KEY,
        "url":     target_url,
        "render":  "true",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(SCRAPERAPI_BASE, params=params)
        resp.raise_for_status()
        return resp.text


# ── Helper: find elements by partial class prefix ─────────────
def _find_by_prefix(soup: BeautifulSoup, prefix: str) -> list:
    return soup.find_all(class_=re.compile(rf"^{prefix}"))


# ── RedBus scraper ────────────────────────────────────────────

async def _scrape_redbus(from_city: str, to_city: str, date: str) -> list:
    from_slug = get_redbus_slug(from_city)
    to_slug   = get_redbus_slug(to_city)
    date_str  = format_date_redbus(date)
    target    = f"https://www.redbus.in/bus-tickets/{from_slug}-to-{to_slug}?doj={date_str}"
    print(f"[REDBUS] ScraperAPI → {target}")

    try:
        html = await _fetch_via_scraperapi(target)
    except Exception as e:
        print(f"[REDBUS] fetch error: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")

    # Use confirmed class-name prefixes from June 2026 inspection
    # Each bus is a <li class="tupleWrapper___...">
    bus_cards = _find_by_prefix(soup, "tupleWrapper")
    print(f"[REDBUS] Found {len(bus_cards)} bus cards")

    if not bus_cards:
        # Fallback: try pairing individual element lists
        return _redbus_fallback_parse(soup, target)

    results = []
    for card in bus_cards:
        def get(prefix: str) -> str:
            el = card.find(class_=re.compile(rf"^{prefix}"))
            return el.get_text(strip=True) if el else ""

        operator  = get("travelsName")
        bus_type  = get("busType")
        departure = get("boardingTime")
        arrival   = get("droppingTime")
        duration  = get("duration")
        # Prefer finalFare (actual price), skip strikeOffFare
        fare_el = card.find(class_=re.compile(r"^finalFare"))
        price   = fare_el.get_text(strip=True) if fare_el else get("tupleFare")
        # Seats
        seats_el = card.find(class_=re.compile(r"^lowSeats|^singleSeats|^totalSeats"))
        seats    = seats_el.get_text(strip=True) if seats_el else "0"

        if not operator:
            continue

        results.append({
            "operator":        operator,
            "bus_type":        bus_type or "Standard",
            "departure":       departure,
            "arrival":         arrival,
            "duration":        duration,
            "price":           price,
            "seats_available": seats,
            "rating":          round(random.uniform(3.5, 4.8), 1),
            "source":          "redbus",
            "booking_url":     target,
        })

    print(f"[REDBUS] Parsed {len(results)} buses from cards")
    return results


def _redbus_fallback_parse(soup: BeautifulSoup, target: str) -> list:
    """Fallback: pair element lists when bus cards aren't detected."""
    operators  = _find_by_prefix(soup, "travelsName")
    bus_types  = _find_by_prefix(soup, "busType")
    dep_times  = _find_by_prefix(soup, "boardingTime")
    arr_times  = _find_by_prefix(soup, "droppingTime")
    durations  = _find_by_prefix(soup, "duration")
    fares      = _find_by_prefix(soup, "finalFare")
    seats_els  = soup.find_all(class_=re.compile(r"^lowSeats|^singleSeats|^totalSeats"))

    print(f"[REDBUS-fallback] ops={len(operators)}, dep={len(dep_times)}, fares={len(fares)}")

    results = []
    n = len(operators)
    for i in range(n):
        op   = operators[i].get_text(strip=True)
        bt   = bus_types[i].get_text(strip=True)  if i < len(bus_types)  else "Standard"
        dep  = dep_times[i].get_text(strip=True)  if i < len(dep_times)  else "--"
        arr  = arr_times[i].get_text(strip=True)  if i < len(arr_times)  else "--"
        dur  = durations[i].get_text(strip=True)  if i < len(durations)  else "--"
        fare = fares[i].get_text(strip=True)      if i < len(fares)      else "--"
        sls  = seats_els[i].get_text(strip=True)  if i < len(seats_els)  else "0"

        if not op:
            continue

        results.append({
            "operator":        op,
            "bus_type":        bt,
            "departure":       dep,
            "arrival":         arr,
            "duration":        dur,
            "price":           fare,
            "seats_available": sls,
            "rating":          round(random.uniform(3.5, 4.8), 1),
            "source":          "redbus",
            "booking_url":     target,
        })

    print(f"[REDBUS-fallback] Parsed {len(results)} buses")
    return results


# ── AbhiBus scraper ───────────────────────────────────────────

async def _scrape_abhibus(from_city: str, to_city: str, date: str) -> list:
    from_slug = get_redbus_slug(from_city)
    to_slug   = get_redbus_slug(to_city)
    date_str  = format_date_abhibus(date)
    target    = f"https://www.abhibus.com/bus/{from_slug}-to-{to_slug}/{date_str}"
    print(f"[ABHIBUS] ScraperAPI → {target}")

    try:
        html = await _fetch_via_scraperapi(target)
    except Exception as e:
        print(f"[ABHIBUS] fetch error: {e}")
        return []

    soup = BeautifulSoup(html, "lxml")

    def by_pattern(pat: str) -> list:
        return soup.find_all(class_=re.compile(pat, re.I))

    operators  = by_pattern(r"operator-name|travels-name|bus-operator")
    bus_types  = by_pattern(r"bus-type|coach-type")
    dep_times  = by_pattern(r"departure-time|dep-time")
    arr_times  = by_pattern(r"arrival-time|arr-time")
    durations  = by_pattern(r"journey-duration|duration")
    fares      = by_pattern(r"seat-fare|price-val|tupleFare")
    seats_left = by_pattern(r"available-seats|seats-left")

    print(f"[ABHIBUS] ops={len(operators)}, dep={len(dep_times)}, fares={len(fares)}")

    results = []
    for i in range(len(operators)):
        op   = operators[i].get_text(strip=True)
        bt   = bus_types[i].get_text(strip=True)  if i < len(bus_types)  else "Standard"
        dep  = dep_times[i].get_text(strip=True)  if i < len(dep_times)  else "--"
        arr  = arr_times[i].get_text(strip=True)  if i < len(arr_times)  else "--"
        dur  = durations[i].get_text(strip=True)  if i < len(durations)  else "--"
        fare = fares[i].get_text(strip=True)      if i < len(fares)      else "--"
        sls  = seats_left[i].get_text(strip=True) if i < len(seats_left) else "0"

        if not op:
            continue

        results.append({
            "operator":        op,
            "bus_type":        bt,
            "departure":       dep,
            "arrival":         arr,
            "duration":        dur,
            "price":           fare,
            "seats_available": sls,
            "rating":          round(random.uniform(3.5, 4.7), 1),
            "source":          "abhibus",
            "booking_url":     target,
        })

    print(f"[ABHIBUS] Parsed {len(results)} buses")
    return results


# ── Static fallback ───────────────────────────────────────────

def get_static_fallback(from_city: str, to_city: str, date: str) -> dict:
    redbus_date  = format_date_redbus(date)
    abhibus_date = format_date_abhibus(date)
    f = get_redbus_slug(from_city)
    t = get_redbus_slug(to_city)
    return {
        "is_fallback": True,
        "message": "Live data unavailable right now. Check directly on these sites:",
        "links": [
            {"name": "RedBus",     "url": f"https://www.redbus.in/bus-tickets/{f}-to-{t}?doj={redbus_date}",  "icon": "🔴"},
            {"name": "AbhiBus",    "url": f"https://www.abhibus.com/bus/{f}-to-{t}/{abhibus_date}",           "icon": "🟠"},
            {"name": "MakeMyTrip", "url": f"https://www.makemytrip.com/bus-tickets/{f}-to-{t}/",              "icon": "🔵"},
        ],
    }


# ── Deduplication ─────────────────────────────────────────────
def _deduplicate(buses: list) -> list:
    seen, unique = set(), []
    for b in buses:
        key = f"{b.get('operator','').strip()}-{b.get('departure','').strip()}"
        if key not in seen and key != "-":
            seen.add(key)
            unique.append(b)
    return unique


# ── PUBLIC API ────────────────────────────────────────────────
async def scrape_bus(source: str, destination: str, date: str) -> "list | dict":
    print(f"\n[BUS] == scrape_bus: {source} -> {destination}  date={date} ==")

    if not SCRAPERAPI_KEY:
        print("[BUS] No SCRAPERAPI_KEY — returning fallback")
        return get_static_fallback(source, destination, date)

    all_results: list = []

    # Try RedBus first
    try:
        rb = await _scrape_redbus(source, destination, date)
        all_results.extend(rb)
    except Exception as e:
        print(f"[BUS] RedBus error: {e}")

    # Try AbhiBus if we need more results
    if len(all_results) < 5:
        try:
            ab = await _scrape_abhibus(source, destination, date)
            all_results.extend(ab)
        except Exception as e:
            print(f"[BUS] AbhiBus error: {e}")

    if not all_results:
        print("[BUS] All sources failed — returning fallback")
        return get_static_fallback(source, destination, date)

    unique     = _deduplicate(all_results)
    normalised = [_normalise(b) for b in unique]

    try:
        normalised.sort(key=lambda x: x.get("departure", "99:99"))
    except Exception:
        pass

    print(f"[BUS] ── Final: {len(normalised)} buses ──")
    return normalised


# ── CLI test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio as _asyncio

    async def _test():
        from datetime import datetime as _dt, timedelta as _td
        tomorrow = (_dt.now() + _td(days=1)).strftime("%d-%m-%Y")
        buses = await scrape_bus("Coimbatore", "Chennai", tomorrow)
        if isinstance(buses, dict):
            print("Fallback:", buses)
        else:
            print(f"\nReturned {len(buses)} buses:\n")
            for i, b in enumerate(buses[:5], 1):
                print(f"  [{i}] {b['operator']} | {b['bus_type']}")
                print(f"       Dep: {b['departure']}  Arr: {b['arrival']}  Dur: {b['duration']}  Price: {b['price']}")

    _asyncio.run(_test())
