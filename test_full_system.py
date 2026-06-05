"""
=============================================================
 BusBot Full System Test Suite  v2
 Tests: Backend API, date resolver, scraper, frontend build
=============================================================
"""
import subprocess
import sys
import os
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "frontend")
API_BASE = "http://localhost:8000"

GREEN  = "\033[92m"
RED    = "\033[91m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

PASS = f"{GREEN}[PASS]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"
INFO = f"{BLUE}[INFO]{RESET}"
WARN = f"{YELLOW}[WARN]{RESET}"

results = []

def record(name, passed, detail=""):
    tag = PASS if passed else FAIL
    print(f"  {tag} {name}" + (f" -- {detail}" if detail else ""))
    results.append((name, passed, detail))


# ─────────────────────────────────────────────────────────────
# SECTION 1 — Python syntax
# ─────────────────────────────────────────────────────────────
def test_python_syntax():
    print(f"\n{INFO} === 1. Python Syntax Check ===")
    for fname in ["main.py", "scrapers.py"]:
        fpath = os.path.join(ROOT, fname)
        r = subprocess.run([sys.executable, "-m", "py_compile", fpath], capture_output=True, text=True)
        record(f"Syntax: {fname}", r.returncode == 0, r.stderr.strip()[:150] if r.stderr else "")


# ─────────────────────────────────────────────────────────────
# SECTION 2 — Date resolver
# ─────────────────────────────────────────────────────────────
def test_date_resolver():
    print(f"\n{INFO} === 2. Date Resolver ===")
    sys.path.insert(0, ROOT)
    try:
        from main import resolve_relative_date
        today    = datetime.now().strftime("%d-%m-%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        day2     = (datetime.now() + timedelta(days=2)).strftime("%d-%m-%Y")
        cases = [
            ("tomorrow",                None,         tomorrow),
            ("tommorow",                None,         tomorrow),
            ("tommorrow",               None,         tomorrow),
            ("today",                   None,         today),
            ("tonight",                 None,         today),
            ("day after tomorrow",      None,         day2),
            ("day after tommorow",      None,         day2),
            ("bus from cbe tomorrow",   None,         tomorrow),
            ("",                        "05-06-2026", "05-06-2026"),
            ("nothing here",            None,         None),
        ]
        for q, ext, exp in cases:
            r = resolve_relative_date(q, ext)
            record(f"  resolve({q!r:.38})", r == exp, f"got={r!r} exp={exp!r}" if r != exp else "")
    except Exception as e:
        record("Date resolver", False, str(e))


# ─────────────────────────────────────────────────────────────
# SECTION 3 — Connecting routes
# ─────────────────────────────────────────────────────────────
def test_connecting_routes():
    print(f"\n{INFO} === 3. Connecting Routes ===")
    sys.path.insert(0, ROOT)
    try:
        from main import find_connecting_route
        cases = [
            ("Coimbatore", "Ooty",        "mettupalayam"),
            ("Chennai",    "Kodaikanal",  "dindigul"),
            ("Chennai",    "Delhi",       None),
            ("Madurai",    "Rameswaram",  "ramanathapuram"),
            ("Bengaluru",  "Ooty",        "mysore"),
        ]
        for src, dst, exp in cases:
            r = find_connecting_route(src, dst)
            record(f"  route({src} -> {dst})", r == exp, f"got={r!r} exp={exp!r}" if r != exp else "")
    except Exception as e:
        record("Connecting routes", False, str(e))


# ─────────────────────────────────────────────────────────────
# SECTION 4 — JSON extractor
# ─────────────────────────────────────────────────────────────
def test_json_extractor():
    print(f"\n{INFO} === 4. JSON Extractor ===")
    sys.path.insert(0, ROOT)
    try:
        from main import extract_json_from_text
        cases = [
            ('{"mode":"bus","source":"Chennai"}',     {"mode": "bus", "source": "Chennai"}),
            ('```json\n{"mode":"bus"}\n```',           {"mode": "bus"}),
            ('<think>x</think>{"mode":"bus"}',        {"mode": "bus"}),
            ("no json here",                          {}),
            ("",                                      {}),
        ]
        for raw, exp in cases:
            r = extract_json_from_text(raw)
            record(f"  extract({raw[:36]!r})", r == exp, f"got={r!r}" if r != exp else "")
    except Exception as e:
        record("JSON extractor", False, str(e))


# ─────────────────────────────────────────────────────────────
# SECTION 5 — Frontend build
# ─────────────────────────────────────────────────────────────
def test_frontend_build():
    print(f"\n{INFO} === 5. Frontend TypeScript Build ===")
    r = subprocess.run(["npm", "run", "build"], capture_output=True, text=True, cwd=FRONTEND, shell=True)
    ok = r.returncode == 0
    ts_errors = [l for l in r.stdout.split("\n") if "error TS" in l]
    record("npm run build exits 0", ok, ("\n    " + "\n    ".join(ts_errors[:5])) if ts_errors else "")
    if ok:
        dist_html = os.path.join(FRONTEND, "dist", "index.html")
        record("dist/index.html exists", os.path.exists(dist_html))


# ─────────────────────────────────────────────────────────────
# SECTION 6 — System prompt rules (static code analysis)
# ─────────────────────────────────────────────────────────────
def test_system_prompt_rules():
    print(f"\n{INFO} === 6. System Prompt / Code Rules ===")
    try:
        with open(os.path.join(ROOT, "main.py"), "r", encoding="utf-8") as f:
            src = f.read()
        checks = [
            ("Mode always set to bus",        'mode = "bus"' in src),
            ("Greeting fast-path present",    "is_pure_greeting" in src),
            ("Friendly error message",        "having a little trouble" in src),
            ("Bus redirect logic present",    "bus_redirect_msg" in src),
            ("Flight keyword blocked",        '"flight"' in src and '"fly"' in src),
            ("Scraper import correct",        "from scrapers import scrape_bus" in src),
            ("No user-visible AI svc error",  'message": "AI Service Error' not in src),
        ]
        for name, ok in checks:
            record(f"  {name}", ok)
    except Exception as e:
        record("main.py read", False, str(e))


# ─────────────────────────────────────────────────────────────
# SECTION 7 — Live API tests
# ─────────────────────────────────────────────────────────────
def test_live_api():
    print(f"\n{INFO} === 7. Live API Tests (http://localhost:8000) ===")
    try:
        import httpx
    except ImportError:
        record("httpx available", False, "pip install httpx")
        return

    def post(payload, timeout=35):
        try:
            r = httpx.post(f"{API_BASE}/search", json=payload, timeout=timeout)
            return r.json()
        except Exception as e:
            return {"error": str(e), "type": "error"}

    # Health
    try:
        r = httpx.get(f"{API_BASE}/docs", timeout=5)
        record("Backend reachable", r.status_code in (200, 404), f"status={r.status_code}")
    except Exception as e:
        record("Backend reachable", False, str(e))
        print(f"  {WARN} Skipping live API tests — start uvicorn first")
        return

    # 7a. Greeting
    resp = post({"query": "hi", "context": {}, "history": []})
    rtype = resp.get("type")
    msg   = resp.get("message", "")
    record("Greeting: type=chat",                rtype == "chat",                              f"type={rtype}")
    record("Greeting: no flight/train mention",  "flight" not in msg.lower() and "train" not in msg.lower(), f"msg={msg[:80]}")
    record("Greeting: asks where from",          "from" in msg.lower() or "where" in msg.lower(), f"msg={msg[:80]}")
    record("Greeting: no mode list",             "irctc" not in msg.lower() and "google flights" not in msg.lower(), f"msg={msg[:80]}")

    # 7b. Flight → redirect
    resp = post({"query": "flight from Chennai to Delhi", "context": {}, "history": []})
    msg  = resp.get("message", "")
    rtype = resp.get("type")
    record("Flight query: no raw error",      "openrouter" not in msg.lower() and "traceback" not in msg.lower(), f"msg={msg[:80]}")
    record("Flight query: redirects to bus",  "bus" in msg.lower() or rtype in ("chat","ask_details"), f"type={rtype}")

    # 7c. Train → redirect
    resp = post({"query": "train from Coimbatore to Chennai", "context": {}, "history": []})
    msg  = resp.get("message", "")
    rtype = resp.get("type")
    record("Train query: redirects to bus",   "bus" in msg.lower() or rtype in ("chat","ask_details"), f"type={rtype}")

    # 7d. From+To only → ask for date
    resp = post({"query": "Coimbatore to Chennai", "context": {}, "history": []})
    rtype   = resp.get("type")
    msg     = resp.get("message", "")
    partial = resp.get("partial_intent", {})
    record("From+To: type=ask_details",              rtype == "ask_details",              f"type={rtype}")
    record("From+To: asks for date",                 "date" in msg.lower() or "travel" in msg.lower(), f"msg={msg[:80]}")
    record("From+To: partial_intent.source filled",  bool(partial.get("source")),         f"partial={partial}")
    record("From+To: partial_intent.dest filled",    bool(partial.get("destination")),    f"partial={partial}")

    # 7e. Typo 'tommorow' → should resolve and return tickets
    resp = post({"query": "Coimbatore to Chennai tommorow", "context": {}, "history": []})
    rtype = resp.get("type")
    record("Typo 'tommorow': resolved to search",    rtype in ("tickets","ask_details","chat"), f"type={rtype}")
    if rtype == "ask_details":
        partial = resp.get("partial_intent", {})
        exp_tom = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        record("Typo 'tommorow': date auto-resolved", partial.get("date") == exp_tom, f"date={partial.get('date')}")

    # 7f. Full search with 'tomorrow' keyword
    print(f"  {INFO}   [7f] Full live search (up to 35s)...")
    resp  = post({"query": "bus from Coimbatore to Chennai tomorrow", "context": {}, "history": []}, timeout=40)
    rtype = resp.get("type")
    record("Full search: returns tickets/chat/route",  rtype in ("tickets","chat","connecting_route"), f"type={rtype}")
    if rtype == "tickets":
        tickets = resp.get("data", [])
        record("Full search: >= 1 result",           len(tickets) >= 1,                        f"count={len(tickets)}")
        if tickets:
            t = tickets[0]
            record("Ticket[0]: has operator",        bool(t.get("operator")),                  f"operator={t.get('operator')}")
            record("Ticket[0]: has price",           bool(t.get("price")),                     f"price={t.get('price')}")
            record("Ticket[0]: has amenities dict",  isinstance(t.get("amenities"), dict),     f"amenities={t.get('amenities')}")
            record("Ticket[0]: has booking_url",     bool(t.get("booking_url")),               f"url={str(t.get('booking_url'))[:60]}")

    # 7g. Unknown city → no raw error
    resp = post({"query": "bus from XYZ123 to ABC999 tomorrow", "context": {}, "history": []})
    msg  = resp.get("message", "")
    record("Unknown city: no traceback exposed",  "traceback" not in msg.lower() and "exception" not in msg.lower(), f"msg={msg[:100]}")
    record("Unknown city: no HTTP error string",  "openrouter" not in msg.lower() and "http 5" not in msg.lower(),  f"msg={msg[:100]}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   BusBot Full System Test Suite  v2")
    print("=" * 60)

    test_python_syntax()
    test_date_resolver()
    test_connecting_routes()
    test_json_extractor()
    test_frontend_build()
    test_system_prompt_rules()
    test_live_api()

    total  = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"  TOTAL: {total}   PASS: {passed}   FAIL: {failed}")
    print("=" * 60)

    if failed > 0:
        print(f"\n{FAIL} Failed tests:")
        for name, ok, detail in results:
            if not ok:
                print(f"  x {name}" + (f"\n    -> {detail}" if detail else ""))
        sys.exit(1)
    else:
        print(f"\n{PASS} All {total} tests passed! System is working correctly.")
        sys.exit(0)
