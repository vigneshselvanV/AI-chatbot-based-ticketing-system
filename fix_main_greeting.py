import sys

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == '# ── STEP 2: Memory Merge — Combine AI extraction with stored context ──':
        new_lines.append('''    merged_query += f"\\nLATEST USER MESSAGE (extract intent from this): {request.query}"
    print(f"Merged query: {merged_query[:500]}")

    is_pure_greeting = request.query.strip().lower() in ["hi", "hello", "hey", "start", "busbot"]
    try:
        if is_pure_greeting and not context:
            intent = {"intent": "greeting"}
            print("Fast-path greeting triggered.")
        else:
            intent_raw = await get_ai_response(merged_query, system_intent, json_mode=True)
            intent = extract_json_from_text(intent_raw)
            print(f"Parsed intent: {intent}")
    except Exception as e:
        print(f"Intent extraction failed: {e}")
        return {"type": "chat", "message": "I'm having a little trouble connecting right now. Please try again! 🚌"}

''')
    new_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Main greeting fix applied!")
