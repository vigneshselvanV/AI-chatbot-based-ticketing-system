import sys

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "intent = await call_ai(user_query, request.history or [], system_intent)" in line:
        lines.insert(i, "        user_query = f\"Context (already known): {json.dumps(ctx)}\\nUser says: {request.query}\"\n")
        break

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Syntax fixed")
