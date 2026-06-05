import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://127.0.0.1:8000/search"

def test_api(query, context={}, history=[]):
    data = json.dumps({'query': query, 'context': context, 'history': history}).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

score = 0
total_tests = 4
weight = 100 / total_tests

print("🚌 Starting Real API Evaluation Test...\n")

# TEST 1: Pure Greeting
print("Test 1: Pure Greeting ('hi')")
res1 = test_api("hi")
passed1 = False
if "error" not in res1:
    if res1.get("type") == "ask_details":
        # Check if it asks for from_city as requested by GREET intent
        if "missing" in res1 and "from_city" in res1.get("missing", []):
             passed1 = True
             print("  ✅ Passed: Bot correctly greeted and asked for from_city.")
        else:
             print("  ❌ Failed: Bot did not explicitly mark from_city as missing.")
    else:
        print(f"  ❌ Failed: Bot returned wrong type ({res1.get('type')})")
else:
    print(f"  ❌ Failed: Server error -> {res1['error']}")

if passed1: score += weight


# TEST 2: Progressive Slot Filling (Giving only Source)
print("\nTest 2: Progressive Form Filling ('Coimbatore')")
res2 = test_api("Coimbatore")
passed2 = False
if "error" not in res2:
    if res2.get("type") == "ask_details":
        partial = res2.get("partial_intent", {})
        if partial.get("from_city", "").lower() == "coimbatore":
             passed2 = True
             print("  ✅ Passed: Bot correctly extracted 'Coimbatore' and asked for destination.")
        else:
             print(f"  ❌ Failed: Did not extract 'Coimbatore'. Extracted: {partial}")
    else:
        print(f"  ❌ Failed: Returned wrong type {res2.get('type')}")
else:
    print(f"  ❌ Failed: Server error -> {res2['error']}")

if passed2: score += weight


# TEST 3: Single Shot Booking
print("\nTest 3: Single Shot Extraction ('Bus from Chennai to Madurai tomorrow')")
# When ready_to_search is true, the backend triggers the scraper. It might return "tickets" or "connecting_route"
res3 = test_api("Bus from Chennai to Madurai tomorrow")
passed3 = False
if "error" not in res3:
    if res3.get("type") in ["tickets", "connecting_route"]:
        passed3 = True
        print(f"  ✅ Passed: Bot extracted all fields correctly and triggered scraper. Returned type: {res3.get('type')}")
    elif res3.get("type") == "ask_details":
        print(f"  ❌ Failed: Bot did not trigger search. It asked for: {res3.get('missing')}")
    else:
        print(f"  ❌ Failed: Returned unexpected type {res3.get('type')}")
else:
    # If the scraper itself throws a 500 error, we still need to evaluate if it tried to scrape.
    if "HTTP Error 500" in res3["error"]:
        print("  ⚠️ Scraper hit a 500 error, but intent extraction likely worked.")
    else:
        print(f"  ❌ Failed: Server error -> {res3['error']}")

if passed3: score += weight


# TEST 4: Airplane Redirection
print("\nTest 4: Redirection Rule ('Flight from Mumbai to Delhi')")
res4 = test_api("Flight from Mumbai to Delhi")
passed4 = False
if "error" not in res4:
    if res4.get("type") == "ask_details":
        msg = res4.get("message", "").lower()
        if "bus" in msg:
            passed4 = True
            print("  ✅ Passed: Bot correctly redirected flight request to bus.")
        else:
            print("  ❌ Failed: Message didn't contain bus redirect logic.")
    else:
        print("  ❌ Failed: Did not ask for details on redirect.")
else:
    print(f"  ❌ Failed: Server error -> {res4['error']}")

if passed4: score += weight

print(f"\n====================================")
print(f"🎯 FINAL SCORE: {int(score)} / 100")
print(f"====================================")
