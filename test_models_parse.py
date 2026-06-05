import re

path = r'C:\Users\user\.gemini\antigravity-ide\brain\2156fdb8-809f-441c-8a9d-6d802a0df819\.system_generated\steps\130\content.md'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

free_models = re.findall(r'"id":"([^"]+:free)"', content)
print('Available :free models on OpenRouter:')
for m in sorted(set(free_models)):
    print(' ', m)
