import sys, os, py_compile
from datetime import datetime, timedelta

sys.path.insert(0, '.')

PASS = "[PASS]"
FAIL = "[FAIL]"

print("=" * 55)
print("   BusBot Quick Unit Tests")
print("=" * 55)

failures = []

def check(name, ok, detail=""):
    tag = PASS if ok else FAIL
    print(f"  {tag} {name}" + (f" => {detail}" if detail else ""))
    if not ok:
        failures.append((name, detail))

# ── 1. Syntax ──────────────────────────────────────────────
print("\n[1] Python Syntax Check")
for fname in ["main.py", "scrapers.py"]:
    try:
        py_compile.compile(fname, doraise=True)
        check(f"Syntax {fname}", True)
    except py_compile.PyCompileError as e:
        check(f"Syntax {fname}", False, str(e)[:120])

# ── 2. Date Resolver ───────────────────────────────────────
print("\n[2] Date Resolver")
from main import resolve_relative_date
today  = datetime.now().strftime("%d-%m-%Y")
tom    = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
day2   = (datetime.now() + timedelta(days=2)).strftime("%d-%m-%Y")

cases = [
    ("tomorrow",           None,         tom),
    ("tommorow",           None,         tom),
    ("tommorrow",          None,         tom),
    ("today",              None,         today),
    ("tonight",            None,         today),
    ("day after tomorrow", None,         day2),
    ("day after tommorow", None,         day2),
    ("bus from cbe tomorrow", None,      tom),
    ("",                   "05-06-2026", "05-06-2026"),
    ("nothing here",       None,         None),
]
for query, ext, exp in cases:
    result = resolve_relative_date(query, ext)
    check(f"  resolve({query!r:.35})", result == exp, f"got={result} exp={exp}")

# ── 3. Connecting Routes ───────────────────────────────────
print("\n[3] Connecting Routes")
from main import find_connecting_route
route_cases = [
    ("Coimbatore", "Ooty",         "mettupalayam"),
    ("Chennai",    "Kodaikanal",   "dindigul"),
    ("Chennai",    "Delhi",        None),
    ("Madurai",    "Rameswaram",   "ramanathapuram"),
    ("Bengaluru",  "Ooty",         "mysore"),
]
for src, dst, exp in route_cases:
    r = find_connecting_route(src, dst)
    check(f"  route({src}->{dst})", r == exp, f"got={r!r} exp={exp!r}")

# ── 4. JSON Extractor ─────────────────────────────────────
print("\n[4] JSON Extractor")
from main import extract_json_from_text
json_cases = [
    ('{"mode":"bus","source":"Chennai"}',        {"mode": "bus", "source": "Chennai"}),
    ('```json\n{"mode":"bus"}\n```',              {"mode": "bus"}),
    ('<think>blah</think>{"mode":"bus"}',         {"mode": "bus"}),
    ("no json here",                             {}),
    ("",                                         {}),
]
for raw, exp in json_cases:
    r = extract_json_from_text(raw)
    check(f"  extract({raw[:35]!r})", r == exp, f"got={r}")

# ── 5. System Prompt Rules ────────────────────────────────
print("\n[5] System Prompt / Code Rules")
with open("main.py", encoding="utf-8") as f:
    src = f.read()

prompt_checks = [
    ("Mode always set to bus",         'mode = "bus"' in src),
    ("Greeting fast-path present",     "is_pure_greeting" in src),
    ("Friendly error message",         "having a little trouble" in src),

    ("Bus redirect logic present",     "bus_redirect_msg" in src),
    ("Flight keyword block present",   '"flight"' in src and '"fly"' in src),
    ("Scraper import correct",         "from scrapers import scrape_bus" in src),
    ("No Ollama-only fallback",        "get_ai_response" in src),
]
for name, ok in prompt_checks:
    check(f"  {name}", ok)

# ── Summary ───────────────────────────────────────────────
print("\n" + "=" * 55)
total = len(cases) + len(route_cases) + len(json_cases) + len(prompt_checks) + 2  # +2 syntax
passed = total - len(failures)
print(f"  Total: {total}  |  Pass: {passed}  |  Fail: {len(failures)}")
print("=" * 55)

if failures:
    print("\nFailed tests:")
    for name, detail in failures:
        print(f"  x {name}" + (f"\n    -> {detail}" if detail else ""))
    sys.exit(1)
else:
    print("\nAll unit tests passed!")
    sys.exit(0)
