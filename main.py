import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from real_bus_data import scrape_bus
from scrapers import BUS_FALLBACK, scrape_bus as _unused_scrape_bus

# ═══════════════════════════════════════════
# Known Connecting Routes (for smart suggestions)
# ═══════════════════════════════════════════
CONNECTING_ROUTES = {
    ("coimbatore", "ooty"): ["mettupalayam"],
    ("chennai", "kodaikanal"): ["dindigul"],
    ("madurai", "rameswaram"): ["ramanathapuram"],
    ("bangalore", "coorg"): ["mysore"],
    ("bengaluru", "coorg"): ["mysore"],
    ("trichy", "yercaud"): ["salem"],
    ("tiruchirapalli", "yercaud"): ["salem"],
    ("chennai", "ooty"): ["coimbatore"],
    ("bangalore", "ooty"): ["mysore"],
    ("bengaluru", "ooty"): ["mysore"],
    ("chennai", "munnar"): ["kochi"],
    ("madurai", "kodaikanal"): ["dindigul"],
    ("coimbatore", "kodaikanal"): ["dindigul"],
    ("bangalore", "wayanad"): ["mysore"],
    ("bengaluru", "wayanad"): ["mysore"],
}

def find_connecting_route(source: str, destination: str):
    """Check if a connecting route exists for this pair."""
    src_lower = source.lower().strip()
    dst_lower = destination.lower().strip()
    stops = CONNECTING_ROUTES.get((src_lower, dst_lower))
    if stops:
        return stops[0]  # Return first intermediate stop
    return None

import os
import random
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

app = FastAPI(title="AI Chat Bot Based Ticketing System Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    context: dict | None = None  # For follow-up conversations
    history: list | None = None

# ═══════════════════════════════════════════
# City Sanitizer
# ═══════════════════════════════════════════
def city_name(name: str) -> str:
    return name.strip().title()

def parse_price(price_str: str) -> int:
    if not price_str or price_str == '--':
        return 999999
    try:
        # Remove currency symbols (e.g. ₹), commas, and whitespace
        clean = re.sub(r'[^\d]', '', price_str)
        return int(clean) if clean else 999999
    except Exception:
        return 999999


# ═══════════════════════════════════════════
# Today's date helper
# ═══════════════════════════════════════════
def get_today_str():
    return datetime.now().strftime("%d-%m-%Y")

def get_tomorrow_str():
    return (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")

def resolve_relative_date(query: str, extracted_date: str = None) -> str:
    """Aggressively parse relative dates from raw query text."""
    query_lower = query.lower()
    
    # Catch day after tomorrow
    if "day after tomorrow" in query_lower or "day after tommorow" in query_lower:
        return (datetime.now() + timedelta(days=2)).strftime("%d-%m-%Y")
    
    # Catch tomorrow and its typos
    if re.search(r'tomm?orr?ow', query_lower):
        return get_tomorrow_str()
        
    # Catch today
    if "today" in query_lower or "tonight" in query_lower:
        return get_today_str()
        
    return extracted_date

# ═══════════════════════════════════════════
# Booking URL Generator
# ═══════════════════════════════════════════
def generate_booking_url(mode: str, source: str, destination: str, date: str, ticket: dict) -> str:
    """Generate a redirect URL to the booking website for a specific ticket."""
    src_slug = source.lower().strip().replace(" ", "-")
    dst_slug = destination.lower().strip().replace(" ", "-")
    src_title = source.strip().title()
    dst_title = destination.strip().title()

    # Parse date
    day, month, year = "01", "06", "2026"
    if date and len(date) == 10:
        if date[4] == "-":
            year, month, day = date.split("-")
        elif date[2] == "-":
            day, month, year = date.split("-")

    month_names = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
    }
    month_name = month_names.get(month, "Jun")

    # Booking URL Generation based on source
    source_platform = ticket.get("source", "redbus").lower() if ticket else "redbus"
    
    if source_platform == "abhibus":
        abhibus_date = f"{day}-{month}-{year}"
        return f"https://www.abhibus.com/bus/{src_slug}-to-{dst_slug}/{abhibus_date}"
        
    elif source_platform == "makemytrip" or source_platform == "mmt":
        return f"https://www.makemytrip.com/bus-tickets/{src_slug}-to-{dst_slug}/"
        
    elif source_platform == "goibibo":
        return f"https://www.goibibo.com/bus/{src_slug}-to-{dst_slug}-bus/"
        
    elif source_platform == "paytm":
        paytm_date = f"{day}-{month}-{year}"
        return f"https://tickets.paytm.com/bus/search/{src_slug}/{dst_slug}/{paytm_date}/1"
        
    else:
        # Default to RedBus
        redbus_date = f"{int(day)}-{month_name}-{year}"
        return f"https://www.redbus.in/bus-tickets/{src_slug}-to-{dst_slug}?doj={redbus_date}"

# ═══════════════════════════════════════════
# Bulletproof JSON Extractor
# ═══════════════════════════════════════════
def extract_json_from_text(raw_text: str) -> dict:
    if not raw_text:
        return {}
    # Remove thinking tags
    raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL)
    try:
        # First try to find a markdown json block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Then try to just find the first { and last }
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start:end+1])
        return {}
    except (json.JSONDecodeError, Exception) as e:
        print("JSON parse error:", e)
        return {}

# ═══════════════════════════════════════════
# LLM Integration (Multi-Model Cascade)
# ═══════════════════════════════════════════

FALLBACK_MODELS = [
    "nousresearch/hermes-3-llama-3.1-405b:free" 
]

def rule_based_parser(text: str, history: list) -> dict:
    lower_text = text.lower()
    cities = [
        # Tamil Nadu
        "tiruchirapalli", "tiruchirappalli", "tiruchirapalli",
        "coimbatore", "chennai", "madurai", "trichy", "tiruchy", "salem",
        "ooty", "kodaikanal", "pondicherry", "puducherry", "theni",
        "rameswaram", "rameshwaram", "tirunelveli", "kanyakumari",
        "vellore", "pollachi", "tuticorin", "thoothukudi", "erode",
        "dindigul", "nagercoil", "nagarcoil", "thanjavur", "tanjore",
        "kumbakonam", "karur", "namakkal", "dharmapuri", "krishnagiri",
        "cuddalore", "nagapattinam", "sivaganga", "ramanathapuram",
        "virudhunagar", "tiruppur", "sivakasi", "karaikudi", "palani",
        "mettupalayam", "coonoor", "yercaud", "velankanni", "hosur",
        "ambur", "ranipet", "tiruvannamalai", "villupuram", "tindivanam",
        "mahabalipuram", "mamallapuram", "chidambaram", "tenkasi",
        # Karnataka
        "bangalore", "bengaluru", "mysore", "mysuru", "hubli", "hubballi",
        "mangalore", "mangaluru", "shimoga", "shivamogga", "belgaum",
        "belagavi", "tumkur", "tumakuru", "hassan", "mandya", "udupi",
        "gulbarga", "kalaburagi", "davanagere", "davangere", "chitradurga",
        "hospet", "hampi", "bagalkot", "raichur", "chikmagalur", "coorg",
        "madikeri",
        # Kerala
        "kochi", "cochin", "thiruvananthapuram", "trivandrum", "kozhikode",
        "calicut", "thrissur", "trichur", "kollam", "kottayam", "palakkad",
        "alappuzha", "alleppey", "kannur", "malappuram", "munnar",
        "thekkady", "wayanad", "varkala",
        # Andhra & Telangana
        "hyderabad", "secunderabad", "vijayawada", "visakhapatnam", "vizag",
        "tirupati", "guntur", "nellore", "warangal", "karimnagar",
        "rajahmundry", "kakinada", "kurnool", "anantapur", "kadapa",
        # Other major cities
        "mumbai", "pune", "nagpur", "delhi", "kolkata", "ahmedabad",
        "surat", "jaipur", "lucknow", "bhopal", "indore", "patna",
        "guwahati", "bhubaneswar", "raipur", "chandigarh", "goa",
        "panaji", "shimla", "dehradun",
    ]

    
    found_cities = []
    import re
    # Sort cities by length descending to match longest first (e.g. tiruchirapalli before trichy)
    sorted_cities = sorted(cities, key=len, reverse=True)
    
    # Find all occurrences of cities in text and store their positions
    occurrences = []
    for c in sorted_cities:
        for match in re.finditer(r'\b' + re.escape(c) + r'\b', lower_text):
            occurrences.append((match.start(), c))
            
    # Sort occurrences by their position in the text
    occurrences.sort(key=lambda x: x[0])
    
    # Remove duplicates that might be substrings
    seen = set()
    for pos, c in occurrences:
        if not any(c in seen_c or seen_c in c for seen_c in seen):
            found_cities.append(c)
            seen.add(c)
            
    # Attempt to intelligently map from/to based on 'from' and 'to' keywords
    from_city = None
    to_city = None
    
    if "from" in lower_text and "to" in lower_text:
        from_idx = lower_text.find("from")
        to_idx = lower_text.find("to")
        # Try to match cities based on position relative to from/to
        for pos, c in occurrences:
            if from_idx < to_idx:
                if pos > from_idx and pos < to_idx and not from_city:
                    from_city = c
                elif pos > to_idx and not to_city:
                    to_city = c
            else:
                if pos > to_idx and pos < from_idx and not to_city:
                    to_city = c
                elif pos > from_idx and not from_city:
                    from_city = c

    # Fallback to positional assignment if from/to keywords didn't map perfectly
    if not from_city and len(found_cities) > 0:
        from_city = found_cities[0]
        if from_city == to_city: from_city = None
    if not to_city and len(found_cities) > 1:
        to_city = [c for c in found_cities if c != from_city][0]
        
    date = None
    if "today" in lower_text or "இன்று" in lower_text or "aaj" in lower_text: date = "today"
    if re.search(r'tomm?orr?ow', lower_text) or "நாளை" in lower_text or "kal" in lower_text: date = "tomorrow"
    if "day after" in lower_text: date = "day_after_tomorrow"
    if "weekend" in lower_text: date = "this_weekend"
    filter_val = None
    if "ac" in lower_text or "a/c" in lower_text: filter_val = "ac"
    if "sleeper" in lower_text: filter_val = "sleeper"
    if "non ac" in lower_text or "non-ac" in lower_text: filter_val = "non_ac"
    if "volvo" in lower_text: filter_val = "volvo"
    if "cheapest" in lower_text or "cheap" in lower_text: filter_val = "cheapest"
    if "fastest" in lower_text or "fast" in lower_text: filter_val = "fastest"
    if "night" in lower_text: filter_val = "night"

    sort_by_val = None
    if "cheapest" in lower_text: sort_by_val = "price_asc"
    elif "fastest" in lower_text: sort_by_val = "duration_asc"
    
    collected = {
        "from_city": from_city,
        "to_city": to_city,
        "date": date,
        "passengers": 1,
        "filter": filter_val,
        "sort_by": sort_by_val
    }

    missing = []
    if not collected["from_city"]: missing.append("from_city")
    if not collected["to_city"]: missing.append("to_city")
    if not collected["date"]: missing.append("date")

    ready_to_search = len(missing) == 0
    field_to_ask = missing[0] if missing else None

    # Detect conversational questions
    question_keywords = ["what", "how", "why", "who", "tell me", "can you", "famous"]
    is_question = any(kw in lower_text for kw in question_keywords)
    
    if is_question and len(found_cities) <= 1 and not ready_to_search:
        return {
            "message": "I only handle bus ticket bookings! 🚌 Where would you like to travel?",
            "intent": "REDIRECT",
            "collected": collected,
            "missing": missing,
            "ready_to_search": False,
            "quick_replies": [],
            "field_to_ask": "from_city",
            "source": "rule_based"
        }

    messages = {
        "from_city": "Where are you traveling from? 🚌",
        "to_city": "Where are you traveling to?",
        "date": "What date would you like to travel? 📅"
    }

    return {
        "message": f"Searching buses from {collected['from_city']} to {collected['to_city']}... 🔍" if ready_to_search else messages.get(field_to_ask, "How can I help you?"),
        "intent": "SEARCH" if ready_to_search else "COLLECT",
        "collected": collected,
        "missing": missing,
        "ready_to_search": ready_to_search,
        "quick_replies": ["Tomorrow", "Day After", "This Weekend"] if field_to_ask == "date" else [],
        "field_to_ask": field_to_ask,
        "source": "rule_based"
    }

import asyncio
import httpx
import json

async def call_ai(user_message: str, history: list, system_prompt: str, retry_count: int = 0) -> dict:
    if retry_count >= len(FALLBACK_MODELS):
        print("All AI failed → Using rule-based parser")
        return rule_based_parser(user_message, history)
        
    current_model = FALLBACK_MODELS[retry_count]
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-OpenRouter-Title": "BusBot AI"
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-4:]:
            if isinstance(msg, dict):
                role = "user" if msg.get("type") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("text", "")})
            elif isinstance(msg, str):
                messages.append({"role": "user", "content": msg})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": current_model,
        "max_tokens": 300,
        "temperature": 0.1,
        "messages": messages
    }
    
    # Sanitize payload to fix utf-8 surrogate errors on Windows
    def sanitize(obj):
        if isinstance(obj, str):
            return obj.encode('utf-16', 'surrogatepass').decode('utf-16')
        elif isinstance(obj, list):
            return [sanitize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        return obj
        
    payload = sanitize(payload)
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 429:
                print(f"Rate limit on {current_model}, waiting 3s...")
                await asyncio.sleep(3)
                return await call_ai(user_message, history, system_prompt, retry_count + 1)
                
            if response.status_code in [500, 502, 503, 504]:
                print(f"{current_model} unavailable, trying fallback...")
                return await call_ai(user_message, history, system_prompt, retry_count + 1)
                
            data = response.json()
            if not data.get("choices") or not data["choices"][0].get("message", {}).get("content"):
                raise Exception("Empty response from AI")
                
            raw_content = data["choices"][0]["message"]["content"]
            
            parsed = extract_json_from_text(raw_content)
            
            if not parsed or "message" not in parsed or "intent" not in parsed:
                raise Exception("Invalid JSON structure")
                
            return parsed
            
    except (httpx.TimeoutException, httpx.RequestError) as e:
        print(f"Network timeout ({current_model}): {e} → retrying next model")
        return await call_ai(user_message, history, system_prompt, retry_count + 1)
    except Exception as e:
        print(f"AI Error ({current_model}): {e} → retrying next model")
        return await call_ai(user_message, history, system_prompt, retry_count + 1)

def filter_and_sort_buses(buses, filter_type, sort_by):
    if not buses:
        return []

    filtered = list(buses)

    # APPLY FILTER
    if filter_type == "ac":
        filtered = [
            b for b in filtered
            if any(k in (b.get("bus_type","") + b.get("busType","")).lower()
                   for k in ["a/c","ac ","air"])
        ]
    elif filter_type == "sleeper":
        filtered = [
            b for b in filtered
            if "sleeper" in (b.get("bus_type","") + b.get("busType","")).lower()
        ]
    elif filter_type == "non_ac":
        filtered = [
            b for b in filtered
            if any(k in (b.get("bus_type","") + b.get("busType","")).lower()
                   for k in ["non-a/c","non ac", "non-ac"])
        ]
    elif filter_type == "volvo":
        filtered = [
            b for b in filtered
            if "volvo" in (b.get("bus_type","") + b.get("operator","")).lower()
        ]
    elif filter_type == "night":
        def is_night(b):
            dep = b.get("departure","00:00")
            try:
                hour = int(dep.split(":")[0])
                return hour >= 20 or hour <= 5
            except:
                return False
        filtered = [b for b in filtered if is_night(b)]

    # If filter removed all → use original
    if len(filtered) == 0:
        filtered = list(buses)

    # APPLY SORT
    def safe_price(b):
        try:
            p = str(b.get("price", b.get("fare","9999")))
            return int(''.join(c for c in p if c.isdigit()) or 9999)
        except:
            return 9999

    def safe_duration(b):
        try:
            d = b.get("duration", b.get("dur","999h"))
            hours = 0
            mins  = 0
            if "h" in d:
                parts = d.replace("h",":").replace("m","").split(":")
                hours = int(parts[0])
                mins  = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + mins
        except:
            return 999

    def safe_rating(b):
        try:
            return float(b.get("rating",0) or 0)
        except:
            return 0

    if sort_by == "price_asc":
        filtered.sort(key=safe_price)
    elif sort_by == "price_desc":
        filtered.sort(key=safe_price, reverse=True)
    elif sort_by == "duration_asc":
        filtered.sort(key=safe_duration)
    elif sort_by == "rating_desc":
        filtered.sort(key=safe_rating, reverse=True)
    elif sort_by == "departure_desc":
        filtered.sort(key=lambda b: b.get("departure","00:00"), reverse=True)
    else:  # departure_asc (default)
        filtered.sort(key=lambda b: b.get("departure","00:00"))

    return filtered

# ═══════════════════════════════════════════
# /search Endpoint — Smart Conversational Router
# ═══════════════════════════════════════════
@app.post("/search")
async def search_tickets(request: SearchRequest):
    print(f"Received query: {request.query}")
    
    query_lower = request.query.strip().lower()
    is_pure_greeting = query_lower in ["hi", "hello", "hey", "start", "busbot"]
    if is_pure_greeting and not request.context:
        return {
            "type": "chat",
            "message": "Hey! 👋 Where are you traveling from? 🚌"
        }
        
    bus_redirect_msg = "I only handle bus ticket bookings! 🚌"
    if "flight" in query_lower or "fly" in query_lower or "train" in query_lower:
        pass  # Handled by AI intent

    
    system_intent = '''You are BusBot, an AI Bus Ticket Assistant.
ONLY help with bus bookings. Never mention flights or trains.

════════════════════════════════
RESPONSE RULES (MUST FOLLOW)
════════════════════════════════
1. ALWAYS respond in this EXACT JSON format:
{
  "message": "your reply to user",
  "intent": "GREET|COLLECT|SEARCH|REDIRECT|ERROR",
  "collected": {
    "from_city": null,
    "to_city": null,
    "date": null,
    "passengers": 1,
    "filter": null,
    "sort_by": null
  },
  "missing": ["from_city","to_city","date"],
  "ready_to_search": false,
  "quick_replies": ["option1","option2","option3"],
  "field_to_ask": "from_city"
}
2. NEVER include text outside JSON.
3. NEVER add markdown, backticks, or explanation.
4. Keep "message" under 30 words always.
5. NEVER ask more than ONE question per response.

════════════════════════════════
GREETING RULE
════════════════════════════════
IF intent = GREET (hi/hello/hey/start):
{
  "message": "Hey! 👋 Where are you traveling from?",
  "intent": "GREET",
  "collected": {
    "from_city": null,
    "to_city": null,
    "date": null,
    "passengers": 1,
    "filter": null,
    "sort_by": null
  },
  "missing": ["from_city","to_city","date"],
  "ready_to_search": false,
  "quick_replies": [],
  "field_to_ask": "from_city"
}

════════════════════════════════
PROGRESSIVE FORM FILLING
════════════════════════════════
Collect ONLY what is missing. ONE field at a time.
NEVER re-ask what user already gave.
PRIORITY ORDER of asking:
  1st → from_city
  2nd → to_city
  3rd → date

FIELD QUESTION TEMPLATES:
  from_city  → "Where are you traveling from? 🚌"
  to_city    → "Where are you traveling to?"
  date       → "What date? 📅"
               quick_replies: ["Tomorrow","Day After","This Weekend"]

IF all 3 required fields collected:
  Set "ready_to_search": true
  Set "intent": "SEARCH"
  message: "Searching buses... 🔍"

════════════════════════════════
ENTITY EXTRACTION RULES
════════════════════════════════
Extract from user message:
  Cities    → Any Indian city names
  Date      → today/tomorrow/day after/DD-MM-YYYY

City Aliases (map these):
  கோவை / Kovai          → Coimbatore
  சென்னை                → Chennai
  மதுரை                 → Madurai
  Bombay / Mumbai        → Mumbai
  Bangalore / Bengaluru  → Bengaluru
  Madras                 → Chennai
  Trichy                 → Tiruchirappalli
  Pondy                  → Pondicherry
  Rameshwaram            → Rameswaram

Date Aliases:
  today          → current date
  tomorrow       → current date + 1
  day after      → current date + 2
  this weekend   → nearest Saturday
  tonight        → current date (evening)

Languages to understand:
  Tamil, Hindi, Telugu, Kannada, English
  Always respond in English JSON only.

════════════════════════════════
REDIRECT RULES (BUS ONLY)
════════════════════════════════
IF user asks for train/flight:
  Extract their route from the query.
  Pre-fill those cities.
  Only ask for the missing field.
  ALWAYS start your message with exactly: "I only do bus bookings! 🚌"
  NEVER say "I cannot help with that."
  ALWAYS redirect and keep the conversation going.

════════════════════════════════
ERROR RESPONSE FORMAT OR OUT-OF-SCOPE
════════════════════════════════
IF you cannot understand the query, or if the user asks a general question (like 'what is famous', 'how to', etc):
{
  "message": "I only handle bus ticket bookings! \ud83d\ude8c Where would you like to travel?",
  "intent": "REDIRECT",
  "collected": {
    "from_city": null, "to_city": null, "date": null, "passengers": 1, "filter": null, "sort_by": null
  },
  "missing": ["from_city","to_city","date"],
  "ready_to_search": false,
  "quick_replies": [],
  "field_to_ask": "from_city"
}
NEVER expose error messages to the user.
NEVER say "503" or "OpenRouter" or "AI error".

════════════════════════════════
FILTER AND SORT DETECTION RULES
════════════════════════════════
When the user message contains filter keywords,
set filter and sort_by in the collected object.

Keywords → filter → sort_by mapping:
  cheapest/cheap/budget/affordable/low cost/
  minimum fare/best price/lowest/மலிவான/सस्ता
  → filter: "cheapest", sort_by: "price_asc"

  ac bus/air conditioned/ac coach/air-con/
  ac only/குளிர்/एसी
  → filter: "ac", sort_by: "price_asc"

  sleeper/sleeping/sleep bus/berth/
  overnight bus/ஸ்லீப்பர்/स्लीपर
  → filter: "sleeper", sort_by: "departure_asc"

  non ac/non-ac/without ac/ordinary/
  normal bus/non air
  → filter: "non_ac", sort_by: "price_asc"

  volvo/luxury bus/premium bus/multi-axle
  → filter: "volvo", sort_by: "rating_desc"

  fastest/quick/express/shortest/early arrival
  → filter: "fastest", sort_by: "duration_asc"

  night bus/night travel/overnight/late night
  → filter: "night", sort_by: "departure_desc"

  If NO filter keyword → filter: null,
                         sort_by: "departure_asc"

When filter is detected and all route details
are present, set ready_to_search: true.
The message should reflect the filter:
  cheapest: "Finding cheapest buses from {from} to {to} on {date}! 💰"
  ac:       "Showing AC buses from {from} to {to} on {date}! ❄️"
  sleeper:  "Showing sleeper buses from {from} to {to} on {date}! 🛏️"
'''

    ctx = request.context or {}
    user_query = request.query
    if ctx:


        user_query = f"Context (already known): {json.dumps(ctx)}\nUser says: {request.query}"
    intent = await call_ai(user_query, request.history or [], system_intent)
    
    # Robustly merge context into intent if the parser missed it
    if ctx:
        collected = intent.get("collected", {})
        if not collected.get("from_city"): collected["from_city"] = ctx.get("from_city")
        if not collected.get("to_city"): collected["to_city"] = ctx.get("to_city")
        if not collected.get("date"): collected["date"] = ctx.get("date")
        if not collected.get("filter"): collected["filter"] = ctx.get("filter")
        if not collected.get("sort_by"): collected["sort_by"] = ctx.get("sort_by")
        
        missing = []
        if not collected.get("from_city"): missing.append("from_city")
        if not collected.get("to_city"): missing.append("to_city")
        if not collected.get("date"): missing.append("date")
        
        intent["missing"] = missing
        intent["ready_to_search"] = (len(missing) == 0)
        intent["collected"] = collected
        
    print(f"Parsed AI Intent: {intent}")

    if not intent.get("ready_to_search"):
        collected = intent.get("collected", {})
        partial_intent = {
            "source": collected.get("from_city"),
            "destination": collected.get("to_city"),
            "date": collected.get("date"),
            "passengers": collected.get("passengers", 1),
            "filter": collected.get("filter"),
            "sort_by": collected.get("sort_by")
        }
        return {
            "type": "ask_details",
            "message": intent.get("message", "Where are you traveling from? 🚌"),
            "partial_intent": partial_intent,
            "quick_replies": intent.get("quick_replies", []),
            "missing": intent.get("missing", [])
        }

    collected = intent.get("collected", {})
    source_raw = collected.get("from_city")
    destination_raw = collected.get("to_city")
    raw_date = collected.get("date")
    
    date = resolve_relative_date(request.query, raw_date)
    if not date:
        date = resolve_relative_date(raw_date or "", None)
        
    mode = "bus"
    preference = None
    filter_type_early = collected.get("filter")
    sort_by_early = collected.get("sort_by") or "departure_asc"
    intent_obj = {
        "source": source_raw,
        "destination": destination_raw,
        "date": date,
        "mode": mode,
        "preference": preference,
        "intent": "search",
        "filter": filter_type_early,
        "sort_by": sort_by_early
    }

    try:
        source = city_name(source_raw)
        destination = city_name(destination_raw)
        results = await scrape_bus(source, destination, date)
        is_fallback_dict = isinstance(results, dict) and results.get("is_fallback")

        if not is_fallback_dict:
            for ticket in results:
                ticket["mode"] = "bus"

        # ── STEP 6.6: Smart Connecting Route Suggestion ──
        if is_fallback_dict or len(results) == 0:
            intermediate = find_connecting_route(source_raw, destination_raw)
            if intermediate:
                print(f"[SMART ROUTE] Trying connecting route: {source} → {intermediate.title()} → {destination}")
                try:
                    leg1_results = await scrape_bus(source, city_name(intermediate), date)
                    leg2_results = await scrape_bus(city_name(intermediate), destination, date)

                    if leg1_results and leg2_results:
                        # Pick best option from each leg
                        leg1_best = leg1_results[0]
                        leg2_best = leg2_results[0]

                        # Calculate totals
                        p1 = parse_price(leg1_best.get("price", "0"))
                        p2 = parse_price(leg2_best.get("price", "0"))
                        total_cost = f"₹{p1 + p2:,}" if p1 < 999999 and p2 < 999999 else "--"

                        # Estimate total duration
                        total_duration = "varies"
                        d1 = leg1_best.get("duration", "")
                        d2 = leg2_best.get("duration", "")
                        if d1 and d2 and d1 != "--" and d2 != "--":
                            import re as _re
                            h1 = int(_re.search(r'(\d+)h', d1).group(1)) if _re.search(r'(\d+)h', d1) else 0
                            m1 = int(_re.search(r'(\d+)m', d1).group(1)) if _re.search(r'(\d+)m', d1) else 0
                            h2 = int(_re.search(r'(\d+)h', d2).group(1)) if _re.search(r'(\d+)h', d2) else 0
                            m2 = int(_re.search(r'(\d+)m', d2).group(1)) if _re.search(r'(\d+)m', d2) else 0
                            total_mins = (h1 * 60 + m1) + (h2 * 60 + m2) + 30  # 30 min layover
                            total_duration = f"{total_mins // 60}h {total_mins % 60}m (incl. layover)"

                        # Add booking URLs
                        leg1_best["booking_url"] = generate_booking_url("bus", source_raw, intermediate, date, {})
                        leg2_best["booking_url"] = generate_booking_url("bus", intermediate, destination_raw, date, {})

                        return {
                            "type": "connecting_route",
                            "source": source_raw.title(),
                            "intermediate": intermediate.title(),
                            "destination": destination_raw.title(),
                            "date": date,
                            "leg1": leg1_best,
                            "leg2": leg2_best,
                            "total_duration": total_duration,
                            "total_cost": total_cost,
                            "intent": intent,
                        }
                except Exception as route_err:
                    print(f"[SMART ROUTE] Connecting route scrape failed: {route_err}")

        if is_fallback_dict:
            return {
                "type": "tickets",
                "data": [],
                "intent": intent,
                "booking_url": generate_booking_url("bus", source_raw, destination_raw, date, {}),
                "search_summary": {
                    "mode": mode,
                    "source": source_raw.title() if source_raw else "",
                    "destination": destination_raw.title() if destination_raw else "",
                    "date": date,
                    "total_results": 0,
                    "ai_recommendation": ""
                }
            }

        # ── STEP 6.7: Apply Preferences ──
        # Extract filter params from AI response
        filter_type = filter_type_early
        sort_by     = sort_by_early

        # Apply filter and sort
        results = filter_and_sort_buses(results, filter_type, sort_by)

        # ── STEP 7: Enrich results with booking URLs and extra details ──
        booking_base_url = generate_booking_url("bus", source_raw, destination_raw, date, {})
        data_source = results[0].get("source", "playwright") if results else "fallback"
        
        for ticket in results:
            if "booking_url" not in ticket:
                ticket["booking_url"] = booking_base_url

        return {
            "type": "tickets",
            "data": results,
            "intent": intent_obj,
            "booking_url": booking_base_url,
            "data_source": data_source,
            "active_filter": filter_type,
            "sort_by": sort_by,
            "search_summary": {
                "mode": mode,
                "source": source_raw.title() if source_raw else "",
                "destination": destination_raw.title() if destination_raw else "",
                "date": date,
                "total_results": len(results),
                "ai_recommendation": ""
            }
        }

    except Exception as e:
        print(f"Scraper crashed: {e}")
        import traceback
        traceback.print_exc()
        route_hint = ""
        if source_raw and destination_raw:
            route_hint = f" for **{source_raw.title()} → {destination_raw.title()}**"
        return {
            "type": "chat",
            "message": (
                f"I'm having a little trouble fetching live results{route_hint} right now. 🔄\n\n"
                "Please try again in a moment — live bus data can sometimes take a second to load. 🚌"
            )
        }

@app.get("/api/buses")
async def get_buses(from_city: str = None, to_city: str = None, date: str = None):
    # Parameter mapping since query parameters are used
    if not from_city and hasattr(request, "query_params"):
        from_city = request.query_params.get("from")
    if not to_city and hasattr(request, "query_params"):
        to_city = request.query_params.get("to")

    from_city = from_city or "Coimbatore"
    to_city = to_city or "Chennai"
    date = date or get_tomorrow_str()
    
    results = await scrape_bus(from_city, to_city, date)
    is_fallback = isinstance(results, dict) and results.get("is_fallback")
    
    if is_fallback or len(results) == 0:
        return {
            "success": False,
            "count": 0,
            "message": "Could not fetch live data right now.",
            "fallback_links": [
                { "name": "RedBus", "url": f"https://www.redbus.in/bus-tickets/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}?doj={date}", "icon": "🔴" },
                { "name": "AbhiBus", "url": f"https://www.abhibus.com/bus/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}?doj={date}", "icon": "🟠" },
                { "name": "MakeMyTrip", "url": f"https://www.makemytrip.com/bus-tickets/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}/", "icon": "🔵" }
            ]
        }
        
    for idx, b in enumerate(results):
        b["booking_url"] = generate_booking_url("bus", from_city, to_city, date, b)
        
    return {
        "success": True,
        "count": len(results),
        "from": from_city,
        "to": to_city,
        "date": date,
        "buses": results,
        "filters": {
            "min_price": min([parse_price(str(r.get("price", "999999"))) for r in results]) if results else 0,
            "max_price": max([parse_price(str(r.get("price", "0"))) for r in results]) if results else 0,
            "operators": list(set([r.get("operator") for r in results])),
            "bus_types": list(set([r.get("bus_type", "Standard") for r in results]))
        }
    }

# ═══════════════════════════════════════════
# Travel Guide Cache (24h TTL)
# ═══════════════════════════════════════════
_travel_guide_cache: dict = {}
CACHE_TTL_SECONDS = 86400  # 24 hours

def get_cached_guide(destination: str):
    key = destination.lower().strip()
    if key in _travel_guide_cache:
        cached_at, data = _travel_guide_cache[key]
        import time
        if time.time() - cached_at < CACHE_TTL_SECONDS:
            return data
    return None

def set_cached_guide(destination: str, data: dict):
    import time
    key = destination.lower().strip()
    _travel_guide_cache[key] = (time.time(), data)

# ═══════════════════════════════════════════
# /api/travel-guide Endpoint
# ═══════════════════════════════════════════
@app.get("/api/travel-guide")
async def get_travel_guide(destination: str = "Rameswaram", fallback: int = 0):
    destination = destination.strip().title()
    
    # Check cache first
    cached = get_cached_guide(destination)
    if cached:
        print(f"[TRAVEL GUIDE] Cache hit for: {destination}")
        return {"success": True, "destination": destination, "data": cached, "cached": True}

    # If frontend requested instant fallback (e.g. after timeout), skip AI
    if fallback:
        print(f"[TRAVEL GUIDE] Instant fallback requested for: {destination}")
        fb = get_destination_fallback(destination)
        return {"success": False, "destination": destination, "data": fb, "cached": False, "error": "fallback"}

    
    print(f"[TRAVEL GUIDE] Fetching guide for: {destination}")
    
    TRAVEL_GUIDE_SYSTEM_PROMPT = f"""You are a travel expert for Indian destinations.
Return ONLY a valid JSON object with travel guide information for "{destination}".
All prices MUST be in Indian Rupees (INR) with ₹ symbol.
All prices must be realistic and current (2026).
Make it specific to {destination} — not generic.

Return this EXACT JSON structure (fill in real data for {destination}):

{{
  "destination": "{destination}",
  "tagline": "One-line description of the place",
  "best_time_to_visit": "Month range",
  "ideal_duration": "X-Y days",
  "budget_summary": {{
    "budget_per_day": "₹X,000 - ₹Y,000",
    "midrange_per_day": "₹X,000 - ₹Y,000",
    "luxury_per_day": "₹X,000 - ₹Y,000"
  }},
  "must_visit_places": [
    {{
      "name": "Place name",
      "type": "Religious/Historical/Nature/Beach/Hill/Museum",
      "lat": 10.0123,
      "lng": 77.4765,
      "entry_fee": "Free or ₹XX",
      "best_time": "Time or Season",
      "duration": "X hours",
      "distance_from_center": "X km",
      "description": "Brief description",
      "maps_query": "Place name {destination}",
      "tips": "Practical tip"
    }}
  ],
  "hotels": [
    {{
      "name": "Hotel name",
      "category": "Budget/Mid-range/Luxury",
      "price_per_night": "₹X,000 - ₹Y,000",
      "rating": 4.0,
      "amenities": ["AC", "WiFi", "Restaurant"],
      "maps_query": "Hotel name {destination}",
      "booking_tip": "Booking advice"
    }}
  ],
  "food": [
    {{
      "name": "Restaurant or food spot name",
      "type": "South Indian/North Indian/Seafood/Street Food",
      "avg_meal_cost": "₹X00 - ₹Y00 per person",
      "must_try": ["Dish 1", "Dish 2"],
      "maps_query": "Restaurant name {destination}"
    }}
  ],
  "day_plan": [
    {{
      "day": 1,
      "title": "Day theme",
      "schedule": [
        {{
          "time": "HH:MM AM/PM",
          "activity": "Activity description",
          "cost": "Free or ₹XX",
          "duration": "X hours/mins"
        }}
      ],
      "total_cost_estimate": "₹X,000 - ₹Y,000"
    }}
  ],
  "total_trip_estimate": {{
    "2_days_budget": "₹X,000 - ₹Y,000",
    "2_days_midrange": "₹X,000 - ₹Y,000",
    "2_days_luxury": "₹X,000 - ₹Y,000",
    "includes": "Hotel + Food + Transport + Entry fees",
    "excludes": "Bus ticket to/from destination"
  }},
  "travel_tips": [
    "Tip 1",
    "Tip 2",
    "Tip 3",
    "Tip 4",
    "Tip 5"
  ],
  "google_maps_places": [
    {{
      "name": "Place name",
      "query": "Search query for Google Maps"
    }}
  ]
}}

Return ONLY valid JSON. No explanation. No markdown. No backticks. All prices in INR with ₹."""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-OpenRouter-Title": "BusBot Travel Guide"
    }
    
    # Try multiple models — primary model first, then fallbacks
    GUIDE_MODELS = [
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-3-9b-it:free",
        "deepseek/deepseek-chat:free",
    ]
    
    for model in GUIDE_MODELS:
        try:
            payload = {
                "model": model,
                "max_tokens": 3000,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": TRAVEL_GUIDE_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Give me a complete travel guide for {destination}, India."}
                ]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 429:
                    print(f"[TRAVEL GUIDE] {model} rate-limited (429), trying next...")
                    await asyncio.sleep(0.5)
                    continue
                if response.status_code in [500, 502, 503, 504]:
                    print(f"[TRAVEL GUIDE] {model} server error ({response.status_code}), trying next...")
                    continue
                
                data = response.json()
                raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not raw:
                    continue
                    
                guide_data = extract_json_from_text(raw)
                if guide_data and "must_visit_places" in guide_data:
                    set_cached_guide(destination, guide_data)
                    print(f"[TRAVEL GUIDE] Successfully fetched guide for {destination} via {model}")
                    return {"success": True, "destination": destination, "data": guide_data, "cached": False}
                else:
                    print(f"[TRAVEL GUIDE] {model} returned invalid JSON, trying next...")
                    
        except Exception as e:
            print(f"[TRAVEL GUIDE] Error with {model}: {e}")
            continue
    
    # Fallback — return rich hardcoded data per destination so UI always works
    fallback = get_destination_fallback(destination)
    return {"success": False, "destination": destination, "data": fallback, "cached": False, "error": "AI unavailable, showing curated info"}


def get_destination_fallback(destination: str) -> dict:
    """Return rich hardcoded travel guide fallback for common destinations."""
    dest_lower = destination.lower().strip()

    # ─── RAMESWARAM ───
    if any(k in dest_lower for k in ["rameswaram", "rameshwaram"]):
        return {
            "destination": destination,
            "tagline": "The Sacred Island City — where land meets the divine sea",
            "best_time_to_visit": "October to April",
            "ideal_duration": "2-3 days",
            "budget_summary": {
                "budget_per_day": "₹800 - ₹1,200",
                "midrange_per_day": "₹2,000 - ₹3,500",
                "luxury_per_day": "₹5,000 - ₹10,000"
            },
            "must_visit_places": [
                {
                    "name": "Ramanathaswamy Temple",
                    "type": "Temple",
                    "entry_fee": "Free (Camera ₹50)",
                    "best_time": "6 AM - 1 PM",
                    "duration": "2-3 hours",
                    "distance_from_center": "0.5 km",
                    "description": "One of the 12 Jyotirlinga temples with 1,212-meter-long corridor — longest in the world. Hosts 22 sacred theerthams (wells).",
                    "maps_query": "Ramanathaswamy Temple Rameswaram Tamil Nadu",
                    "tips": "Dress code strictly enforced — wear dhoti/saree. Visit early morning for the ablution ceremony."
                },
                {
                    "name": "Pamban Bridge",
                    "type": "Landmark",
                    "entry_fee": "Free",
                    "best_time": "Sunrise / Sunset",
                    "duration": "1 hour",
                    "distance_from_center": "2 km",
                    "description": "India's first sea bridge (1914) connecting Rameswaram to mainland. The cantilever section opens for ships to pass — a breathtaking sight.",
                    "maps_query": "Pamban Bridge Rameswaram Tamil Nadu",
                    "tips": "Watch from the new road bridge for the best view. Train timings: check if a train is scheduled for a thrilling sight."
                },
                {
                    "name": "Dhanushkodi",
                    "type": "Scenic",
                    "entry_fee": "₹50 (jeep/vehicle)",
                    "best_time": "Early morning",
                    "duration": "3-4 hours",
                    "distance_from_center": "18 km",
                    "description": "Ghost town at India's southeastern tip where Bay of Bengal meets Indian Ocean. Ruins of the 1964 cyclone-destroyed town stand eerily.",
                    "maps_query": "Dhanushkodi Beach Tamil Nadu",
                    "tips": "Only jeeps allowed on the sandy road. Carry water and snacks — no shops there. Start by 6 AM."
                },
                {
                    "name": "Agni Theertham Beach",
                    "type": "Beach",
                    "entry_fee": "Free",
                    "best_time": "Early morning",
                    "duration": "1 hour",
                    "distance_from_center": "0.3 km",
                    "description": "Sacred beach where pilgrims take holy dip before entering the main temple. Calm waters and beautiful sunrise.",
                    "maps_query": "Agni Theertham Beach Rameswaram",
                    "tips": "Best for sunrise photography. Avoid afternoons — it gets very hot."
                },
                {
                    "name": "APJ Abdul Kalam Memorial",
                    "type": "Museum",
                    "entry_fee": "₹10",
                    "best_time": "9 AM - 5 PM",
                    "duration": "1-1.5 hours",
                    "distance_from_center": "1 km",
                    "description": "Childhood home and museum of India's Missile Man and former President. Includes personal artifacts, photos, and exhibits.",
                    "maps_query": "APJ Abdul Kalam House Rameswaram",
                    "tips": "Very inspirational visit. Photography allowed inside."
                }
            ],
            "hotels": [
                {"name": "Hotel Sunrise Rameswaram", "category": "Budget", "price_per_night": "₹800 - ₹1,500", "rating": 3.8, "amenities": ["AC", "WiFi", "Hot Water"], "maps_query": "Hotel Sunrise Rameswaram", "booking_tip": "Book directly for best rates. Located near the temple."},
                {"name": "TTDC Hotel Tamil Nadu", "category": "Mid-range", "price_per_night": "₹2,500 - ₹4,000", "rating": 4.0, "amenities": ["AC", "WiFi", "Restaurant", "Sea View"], "maps_query": "TTDC Hotel Tamil Nadu Rameswaram", "booking_tip": "Government hotel — clean and reliable. Book via TTDC website."},
                {"name": "Hotel Pams Paradise", "category": "Luxury", "price_per_night": "₹5,000 - ₹9,000", "rating": 4.3, "amenities": ["AC", "WiFi", "Pool", "Restaurant", "Sea View"], "maps_query": "Hotel Pams Paradise Rameswaram", "booking_tip": "Best luxury option. Book 2 weeks in advance for weekends."}
            ],
            "food": [
                {"name": "Sri Murugan Mess", "type": "Vegetarian South Indian", "avg_meal_cost": "₹80 - ₹150", "must_try": ["Fish Curry", "Crab Curry", "Prawn Biryani"], "maps_query": "Sri Murugan Mess Rameswaram"},
                {"name": "Hotel Vasantha Bhavan", "type": "Pure Vegetarian", "avg_meal_cost": "₹60 - ₹120", "must_try": ["Idli Sambar", "Meals", "Pongal"], "maps_query": "Hotel Vasantha Bhavan Rameswaram"},
                {"name": "Seafood Stalls near Beach", "type": "Seafood", "avg_meal_cost": "₹200 - ₹400", "must_try": ["Grilled Fish", "Crab Fry", "Lobster"], "maps_query": "Seafood stalls Rameswaram beach"}
            ],
            "day_plan": [
                {"day": 1, "title": "Sacred Temples & Beach", "schedule": [
                    {"time": "6:00 AM", "activity": "Agni Theertham Beach — holy dip & sunrise", "cost": "Free", "duration": "45 min"},
                    {"time": "7:00 AM", "activity": "Ramanathaswamy Temple — 22 theerthams", "cost": "Free", "duration": "2.5 hrs"},
                    {"time": "10:00 AM", "activity": "Breakfast at Vasantha Bhavan", "cost": "₹80", "duration": "45 min"},
                    {"time": "11:00 AM", "activity": "APJ Abdul Kalam Memorial", "cost": "₹10", "duration": "1.5 hrs"},
                    {"time": "1:00 PM", "activity": "Seafood lunch near Pamban", "cost": "₹300", "duration": "1 hr"},
                    {"time": "3:00 PM", "activity": "Pamban Bridge viewpoint", "cost": "Free", "duration": "1 hr"},
                    {"time": "5:00 PM", "activity": "Sunset at beach", "cost": "Free", "duration": "1 hr"}
                ], "total_cost_estimate": "₹500 - ₹800"},
                {"day": 2, "title": "Dhanushkodi & Departure", "schedule": [
                    {"time": "6:00 AM", "activity": "Jeep safari to Dhanushkodi", "cost": "₹150 - ₹200", "duration": "4 hrs"},
                    {"time": "11:00 AM", "activity": "Return & visit Ariyaman Beach", "cost": "Free", "duration": "1.5 hrs"},
                    {"time": "1:00 PM", "activity": "Lunch & shopping for conch shells", "cost": "₹200 - ₹500", "duration": "2 hrs"}
                ], "total_cost_estimate": "₹400 - ₹700"}
            ],
            "total_trip_estimate": {
                "2_days_budget": "₹2,500 - ₹4,000",
                "2_days_midrange": "₹5,000 - ₹8,000",
                "2_days_luxury": "₹12,000 - ₹20,000",
                "includes": "Hotel + Food + Local transport + Entry fees",
                "excludes": "Bus/train ticket to Rameswaram"
            },
            "travel_tips": [
                "Rameswaram is a pilgrimage city — dress conservatively, especially at temples",
                "Hire a cycle or auto for local transport (cheaper than taxis)",
                "Carry cash — most small shops don't accept cards or UPI",
                "Best season: November to February. Avoid April-June (extreme heat)",
                "Buy fresh conch shells and handicrafts from the beach market (negotiate!)",
                "The famous 'Rameswaram crab curry' is a must-try at local mess restaurants"
            ],
            "google_maps_places": [
                {"name": "Ramanathaswamy Temple", "query": "Ramanathaswamy Temple Rameswaram"},
                {"name": "Pamban Bridge", "query": "Pamban Bridge Rameswaram"},
                {"name": "Dhanushkodi", "query": "Dhanushkodi Beach Tamil Nadu"}
            ]
        }

    # ─── OOTY ───
    if any(k in dest_lower for k in ["ooty", "udhagamandalam", "ootacamund"]):
        return {
            "destination": destination,
            "tagline": "Queen of Hill Stations — misty mountains, tea gardens & toy trains",
            "best_time_to_visit": "April to June, October to December",
            "ideal_duration": "3-4 days",
            "budget_summary": {
                "budget_per_day": "₹1,000 - ₹2,000",
                "midrange_per_day": "₹3,000 - ₹6,000",
                "luxury_per_day": "₹8,000 - ₹18,000"
            },
            "must_visit_places": [
                {"name": "Ooty Lake", "type": "Scenic", "entry_fee": "Boating ₹50-₹150", "best_time": "9 AM - 5 PM", "duration": "2 hours", "distance_from_center": "1 km", "description": "Artificial lake built in 1825 surrounded by eucalyptus trees. Boating is the highlight.", "maps_query": "Ooty Lake Ooty Tamil Nadu", "tips": "Go early on weekdays to avoid crowds. Pedal boats are the most popular."},
                {"name": "Nilgiri Mountain Railway", "type": "Landmark", "entry_fee": "₹25 - ₹200", "best_time": "Morning departures", "duration": "5 hours (full trip)", "distance_from_center": "0.5 km", "description": "UNESCO World Heritage toy train from Mettupalayam to Ooty through 16 tunnels and 250 bridges.", "maps_query": "Ooty Railway Station Nilgiri Mountain Railway", "tips": "Book tickets 30 days in advance on IRCTC. Sit on the left side going up for best views."},
                {"name": "Botanical Gardens", "type": "Park", "entry_fee": "₹30", "best_time": "9 AM - 6 PM", "duration": "2 hours", "distance_from_center": "2 km", "description": "151-year-old garden with 650+ plant species, a 20-million-year-old fossil tree, and a summer flower show.", "maps_query": "Government Botanical Garden Ooty", "tips": "Best in April-May when the flower show is on. Morning has the freshest blooms."},
                {"name": "Doddabetta Peak", "type": "Hill", "entry_fee": "₹30", "best_time": "Clear mornings", "duration": "1.5 hours", "distance_from_center": "9 km", "description": "Highest peak in the Nilgiris at 2,637 m. On clear days you can see Coimbatore city from the top.", "maps_query": "Doddabetta Peak Ooty", "tips": "Very foggy in monsoon. Mornings before 10 AM give the best clear views. Carry a jacket."},
                {"name": "Tea Factory & Museum", "type": "Museum", "entry_fee": "₹50", "best_time": "10 AM - 5 PM", "duration": "1.5 hours", "distance_from_center": "3 km", "description": "See how Nilgiri tea is made from leaf to cup. Buy fresh tea directly from the factory at best prices.", "maps_query": "Tea factory Ooty Nilgiri", "tips": "Buy at least 1 kg of fresh tea as a souvenir — much cheaper than market price."}
            ],
            "hotels": [
                {"name": "Zostel Ooty", "category": "Budget", "price_per_night": "₹600 - ₹1,200", "rating": 4.2, "amenities": ["WiFi", "Common Area", "Breakfast"], "maps_query": "Zostel Ooty", "booking_tip": "Best for solo travellers. Book 2 weeks in advance."},
                {"name": "Savoy Hotel", "category": "Mid-range", "price_per_night": "₹4,000 - ₹7,000", "rating": 4.4, "amenities": ["AC", "WiFi", "Restaurant", "Garden", "Fireplace"], "maps_query": "Savoy Hotel Ooty", "booking_tip": "Heritage property — experience colonial architecture."},
                {"name": "Taj Savoy Hotel", "category": "Luxury", "price_per_night": "₹10,000 - ₹18,000", "rating": 4.7, "amenities": ["AC", "WiFi", "Pool", "Spa", "Restaurant", "Garden"], "maps_query": "Taj Savoy Ooty", "booking_tip": "Best luxury experience. Book well in advance for summer season."}
            ],
            "food": [
                {"name": "Hotel Dasaprakash", "type": "South Indian Vegetarian", "avg_meal_cost": "₹80 - ₹150", "must_try": ["Masala Dosa", "Rava Idli", "Filter Coffee"], "maps_query": "Hotel Dasaprakash Ooty"},
                {"name": "Hyderabad Biryani", "type": "Non-Vegetarian", "avg_meal_cost": "₹120 - ₹250", "must_try": ["Mutton Biryani", "Chicken Curry"], "maps_query": "Biryani restaurant Ooty"},
                {"name": "Ooty Chocolate Shop", "type": "Sweets & Chocolates", "avg_meal_cost": "₹100 - ₹300", "must_try": ["Homemade Chocolate", "Varkey", "Ooty Shortbread"], "maps_query": "Ooty chocolate shop market"}
            ],
            "day_plan": [
                {"day": 1, "title": "Lakes, Gardens & Toy Train", "schedule": [
                    {"time": "8:00 AM", "activity": "Toy Train ride Ooty to Coonoor", "cost": "₹25", "duration": "2 hrs"},
                    {"time": "11:00 AM", "activity": "Botanical Gardens stroll", "cost": "₹30", "duration": "2 hrs"},
                    {"time": "1:30 PM", "activity": "Lunch at Dasaprakash", "cost": "₹120", "duration": "1 hr"},
                    {"time": "3:00 PM", "activity": "Ooty Lake boating", "cost": "₹100", "duration": "2 hrs"},
                    {"time": "5:30 PM", "activity": "Shopping for chocolates & tea", "cost": "₹500", "duration": "1.5 hrs"}
                ], "total_cost_estimate": "₹800 - ₹1,500"},
                {"day": 2, "title": "Peaks, Tea & Viewpoints", "schedule": [
                    {"time": "7:00 AM", "activity": "Doddabetta Peak at sunrise", "cost": "₹30", "duration": "2 hrs"},
                    {"time": "10:00 AM", "activity": "Tea Factory tour & tasting", "cost": "₹50", "duration": "1.5 hrs"},
                    {"time": "12:00 PM", "activity": "Lunch at tea estate café", "cost": "₹200", "duration": "1 hr"},
                    {"time": "2:00 PM", "activity": "Pykara Waterfalls", "cost": "₹30", "duration": "2.5 hrs"}
                ], "total_cost_estimate": "₹350 - ₹700"}
            ],
            "total_trip_estimate": {
                "2_days_budget": "₹2,500 - ₹4,000",
                "2_days_midrange": "₹7,000 - ₹13,000",
                "2_days_luxury": "₹20,000 - ₹35,000",
                "includes": "Hotel + Food + Entry fees + Local transport",
                "excludes": "Toy train ticket (book separately on IRCTC)"
            },
            "travel_tips": [
                "Carry a warm jacket — temperatures drop to 5-10°C in December-January",
                "Book Nilgiri Mountain Railway tickets 30 days in advance on IRCTC",
                "Visit during April-May for the famous Flower Show at Botanical Gardens",
                "Buy fresh Nilgiri tea and homemade chocolates as souvenirs",
                "Hire a taxi for the day (~₹1,500-₹2,000) to cover all viewpoints",
                "Avoid monsoon season (July-September) — roads become slippery and foggy"
            ],
            "google_maps_places": [
                {"name": "Ooty Lake", "query": "Ooty Lake Tamil Nadu"},
                {"name": "Botanical Gardens", "query": "Government Botanical Garden Ooty"},
                {"name": "Doddabetta Peak", "query": "Doddabetta Peak Ooty"}
            ]
        }

    # ─── MADURAI ───
    if any(k in dest_lower for k in ["madurai"]):
        return {
            "destination": destination,
            "tagline": "The Temple City — where tradition lives in every stone",
            "best_time_to_visit": "October to March",
            "ideal_duration": "2-3 days",
            "budget_summary": {
                "budget_per_day": "₹700 - ₹1,200",
                "midrange_per_day": "₹2,000 - ₹4,000",
                "luxury_per_day": "₹5,000 - ₹12,000"
            },
            "must_visit_places": [
                {"name": "Meenakshi Amman Temple", "type": "Temple", "entry_fee": "Free (Camera ₹50)", "best_time": "5 AM - 7 AM or 6 PM - 9 PM", "duration": "2-3 hours", "distance_from_center": "Center", "description": "One of Tamil Nadu's most iconic temples with 14 magnificent gopurams covered in thousands of colorful sculptures.", "maps_query": "Meenakshi Amman Temple Madurai", "tips": "Visit during evening aarti (6-9 PM) for the most divine experience. Dress code required."},
                {"name": "Thirumalai Nayakkar Mahal", "type": "Historical", "entry_fee": "₹50", "best_time": "9 AM - 5 PM", "duration": "1.5 hours", "distance_from_center": "1.5 km", "description": "17th-century Indo-Saracenic palace with massive hall. Sound & light show in evenings.", "maps_query": "Thirumalai Nayakkar Palace Madurai", "tips": "Evening sound & light show (6:45 PM) is a must-watch. Very atmospheric."},
                {"name": "Gandhi Memorial Museum", "type": "Museum", "entry_fee": "Free", "best_time": "10 AM - 5 PM", "duration": "1-2 hours", "distance_from_center": "2 km", "description": "Tribute to Mahatma Gandhi. Features the dhoti worn during his assassination and powerful exhibits.", "maps_query": "Gandhi Memorial Museum Madurai", "tips": "Very moving experience. Photography inside the main hall is restricted."},
                {"name": "Alagar Kovil", "type": "Temple", "entry_fee": "Free", "best_time": "7 AM - 12 PM", "duration": "2 hours", "distance_from_center": "22 km", "description": "Ancient Vishnu temple in Alagar Hills. Beautiful hillside location with steps to the top.", "maps_query": "Alagar Kovil Madurai", "tips": "Take an auto or local bus. The climb to the top offers panoramic views."}
            ],
            "hotels": [
                {"name": "Hotel Supreme", "category": "Budget", "price_per_night": "₹1,000 - ₹2,000", "rating": 3.9, "amenities": ["AC", "WiFi", "Restaurant"], "maps_query": "Hotel Supreme Madurai", "booking_tip": "Close to temple. Book directly for 10% discount."},
                {"name": "Hotel Heritage Madurai", "category": "Mid-range", "price_per_night": "₹3,500 - ₹6,000", "rating": 4.3, "amenities": ["AC", "WiFi", "Pool", "Restaurant"], "maps_query": "Heritage Madurai Hotel", "booking_tip": "Heritage property. Early check-in usually available."},
                {"name": "Taj Gateway Hotel Madurai", "category": "Luxury", "price_per_night": "₹7,000 - ₹14,000", "rating": 4.6, "amenities": ["AC", "WiFi", "Pool", "Spa", "Restaurant"], "maps_query": "Taj Gateway Hotel Madurai", "booking_tip": "Book 2 weeks ahead. Temple-view rooms are premium."}
            ],
            "food": [
                {"name": "Murugan Idli Shop", "type": "South Indian Vegetarian", "avg_meal_cost": "₹60 - ₹120", "must_try": ["Soft Idli", "Chutney", "Filter Coffee"], "maps_query": "Murugan Idli Shop Madurai"},
                {"name": "Amma Mess", "type": "Non-Vegetarian", "avg_meal_cost": "₹100 - ₹200", "must_try": ["Mutton Kheema", "Madurai Biryani", "Chicken Roast"], "maps_query": "Amma Mess Madurai"},
                {"name": "Jigarthanda Shops", "type": "Street Food & Drinks", "avg_meal_cost": "₹30 - ₹60", "must_try": ["Jigarthanda", "Paal Ice"], "maps_query": "Jigarthanda shops Madurai"}
            ],
            "day_plan": [
                {"day": 1, "title": "Temple City Exploration", "schedule": [
                    {"time": "5:30 AM", "activity": "Meenakshi Temple morning darshan", "cost": "Free", "duration": "2.5 hrs"},
                    {"time": "8:30 AM", "activity": "Breakfast at Murugan Idli Shop", "cost": "₹80", "duration": "45 min"},
                    {"time": "10:00 AM", "activity": "Thirumalai Nayakkar Palace", "cost": "₹50", "duration": "1.5 hrs"},
                    {"time": "12:00 PM", "activity": "Lunch at Amma Mess", "cost": "₹150", "duration": "1 hr"},
                    {"time": "2:00 PM", "activity": "Gandhi Memorial Museum", "cost": "Free", "duration": "1.5 hrs"},
                    {"time": "4:00 PM", "activity": "Jigarthanda at famous old shop", "cost": "₹50", "duration": "30 min"},
                    {"time": "6:45 PM", "activity": "Sound & Light Show at Palace", "cost": "₹25", "duration": "1 hr"}
                ], "total_cost_estimate": "₹400 - ₹700"}
            ],
            "total_trip_estimate": {
                "2_days_budget": "₹2,000 - ₹3,500",
                "2_days_midrange": "₹5,000 - ₹8,000",
                "2_days_luxury": "₹12,000 - ₹20,000",
                "includes": "Hotel + Food + Entry fees + Local auto",
                "excludes": "Bus/train to Madurai"
            },
            "travel_tips": [
                "Meenakshi Temple is best visited at 5 AM for the spiritual morning rituals",
                "Madurai's famous Jigarthanda drink is unique — don't leave without trying it",
                "Dress conservatively for temple visits — sarongs are available at temple entrance",
                "Avoid visiting during summer (April-June) — extremely hot",
                "Auto-rickshaws are the best way to get around. Negotiate fares beforehand"
            ],
            "google_maps_places": [
                {"name": "Meenakshi Temple", "query": "Meenakshi Amman Temple Madurai"},
                {"name": "Thirumalai Nayakkar Palace", "query": "Thirumalai Nayakkar Palace Madurai"}
            ]
        }

    # ─── GENERIC FALLBACK for any other destination ───
    return {
        "destination": destination,
        "tagline": f"Discover the wonders of {destination}",
        "best_time_to_visit": "October to March (winter season)",
        "ideal_duration": "2-3 days",
        "budget_summary": {
            "budget_per_day": "₹1,000 - ₹2,000",
            "midrange_per_day": "₹3,000 - ₹5,000",
            "luxury_per_day": "₹7,000 - ₹15,000"
        },
        "must_visit_places": [
            {
                "name": f"{destination} City Center",
                "type": "Landmark",
                "entry_fee": "Free",
                "best_time": "9 AM - 6 PM",
                "duration": "2-3 hours",
                "distance_from_center": "0 km",
                "description": f"Explore the heart of {destination} — vibrant streets, local markets, and iconic landmarks await.",
                "maps_query": f"City center {destination} India",
                "tips": f"Ask locals for hidden gems — {destination} has many off-the-beaten-path spots."
            },
            {
                "name": f"{destination} Main Temple/Monument",
                "type": "Historical",
                "entry_fee": "₹20 - ₹50",
                "best_time": "Early morning",
                "duration": "1-2 hours",
                "distance_from_center": "1-2 km",
                "description": f"The most iconic historical or religious site in {destination}. A must-see for first-time visitors.",
                "maps_query": f"main temple monument {destination} India",
                "tips": "Visit early morning to avoid crowds and get the best photography light."
            },
            {
                "name": f"{destination} Local Market",
                "type": "Shopping",
                "entry_fee": "Free",
                "best_time": "Evening (4 PM - 8 PM)",
                "duration": "1-2 hours",
                "distance_from_center": "0.5 km",
                "description": f"Browse local crafts, textiles, spices, and street food. Best way to experience local culture of {destination}.",
                "maps_query": f"local market {destination} India",
                "tips": "Bargaining is expected and accepted. Start at 60% of the asking price."
            }
        ],
        "hotels": [
            {"name": f"Budget Hotel {destination}", "category": "Budget", "price_per_night": "₹800 - ₹1,500", "rating": 3.5, "amenities": ["AC", "WiFi"], "maps_query": f"budget hotel {destination}", "booking_tip": "Book on MakeMyTrip or OYO for best rates."},
            {"name": f"Mid-range Resort {destination}", "category": "Mid-range", "price_per_night": "₹2,500 - ₹5,000", "rating": 4.0, "amenities": ["AC", "WiFi", "Restaurant", "Pool"], "maps_query": f"hotel resort {destination} India", "booking_tip": "Check reviews on TripAdvisor before booking."}
        ],
        "food": [
            {"name": "Local Dhaba", "type": "South Indian", "avg_meal_cost": "₹80 - ₹150", "must_try": ["Local Thali", "Idli Sambar", "Filter Coffee"], "maps_query": f"local restaurant {destination}"},
            {"name": "Street Food Stalls", "type": "Street Food", "avg_meal_cost": "₹30 - ₹80", "must_try": ["Local specialties", "Chai"], "maps_query": f"street food {destination} India"}
        ],
        "day_plan": [
            {"day": 1, "title": f"Explore {destination}", "schedule": [
                {"time": "9:00 AM", "activity": "Visit main historical monument", "cost": "₹50", "duration": "2 hrs"},
                {"time": "12:00 PM", "activity": "Local restaurant lunch", "cost": "₹150", "duration": "1 hr"},
                {"time": "2:00 PM", "activity": "Local market shopping", "cost": "₹300-₹500", "duration": "2 hrs"},
                {"time": "5:00 PM", "activity": "Sunset viewpoint", "cost": "Free", "duration": "1 hr"}
            ], "total_cost_estimate": "₹600 - ₹900"}
        ],
        "total_trip_estimate": {
            "2_days_budget": "₹2,500 - ₹4,000",
            "2_days_midrange": "₹6,000 - ₹10,000",
            "2_days_luxury": "₹14,000 - ₹25,000",
            "includes": "Hotel + Food + Transport + Entry fees",
            "excludes": "Bus/train ticket to destination"
        },
        "travel_tips": [
            f"Carry cash — many shops in {destination} may not accept digital payments",
            "Book accommodation in advance during weekends and holidays",
            "Hire a local guide for a richer, more authentic experience",
            "Carry a water bottle and sunscreen — India can be very hot",
            "Try local street food for the most authentic flavors",
            "Check local festival calendar — timing your visit around festivals adds magic"
        ],
        "google_maps_places": [
            {"name": destination, "query": f"tourist places in {destination} India"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
