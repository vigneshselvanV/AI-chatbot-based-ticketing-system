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
from scrapers import scrape_bus, scrape_flight, scrape_train

import os
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

# ═══════════════════════════════════════════
# City Sanitizer
# ═══════════════════════════════════════════
CITY_TO_IATA = {
    "coimbatore": "CJB", "chennai": "MAA", "madurai": "IXM",
    "rameswaram": "IXM", "bangalore": "BLR", "bengaluru": "BLR",
    "mumbai": "BOM", "delhi": "DEL", "hyderabad": "HYD",
    "pune": "PNQ", "kolkata": "CCU", "kochi": "COK", "goa": "GOI",
    "trichy": "TRZ", "tiruchirapalli": "TRZ", "salem": "SXV",
    "tiruchendur": "TCR", "tuticorin": "TCZ", "jaipur": "JAI",
    "ahmedabad": "AMD", "lucknow": "LKO", "new delhi": "DEL",
}

def city_code(name: str) -> str:
    return CITY_TO_IATA.get(name.lower().strip(), name.strip().upper()[:3])

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

    if mode == "bus":
        redbus_date = f"{int(day)}-{month_name}-{year}"
        return (
            f"https://www.redbus.in/bus-tickets/{src_slug}-to-{dst_slug}"
            f"?fromCityName={src_title}&toCityName={dst_title}&onward={redbus_date}"
        )
    elif mode == "flight":
        # Google Flights URL
        src_iata = city_code(source)
        dst_iata = city_code(destination)
        gf_date = f"{year}-{month}-{day}"
        return (
            f"https://www.google.com/travel/flights?q=Flights+from+{src_title}+to+{dst_title}"
            f"+on+{int(day)}+{month_name}+{year}&curr=INR"
        )
    elif mode == "train":
        return f"https://www.redbus.in/railways"
    else:
        return "#"

# ═══════════════════════════════════════════
# Bulletproof JSON Extractor
# ═══════════════════════════════════════════
def extract_json_from_text(raw_text: str) -> dict:
    if not raw_text:
        return {}
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return {}
    except (json.JSONDecodeError, Exception):
        return {}

# ═══════════════════════════════════════════
# LLM Integration (OpenRouter → Ollama fallback)
# ═══════════════════════════════════════════
async def get_ai_response(prompt: str, system_prompt: str, json_mode: bool = False) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "TicketBot"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise Exception(f"OpenRouter HTTP {response.status_code}: {response.text}")
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"OpenRouter failed: {e}")
        # Try local Ollama fallback ONLY if we are running locally
        if "render" not in os.getenv("RENDER_EXTERNAL_URL", ""):
            print("Falling back to local Ollama...")
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
            }
            if json_mode:
                payload["format"] = "json"

            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json().get("response", "")
                except Exception as e2:
                    print(f"Local Ollama also failed: {e2}")
        raise Exception(f"AI Service Error: {str(e)}")

# ═══════════════════════════════════════════
# /search Endpoint — Smart Conversational Router
# ═══════════════════════════════════════════
@app.post("/search")
async def search_tickets(request: SearchRequest):
    print(f"Received query: {request.query}")
    print(f"Context: {request.context}")

    today = get_today_str()
    tomorrow = get_tomorrow_str()

    # ── STEP 1: Intent Extraction ──
    system_intent = (
        'You are an intent parser. Extract travel info into EXACTLY this JSON format: '
        '{"mode": "bus|train|flight|all", "source": "City", "destination": "City", "date": "DD-MM-YYYY"}. '
        'Output ABSOLUTELY NOTHING ELSE. No markdown, no backticks, no greetings. '
        'Rules: '
        '- bus/coach/travels → mode is "bus". '
        '- train/express/railway → mode is "train". '
        '- flight/fly/plane/air → mode is "flight". '
        '- compare/comparison/all/every mode/cheapest way/best way/options → mode is "all". '
        '- If the user just says "travel" or "ticket" or "go to" without specifying a mode, set mode to "all". '
        '- If no source/destination found → return {"mode": null, "source": null, "destination": null, "date": null}. '
        '- If date is missing, set date to null (do NOT guess a date). '
        f'- Convert relative dates: today={today}, tomorrow={tomorrow}. '
        '- "next week" means 7 days from today. '
        '- IMPORTANT: Only set source and destination if the user explicitly mentions cities/places.'
    )

    # Merge context from follow-up conversation
    context = request.context or {}
    merged_query = request.query

    # If we have prior context (from a follow-up), merge it
    if context.get("source") or context.get("destination"):
        ctx_parts = []
        if context.get("mode"):
            ctx_parts.append(f"mode: {context['mode']}")
        if context.get("source"):
            ctx_parts.append(f"from: {context['source']}")
        if context.get("destination"):
            ctx_parts.append(f"to: {context['destination']}")
        if context.get("date"):
            ctx_parts.append(f"on: {context['date']}")
        merged_query = f"Previously mentioned: {', '.join(ctx_parts)}. User now says: {request.query}"
        print(f"Merged query: {merged_query}")

    try:
        intent_raw = await get_ai_response(merged_query, system_intent, json_mode=True)
        intent = extract_json_from_text(intent_raw)
        print(f"Parsed intent: {intent}")
    except Exception as e:
        print(f"Intent extraction failed: {e}")
        return {"type": "chat", "message": f"Sorry, I couldn't understand your request. Error details: {str(e)}"}

    # ── STEP 2: Smart Follow-Up — Ask for missing details ──
    source_raw = intent.get("source") or intent.get("origin")
    destination_raw = intent.get("destination")
    date = intent.get("date")
    mode = (intent.get("mode") or "").lower() if intent.get("mode") else ""

    # Has some travel intent but missing required fields
    query_lower = request.query.lower()
    has_travel_intent = any(kw in query_lower for kw in [
        "bus", "train", "flight", "fly", "travel", "ticket", "book",
        "go to", "going to", "from", "ride", "journey", "trip"
    ]) or (source_raw and destination_raw)

    if has_travel_intent:
        missing_fields = []
        partial_intent = {
            "source": source_raw,
            "destination": destination_raw,
            "date": date,
            "mode": mode if mode else None,
        }

        if not source_raw:
            missing_fields.append("source city (where are you traveling from?)")
        if not destination_raw:
            missing_fields.append("destination city (where do you want to go?)")
        if not date:
            missing_fields.append("travel date")
        if not mode:
            missing_fields.append("travel mode (bus 🚌, train 🚆, or flight ✈️)")

        if missing_fields:
            # Generate a friendly follow-up message
            known_parts = []
            if source_raw:
                known_parts.append(f"from **{source_raw.title()}**")
            if destination_raw:
                known_parts.append(f"to **{destination_raw.title()}**")
            if mode:
                known_parts.append(f"by **{mode}**")
            if date:
                known_parts.append(f"on **{date}**")

            if known_parts:
                known_str = "Got it! You want to travel " + " ".join(known_parts) + ". "
            else:
                known_str = "I'd love to help you find tickets! "

            missing_str = "Could you also tell me:\n"
            for i, field in enumerate(missing_fields, 1):
                missing_str += f"  {i}. Your {field}\n"

            missing_str += "\nFor example: *\"tomorrow by bus\"* or *\"15-06-2026 by train\"*"

            return {
                "type": "ask_details",
                "message": known_str + missing_str,
                "partial_intent": partial_intent,
                "missing": [f.split(" (")[0] for f in missing_fields]
            }

    # ── STEP 3: No travel intent at all → chat ──
    if not source_raw or not destination_raw:
        system_chat = (
            "You are a friendly travel assistant chatbot. "
            "Help users search for bus, train, and flight tickets across India. "
            "If the user greets you, greet them back warmly and give examples of what they can ask. "
            "Examples: 'Find me a bus from Chennai to Madurai tomorrow', "
            "'Show flights from Delhi to Mumbai on 15 June 2026', "
            "'Check trains from Coimbatore to Rameswaram'. "
            "Keep responses concise and helpful."
        )
        try:
            chat_msg = await get_ai_response(request.query, system_chat)
            return {"type": "chat", "message": chat_msg}
        except Exception:
            return {
                "type": "chat",
                "message": (
                    "👋 Hello! I'm your AI travel assistant. I can help you find:\n\n"
                    "🚌 **Bus tickets** — powered by RedBus\n"
                    "✈️ **Flight tickets** — powered by Google Flights\n"
                    "🚆 **Train tickets** — powered by erail.in\n\n"
                    "Just tell me something like:\n"
                    "*\"Find me a bus from Coimbatore to Rameswaram tomorrow\"*"
                )
            }

    # ── STEP 4: Mode validation ──
    if mode not in ["bus", "train", "flight", "all"]:
        if any(kw in query_lower for kw in ["flight", "fly", "plane", "air"]):
            mode = "flight"
        elif any(kw in query_lower for kw in ["train", "express", "railway"]):
            mode = "train"
        elif any(kw in query_lower for kw in ["bus", "coach", "travels"]):
            mode = "bus"
        else:
            mode = "all"
        intent["mode"] = mode

    # ── STEP 5: Default date to tomorrow if missing ──
    if not date:
        date = tomorrow
        intent["date"] = date

    # ── STEP 6: Trigger Scrapers ──
    try:
        if mode == "flight":
            source = city_code(source_raw)
            destination = city_code(destination_raw)
            results = await scrape_flight(source, destination, date)
            for ticket in results:
                ticket["mode"] = "flight"
        elif mode == "train":
            source = city_name(source_raw)
            destination = city_name(destination_raw)
            results = await scrape_train(source, destination, date)
            for ticket in results:
                ticket["mode"] = "train"
        elif mode == "bus":
            source = city_name(source_raw)
            destination = city_name(destination_raw)
            results = await scrape_bus(source, destination, date)
            for ticket in results:
                ticket["mode"] = "bus"
        else:  # mode == "all"
            # Parallel scraping
            flight_task = scrape_flight(city_code(source_raw), city_code(destination_raw), date)
            bus_task = scrape_bus(city_name(source_raw), city_name(destination_raw), date)
            train_task = scrape_train(city_name(source_raw), city_name(destination_raw), date)
            
            flight_res, bus_res, train_res = await asyncio.gather(
                flight_task, bus_task, train_task, return_exceptions=True
            )
            
            # Catch exceptions to prevent one failure from killing the comparison
            if isinstance(flight_res, Exception):
                print(f"[BACKEND] Flight scrape failed: {flight_res}")
                flight_res = []
            if isinstance(bus_res, Exception):
                print(f"[BACKEND] Bus scrape failed: {bus_res}")
                bus_res = []
            if isinstance(train_res, Exception):
                print(f"[BACKEND] Train scrape failed: {train_res}")
                train_res = []
            
            # Combine results with appropriate transport mode tag
            results = []
            for t in flight_res:
                t["mode"] = "flight"
                results.append(t)
            for t in bus_res:
                t["mode"] = "bus"
                results.append(t)
            for t in train_res:
                t["mode"] = "train"
                results.append(t)

        # ── STEP 7: Enrich results with booking URLs and extra details ──
        if mode == "all":
            flight_booking_url = generate_booking_url("flight", source_raw, destination_raw, date, {})
            bus_booking_url = generate_booking_url("bus", source_raw, destination_raw, date, {})
            train_booking_url = generate_booking_url("train", source_raw, destination_raw, date, {})
            
            for ticket in results:
                t_mode = ticket.get("mode", "bus")
                if t_mode == "flight":
                    ticket["booking_url"] = flight_booking_url
                elif t_mode == "train":
                    ticket["booking_url"] = train_booking_url
                else:
                    ticket["booking_url"] = bus_booking_url
            
            # Sort combined results by price
            results.sort(key=lambda x: parse_price(x.get("price")))
            booking_base_url = ""
            data_source = "All Modes"
        else:
            booking_base_url = generate_booking_url(mode, source_raw, destination_raw, date, {})
            for ticket in results:
                ticket["booking_url"] = booking_base_url
            
            source_sites = {
                "bus": "RedBus",
                "flight": "Google Flights",
                "train": "erail.in"
            }
            data_source = source_sites.get(mode, "Web")

        return {
            "type": "tickets",
            "data": results,
            "intent": intent,
            "booking_url": booking_base_url,
            "data_source": data_source,
            "search_summary": {
                "mode": mode,
                "source": source_raw.title() if source_raw else "",
                "destination": destination_raw.title() if destination_raw else "",
                "date": date,
                "total_results": len(results),
            }
        }

    except Exception as e:
        print(f"Scraper crashed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "type": "chat",
            "message": f"I found your route ({source_raw} → {destination_raw} on {date}) but the live scraper encountered an error. Please try again in a moment."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
