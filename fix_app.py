import sys

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "setConversationContext(data.partial_intent);" in line:
        lines.insert(i + 2, "        if (data.quick_replies && data.quick_replies.length > 0) {\n")
        lines.insert(i + 3, "          setSuggestedQueries(data.quick_replies);\n")
        lines.insert(i + 4, "        }\n")
        break

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("app.tsx fixed")
