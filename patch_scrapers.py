import re

with open("scrapers.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace Date helpers
date_helpers = """# ════════════════════════════════════════════════════════════
# Date helpers
# ════════════════════════════════════════════════════════════
def resolve_date(date_str: str):
    from datetime import datetime, timedelta
    today = datetime.now()
    if date_str == "today": return today
    if date_str == "tomorrow": return today + timedelta(days=1)
    if date_str == "day_after_tomorrow": return today + timedelta(days=2)
    
    try:
        if date_str and len(date_str) == 10:
            if date_str[4] == "-":
                return datetime.strptime(date_str, "%Y-%m-%d")
            elif date_str[2] == "-":
                return datetime.strptime(date_str, "%d-%m-%Y")
    except Exception:
        pass
    return today

def format_date_for_redbus(date_str: str) -> str:
    d = resolve_date(date_str)
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    return f"{d.day:02d}-{months[d.month-1]}-{d.year}"

def format_date_for_abhibus(date_str: str) -> str:
    d = resolve_date(date_str)
    return f"{d.day:02d}-{d.month:02d}-{d.year}"
"""
content = re.sub(
    r"# ════════════════════════════════════════════════════════════\n# Date helpers\n# ════════════════════════════════════════════════════════════.*?def build_redbus_url[^\n]*\n.*?\)\n",
    date_helpers,
    content,
    flags=re.DOTALL
)

# Replace everything from STEP 1 onwards
scraping_logic = """# ════════════════════════════════════════════════════════════
# STEP 1 — Playwright RedBus
# ════════════════════════════════════════════════════════════
async def _scrape_redbus(from_city: str, to_city: str, date: str) -> list:
    from_slug = from_city.lower().replace(" ", "-")
    to_slug = to_city.lower().replace(" ", "-")
    date_str = format_date_for_redbus(date)
    url = f"https://www.redbus.in/bus-tickets/{from_slug}-to-{to_slug}?doj={date_str}"
    
    results = []
    print(f"[REDBUS] Navigating to: {url}")
    
    async with async_playwright() as pw:
        browser = None
        try:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--window-size=1366,768",
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
            )
            page = await context.new_page()
            
            try:
                await Stealth().apply_stealth_async(page)
            except Exception:
                pass
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            try:
                await page.wait_for_selector(".bus-item", timeout=20000)
            except PlaywrightTimeout:
                pass
                
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            buses = await page.evaluate('''
                () => {
                    const items = document.querySelectorAll('.bus-item');
                    return Array.from(items).map(item => {
                        const getText = sel => item.querySelector(sel)?.innerText?.trim() || '';
                        return {
                            operator: getText('.travels'),
                            bus_type: getText('.bus-type'),
                            departure: getText('.dp-time'),
                            arrival: getText('.bp-time'),
                            duration: getText('.dur'),
                            price: getText('.fare .f-19') || getText('.fare span'),
                            seats_available: getText('.seat-left') || "0",
                            rating: parseFloat(getText('.rating-container')) || 0.0,
                            cancellation: (item.querySelector('[class*="cancel"]')?.innerText || "").includes('Free'),
                            live_tracking: item.querySelector('[class*="tracking"]') !== null
                        };
                    });
                }
            ''')
            
            results = [b for b in buses if b.get('operator') and b.get('price')]
        except Exception as e:
            print(f"[REDBUS] Error: {e}")
        finally:
            if browser:
                await browser.close()
                
    return results

# ════════════════════════════════════════════════════════════
# STEP 2 — Playwright AbhiBus
# ════════════════════════════════════════════════════════════
async def _scrape_abhibus(from_city: str, to_city: str, date: str) -> list:
    from_slug = from_city.lower().replace(" ", "-")
    to_slug = to_city.lower().replace(" ", "-")
    date_str = format_date_for_abhibus(date)
    url = f"https://www.abhibus.com/bus/{from_slug}-to-{to_slug}/{date_str}"
    
    results = []
    print(f"[ABHIBUS] Navigating to: {url}")
    
    async with async_playwright() as pw:
        browser = None
        try:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            try:
                await page.wait_for_selector(".search-result-item", timeout=20000)
            except PlaywrightTimeout:
                pass
                
            buses = await page.evaluate('''
                () => {
                    const items = document.querySelectorAll('.search-result-item, .bus-card-item');
                    return Array.from(items).map(item => {
                        const getText = sel => item.querySelector(sel)?.innerText?.trim() || '';
                        return {
                            operator: getText('.operator-name, .bus-operator'),
                            bus_type: getText('.bus-type, .coach-type'),
                            departure: getText('.departure-time, .dep-time'),
                            arrival: getText('.arrival-time, .arr-time'),
                            duration: getText('.journey-duration, .duration'),
                            price: getText('.seat-fare, .price-val'),
                            seats_available: getText('.available-seats, .seats-left') || "0",
                            rating: parseFloat(getText('.rating-value')) || 0.0,
                            cancellation: (getText('.cancellation-policy') || "").includes('Free')
                        };
                    });
                }
            ''')
            
            results = [b for b in buses if b.get('operator') and b.get('price')]
        except Exception as e:
            print(f"[ABHIBUS] Error: {e}")
        finally:
            if browser:
                await browser.close()
                
    return results

# ════════════════════════════════════════════════════════════
# STEP 3 & 4 — MMT & GoIbibo Stubs
# ════════════════════════════════════════════════════════════
async def _scrape_mmt_bus(from_city: str, to_city: str, date: str) -> list:
    # Future implementation for MMT buses
    print("[MMT] Scraper stub called")
    return []

async def _scrape_goibibo_bus(from_city: str, to_city: str, date: str) -> list:
    # Future implementation for GoIbibo buses
    print("[GOIBIBO] Scraper stub called")
    return []

# ════════════════════════════════════════════════════════════
# Master Scraper & Deduplication
# ════════════════════════════════════════════════════════════
def deduplicate_buses(buses: list) -> list:
    seen = set()
    unique = []
    for bus in buses:
        key = f"{bus.get('operator')}-{bus.get('departure')}"
        if key not in seen:
            seen.add(key)
            unique.append(bus)
    return unique

def get_static_fallback(from_city: str, to_city: str, date: str) -> dict:
    return {
        "is_fallback": True,
        "message": "⚠️ Live data unavailable right now. Check directly on these sites:",
        "links": [
            {
                "name": "RedBus",
                "url": f"https://www.redbus.in/bus-tickets/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}?doj={format_date_for_redbus(date)}",
                "icon": "🔴"
            },
            {
                "name": "AbhiBus",
                "url": f"https://www.abhibus.com/bus/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}?doj={format_date_for_abhibus(date)}",
                "icon": "🟠"
            },
            {
                "name": "MakeMyTrip",
                "url": f"https://www.makemytrip.com/bus-tickets/{from_city.lower().replace(' ', '-')}-to-{to_city.lower().replace(' ', '-')}/",
                "icon": "🔵"
            }
        ]
    }

# ════════════════════════════════════════════════════════════
# PUBLIC API — scrape_bus()
# ════════════════════════════════════════════════════════════
async def scrape_bus(source: str, destination: str, date: str) -> list | dict:
    print(f"\\n[BUS] ══ scrape_bus: {source} → {destination}  date={date} ══")
    
    scrapers = [
        {"name": "redbus", "fn": lambda: _scrape_redbus(source, destination, date)},
        {"name": "abhibus", "fn": lambda: _scrape_abhibus(source, destination, date)},
        {"name": "mmt", "fn": lambda: _scrape_mmt_bus(source, destination, date)},
        {"name": "goibibo", "fn": lambda: _scrape_goibibo_bus(source, destination, date)}
    ]
    
    all_results = []
    
    for scraper in scrapers:
        print(f"[MASTER] Trying {scraper['name']}...")
        try:
            results = await scraper["fn"]()
            if results and len(results) > 0:
                all_results.extend(results)
                if len(all_results) >= 5:
                    break
        except Exception as e:
            print(f"[MASTER] {scraper['name']} failed: {e}")
            continue
            
    if len(all_results) == 0:
        print("[MASTER] All sources failed, returning static fallback dict.")
        return get_static_fallback(source, destination, date)
        
    unique = deduplicate_buses(all_results)
    
    try:
        unique.sort(key=lambda a: a.get('departure', '99:99'))
    except Exception:
        pass
        
    normalised = [_normalise_result(r, "live") for r in unique]
    print(f"[MASTER] ── Final result: {len(normalised)} buses")
    return normalised

# ════════════════════════════════════════════════════════════
# CLI test harness
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import asyncio
    async def _test():
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        print("=" * 60)
        print("  BusBot Scraper CLI Test")
        print("=" * 60)
        buses = await scrape_bus("Coimbatore", "Chennai", tomorrow)
        if isinstance(buses, dict):
            print("Returned Fallback Dictionary:")
            print(buses)
        else:
            print(f"\\nReturned {len(buses)} buses:\\n")
            for i, b in enumerate(buses[:5], 1):
                print(f"  [{i}] {b['operator']} | {b['bus_type']}")
                print(f"       {b['departure']} → {b['arrival']}  ({b['duration']})  {b['price']}")
                print(f"       Rating: {b['rating']}  Seats: {b['seats_available']}  Source: {b['source']}")
                print(f"       Amenities: {', '.join(b['amenity_list'][:4])}")
                print()

    asyncio.run(_test())
"""

content = re.sub(
    r"# ════════════════════════════════════════════════════════════\n# STEP 1 — Playwright \(primary, headless Chromium\)\n# ════════════════════════════════════════════════════════════.*",
    scraping_logic,
    content,
    flags=re.DOTALL
)

with open("scrapers.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to scrapers.py")
