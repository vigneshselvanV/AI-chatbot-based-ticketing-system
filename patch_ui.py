import sys

# Patch App.tsx
with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    app_code = f.read()

# 1. Error Message Fix & Silent Retry
old_catch = """    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), type: 'bot',
        text: '⚠️ Connection error. Please make sure the backend server is running on port 8000.'
      }]);
    } finally {"""

new_catch = """    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), type: 'bot',
        text: '┌─────────────────────────────────┐\\n│  ⚠️ Slight hiccup!             │\\n│  Retrying automatically...     │\\n│  [Loading spinner]             │\\n└─────────────────────────────────┘',
        isMarkdown: true
      }]);
      // Silently retry after 2 seconds
      setTimeout(async () => {
        try {
          const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
          const res = await fetch(`${apiBase}/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: queryText, context: conversationContext, history: messages.slice(-6) })
          });
          const data = await res.json();
          if (data.type === "tickets") {
            setTickets(data.data || []);
            setSearchSummary(data.search_summary || null);
            setMessages(prev => [...prev.slice(0, -1), {
              id: Date.now().toString(), type: 'bot',
              text: `✅ Found **${data.data.length} bus options**.\\n\\n👉 Click on any result to see full details and book!`,
              isMarkdown: true
            }]);
          } else {
             setMessages(prev => [...prev.slice(0, -1), { id: Date.now().toString(), type: 'bot', text: 'Live bus data is temporarily unavailable. Check RedBus directly.'}]);
          }
        } catch (e) {
          setMessages(prev => [...prev.slice(0, -1), { id: Date.now().toString(), type: 'bot', text: 'Live bus data is temporarily unavailable. Check RedBus directly.'}]);
        }
      }, 2000);
    } finally {"""

app_code = app_code.replace(old_catch, new_catch)

# 2. Add Filter state and UI
if 'const [activeFilter, setActiveFilter] = useState<string>("All");' not in app_code:
    app_code = app_code.replace("const [activeTab, setActiveTab] = useState<'all' | 'saved'>('all');", 
                                "const [activeTab, setActiveTab] = useState<'all' | 'saved'>('all');\n  const [activeFilter, setActiveFilter] = useState<string>('All');")

# Filter logic in rendering
filter_logic = """
  const applyFilters = (tks: TicketResult[]) => {
    if (activeFilter === 'All') return tks;
    if (activeFilter === 'Cheapest') return [...tks].sort((a, b) => parseInt((a.price||'0').replace(/\\D/g,'')) - parseInt((b.price||'0').replace(/\\D/g,'')));
    if (activeFilter === 'Fastest') return [...tks].sort((a, b) => parseInt((a.duration||'0').replace(/\\D/g,'')) - parseInt((b.duration||'0').replace(/\\D/g,'')));
    if (activeFilter === 'AC') return tks.filter(t => t.amenities?.ac || (t.type||'').toLowerCase().includes('ac'));
    if (activeFilter === 'Sleeper') return tks.filter(t => t.amenities?.sleeper || (t.type||'').toLowerCase().includes('sleep'));
    if (activeFilter === 'Evening') return tks.filter(t => { const h = parseInt((t.departure||'0').split(':')[0]); return h >= 16 && h < 20; });
    if (activeFilter === 'Night') return tks.filter(t => { const h = parseInt((t.departure||'0').split(':')[0]); return h >= 20 || h < 4; });
    if (activeFilter === 'Early Morning') return tks.filter(t => { const h = parseInt((t.departure||'0').split(':')[0]); return h >= 4 && h < 8; });
    return tks;
  };
  const filteredTickets = activeTab === 'saved' ? savedTickets : applyFilters(tickets);
"""
app_code = app_code.replace("const filteredTickets = activeTab === 'saved' ? savedTickets : tickets;", filter_logic)

filter_ui = """
            {activeTab === 'all' && (
              <div className="filter-bar" style={{ display: 'flex', gap: '8px', overflowX: 'auto', padding: '0 2px 12px 2px', marginBottom: '16px', scrollbarWidth: 'none' }}>
                {['All', 'Cheapest', 'Fastest', 'AC', 'Sleeper', 'Evening', 'Night', 'Early Morning'].map(f => (
                  <button key={f} onClick={() => setActiveFilter(f)} style={{ whiteSpace: 'nowrap', padding: '6px 12px', borderRadius: '16px', border: activeFilter === f ? '1px solid #4f46e5' : '1px solid #e5e7eb', background: activeFilter === f ? '#e0e7ff' : '#ffffff', color: activeFilter === f ? '#4f46e5' : '#4b5563', fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>
                    {f}
                  </button>
                ))}
              </div>
            )}
            <div className="ticket-cards">"""
app_code = app_code.replace('<div className="ticket-cards">', filter_ui)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(app_code)


# Patch TicketCard.tsx
with open('frontend/src/components/TicketCard.tsx', 'r', encoding='utf-8') as f:
    tc_code = f.read()

# Replace expand indicator with standard buttons
old_expand = """      <div className="expand-indicator" onClick={onToggleExpand}>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        <span>{isExpanded ? 'Less details' : 'Select Seats & Book'}</span>
      </div>"""

new_expand = """      <div style={{ display: 'flex', gap: '12px', padding: '0 20px 16px 20px', marginTop: '16px' }}>
        <button onClick={onToggleExpand} style={{ flex: 1, padding: '10px', background: '#34d399', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}>
          Select Seat 💺
        </button>
        <button onClick={onToggleExpand} style={{ flex: 1, padding: '10px', background: '#f3f4f6', color: '#4b5563', border: 'none', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}>
          Details 👁️
        </button>
      </div>"""

tc_code = tc_code.replace(old_expand, new_expand)

# Add Free cancellation
old_chips = """      <div className="card-chips" style={{ marginTop: '16px' }}>
        {ticket.seats && ticket.seats !== '--' && (
          <span className="info-chip">{ticket.seats}</span>
        )}
        {ticket.rating && ticket.rating !== '--' && (
          <span className="info-chip rating-chip">
            <Star size={12} /> {ticket.rating}
          </span>
        )}
      </div>"""

new_chips = """      <div className="card-chips" style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px', padding: '0 20px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
            <span className="info-chip">🪑 {ticket.seats || '--'}</span>
        </div>
        <div style={{ fontSize: '12px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 500 }}>
          ✅ Free Cancellation
        </div>
      </div>"""

tc_code = tc_code.replace(old_chips, new_chips)

with open('frontend/src/components/TicketCard.tsx', 'w', encoding='utf-8') as f:
    f.write(tc_code)

print("UI patches applied!")
