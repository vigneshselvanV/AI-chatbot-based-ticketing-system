from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
import datetime

# ── Color palette ────────────────────────────────────────────────────────────
PRIMARY      = colors.HexColor('#1a1a2e')   # Deep navy
ACCENT       = colors.HexColor('#6c63ff')   # Vivid purple
ACCENT2      = colors.HexColor('#00d4aa')   # Teal
LIGHT_BG     = colors.HexColor('#f0f4ff')   # Soft blue-white
HEADER_BG    = colors.HexColor('#0f3460')   # Dark blue header
TEXT_DARK    = colors.HexColor('#1a1a2e')
TEXT_MUTED   = colors.HexColor('#555577')
WHITE        = colors.white
GOLD         = colors.HexColor('#f5a623')
GRAD_END     = colors.HexColor('#e94560')   # accent red

OUTPUT_PATH = "AI_Bus_Ticketing_System_Abstract.pdf"
W, H = A4   # 595.28 x 841.89 pts


# ── Custom canvas with header/footer ─────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page(num_pages)
            super().showPage()
        super().save()

    def draw_page(self, total):
        page = self._pageNumber
        # Footer bar
        self.setFillColor(PRIMARY)
        self.rect(0, 0, W, 28, fill=1, stroke=0)
        self.setFont("Helvetica", 8)
        self.setFillColor(WHITE)
        self.drawString(2*cm, 10, "AI Chat Bot Based Bus Ticketing System  •  Confidential")
        self.drawRightString(W - 2*cm, 10, f"Page {page} of {total}")

        # Top decorative strip (only page 1 has the big header, others get a thin strip)
        if page > 1:
            self.setFillColor(HEADER_BG)
            self.rect(0, H - 18, W, 18, fill=1, stroke=0)
            self.setFont("Helvetica-Bold", 9)
            self.setFillColor(WHITE)
            self.drawString(2*cm, H - 13, "AI Chat Bot Based Bus Ticketing System")


# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    styles = getSampleStyleSheet()

    custom = {
        'CoverTitle': ParagraphStyle(
            'CoverTitle', fontSize=26, leading=34,
            textColor=WHITE, alignment=TA_CENTER,
            fontName='Helvetica-Bold', spaceAfter=6
        ),
        'CoverSub': ParagraphStyle(
            'CoverSub', fontSize=13, leading=18,
            textColor=colors.HexColor('#c0d0ff'), alignment=TA_CENTER,
            fontName='Helvetica', spaceAfter=4
        ),
        'CoverMeta': ParagraphStyle(
            'CoverMeta', fontSize=9, leading=14,
            textColor=colors.HexColor('#a0b0dd'), alignment=TA_CENTER,
            fontName='Helvetica'
        ),
        'SectionHeading': ParagraphStyle(
            'SectionHeading', fontSize=14, leading=20,
            textColor=HEADER_BG, fontName='Helvetica-Bold',
            spaceBefore=16, spaceAfter=6,
            leftIndent=0
        ),
        'SubHeading': ParagraphStyle(
            'SubHeading', fontSize=11, leading=16,
            textColor=ACCENT, fontName='Helvetica-Bold',
            spaceBefore=10, spaceAfter=4
        ),
        'Body': ParagraphStyle(
            'Body', fontSize=10, leading=16,
            textColor=TEXT_DARK, fontName='Helvetica',
            alignment=TA_JUSTIFY, spaceAfter=6
        ),
        'BulletItem': ParagraphStyle(
            'BulletItem', fontSize=10, leading=15,
            textColor=TEXT_DARK, fontName='Helvetica',
            leftIndent=16, spaceAfter=3,
            bulletIndent=4, bulletFontName='Helvetica',
            bulletFontSize=10
        ),
        'AbstractBox': ParagraphStyle(
            'AbstractBox', fontSize=10.5, leading=17,
            textColor=TEXT_DARK, fontName='Helvetica',
            alignment=TA_JUSTIFY, spaceAfter=0
        ),
        'Keyword': ParagraphStyle(
            'Keyword', fontSize=9, leading=14,
            textColor=TEXT_MUTED, fontName='Helvetica-Oblique',
            alignment=TA_CENTER, spaceBefore=6
        ),
        'Caption': ParagraphStyle(
            'Caption', fontSize=8.5, leading=12,
            textColor=TEXT_MUTED, fontName='Helvetica-Oblique',
            alignment=TA_CENTER
        ),
    }
    return custom


# ── Flowable helpers ──────────────────────────────────────────────────────────
class ColorRect(Flowable):
    """A colored horizontal rule / banner."""
    def __init__(self, width, height, fill_color, radius=0):
        super().__init__()
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.radius = radius

    def draw(self):
        self.canv.setFillColor(self.fill_color)
        if self.radius:
            self.canv.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=0)
        else:
            self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


def hr(color=ACCENT, width=None, thickness=1.5):
    return HRFlowable(width=width or '100%', thickness=thickness, color=color, spaceAfter=4, spaceBefore=2)


def section_heading(text, styles):
    # Draw a left colored bar using a table trick
    data = [[
        '',       # colored bar cell
        Paragraph(text, styles['SectionHeading'])
    ]]
    t = Table(data, colWidths=[6, None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), ACCENT),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',(0, 0), (-1, -1), 0),
        ('RIGHTPADDING',(0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    return t


def info_box(content_paras, styles, bg=LIGHT_BG, border=ACCENT):
    """Wraps paragraphs in a colored rounded box via a 1-cell Table."""
    cell = [p for p in content_paras]
    t = Table([[cell]], colWidths=[None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX',        (0, 0), (-1, -1), 1.5, border),
        ('LEFTPADDING',(0, 0), (-1, -1), 14),
        ('RIGHTPADDING',(0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 12),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def bullet(text, styles):
    return Paragraph(f"<bullet>&#x2022;</bullet> {text}", styles['BulletItem'])


def tech_table(data_rows, styles):
    """Two-column table: Component | Technology."""
    header = [
        Paragraph('<b>Component</b>', styles['Body']),
        Paragraph('<b>Technology / Library</b>', styles['Body'])
    ]
    rows = [header] + [
        [Paragraph(k, styles['Body']), Paragraph(v, styles['Body'])]
        for k, v in data_rows
    ]
    t = Table(rows, colWidths=[5.5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR',  (0, 0), (-1, 0), WHITE),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#c0c8e8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',(0, 0), (-1, -1), 10),
        ('TOPPADDING',  (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


# ── Cover Page ────────────────────────────────────────────────────────────────
def build_cover(styles):
    story = []

    # Big header background (simulate with a table)
    header_content = [
        Spacer(1, 1.2*cm),
        Paragraph("🚌 AI CHAT BOT BASED", styles['CoverTitle']),
        Paragraph("BUS TICKETING SYSTEM", styles['CoverTitle']),
        Spacer(1, 0.3*cm),
        Paragraph("Project Abstract &amp; Technical Description", styles['CoverSub']),
        Spacer(1, 0.5*cm),
        Paragraph(
            f"Version 1.0  •  {datetime.datetime.now().strftime('%B %Y')}  •  Confidential",
            styles['CoverMeta']
        ),
        Spacer(1, 1*cm),
    ]
    header_table = Table([[header_content]], colWidths=[None])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), 30),
        ('RIGHTPADDING',(0, 0), (-1, -1), 30),
        ('TOPPADDING',  (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)

    # Accent strip
    story.append(ColorRect(W - 4*cm, 6, ACCENT))
    story.append(Spacer(1, 0.8*cm))

    # Quick-stat cards row
    stats = [
        ("3+", "AI Models"),
        ("10", "Bus Scrapers"),
        ("15+", "Indian Cities"),
        ("4", "Smart Filters"),
    ]
    stat_cells = []
    for num, label in stats:
        cell = [
            Paragraph(f'<font size="22" color="{ACCENT.hexval()}"><b>{num}</b></font>', styles['Body']),
            Paragraph(f'<font size="9" color="{TEXT_MUTED.hexval()}">{label}</font>', styles['Caption']),
        ]
        stat_cells.append(cell)

    stat_table = Table([stat_cells], colWidths=[None]*4)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX',        (0, 0), (-1, -1), 1, ACCENT),
        ('INNERGRID',  (0, 0), (-1, -1), 0.5, colors.HexColor('#c0c8e8')),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 12),
    ]))
    story.append(stat_table)

    story.append(Spacer(1, 0.8*cm))

    # Short project tagline box
    tagline = (
        "An intelligent, real-time bus ticket discovery platform powered by AI-driven "
        "natural language understanding, live web scraping from RedBus, and a premium "
        "glassmorphism React interface — enabling travellers to find, compare and book "
        "buses across South India through simple conversational queries."
    )
    story.append(info_box(
        [Paragraph(tagline, styles['AbstractBox'])],
        styles, bg=colors.HexColor('#eef2ff'), border=ACCENT
    ))

    story.append(Spacer(1, 1.2*cm))
    return story


# ── Abstract ──────────────────────────────────────────────────────────────────
def build_abstract(styles):
    story = []
    story.append(section_heading("ABSTRACT", styles))
    story.append(Spacer(1, 0.3*cm))

    abstract_text = """
The <b>AI Chat Bot Based Bus Ticketing System</b> is a full-stack web application that 
reimagines how travellers discover and book bus tickets in India. Instead of navigating 
complex booking portals, users interact with a smart conversational AI assistant that 
interprets natural-language queries such as <i>"Find me the cheapest AC bus from Madurai 
to Chennai tomorrow"</i> and instantly returns filtered, sorted, real-time bus data 
sourced directly from RedBus.
<br/><br/>
The system integrates a <b>multi-model AI pipeline</b> using OpenRouter (supporting models 
such as Nous Hermes 3 Llama-3.1-405B) to extract travel intent — source city, 
destination city, travel date, bus-type preference, and sorting criteria — from 
unstructured user messages. A robust <b>rule-based fallback parser</b> ensures 100% 
reliability even when AI rate-limits are encountered.
<br/><br/>
On the data side, a Playwright-powered scraper retrieves live bus listings, seat 
availability, pricing, operator details, and booking URLs from RedBus's internal 
GraphQL API. The backend, built with <b>FastAPI (Python)</b>, applies intelligent 
filter-and-sort logic before returning results, ensuring queries like "sleeper bus" 
or "cheapest" surface truly relevant options at the top.
<br/><br/>
The frontend is a <b>React + TypeScript (Vite)</b> single-page application featuring a 
2026-style <b>glassmorphism UI</b> with a dark/light theme toggle (persisted via 
localStorage), animated badge highlights for active filters (❄️ AC, 🛏️ Sleeper, 
💰 Cheapest), a smart connecting-route suggester for indirect journeys, an AI-powered 
Travel Guide panel, an interactive map, and a complete booking history tracker.
<br/><br/>
Together, these components deliver a seamless, end-to-end travel search experience 
that reduces the cognitive load of ticket booking to a single natural-language prompt.
"""
    story.append(info_box(
        [Paragraph(abstract_text.strip(), styles['AbstractBox'])],
        styles, bg=colors.HexColor('#f5f7ff'), border=ACCENT2
    ))
    story.append(Spacer(1, 0.4*cm))

    # Keywords
    story.append(Paragraph(
        "<b>Keywords:</b> Conversational AI, Bus Ticketing, Natural Language Processing, "
        "Web Scraping, FastAPI, React, Playwright, OpenRouter, Glassmorphism UI, "
        "Real-time Data, Smart Filters",
        styles['Keyword']
    ))
    story.append(Spacer(1, 0.3*cm))
    return story


# ── Project Description ───────────────────────────────────────────────────────
def build_description(styles):
    story = []

    # ── 1. Introduction ──────────────────────────────────────────────────────
    story.append(section_heading("1. INTRODUCTION", styles))
    story.append(Spacer(1, 0.2*cm))
    intro = (
        "Online bus ticket booking in India is fragmented across multiple platforms "
        "(RedBus, AbhiBus, MakeMyTrip, etc.), each with its own search interface and "
        "filtering mechanisms. First-time travellers and non-technical users often "
        "struggle to compare options across operators, seat types, and prices."
        "<br/><br/>"
        "This project addresses that friction by providing a <b>unified AI chat interface</b> "
        "that acts as a personal travel assistant. Users describe their journey in plain "
        "English; the system does all the heavy lifting — parsing intent, fetching live "
        "data, applying smart filters, and presenting results in a visually rich dashboard."
    )
    story.append(Paragraph(intro, styles['Body']))

    # ── 2. System Architecture ───────────────────────────────────────────────
    story.append(Spacer(1, 0.2*cm))
    story.append(section_heading("2. SYSTEM ARCHITECTURE", styles))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "The system follows a classic <b>three-tier architecture</b>: a React frontend, "
        "a FastAPI backend, and external data sources accessed via scraping.",
        styles['Body']
    ))
    story.append(Spacer(1, 0.25*cm))

    arch_data = [
        ("Frontend (Client)", "React 18 + TypeScript + Vite + Vanilla CSS (Glassmorphism)"),
        ("Backend (Server)", "Python 3.11+ · FastAPI · Uvicorn ASGI"),
        ("AI Engine", "OpenRouter API (Nous Hermes 3 / Llama 3.1 405B) + Rule-based fallback"),
        ("Web Scraper", "Playwright (async) · RedBus GraphQL API interception"),
        ("State / Storage", "React useState / useEffect · localStorage (theme + history)"),
        ("Deployment", "Docker-ready · CORS-enabled · .env configuration"),
    ]
    story.append(tech_table(arch_data, styles))

    # ── 3. Core Features ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("3. CORE FEATURES", styles))
    story.append(Spacer(1, 0.15*cm))

    features = [
        ("<b>Conversational AI Search</b> — Users type or speak natural-language queries. "
         "The AI extracts source, destination, date, filter, and sort preference in a "
         "single call or through a guided multi-turn dialogue."),
        ("<b>Smart AI Filtering</b> — Detects keywords such as 'cheapest', 'AC bus', "
         "'sleeper', 'Volvo', 'fastest', 'night bus' and applies them server-side "
         "before returning results, so the top card always matches the user's preference."),
        ("<b>Live Bus Data</b> — Playwright scrapes RedBus's live JSON API on every "
         "fresh query (10-second cache for repeated queries), returning real prices, "
         "seat availability, operator names, departure/arrival times, and booking links."),
        ("<b>Smart Connecting Routes</b> — If no direct bus exists, the system "
         "automatically suggests a two-leg route via a known intermediate city "
         "(e.g., Chennai → Dindigul → Kodaikanal)."),
        ("<b>Premium Glassmorphism UI</b> — 2026-style dark/light theme with CSS "
         "variables, backdrop-filter blur panels, animated filter badges, micro-animations, "
         "and a persistent theme toggle stored in localStorage."),
        ("<b>Travel Guide Panel</b> — AI-generated travel tips, famous places, food "
         "recommendations, and best time to visit for the destination city."),
        ("<b>Interactive Map</b> — Leaflet.js map highlighting tourist spots near the "
         "destination, sourced via curated data."),
        ("<b>Booking History &amp; Reviews</b> — In-browser booking tracker with "
         "confirmation IDs, and an operator review system with star ratings."),
        ("<b>Voice Input</b> — Web Speech API integration for hands-free search."),
        ("<b>User Personalisation</b> — Greeting, frequent-route suggestions, and "
         "AI-powered quick-reply chips based on past searches."),
    ]
    for f in features:
        story.append(bullet(f, styles))
    story.append(Spacer(1, 0.1*cm))

    # ── 4. AI Pipeline ───────────────────────────────────────────────────────
    story.append(section_heading("4. AI INTENT PIPELINE", styles))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "The AI pipeline is designed for <b>maximum reliability under free-tier rate limits</b>:",
        styles['Body']
    ))
    pipeline_steps = [
        "User message arrives at the <b>/search</b> FastAPI endpoint along with "
        "conversation history (last 6 messages) and partial context (e.g., already-known city).",
        "A <b>system prompt</b> instructs the AI to return a strict JSON object with fields: "
        "from_city, to_city, date, passengers, filter, sort_by.",
        "The primary model (Nous Hermes 3 Llama-3.1-405B via OpenRouter) is called. "
        "On rate-limit (HTTP 429) or empty response, the system automatically retries "
        "the next available model from the fallback chain.",
        "If all AI models fail, the <b>rule-based parser</b> applies regex patterns "
        "to extract city names, dates (relative: today, tomorrow, weekend), "
        "filter keywords (ac, sleeper, cheapest, volvo, night), and sort preferences.",
        "The parsed <b>collected</b> object is checked for completeness. Missing fields "
        "trigger an ask_details response with quick-reply chips (Tomorrow / Day After / "
        "This Weekend).",
        "Once all required fields are present, the system calls the scraper, applies "
        "filter_and_sort_buses(), and returns the enriched ticket list.",
    ]
    for i, step in enumerate(pipeline_steps, 1):
        story.append(bullet(f"<b>Step {i}:</b> {step}", styles))
    story.append(Spacer(1, 0.1*cm))

    # ── 5. Technology Stack ──────────────────────────────────────────────────
    story.append(section_heading("5. FULL TECHNOLOGY STACK", styles))
    story.append(Spacer(1, 0.15*cm))
    tech_data = [
        ("Language (Backend)",    "Python 3.11+"),
        ("Web Framework",         "FastAPI 0.110+ · Pydantic · Uvicorn"),
        ("AI / LLM",              "OpenRouter API · Nous Hermes 3 Llama 3.1 405B (free tier)"),
        ("Web Scraping",          "Playwright (async) · httpx · BeautifulSoup"),
        ("Language (Frontend)",   "TypeScript 5 · React 18"),
        ("Build Tool",            "Vite 6 · ESBuild"),
        ("Styling",               "Vanilla CSS · CSS Custom Properties · Glassmorphism"),
        ("Mapping",               "Leaflet.js · React-Leaflet"),
        ("Icons",                 "Lucide React"),
        ("Voice",                 "Web Speech API"),
        ("HTTP Client",           "Fetch API · httpx (async)"),
        ("Persistence",           "localStorage (theme, history, sessions)"),
        ("Containerisation",      "Docker · Docker Compose"),
        ("Version Control",       "Git"),
    ]
    story.append(tech_table(tech_data, styles))

    # ── 6. Data Flow ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("6. DATA FLOW", styles))
    story.append(Spacer(1, 0.15*cm))
    flow_text = (
        "1. <b>User Input</b> → React UI sends POST /search with {query, context, history}.<br/>"
        "2. <b>Intent Parsing</b> → FastAPI calls AI/rule-based parser → returns collected JSON.<br/>"
        "3. <b>Data Fetch</b> → Playwright intercepts RedBus GraphQL API → returns bus list.<br/>"
        "4. <b>Filter &amp; Sort</b> → filter_and_sort_buses() applies ac/sleeper/cheapest logic.<br/>"
        "5. <b>Response</b> → Returns {type, data[], intent, active_filter, sort_by, search_summary}.<br/>"
        "6. <b>UI Update</b> → React sets activeFilter state → badge &amp; card highlights rendered.<br/>"
        "7. <b>Side Effects</b> → Travel Guide, booking history, chat transcript all updated."
    )
    story.append(Paragraph(flow_text, styles['Body']))

    # ── 7. Limitations & Future Scope ────────────────────────────────────────
    story.append(Spacer(1, 0.2*cm))
    story.append(section_heading("7. LIMITATIONS &amp; FUTURE SCOPE", styles))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("<b>Current Limitations:</b>", styles['SubHeading']))
    limits = [
        "Free-tier AI models (OpenRouter) are subject to rate limits; the rule-based "
        "parser provides a reliable fallback but has reduced semantic understanding.",
        "Web scraping is dependent on RedBus DOM/API structure; changes to the target "
        "site may require scraper updates.",
        "No real payment gateway integration; booking redirects to the third-party site.",
        "Bus data is limited to routes supported by RedBus India.",
    ]
    for l in limits:
        story.append(bullet(l, styles))

    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph("<b>Future Enhancements:</b>", styles['SubHeading']))
    future = [
        "Integrate a fine-tuned domain-specific NLP model for richer intent extraction.",
        "Add support for train, flight, and cab bookings via additional scrapers.",
        "Real-time seat-map visualisation and live seat-selection within the app.",
        "Payment gateway integration (Razorpay / Stripe) for end-to-end booking.",
        "Progressive Web App (PWA) with offline caching and push notifications.",
        "Multi-language support (Tamil, Hindi, Kannada) for regional user accessibility.",
        "Backend database (PostgreSQL) for persistent user profiles and booking records.",
        "Price prediction using historical data and ML regression models.",
    ]
    for f in future:
        story.append(bullet(f, styles))

    # ── 8. Conclusion ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(section_heading("8. CONCLUSION", styles))
    story.append(Spacer(1, 0.15*cm))
    conclusion = (
        "The AI Chat Bot Based Bus Ticketing System successfully demonstrates how "
        "conversational AI, real-time web scraping, and modern frontend engineering can "
        "be combined to simplify a complex real-world problem. The system transforms a "
        "traditionally friction-heavy bus booking experience into a natural, "
        "zero-learning-curve interaction available at <b>http://localhost:5173</b>."
        "<br/><br/>"
        "By using a layered AI approach — primary LLM → model fallback → rule-based parser — "
        "the system achieves near-100% uptime for intent extraction while remaining "
        "cost-free on the AI inference side. The premium glassmorphism UI, smart filter "
        "badges, connecting-route intelligence, and Travel Guide panel elevate it well "
        "beyond a simple search tool into a comprehensive travel companion."
        "<br/><br/>"
        "This project serves as a strong foundation for a production-grade, AI-first "
        "travel platform targeting India's rapidly growing online ticketing market."
    )
    story.append(Paragraph(conclusion, styles['Body']))

    return story


# ── Main builder ──────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=2.2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
        title="AI Chat Bot Based Bus Ticketing System — Abstract & Description",
        author="Project Team",
        subject="Project Documentation",
    )

    styles = build_styles()
    story = []

    story += build_cover(styles)
    story.append(Spacer(1, 0.5*cm))
    story += build_abstract(styles)
    story.append(Spacer(1, 0.3*cm))
    story += build_description(styles)
    story.append(Spacer(1, 1*cm))

    # Final footer note
    story.append(hr(ACCENT2))
    story.append(Paragraph(
        f"Generated on {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}  •  "
        f"Generated on {datetime.datetime.now().strftime('%d %B %Y, %H:%M')}  |  "
        "AI Chat Bot Based Bus Ticketing System  |  For academic / presentation use",
        styles['Caption']
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
