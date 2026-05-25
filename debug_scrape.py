"""Test Google Flights and RedBus Trains to find correct URL formats and DOM structure."""
import asyncio
import json
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def _create_stealth_page(playwright):
    browser = await playwright.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled', '--window-size=1920,1080']
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    return browser, page


async def test_google_flights():
    """Test Google Flights DOM structure."""
    print("=" * 60)
    print("TESTING GOOGLE FLIGHTS")
    print("=" * 60)

    async with async_playwright() as p:
        browser, page = await _create_stealth_page(p)

        # Google Flights text search URL
        url = "https://www.google.com/travel/flights?q=Flights+from+Delhi+to+Mumbai+on+1+June+2026&curr=INR&hl=en"
        print(f"Navigating to: {url}")
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(15000)

        title = await page.title()
        print(f"Title: {title}")

        body_text = await page.evaluate("() => document.body.innerText")
        with open("debug_google_flights_text.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Body text saved ({len(body_text)} chars)")

        # Print lines with times or prices
        lines = body_text.split('\n')
        print(f"Total lines: {len(lines)}")
        print("\n--- Lines with flight data ---")
        airlines = ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'AirAsia', 'Go First', 'Akasa', 'Air India Express', 'StarAir', 'Alliance Air']
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            has_airline = any(a in line for a in airlines)
            has_time = bool(re.search(r'\d{1,2}:\d{2}', line))
            has_price = '₹' in line or '₹' in line
            if has_airline or has_time or has_price:
                print(f"  L{i}: {line[:150]}")

        # Try targeted extraction
        print("\n--- Targeted Google Flights Extraction ---")
        flights = await page.evaluate("""
            () => {
                const flights = [];
                const body = document.body.innerText;
                const lines = body.split('\\n').map(l => l.trim()).filter(l => l);
                
                const airlines = ['IndiGo', 'Air India Express', 'Air India', 'SpiceJet', 'Vistara', 'AirAsia', 'Go First', 'Akasa Air', 'StarAir', 'Alliance Air', 'Fly91'];
                
                for (let i = 0; i < lines.length; i++) {
                    let foundAirline = null;
                    for (const a of airlines) {
                        if (lines[i].includes(a)) {
                            foundAirline = a;
                            break;
                        }
                    }
                    
                    if (foundAirline) {
                        const context = lines.slice(Math.max(0, i - 3), Math.min(lines.length, i + 15));
                        const contextStr = context.join(' | ');
                        
                        // Collect times from surrounding lines
                        const allTimes = [];
                        for (const ctx of context) {
                            const m = ctx.match(/\\b(\\d{1,2}:\\d{2})\\s*(AM|PM|am|pm)?\\b/g);
                            if (m) allTimes.push(...m);
                        }
                        
                        // Duration
                        let duration = '--';
                        for (const ctx of context) {
                            const m = ctx.match(/(\\d{1,2})\\s*(?:hr?|hour)\\s*(\\d{1,2})?\\s*(?:min|m)?/i);
                            if (m) { 
                                duration = m[2] ? `${m[1]}h ${m[2]}m` : `${m[1]}h`;
                                break; 
                            }
                        }
                        
                        // Price
                        let price = '--';
                        for (const ctx of context) {
                            const m = ctx.match(/₹\\s*([\\d,]+)/);
                            if (m) { price = '₹' + m[1]; break; }
                        }
                        
                        flights.push({
                            airline: foundAirline,
                            departure: allTimes[0] || '--',
                            arrival: allTimes.length > 1 ? allTimes[1] : '--',
                            duration: duration,
                            price: price,
                            raw_times: allTimes.slice(0, 4),
                            raw_context: contextStr.substring(0, 250)
                        });
                    }
                    if (flights.length >= 8) break;
                }
                return flights;
            }
        """)

        print(f"\nExtracted {len(flights)} flights:")
        for f in flights:
            print(f"  {f['airline']}: dep={f['departure']} arr={f['arrival']} dur={f['duration']} price={f['price']}")
            print(f"    Times: {f.get('raw_times', [])}")
            print(f"    Context: {f.get('raw_context', '')[:200]}")

        await page.screenshot(path="debug_google_flights.png", full_page=False)
        await browser.close()


async def test_redbus_trains():
    """Test RedBus train (RedRail) DOM structure."""
    print("\n" + "=" * 60)
    print("TESTING REDBUS TRAINS (RedRail)")
    print("=" * 60)

    async with async_playwright() as p:
        browser, page = await _create_stealth_page(p)

        # Try multiple RedBus train URLs
        urls = [
            "https://www.redbus.in/railways/Chennai-to-Mumbai",
            "https://www.redbus.in/railways/trains-between-stations?fromCity=MAS&toCity=CSTM&date=01-Jun-2026",
            "https://www.redbus.in/railways/MAS-to-CSTM",
        ]

        for url in urls:
            print(f"\n--- Trying: {url} ---")
            try:
                api_results = []
                async def capture_api(response):
                    try:
                        resp_url = response.url
                        if any(kw in resp_url.lower() for kw in ['train', 'rail', 'search', 'schedule']):
                            ct = response.headers.get('content-type', '')
                            if 'json' in ct:
                                body = await response.text()
                                if len(body) > 100:
                                    data = json.loads(body)
                                    print(f"  [API] {resp_url[:100]} - keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                                    api_results.append({'url': resp_url, 'data': data})
                    except:
                        pass

                page.on('response', capture_api)
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(12000)

                title = await page.title()
                body_text = await page.evaluate("() => document.body.innerText.substring(0, 3000)")
                print(f"  Title: {title}")

                has_trains = any(kw in body_text for kw in ['Express', 'Rajdhani', 'departure', 'Departs'])
                has_error = any(kw in body_text.lower() for kw in ['oops', '404', 'not found'])
                print(f"  Has train data: {has_trains}, Has error: {has_error}")

                if has_trains and not has_error:
                    print(f"  *** THIS URL WORKS! ***")
                    # Save the text
                    with open("debug_redbus_train_text.txt", "w", encoding="utf-8") as f:
                        f.write(body_text)

                    # Print relevant lines
                    lines = body_text.split('\n')
                    train_keywords = ['Express', 'Rajdhani', 'Shatabdi', 'Duronto', 'Vande Bharat', 'Superfast', 'Mail', 'Special']
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if any(kw in line for kw in train_keywords) or re.search(r'\b\d{5}\b', line):
                            print(f"    L{i}: {line[:120]}")

                    # Try extraction
                    trains = await page.evaluate("""
                        () => {
                            const trains = [];
                            const body = document.body.innerText;
                            const lines = body.split('\\n').map(l => l.trim()).filter(l => l);
                            
                            const trainPatterns = ['Express', 'Rajdhani', 'Shatabdi', 'Duronto', 'Vande Bharat', 'Superfast', 'Mail', 'Garib Rath', 'Humsafar', 'Tejas', 'Special'];
                            
                            for (let i = 0; i < lines.length; i++) {
                                const line = lines[i];
                                const hasTrainName = trainPatterns.some(p => line.includes(p));
                                const numberMatch = line.match(/\\b(\\d{5})\\b/);
                                
                                if (hasTrainName || numberMatch) {
                                    const context = lines.slice(Math.max(0, i - 3), Math.min(lines.length, i + 10));
                                    const contextStr = context.join(' | ');
                                    
                                    const times = [];
                                    for (const ctx of context) {
                                        const m = ctx.match(/\\b(\\d{1,2}:\\d{2})\\b/g);
                                        if (m) times.push(...m);
                                    }
                                    
                                    const durMatch = contextStr.match(/(\\d{1,2}h\\s*\\d{1,2}m)/i);
                                    const priceMatch = contextStr.match(/₹\\s*([\\d,]+)/);
                                    const numMatch = contextStr.match(/\\b(\\d{5})\\b/);
                                    
                                    trains.push({
                                        train: line.substring(0, 60),
                                        number: numMatch ? numMatch[1] : '--',
                                        departure: times[0] || '--',
                                        arrival: times.length > 1 ? times[1] : '--',
                                        duration: durMatch ? durMatch[1] : '--',
                                        price: priceMatch ? '₹' + priceMatch[1] : '--',
                                        raw_context: contextStr.substring(0, 200)
                                    });
                                }
                                if (trains.length >= 8) break;
                            }
                            return trains;
                        }
                    """)

                    print(f"\n  Extracted {len(trains)} trains:")
                    for t in trains:
                        print(f"    {t['train']}: #{t['number']} dep={t['departure']} arr={t['arrival']} dur={t['duration']} price={t['price']}")
                        print(f"      Context: {t.get('raw_context', '')[:150]}")

                    await page.screenshot(path="debug_redbus_train.png", full_page=False)
                    page.remove_listener('response', capture_api)
                    break
                else:
                    print(f"  First 300 chars: {body_text[:300]}")

                page.remove_listener('response', capture_api)
            except Exception as e:
                print(f"  Error: {e}")

        await browser.close()


async def main():
    await test_google_flights()
    await test_redbus_trains()
    print("\n\nDone! Check debug_google_flights.png and debug_redbus_train.png")

if __name__ == "__main__":
    asyncio.run(main())
