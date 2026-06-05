import json

with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Replace AI Logic
ai_start_idx = code.find("# ═══════════════════════════════════════════\n# LLM Integration (OpenRouter → Ollama fallback)")
ai_end_idx = code.find("raise Exception(f\"AI Service Error: {str(e)}\")")

if ai_start_idx != -1 and ai_end_idx != -1:
    old_ai_block = code[ai_start_idx : ai_end_idx + len("raise Exception(f\"AI Service Error: {str(e)}\")")]
    new_ai_block = """# ═══════════════════════════════════════════
# LLM Integration (Multi-Model Cascade)
# ═══════════════════════════════════════════

FALLBACK_MODELS = [
    "openai/gpt-oss-120b:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-7b-it:free",
    "meta-llama/llama-3-8b-instruct:free"
]

def rule_based_parser(text: str, history: list) -> dict:
    lower_text = text.lower()
    cities = [
        "coimbatore","chennai","bangalore","bengaluru",
        "mumbai","delhi","madurai","trichy","salem",
        "ooty","kodaikanal","pondicherry","hyderabad",
        "pune","kolkata","ahmedabad","surat","jaipur",
        "kochi","calicut","thrissur","coorg","mysore"
    ]
    
    found_cities = [c for c in cities if c in lower_text]
    
    date = None
    if "today" in lower_text or "இன்று" in lower_text or "aaj" in lower_text: date = "today"
    if "tomorrow" in lower_text or "நாளை" in lower_text or "kal" in lower_text: date = "tomorrow"
    if "day after" in lower_text: date = "day_after_tomorrow"
    if "weekend" in lower_text: date = "this_weekend"
                
    collected = {
        "from_city": found_cities[0] if len(found_cities) > 0 else None,
        "to_city": found_cities[1] if len(found_cities) > 1 else None,
        "date": date,
        "passengers": 1
    }

    missing = []
    if not collected["from_city"]: missing.append("from_city")
    if not collected["to_city"]: missing.append("to_city")
    if not collected["date"]: missing.append("date")

    ready_to_search = len(missing) == 0
    field_to_ask = missing[0] if missing else None

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
        "X-Title": "BusBot AI"
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-4:]:
            role = "user" if msg.get("type") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("text", "")})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": current_model,
        "max_tokens": 300,
        "temperature": 0.1,
        "messages": messages
    }
    
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
            
            cleaned = raw_content.replace('```json', '').replace('```', '').strip()
            parsed = json.loads(cleaned)
            
            if "message" not in parsed or "intent" not in parsed:
                raise Exception("Invalid JSON structure")
                
            return parsed
            
    except (httpx.TimeoutException, httpx.RequestError) as e:
        print(f"Network timeout ({current_model}): {e} → retrying next model")
        return await call_ai(user_message, history, system_prompt, retry_count + 1)
    except Exception as e:
        print(f"AI Error ({current_model}): {e} → retrying next model")
        return await call_ai(user_message, history, system_prompt, retry_count + 1)"""
    code = code.replace(old_ai_block, new_ai_block)
else:
    print("Could not find old AI block indices.")


# 2. Replace Search Logic
search_start_idx = code.find("async def search_tickets(request: SearchRequest):")
search_end_idx = code.find("    try:\n        source = city_name(source_raw)")

if search_start_idx != -1 and search_end_idx != -1:
    old_search_block = code[search_start_idx : search_end_idx]
    
    new_search_block = """async def search_tickets(request: SearchRequest):
    print(f"Received query: {request.query}")
    
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
    "passengers": 1
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
    "passengers": 1
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
  NEVER say "I cannot help with that."
  ALWAYS redirect and keep the conversation going.

════════════════════════════════
ERROR RESPONSE FORMAT
════════════════════════════════
IF you cannot understand the query:
{
  "message": "Where are you traveling from? 🚌",
  "intent": "COLLECT",
  "collected": {
    "from_city": null, "to_city": null, "date": null, "passengers": 1
  },
  "missing": ["from_city","to_city","date"],
  "ready_to_search": false,
  "quick_replies": [],
  "field_to_ask": "from_city"
}
NEVER expose error messages to the user.
NEVER say "503" or "OpenRouter" or "AI error".
'''

    ctx = request.context or {}
    user_query = request.query
    if ctx:
        user_query = f"Context (already known): {json.dumps(ctx)}\nUser says: {request.query}"

    intent = await call_ai(user_query, request.history or [], system_intent)
    print(f"Parsed AI Intent: {intent}")

    if not intent.get("ready_to_search"):
        return {
            "type": "ask_details",
            "message": intent.get("message", "Where are you traveling from? 🚌"),
            "partial_intent": intent.get("collected", {}),
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
    intent_obj = {
        "source": source_raw,
        "destination": destination_raw,
        "date": date,
        "mode": mode,
        "preference": preference,
        "intent": "search"
    }

"""
    code = code.replace(old_search_block, new_search_block)
else:
    print("Could not find search block indices.")


with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Engine refactored.")
