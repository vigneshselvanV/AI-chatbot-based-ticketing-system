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
    history: list | None = None

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
        return f"https://www.irctc.co.in/nget/train-search"
    else:
        return "#"

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
# LLM Integration (OpenRouter → Ollama fallback)
# ═══════════════════════════════════════════
async def get_ai_response(prompt: str, system_prompt: str, json_mode: bool = False, history: list = None) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "TicketBot"
        }
        
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history[-8:]:
                role = "user" if msg.get("type") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("text", "")})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "openai/gpt-oss-120b:free",
            "messages": messages
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            data = response.json() if response.text else {}
            if response.status_code != 200 or "choices" not in data:
                error_msg = data.get("error", {}).get("message", response.text)
                raise Exception(f"OpenRouter HTTP {response.status_code}: {error_msg}")
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

    # ── STEP 1: Intent Extraction (Memory-Aware) ──
    system_intent = (
        'You are a STRICT intent extraction API for an Indian travel booking assistant. '
        'You MUST output ONLY valid JSON. Do NOT answer the user. Do NOT chat. '
        'Extract travel info into EXACTLY this JSON format: '
        '{"mode": "bus|train|flight|all", "source": "City", "destination": "City", '
        '"date": "DD-MM-YYYY", "preference": "cheapest|ac|seater|sleeper|null", '
        '"intent": "search|change_mode|change_date|greeting|help|cancel"}. '
        '\n'
        'MEMORY RULES (CRITICAL): '
        '- You will receive PREVIOUSLY KNOWN context. ALWAYS preserve those values. '
        '- Only OVERRIDE a field if the user EXPLICITLY provides a new value. '
        '- If the user says just "tomorrow" → only update date, keep source/destination/mode from context. '
        '- If the user says "by train" or "show trains" → only update mode, keep everything else. '
        '- If the user says "show flights instead" → intent is "change_mode", update mode to "flight", keep source/destination/date. '
        '- NEVER set a field to null if it was already known from context. '
        '\n'
        'MODE DETECTION: '
        '- bus/coach/travels/redbus → mode is "bus". '
        '- train/express/railway/irctc → mode is "train". '
        '- flight/fly/plane/air → mode is "flight". '
        '- compare/comparison/all/every mode/cheapest way/best way/options → mode is "all". '
        '- If the user just says "travel"/"ticket"/"go to" without specifying mode, set mode to "all". '
        '\n'
        'PREFERENCE DETECTION: '
        '- cheapest/lowest price/budget → preference is "cheapest". '
        '- ac/air conditioned → preference is "ac". '
        '- seater/seat → preference is "seater". '
        '- sleeper/berth → preference is "sleeper". '
        '\n'
        'SHORT MESSAGE UNDERSTANDING: '
        '- "tomorrow" / "today" / "next friday" / "15 June" → update date only. '
        '- "by train" / "train" → update mode only. '
        '- "2 people" → ignore (not a field we track). '
        '- City name alone (e.g. "Coimbatore") → likely source or destination based on context. '
        '- "from X" → source is X. "to Y" → destination is Y. '
        '\n'
        'DATE RULES: '
        '- If date is missing AND not in context, set date to null (do NOT guess). '
        f'- Convert relative dates: today={today}, tomorrow={tomorrow}. '
        '- "next week" means 7 days from today. "day after tomorrow" means 2 days from today. '
        '- "tonight" means today. "this weekend" means the coming Saturday. '
        '\n'
        'INTENT DETECTION: '
        '- Normal search → intent is "search". '
        '- "show X instead" / "switch to X" → intent is "change_mode". '
        '- Changing date only → intent is "change_date". '
        '- Greetings (hi/hello/hey) → intent is "greeting". '
        '- If no travel info at all → return all fields as null with intent "greeting" or "help". '
        '\n'
        'IMPORTANT: Only set source/destination if the user EXPLICITLY mentions cities/places. '
        'DO NOT infer city names from non-city words.'
    )

    # ── Build memory-aware context ──
    context = request.context or {}
    merged_query = request.query

    # Build context string from stored partial_intent
    ctx_parts = []
    if context.get("mode"):
        ctx_parts.append(f"mode: {context['mode']}")
    if context.get("source"):
        ctx_parts.append(f"source: {context['source']}")
    if context.get("destination"):
        ctx_parts.append(f"destination: {context['destination']}")
    if context.get("date"):
        ctx_parts.append(f"date: {context['date']}")
    if context.get("preference"):
        ctx_parts.append(f"preference: {context['preference']}")
    ctx_str = ", ".join(ctx_parts) if ctx_parts else "None"

    # Build conversation history
    history_str = ""
    if request.history:
        history_msgs = []
        for msg in request.history[-8:]:
            role = "User" if msg.get("type") == "user" else "Assistant"
            text = msg.get("text", "")
            if len(text) > 300:
                text = text[:300] + "... [truncated]"
            history_msgs.append(f"{role}: {text}")
        if history_msgs:
            history_str = "\n".join(history_msgs)

    # Assemble the full prompt with memory context
    merged_query = (
        f"PREVIOUSLY KNOWN CONTEXT (preserve these unless user overrides): [{ctx_str}]\n"
    )
    if history_str:
        merged_query += f"\nCONVERSATION HISTORY (for understanding flow only):\n{history_str}\n"
    merged_query += f"\nLATEST USER MESSAGE (extract intent from this): {request.query}"
    print(f"Merged query: {merged_query[:500]}")

    try:
        intent_raw = await get_ai_response(merged_query, system_intent, json_mode=True)
        intent = extract_json_from_text(intent_raw)
        print(f"Parsed intent: {intent}")
    except Exception as e:
        print(f"Intent extraction failed: {e}")
        return {"type": "chat", "message": f"Sorry, I couldn't understand your request. Error details: {str(e)}"}

    # ── STEP 2: Memory Merge — Combine AI extraction with stored context ──
    # The AI should preserve context, but we double-check here
    source_raw = intent.get("source") or intent.get("origin") or context.get("source")
    destination_raw = intent.get("destination") or context.get("destination")
    date = intent.get("date") or context.get("date")
    mode = (intent.get("mode") or context.get("mode") or "").lower()
    preference = intent.get("preference") or context.get("preference")
    detected_intent = (intent.get("intent") or "search").lower()

    # Update intent dict with merged values
    intent["source"] = source_raw
    intent["destination"] = destination_raw
    intent["date"] = date
    intent["mode"] = mode if mode else None
    intent["preference"] = preference
    print(f"Merged intent: src={source_raw}, dst={destination_raw}, date={date}, mode={mode}, pref={preference}")

    # Has some travel intent but missing required fields
    query_lower = request.query.lower()
    has_travel_intent = (
        any(kw in query_lower for kw in [
            "bus", "train", "flight", "fly", "travel", "ticket", "book",
            "go to", "going to", "from", "ride", "journey", "trip",
            "search", "find", "show", "check", "compare"
        ])
        or (source_raw and destination_raw)
        or detected_intent in ("search", "change_mode", "change_date")
        or bool(context)  # If we already have context, user is in a booking flow
    )

    if has_travel_intent:
        partial_intent = {
            "source": source_raw,
            "destination": destination_raw,
            "date": date,
            "mode": mode if mode else None,
            "preference": preference,
        }

        # Determine what's missing
        missing_fields = []
        missing_keys = []
        if not source_raw:
            missing_fields.append("source city")
            missing_keys.append("source city")
        if not destination_raw:
            missing_fields.append("destination city")
            missing_keys.append("destination city")
        if not date:
            missing_fields.append("travel date")
            missing_keys.append("travel date")
        if not mode:
            missing_fields.append("travel mode")
            missing_keys.append("travel mode")

        if missing_fields:
            # ── SMART SINGLE-QUESTION SLOT FILLING ──
            # Ask for only ONE missing field at a time, in priority order
            # Priority: source → destination → mode → date
            known_parts = []
            if source_raw:
                known_parts.append(f"from **{source_raw.title()}**")
            if destination_raw:
                known_parts.append(f"to **{destination_raw.title()}**")
            if mode:
                mode_emoji = {"bus": "🚌", "train": "🚆", "flight": "✈️", "all": "🔄"}.get(mode, "")
                known_parts.append(f"by **{mode}** {mode_emoji}")
            if date:
                known_parts.append(f"on **{date}**")

            # Acknowledge what we know
            if known_parts:
                ack = "Got it! " + " ".join(known_parts) + ". "
            else:
                ack = "I'd love to help you find tickets! "

            # Ask for the FIRST missing field only (natural, concise)
            first_missing = missing_fields[0]
            if first_missing == "source city":
                question = "Where are you traveling **from**?"
            elif first_missing == "destination city":
                question = "Where do you want to **go**?"
            elif first_missing == "travel mode":
                question = "How would you like to travel — bus 🚌, train 🚆, or flight ✈️?"
            elif first_missing == "travel date":
                question = "What date would you like to travel?"
            else:
                question = f"Could you tell me your {first_missing}?"

            return {
                "type": "ask_details",
                "message": ack + question,
                "partial_intent": partial_intent,
                "missing": missing_keys
            }

    # ── STEP 3: No travel intent at all → chat ──
    if not source_raw or not destination_raw:
        system_chat = (
            "You are a friendly, fast, and professional AI travel assistant for India. "
            "Your personality is warm, concise, and human-like. Use emojis naturally (🚌 🚆 ✈️). "
            "NEVER give long robotic paragraphs. Keep responses SHORT (2-4 sentences max). "
            "If the user greets you, greet them back warmly and briefly mention you can help with buses, trains, and flights. "
            "If they ask about you, explain you are an AI travel assistant that finds live bus, train, and flight tickets across India. "
            "If they ask anything off-topic, answer briefly and gently guide them back to booking. "
            "If they seem to want to travel but haven't given details, ask what route they want. "
            "NEVER say 'How can I assist you today?' — instead say something natural like "
            "'Where would you like to go?' or 'What trip are you planning?' "
            "Keep it conversational, fast, and smart."
        )
        try:
            chat_msg = await get_ai_response(request.query, system_chat, history=request.history)
            return {"type": "chat", "message": chat_msg}
        except Exception:
            return {
                "type": "chat",
                "message": (
                    "👋 Hey there! I'm your AI travel buddy.\n\n"
                    "I can find you live tickets for:\n"
                    "🚌 **Buses** • 🚆 **Trains** • ✈️ **Flights**\n\n"
                    "Just tell me where you want to go!\n"
                    "*Example: \"Bus from Chennai to Bangalore tomorrow\"*"
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

        # ── STEP 6.5: Apply Preferences ──
        preference = intent.get("preference")
        if preference == "ac":
            results = [r for r in results if "ac" in str(r.get("type", "")).lower() or "ac" in str(r.get("coach", "")).lower() or "ac" in str(r.get("seats", "")).lower()]
        elif preference == "seater":
            results = [r for r in results if "seat" in str(r.get("type", "")).lower() or "seater" in str(r.get("type", "")).lower()]
        elif preference == "sleeper":
            results = [r for r in results if "sleep" in str(r.get("type", "")).lower() or "sleeper" in str(r.get("type", "")).lower()]
        
        if preference == "cheapest":
            results.sort(key=lambda x: parse_price(x.get("price")))

        # ── STEP 7: Enrich results with booking URLs and extra details ──
        ai_recommendation = ""
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

            # Generate AI Recommendation
            try:
                top_results = "\n".join([
                    f"- {t.get('mode', '').title()}: {t.get('operator', t.get('airline', t.get('train', 'Unknown')))} | Price: {t.get('price')} | Duration: {t.get('duration')} | Departs: {t.get('departure')}"
                    for t in results[:8]
                ])
                prompt = (
                    f"You are a travel expert analyzing tickets from {source_raw} to {destination_raw}.\n"
                    f"Here are the top options sorted by price:\n{top_results}\n\n"
                    f"Provide a brief, helpful recommendation (2-3 sentences). "
                    f"Highlight the best and worst transport sectors based on price vs duration, and give your final recommendation."
                )
                sys_prompt = "You are an expert AI Travel agent. Keep recommendations concise and use emojis. Do not output JSON."
                ai_recommendation = await get_ai_response(prompt, sys_prompt)
            except Exception as e:
                print(f"AI Recommendation failed: {e}")
                ai_recommendation = "Our AI couldn't generate a custom recommendation right now, but you can explore the options below!"

        else:
            booking_base_url = generate_booking_url(mode, source_raw, destination_raw, date, {})
            for ticket in results:
                ticket["booking_url"] = booking_base_url
            
            source_sites = {
                "bus": "RedBus",
                "flight": "Google Flights",
                "train": "IRCTC (Live)"
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
                "ai_recommendation": ai_recommendation
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
