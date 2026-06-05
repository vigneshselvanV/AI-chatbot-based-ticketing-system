import asyncio, sys, json, os
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import httpx
from dotenv import load_dotenv
load_dotenv()

MODEL = "nousresearch/hermes-3-llama-3.1-405b:free"
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

SYSTEM = (
    'You are BusBot, an AI bus booking assistant. '
    'Always respond ONLY in JSON:\n'
    '{"message":"...","intent":"GREET|COLLECT|SEARCH|REDIRECT","collected":{"from_city":null,"to_city":null,"date":null,"passengers":1},'
    '"missing":["from_city","to_city","date"],"ready_to_search":false,"quick_replies":[],"field_to_ask":"from_city"}'
)

async def test_model(user_msg: str):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-OpenRouter-Title": "BusBot AI"
    }
    payload = {
        "model": MODEL,
        "max_tokens": 300,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg}
        ]
    }
    print(f"\n{'='*60}")
    print(f"Testing: '{user_msg}'")
    print(f"Model:   {MODEL}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        print(f"HTTP Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error body: {resp.text[:300]}")
            return
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        model_used = data.get("model", "unknown")
        print(f"Model responded: {model_used}")
        print(f"Raw response:\n{content}")
        # Try parse JSON
        try:
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
            print(f"\n✅ Valid JSON! intent={parsed.get('intent')}, message={parsed.get('message')}")
        except Exception as e:
            print(f"\n⚠️  JSON parse failed: {e}")

async def main():
    await test_model("hi")
    await test_model("Coimbatore to Chennai tomorrow")

asyncio.run(main())
