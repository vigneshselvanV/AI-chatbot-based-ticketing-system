import sys
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == 'print(f"Scraper crashed: {e}")':
        new_lines.append('''        # ── STEP 7: Enrich results with booking URLs and extra details ──
        booking_base_url = generate_booking_url("bus", source_raw, destination_raw, date, {})
        data_source = results[0].get("source", "playwright") if results else "fallback"
        
        for ticket in results:
            if "booking_url" not in ticket:
                ticket["booking_url"] = booking_base_url

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
                "ai_recommendation": ""
            }
        }

    except Exception as e:
''')
    new_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("main.py fixed!")
