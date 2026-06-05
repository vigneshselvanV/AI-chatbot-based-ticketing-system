import re

CSS_PATH = r"d:\-----projects-----\AI chat bot based ticketing system\one last time - Copy (2)(real data)\frontend\src\index.css"

with open(CSS_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    "#080b18": "var(--bg-base)",
    "#0d1124": "var(--bg-surface-1)",
    "#1a1f35": "var(--bg-surface-3)",
    "#1e2440": "var(--bg-surface-4)",
    "#6366f1": "var(--brand)",
    "#4f46e5": "var(--brand-hover)",
    "#ffffff": "var(--text-primary)",
    "#9ca3af": "var(--text-secondary)",
    "#6b7280": "var(--text-tertiary)",
    "#4ade80": "var(--price-color)",
    "#2d3555": "var(--border-default)",
}

# Replace case-insensitively
for old_color, new_color in replacements.items():
    content = re.sub(re.escape(old_color), new_color, content, flags=re.IGNORECASE)

with open(CSS_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("Colors replaced successfully.")
