"""
generate_project_report.py  -  Clean Project Report PDF
Run: python generate_project_report.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas as pdf_canvas
import datetime

# ── Colors ─────────────────────────────────────────────────────────────────────
NAVY      = colors.HexColor('#0f3460')
PURPLE    = colors.HexColor('#6c63ff')
TEAL      = colors.HexColor('#00c9a7')
WHITE     = colors.white
LIGHT     = colors.HexColor('#f4f6fc')
DARK      = colors.HexColor('#1a1a2e')
MUTED     = colors.HexColor('#6b7280')
DIVIDER   = colors.HexColor('#e2e8f0')
GOLD      = colors.HexColor('#f59e0b')
RED       = colors.HexColor('#ef4444')
GREEN     = colors.HexColor('#10b981')

W, H = A4
OUT = "AI_Bus_Ticketing_Project_Report.pdf"


# ── Canvas: page numbers + running header ──────────────────────────────────────
class PageCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            pg = self._pageNumber
            # ── header rule (skip page 1 which has its own cover)
            if pg > 1:
                self.setStrokeColor(PURPLE)
                self.setLineWidth(3)
                self.line(0, H - 1.2*cm, W, H - 1.2*cm)
                self.setStrokeColor(DIVIDER)
                self.setLineWidth(0.5)
                self.line(0, H - 1.25*cm, W, H - 1.25*cm)
                self.setFont("Helvetica-Bold", 8)
                self.setFillColor(NAVY)
                self.drawString(2*cm, H - 0.9*cm, "AI Chat Bot Based Bus Ticketing System")
                self.setFont("Helvetica", 8)
                self.setFillColor(MUTED)
                self.drawRightString(W - 2*cm, H - 0.9*cm, "Project Report")

            # ── footer
            self.setStrokeColor(DIVIDER)
            self.setLineWidth(0.5)
            self.line(2*cm, 1.2*cm, W - 2*cm, 1.2*cm)
            self.setFont("Helvetica", 8)
            self.setFillColor(MUTED)
            self.drawString(2*cm, 0.7*cm, f"Page {pg} of {total}")
            self.drawRightString(W - 2*cm, 0.7*cm,
                f"Generated {datetime.datetime.now().strftime('%d %b %Y')}")
            super().showPage()
        super().save()


# ── Style factory ──────────────────────────────────────────────────────────────
def S(name, **kw):
    defaults = dict(fontName='Helvetica', fontSize=11, leading=17,
                    textColor=DARK, alignment=TA_JUSTIFY)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


STYLES = {
    # Cover
    'cover_tag':    S('cover_tag', fontSize=10, textColor=PURPLE, fontName='Helvetica-Bold',
                      alignment=TA_CENTER, spaceAfter=4),
    'cover_title':  S('cover_title', fontSize=32, leading=40, textColor=NAVY,
                      fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=6),
    'cover_sub':    S('cover_sub', fontSize=13, textColor=MUTED, alignment=TA_CENTER,
                      spaceAfter=4),
    'cover_date':   S('cover_date', fontSize=9, textColor=MUTED, alignment=TA_CENTER),

    # Section headings
    'h1':  S('h1', fontSize=16, leading=22, textColor=NAVY, fontName='Helvetica-Bold',
              spaceBefore=18, spaceAfter=4, alignment=TA_LEFT),
    'h2':  S('h2', fontSize=12, leading=18, textColor=PURPLE, fontName='Helvetica-Bold',
              spaceBefore=12, spaceAfter=3, alignment=TA_LEFT),

    # Body
    'body':   S('body', fontSize=10.5, leading=17, textColor=DARK, spaceAfter=5),
    'bullet': S('bullet', fontSize=10.5, leading=16, textColor=DARK,
                leftIndent=14, spaceAfter=3, alignment=TA_LEFT),
    'muted':  S('muted', fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceAfter=2),
    'note':   S('note', fontSize=9.5, textColor=MUTED, fontName='Helvetica-Oblique',
                alignment=TA_LEFT, spaceAfter=3),

    # Table cells
    'cell_hd': S('cell_hd', fontSize=9.5, textColor=WHITE, fontName='Helvetica-Bold',
                 alignment=TA_LEFT, leading=14),
    'cell':    S('cell', fontSize=9.5, textColor=DARK, alignment=TA_LEFT, leading=14),
    'cell_hi': S('cell_hi', fontSize=9.5, textColor=NAVY, fontName='Helvetica-Bold',
                 alignment=TA_LEFT, leading=14),
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def sp(h=0.2): return Spacer(1, h*cm)
def hr(color=DIVIDER): return HRFlowable(width='100%', thickness=0.5, color=color,
                                          spaceAfter=3, spaceBefore=3)
def purple_hr(): return HRFlowable(width='100%', thickness=2, color=PURPLE,
                                    spaceAfter=6, spaceBefore=2)

def P(text, style='body'): return Paragraph(text, STYLES[style])

def bull(text): return Paragraph(f"<font color='#6c63ff'>&#x25CF;</font>  {text}", STYLES['bullet'])

def h1(text):
    """Section heading with left purple bar effect via table."""
    row = [[Paragraph(text, STYLES['h1'])]]
    t = Table(row, colWidths=[None])
    t.setStyle(TableStyle([
        ('LINECOLOR',    (0,0),(0,0), PURPLE),
        ('LINEWIDTH',    (0,0),(0,0), 0),
        ('LINEBEFORE',   (0,0),(0,0), 4, PURPLE),
        ('LEFTPADDING',  (0,0),(0,0), 10),
        ('TOPPADDING',   (0,0),(0,0), 2),
        ('BOTTOMPADDING',(0,0),(0,0), 2),
    ]))
    return t

def two_col_table(rows, col1=6*cm, col2=9.5*cm):
    """Simple two-column info table."""
    data = [[Paragraph(k, STYLES['cell_hi']), Paragraph(v, STYLES['cell'])] for k, v in rows]
    t = Table(data, colWidths=[col1, col2])
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0),(-1,-1), [LIGHT, WHITE]),
        ('GRID',           (0,0),(-1,-1), 0.4, DIVIDER),
        ('LEFTPADDING',    (0,0),(-1,-1), 10),
        ('RIGHTPADDING',   (0,0),(-1,-1), 10),
        ('TOPPADDING',     (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 6),
        ('VALIGN',         (0,0),(-1,-1), 'TOP'),
    ]))
    return t

def header_table(rows, headers, col_widths):
    """Table with colored header row."""
    hrow = [Paragraph(h, STYLES['cell_hd']) for h in headers]
    data = [hrow] + [[Paragraph(c, STYLES['cell']) for c in r] for r in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [LIGHT, WHITE]),
        ('GRID',          (0,0),(-1,-1), 0.4, DIVIDER),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    return t

def highlight_box(text, border=PURPLE, bg=None):
    """A styled callout box."""
    bg = bg or colors.HexColor('#f0f0ff')
    row = [[Paragraph(text, STYLES['body'])]]
    t = Table(row, colWidths=[None])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(0,0), bg),
        ('BOX',          (0,0),(0,0), 1.5, border),
        ('LEFTPADDING',  (0,0),(0,0), 14),
        ('RIGHTPADDING', (0,0),(0,0), 14),
        ('TOPPADDING',   (0,0),(0,0), 10),
        ('BOTTOMPADDING',(0,0),(0,0), 10),
    ]))
    return t

def stat_row(items):
    """A row of stat chips: [(value, label, color), ...]"""
    cells = []
    for val, lbl, col in items:
        cell = [
            Paragraph(f'<font size="20" color="{col}"><b>{val}</b></font>',
                      STYLES['cover_sub']),
            Paragraph(f'<font size="9" color="#6b7280">{lbl}</font>',
                      STYLES['muted']),
        ]
        cells.append(cell)
    t = Table([cells], colWidths=[None]*len(items))
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), LIGHT),
        ('BOX',           (0,0),(-1,-1), 1, DIVIDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.5, DIVIDER),
        ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
    ]))
    return t


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def cover(story):
    story.append(sp(3.5))
    # Purple top accent
    story.append(HRFlowable(width='30%', thickness=4, color=PURPLE,
                             spaceAfter=10, spaceBefore=0, hAlign='CENTER'))
    story.append(P("PROJECT REPORT", 'cover_tag'))
    story.append(sp(0.3))
    story.append(P("AI Chat Bot Based", 'cover_title'))
    story.append(P("Bus Ticketing System", 'cover_title'))
    story.append(sp(0.3))
    story.append(HRFlowable(width='20%', thickness=2, color=TEAL,
                             spaceAfter=10, spaceBefore=0, hAlign='CENTER'))
    story.append(sp(0.3))
    story.append(P("A full-stack AI-powered travel assistant that finds, filters,<br/>"
                   "and presents live bus tickets through natural language conversation.",
                   'cover_sub'))
    story.append(sp(1.5))
    story.append(stat_row([
        ("3+",  "AI Models",      PURPLE.hexval()),
        ("10",  "Bus Scrapers",   TEAL.hexval()),
        ("15+", "Indian Cities",  NAVY.hexval()),
        ("4",   "Smart Filters",  GOLD.hexval()),
        ("8",   "UI Components",  RED.hexval()),
    ]))
    story.append(sp(2.5))
    story.append(P(datetime.datetime.now().strftime('%B %Y'), 'cover_date'))
    story.append(PageBreak())


def section_what_we_built(story):
    story.append(h1("1.  What We Built"))
    story.append(sp(0.2))
    story.append(P(
        "We built an <b>AI-powered bus ticket search system</b> that lets travellers "
        "find and compare real bus tickets by simply chatting in plain English. "
        "Instead of navigating complex booking websites, the user types something like "
        "<i>\"Find me the cheapest AC bus from Madurai to Chennai tomorrow\"</i> and "
        "the system instantly returns live, filtered, sorted results directly from RedBus."
    ))
    story.append(sp(0.2))
    story.append(highlight_box(
        "<b>Core Idea:</b> Replace the traditional search form with a smart conversational "
        "AI that understands what the user wants, fetches live data, and shows only the "
        "most relevant results — no manual filtering required.",
        border=PURPLE, bg=colors.HexColor('#f0f0ff')
    ))
    story.append(sp(0.4))


def section_problem(story):
    story.append(h1("2.  Problem We Solved"))
    story.append(sp(0.2))
    story.append(P("Bus booking in India has three major pain points:"))
    story.append(sp(0.1))
    for pt in [
        "<b>Fragmented platforms</b> — RedBus, AbhiBus, MakeMyTrip all have different UIs and filters.",
        "<b>Manual filtering</b> — Users must manually sort by price, type, timing, operator.",
        "<b>Complex interfaces</b> — Non-technical travellers find booking portals confusing.",
        "<b>No single conversational interface</b> — Nobody accepts plain English queries.",
    ]:
        story.append(bull(pt))
    story.append(sp(0.3))


def section_what_we_did(story):
    story.append(h1("3.  What We Did — Feature by Feature"))
    story.append(sp(0.2))

    # 3.1
    story.append(P("<b>3.1  Conversational AI Chat Interface</b>", 'h2'))
    story.append(P(
        "Built a chat UI where users type natural language queries. The system extracts "
        "travel intent — source city, destination, date, bus type, price preference — "
        "using an AI model via OpenRouter. When the AI hits rate limits, a built-in "
        "rule-based parser handles the request as a fallback."
    ))
    for pt in [
        "Multi-turn conversation: bot asks follow-up questions if info is missing",
        "Quick-reply chips (Tomorrow / Day After / This Weekend) for faster input",
        "Chat history preserved within the session",
        "Voice input support using Web Speech API",
    ]:
        story.append(bull(pt))
    story.append(sp(0.3))

    # 3.2
    story.append(P("<b>3.2  Live Bus Data Scraping</b>", 'h2'))
    story.append(P(
        "Used Playwright (headless browser automation) to scrape live bus data from "
        "RedBus by intercepting its internal GraphQL API. Every search returns real, "
        "up-to-date bus information — not dummy or cached data."
    ))
    story.append(P("Each bus result includes:"))
    for pt in [
        "Operator name (e.g. SETC, FlixBus, KPN, Orange Travels)",
        "Departure & arrival times, journey duration",
        "Price in INR (live from RedBus)",
        "Seats available (urgent flag if < 5 seats left)",
        "Bus type: AC / Sleeper / Volvo / Non-AC",
        "Amenities: WiFi, charging, live tracking",
        "Free cancellation flag",
        "Direct booking URL back to RedBus",
    ]:
        story.append(bull(pt))
    story.append(sp(0.3))

    # 3.3
    story.append(P("<b>3.3  Smart AI Filtering & Sorting</b>", 'h2'))
    story.append(P(
        "The AI detects filter and sort intent from the user's message and applies "
        "it server-side before returning results. The top result always matches "
        "what the user asked for."
    ))
    story.append(sp(0.15))
    story.append(header_table(
        [
            ["cheapest",  "Sorts all buses by price — lowest first. Badge: 💰 CHEAPEST"],
            ["ac",        "Filters to AC buses only. Badge: ❄️ BEST AC BUS"],
            ["sleeper",   "Filters to sleeper buses. Badge: 🛏 BEST SLEEPER"],
            ["non_ac",    "Shows economy non-AC options only"],
            ["volvo",     "Filters luxury/Volvo operators"],
            ["fastest",   "Sorts by journey duration — shortest first"],
            ["night bus", "Shows buses departing after 8 PM only"],
        ],
        ["Keyword Detected", "What Happens"],
        [4.5*cm, 11*cm]
    ))
    story.append(sp(0.3))

    # 3.4
    story.append(P("<b>3.4  Smart Connecting Route Suggestion</b>", 'h2'))
    story.append(P(
        "If no direct bus exists between two cities, the system automatically "
        "suggests a two-leg connecting route through a known intermediate stop. "
        "Examples: Chennai → Dindigul → Kodaikanal, Coimbatore → Mettupalayam → Ooty."
    ))
    story.append(sp(0.3))

    # 3.5
    story.append(P("<b>3.5  Premium Glassmorphism UI</b>", 'h2'))
    story.append(P(
        "Designed a 2026-style modern interface with glassmorphism panels, "
        "smooth animations, and a Dark / Light theme toggle that persists in localStorage."
    ))
    for pt in [
        "Dark/Light theme toggle — preference saved in localStorage",
        "Animated filter badges on the results panel",
        "\"BEST AC BUS\" / \"CHEAPEST\" / \"BEST SLEEPER\" highlight card on top result",
        "Micro-animations on hover for all interactive elements",
        "Backdrop-filter blur glass cards throughout the UI",
    ]:
        story.append(bull(pt))
    story.append(sp(0.3))

    # 3.6
    story.append(P("<b>3.6  AI Travel Guide Panel</b>", 'h2'))
    story.append(P(
        "After a bus search, a Travel Guide tab appears for the destination city. "
        "An AI model generates travel tips, top places to visit, local food "
        "recommendations, and best time to visit."
    ))
    story.append(sp(0.3))

    # 3.7
    story.append(P("<b>3.7  Interactive Map</b>", 'h2'))
    story.append(P(
        "Built using Leaflet.js — shows an interactive map with pin markers for "
        "tourist spots near the destination. Clicking a marker shows the place name and details."
    ))
    story.append(sp(0.3))

    # 3.8
    story.append(P("<b>3.8  Booking History Tracker</b>", 'h2'))
    story.append(P(
        "Users can complete a booking flow inside the app. The system generates a "
        "confirmation ID, stores the booking in localStorage, and shows a full "
        "booking history panel with operator, route, date, seat, and amount."
    ))
    story.append(sp(0.3))

    # 3.9
    story.append(P("<b>3.9  Bus Operator Reviews</b>", 'h2'))
    story.append(P(
        "Users can rate bus operators with a star rating. Ratings are displayed "
        "on each ticket card to help others pick the best operator."
    ))
    story.append(sp(0.3))

    # 3.10
    story.append(P("<b>3.10  User Personalisation</b>", 'h2'))
    story.append(P(
        "The app greets the user by name on return visits, remembers frequently "
        "searched routes, and suggests smart quick replies based on past searches."
    ))
    story.append(sp(0.3))


def section_tech(story):
    story.append(h1("4.  Languages & Technologies Used"))
    story.append(sp(0.2))

    story.append(P("<b>Frontend</b>", 'h2'))
    story.append(two_col_table([
        ("React 18",         "Component-based UI framework for building the chat interface and results"),
        ("TypeScript 5",     "Strongly-typed JavaScript — catches bugs at compile time"),
        ("Vite 6",           "Build tool and dev server with Hot Module Replacement"),
        ("Vanilla CSS",      "Full custom styling — glassmorphism, CSS variables, animations"),
        ("Leaflet.js",       "Interactive map showing tourist spots near the destination"),
        ("Lucide React",     "Clean icon library used throughout the UI"),
        ("Web Speech API",   "Browser-native voice input for hands-free search"),
        ("localStorage",     "Persists theme preference, booking history, chat sessions"),
    ]))
    story.append(sp(0.3))

    story.append(P("<b>Backend</b>", 'h2'))
    story.append(two_col_table([
        ("Python 3.11+",    "Core programming language for the backend"),
        ("FastAPI",         "Modern async REST API framework — fast, auto-generates docs"),
        ("Uvicorn",         "ASGI server that runs the FastAPI application"),
        ("Pydantic",        "Data validation and request/response schema definitions"),
        ("httpx",           "Async HTTP client for making AI API calls to OpenRouter"),
        ("python-dotenv",   "Loads API keys and config from .env files"),
        ("Docker",          "Containerises the backend for easy deployment anywhere"),
    ]))
    story.append(sp(0.3))

    story.append(P("<b>AI & Scraping</b>", 'h2'))
    story.append(two_col_table([
        ("OpenRouter API",       "Gateway to multiple free/paid LLM models"),
        ("Nous Hermes 3\n(Llama 3.1 405B)", "Primary AI model for extracting travel intent from user messages"),
        ("Rule-Based Parser",    "Regex fallback that handles queries when AI hits rate limits"),
        ("Playwright",           "Async headless browser — intercepts RedBus GraphQL API for live data"),
        ("BeautifulSoup",        "HTML parser used as secondary fallback for bus data"),
        ("Git",                  "Version control used throughout the project"),
    ]))
    story.append(sp(0.3))


def section_architecture(story):
    story.append(h1("5.  How It All Works Together"))
    story.append(sp(0.2))
    story.append(P(
        "The system follows a clean three-tier architecture. "
        "The flow from user message to final result takes under 10 seconds:"
    ))
    story.append(sp(0.15))

    steps = [
        ("1", "User sends a chat message",
         "React UI posts the query + conversation history to the FastAPI backend."),
        ("2", "AI parses the intent",
         "OpenRouter calls the Nous Hermes 3 model which returns a structured JSON "
         "with from_city, to_city, date, filter, sort_by. If rate-limited, "
         "the rule-based regex parser takes over."),
        ("3", "Bot asks follow-up if needed",
         "If any required field is missing, the bot sends a polite question with "
         "quick-reply chips to speed up input."),
        ("4", "Playwright scrapes RedBus",
         "Once all fields are collected, a headless Chromium browser navigates to "
         "RedBus, intercepts the GraphQL API response, and returns live bus data."),
        ("5", "Filter & Sort applied",
         "The filter_and_sort_buses() function applies the detected preference "
         "(e.g. sort by price for 'cheapest') before returning results."),
        ("6", "Results shown in the UI",
         "React renders ticket cards with badges, booking links, and an "
         "active-filter banner at the top of the results panel."),
    ]

    for num, title, desc in steps:
        row = [[
            Paragraph(num, ParagraphStyle('n', fontSize=14, fontName='Helvetica-Bold',
                                          textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(f"<b>{title}</b><br/>{desc}", STYLES['body'])
        ]]
        t = Table(row, colWidths=[1*cm, 14.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,0), PURPLE),
            ('BACKGROUND',    (1,0),(1,0), LIGHT),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('RIGHTPADDING',  (0,0),(-1,-1), 10),
            ('TOPPADDING',    (0,0),(-1,-1), 8),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('LINEBELOW',     (0,0),(-1,-1), 0.5, DIVIDER),
        ]))
        story.append(t)
    story.append(sp(0.4))


def section_results(story):
    story.append(h1("6.  Key Results & Achievements"))
    story.append(sp(0.2))

    story.append(header_table(
        [
            ["Live Bus Data",        "Real-time bus listings from RedBus — prices, seats, times, operators"],
            ["AI Filtering",         "Correctly detects cheapest / AC / sleeper / Volvo / fastest / night"],
            ["Filter Badges",        "Active filter banner + 'BEST AC BUS' badge shown on top card"],
            ["Multi-turn Dialogue",  "Bot holds context across messages, asks only for what is missing"],
            ["Connecting Routes",    "Auto-suggests 2-leg route when no direct bus found"],
            ["Theme Toggle",         "Dark/Light mode switch — preference saved in localStorage"],
            ["Travel Guide",         "AI generates destination tips after every bus search"],
            ["Voice Search",         "Hands-free query via Web Speech API"],
            ["Booking Tracker",      "Full in-app booking flow with confirmation ID and history"],
            ["Zero AI Cost",         "Primary model on free tier; rule-based fallback means always works"],
        ],
        ["Feature", "Outcome"],
        [5.5*cm, 10*cm]
    ))
    story.append(sp(0.4))


def section_future(story):
    story.append(h1("7.  What Can Be Improved Next"))
    story.append(sp(0.2))
    for pt in [
        "<b>Payment Integration</b> — Add Razorpay / Stripe for end-to-end booking without leaving the app",
        "<b>Train & Flight Support</b> — Expand beyond buses to cover trains and flights",
        "<b>Database Backend</b> — Replace localStorage with PostgreSQL for persistent user data",
        "<b>PWA / Mobile App</b> — Offline support and push notifications via Progressive Web App",
        "<b>Multi-language</b> — Support Tamil, Hindi, Kannada for regional users",
        "<b>Price Prediction</b> — ML model to predict fare changes using historical data",
        "<b>Real-time Seat Map</b> — Let users pick seats inside the app before booking",
        "<b>Fine-tuned NLP Model</b> — Train a domain-specific model for richer intent understanding",
    ]:
        story.append(bull(pt))
    story.append(sp(0.4))


def section_summary(story):
    story.append(h1("8.  Summary"))
    story.append(sp(0.2))
    story.append(highlight_box(
        "We built a complete, working AI-powered bus ticketing assistant using "
        "<b>React + TypeScript</b> on the frontend, <b>FastAPI + Python</b> on the backend, "
        "<b>OpenRouter LLM + rule-based parser</b> for AI, and <b>Playwright</b> for "
        "live data scraping. The system handles the entire journey from a plain-English "
        "user query to filtered, live bus results with booking links — in one seamless interface.",
        border=TEAL, bg=colors.HexColor('#f0fffe')
    ))
    story.append(sp(0.3))
    story.append(P(
        "The project demonstrates how modern AI, web scraping, and thoughtful UI design "
        "can be combined to solve a real, everyday problem for millions of bus travellers in India.",
        'body'
    ))
    story.append(sp(0.5))


# ── Build PDF ─────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        topMargin=2.2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title="AI Bus Ticketing System — Project Report",
        author="Project Team",
    )
    story = []

    cover(story)
    section_what_we_built(story)
    section_problem(story)
    section_what_we_did(story)
    section_tech(story)
    section_architecture(story)
    section_results(story)
    section_future(story)
    section_summary(story)

    doc.build(story, canvasmaker=PageCanvas)
    print(f"PDF saved: {OUT}")


if __name__ == "__main__":
    build()
