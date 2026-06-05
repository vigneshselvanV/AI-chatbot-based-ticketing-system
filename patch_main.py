import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace lines 468 to 480
old_block_1 = """        for ticket in results:
            ticket["mode"] = "bus"

        # ── STEP 6.5: Check if results are fallback (no real buses found) ──
        is_fallback = (
            len(results) == 3
            and results[0].get("operator", "").endswith("Travels")
            and results[1].get("operator", "").endswith("Express")
            and results[2].get("operator") == "State Transport"
        )

        # ── STEP 6.6: Smart Connecting Route Suggestion ──
        if is_fallback or len(results) == 0:"""

new_block_1 = """        is_fallback_dict = isinstance(results, dict) and results.get("is_fallback")

        if not is_fallback_dict:
            for ticket in results:
                ticket["mode"] = "bus"

        # ── STEP 6.6: Smart Connecting Route Suggestion ──
        if is_fallback_dict or len(results) == 0:"""

content = content.replace(old_block_1, new_block_1)

# Now, after connecting route fails or isn't applicable, we need to return the fallback dict if it is one.
# We'll inject this check right before STEP 6.7
old_block_2 = """        # ── STEP 6.7: Apply Preferences ──"""

new_block_2 = """        if is_fallback_dict:
            return {
                "type": "fallback",
                "data": results,
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

        # ── STEP 6.7: Apply Preferences ──"""

content = content.replace(old_block_2, new_block_2)

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to main.py")
