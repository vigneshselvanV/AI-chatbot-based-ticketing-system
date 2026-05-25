import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Plane, Bus, Train, Calendar, MapPin, Loader2, ExternalLink, Clock, Star, IndianRupee, ArrowRight, Sparkles, ChevronDown, ChevronUp, LogOut } from 'lucide-react';
import './index.css';
import { AuthModal } from './components/AuthModal';
import type { User as AuthUser } from './components/AuthModal';

interface Message {
  id: string;
  type: 'user' | 'bot';
  text: string;
  isMarkdown?: boolean;
}

interface IntentData {
  source?: string | null;
  origin?: string | null;
  destination?: string | null;
  date?: string | null;
  mode?: string | null;
}

interface TicketResult {
  [key: string]: string;
}

interface SearchSummary {
  mode: string;
  source: string;
  destination: string;
  date: string;
  total_results: number;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init', type: 'bot',
      text: '👋 Hello! I\'m your AI travel assistant.\n\nI can help you find live tickets for:\n🚌 **Buses** — from RedBus\n✈️ **Flights** — from Google Flights\n🚆 **Trains** — from MakeMyTrip\n\nJust type something like:\n*"Check bus for Coimbatore to Rameswaram"*',
      isMarkdown: true
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tickets, setTickets] = useState<TicketResult[]>([]);
  const [intent, setIntent] = useState<IntentData | null>(null);
  const [bookingUrl, setBookingUrl] = useState<string>('');
  const [dataSource, setDataSource] = useState<string>('');
  const [searchSummary, setSearchSummary] = useState<SearchSummary | null>(null);
  const [expandedTicket, setExpandedTicket] = useState<number | null>(null);
  const [conversationContext, setConversationContext] = useState<Record<string, string | null>>({});
  const [activeTab, setActiveTab] = useState<'all' | 'flight' | 'train' | 'bus'>('all');
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    "Bus from Chennai to Madurai tomorrow",
    "Flights from Delhi to Mumbai",
    "Train from Coimbatore to Rameswaram"
  ]);

  // Auth State
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  useEffect(() => {
    // Check local storage for existing session
    const savedUser = localStorage.getItem('travel_ai_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error("Error parsing user from localStorage", e);
      }
    }
  }, []);

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('travel_ai_user');
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    setSuggestedQueries([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), type: 'user', text: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    const queryText = input.trim();
    setInput('');
    setIsLoading(true);
    setSuggestedQueries([]);

    try {
      const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText, context: conversationContext })
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      if (data.type === "chat") {
        setMessages(prev => [...prev, {
          id: Date.now().toString(), type: 'bot',
          text: data.message, isMarkdown: true
        }]);
        setTickets([]);
        setIntent(null);
        setSearchSummary(null);

      } else if (data.type === "ask_details") {
        // The AI is asking for missing details — show the question
        setMessages(prev => [...prev, {
          id: Date.now().toString(), type: 'bot',
          text: data.message, isMarkdown: true
        }]);

        // Save partial intent as conversation context for follow-up
        if (data.partial_intent) {
          setConversationContext(data.partial_intent);
        }

        // Suggest quick options based on what's missing
        const quickSuggestions: string[] = [];
        if (data.missing?.includes("travel date")) {
          quickSuggestions.push("Tomorrow");
          quickSuggestions.push("Day after tomorrow");
        }
        if (data.missing?.includes("travel mode")) {
          quickSuggestions.push("By bus 🚌");
          quickSuggestions.push("By train 🚆");
          quickSuggestions.push("By flight ✈️");
        }
        if (quickSuggestions.length > 0) {
          setSuggestedQueries(quickSuggestions);
        }

      } else if (data.type === "tickets") {
        const mode = data.intent?.mode || "result";
        setIntent(data.intent);
        setTickets(data.data || []);
        setBookingUrl(data.booking_url || '');
        setDataSource(data.data_source || '');
        setSearchSummary(data.search_summary || null);
        setConversationContext({}); // Clear context after successful search
        setExpandedTicket(null);
        setActiveTab('all');

        if (!data.data || data.data.length === 0) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(), type: 'bot',
            text: '❌ No results found for this route. Try a different date or route.'
          }]);
        } else {
          const sourceLabel = data.search_summary?.source || '';
          const destLabel = data.search_summary?.destination || '';
          const dateLabel = data.search_summary?.date || '';
          const count = data.data.length;
          const msgText = mode === 'all'
            ? `✅ Found **${count} travel options** from ${sourceLabel} to ${destLabel} on ${dateLabel} comparing Flights, Trains & Buses.\n\n📊 Live comparison data ready.\n\n👉 Click on any result to see full details, or use the filter tabs on the right!`
            : `✅ Found **${count} ${mode} options** from ${sourceLabel} to ${destLabel} on ${dateLabel}.\n\n📊 Live data from **${data.data_source}**.\n\n👉 Click on any result to see full details and book!`;
          setMessages(prev => [...prev, {
            id: Date.now().toString(), type: 'bot',
            text: msgText,
            isMarkdown: true
          }]);
        }
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), type: 'bot',
        text: '⚠️ Connection error. Please make sure the backend server is running on port 8000.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const getModeIcon = (mode: string | null | undefined) => {
    if (!mode) return <Sparkles size={16} />;
    switch (mode.toLowerCase()) {
      case 'flight': return <Plane size={16} />;
      case 'bus': return <Bus size={16} />;
      case 'train': return <Train size={16} />;
      default: return <Sparkles size={16} />;
    }
  };

  const getModeColor = (mode: string | null | undefined): string => {
    if (!mode) return '#a5b4fc';
    switch (mode.toLowerCase()) {
      case 'flight': return '#60a5fa';
      case 'bus': return '#34d399';
      case 'train': return '#f59e0b';
      default: return '#a5b4fc';
    }
  };

  // Render markdown-like text
  const renderText = (text: string) => {
    const parts = text.split('\n');
    return parts.map((line, i) => {
      // Bold **text**
      let rendered = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      // Italic *text*
      rendered = rendered.replace(/\*(.+?)\*/g, '<em>$1</em>');
      return <span key={i} dangerouslySetInnerHTML={{ __html: rendered + (i < parts.length - 1 ? '<br/>' : '') }} />;
    });
  };

  // Get primary display value for a ticket (operator/airline/train)
  const getTicketLabel = (ticket: TicketResult): string => {
    return ticket.operator || ticket.airline || ticket.train || 'Unknown';
  };

  const getTicketSubLabel = (ticket: TicketResult): string => {
    return ticket.type || ticket.number || ticket.stops || '';
  };

  const getTicketPrice = (ticket: TicketResult): string => {
    return ticket.price || ticket.fare || '--';
  };

  const getTicketDeparture = (ticket: TicketResult): string => {
    return ticket.departure || '--';
  };

  const getTicketArrival = (ticket: TicketResult): string => {
    return ticket.arrival || '--';
  };

  const getTicketDuration = (ticket: TicketResult): string => {
    return ticket.duration || '--';
  };

  const comparisonHighlights = React.useMemo(() => {
    if (!tickets || tickets.length === 0 || intent?.mode !== 'all') {
      return null;
    }

    const parseDurationToMinutes = (durStr: string): number => {
      if (!durStr || durStr === '--') return 999999;
      try {
        let hours = 0;
        let minutes = 0;
        const hrMatch = durStr.match(/(\d+)\s*h/i);
        const minMatch = durStr.match(/(\d+)\s*m/i);
        if (hrMatch) hours = parseInt(hrMatch[1], 10);
        if (minMatch) minutes = parseInt(minMatch[1], 10);
        return hours * 60 + minutes;
      } catch (e) {
        return 999999;
      }
    };

    const parsePriceToInt = (priceStr: string): number => {
      if (!priceStr || priceStr === '--') return 999999;
      try {
        const clean = priceStr.replace(/[^\d]/g, '');
        return clean ? parseInt(clean, 10) : 999999;
      } catch (e) {
        return 999999;
      }
    };

    let cheapest = tickets[0];
    let fastest = tickets[0];
    let minPrice = parsePriceToInt(getTicketPrice(cheapest));
    let minDuration = parseDurationToMinutes(getTicketDuration(fastest));

    for (let i = 1; i < tickets.length; i++) {
      const t = tickets[i];
      const p = parsePriceToInt(getTicketPrice(t));
      const d = parseDurationToMinutes(getTicketDuration(t));

      if (p < minPrice) {
        minPrice = p;
        cheapest = t;
      }
      if (d < minDuration) {
        minDuration = d;
        fastest = t;
      }
    }

    return { cheapest, fastest };
  }, [tickets, intent]);

  const filteredTickets = tickets.filter(ticket => {
    if (activeTab === 'all') return true;
    const ticketMode = ticket.mode || intent?.mode || 'bus';
    return ticketMode === activeTab;
  });

  const hasResults = tickets.length > 0;
  const intentSource = intent?.source || intent?.origin || null;
  const modeColor = getModeColor(intent?.mode);

  return (
    <div className="app-container">
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
        onLogin={(newUser) => {
          setUser(newUser);
          setShowAuthModal(false);
        }} 
      />

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <Bot className="header-icon" size={28} />
          <h1>AI Travel Assistant</h1>
        </div>
        
        <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '16px', marginLeft: 'auto' }}>
          {searchSummary && (
            <div className="header-search-info" style={{ marginRight: '20px' }}>
              {getModeIcon(searchSummary.mode)}
              <span>{searchSummary.source} → {searchSummary.destination}</span>
              <span className="header-divider">|</span>
              <Calendar size={14} />
              <span>{searchSummary.date}</span>
            </div>
          )}
          
          {user ? (
            <div className="user-profile">
              <div style={{ width: '24px', height: '24px', borderRadius: '9999px', background: 'linear-gradient(to right, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 'bold', color: 'white' }}>
                {user.name.charAt(0).toUpperCase()}
              </div>
              <span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'rgba(255,255,255,0.9)' }}>{user.name}</span>
              <button 
                onClick={handleLogout}
                title="Sign Out"
                style={{ marginLeft: '8px' }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button 
              onClick={() => setShowAuthModal(true)}
              className="login-btn"
            >
              <User size={16} />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Chat Section */}
        <section className={`chat-section ${hasResults ? 'has-results' : ''}`}>
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.type}`}>
                <div className="avatar">
                  {msg.type === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="#a5b4fc" />}
                </div>
                <div className="message-bubble">
                  {msg.isMarkdown ? renderText(msg.text) : msg.text}
                </div>
              </div>
            ))}

            {/* Suggested Quick Actions */}
            {suggestedQueries.length > 0 && !isLoading && (
              <div className="suggestions-container">
                {suggestedQueries.map((suggestion, idx) => (
                  <button
                    key={idx}
                    className="suggestion-chip"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <Sparkles size={14} />
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

            {isLoading && (
              <div className="message bot">
                <div className="avatar">
                  <Bot size={20} color="#a5b4fc" />
                </div>
                <div className="message-bubble loading-bubble">
                  <div className="loading-dots">
                    <div className="dot"></div>
                    <div className="dot"></div>
                    <div className="dot"></div>
                  </div>
                  <div className="loading-text">
                    🔍 Scanning live websites... this may take up to 30 seconds
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <form onSubmit={handleSubmit} className="input-container">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask about buses, flights, or trains..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!input.trim() || isLoading}
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </form>
          </div>
        </section>

        {/* Results Section — Card-based */}
        {hasResults && (
          <section className="results-section">
            {/* Results Header */}
            <div className="results-header">
              <div>
                <h2>
                  {intent?.mode === 'all' ? <Sparkles className="header-icon" size={20} /> : getModeIcon(intent?.mode)} 
                  {intent?.mode === 'all' ? ' Travel Comparison' : ` Available ${intent?.mode?.charAt(0).toUpperCase()}${intent?.mode?.slice(1) || ''} Options`}
                </h2>
                <p className="results-subtitle">
                  {intent?.mode === 'all' ? `${tickets.length} options comparing Flights, Trains & Buses` : `${tickets.length} results from `}
                  {intent?.mode !== 'all' && <span className="source-label">{dataSource}</span>}
                </p>
              </div>
              {bookingUrl && intent?.mode !== 'all' && (
                <a
                  href={bookingUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="view-all-btn"
                >
                  View all on {dataSource} <ExternalLink size={14} />
                </a>
              )}
            </div>

            {/* Route & Date Badges */}
            {intent && (
              <div className="intent-badges">
                {intentSource && intent.destination && (
                  <div className="badge route-badge" style={{ borderColor: `${modeColor}40` }}>
                    <MapPin size={14} style={{ color: modeColor }} />
                    {intentSource} <ArrowRight size={12} /> {intent.destination}
                  </div>
                )}
                {intent.date && (
                  <div className="badge date-badge" style={{ borderColor: `${modeColor}40` }}>
                    <Calendar size={14} style={{ color: modeColor }} />
                    {intent.date}
                  </div>
                )}
              </div>
            )}

            {/* Comparison Highlights */}
            {comparisonHighlights && (
              <div className="comparison-highlights">
                <div className="highlight-card cheapest" onClick={() => {
                  const idx = filteredTickets.findIndex(t => t === comparisonHighlights.cheapest);
                  if (idx !== -1) setExpandedTicket(idx);
                }}>
                  <div className="highlight-badge cheapest">💰 CHEAPEST OPTION</div>
                  <div className="highlight-content">
                    <div className="highlight-main">
                      <span className="highlight-title">
                        {getTicketLabel(comparisonHighlights.cheapest)}
                      </span>
                      <span className="highlight-mode-tag" style={{ background: `${getModeColor(comparisonHighlights.cheapest.mode)}20`, color: getModeColor(comparisonHighlights.cheapest.mode) }}>
                        {getModeIcon(comparisonHighlights.cheapest.mode)} {comparisonHighlights.cheapest.mode?.toUpperCase()}
                      </span>
                    </div>
                    <div className="highlight-details">
                      <span className="highlight-price">{getTicketPrice(comparisonHighlights.cheapest)}</span>
                      <span className="highlight-duration">⏱️ {getTicketDuration(comparisonHighlights.cheapest)}</span>
                    </div>
                  </div>
                </div>

                <div className="highlight-card fastest" onClick={() => {
                  const idx = filteredTickets.findIndex(t => t === comparisonHighlights.fastest);
                  if (idx !== -1) setExpandedTicket(idx);
                }}>
                  <div className="highlight-badge fastest">⚡ FASTEST OPTION</div>
                  <div className="highlight-content">
                    <div className="highlight-main">
                      <span className="highlight-title">
                        {getTicketLabel(comparisonHighlights.fastest)}
                      </span>
                      <span className="highlight-mode-tag" style={{ background: `${getModeColor(comparisonHighlights.fastest.mode)}20`, color: getModeColor(comparisonHighlights.fastest.mode) }}>
                        {getModeIcon(comparisonHighlights.fastest.mode)} {comparisonHighlights.fastest.mode?.toUpperCase()}
                      </span>
                    </div>
                    <div className="highlight-details">
                      <span className="highlight-price">{getTicketPrice(comparisonHighlights.fastest)}</span>
                      <span className="highlight-duration">⏱️ {getTicketDuration(comparisonHighlights.fastest)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Filter Tabs */}
            {intent?.mode === 'all' && (
              <div className="filter-tabs">
                <button
                  className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('all'); setExpandedTicket(null); }}
                >
                  📊 All Options ({tickets.length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'flight' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('flight'); setExpandedTicket(null); }}
                  disabled={!tickets.some(t => t.mode === 'flight')}
                >
                  ✈️ Flights ({tickets.filter(t => t.mode === 'flight').length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'train' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('train'); setExpandedTicket(null); }}
                  disabled={!tickets.some(t => t.mode === 'train')}
                >
                  🚆 Trains ({tickets.filter(t => t.mode === 'train').length})
                </button>
                <button
                  className={`tab-btn ${activeTab === 'bus' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('bus'); setExpandedTicket(null); }}
                  disabled={!tickets.some(t => t.mode === 'bus')}
                >
                  🚌 Buses ({tickets.filter(t => t.mode === 'bus').length})
                </button>
              </div>
            )}

            {/* Ticket Cards */}
            <div className="ticket-cards">
              {filteredTickets.map((ticket, idx) => {
                const isExpanded = expandedTicket === idx;
                const label = getTicketLabel(ticket);
                const subLabel = getTicketSubLabel(ticket);
                const price = getTicketPrice(ticket);
                const departure = getTicketDeparture(ticket);
                const arrival = getTicketArrival(ticket);
                const duration = getTicketDuration(ticket);

                const ticketMode = ticket.mode || intent?.mode || 'bus';
                const ticketColor = getModeColor(ticketMode);
                const ticketSource = ticketMode === 'flight' ? 'Google Flights' : ticketMode === 'train' ? 'RedBus RedRail' : 'RedBus';

                return (
                  <div
                    key={idx}
                    className={`ticket-card ${isExpanded ? 'expanded' : ''}`}
                    onClick={() => setExpandedTicket(isExpanded ? null : idx)}
                    style={{ '--mode-color': ticketColor } as React.CSSProperties}
                  >
                    {/* Card Header */}
                    <div className="card-header">
                      <div className="card-operator">
                        <div className="operator-icon" style={{ background: `${ticketColor}20`, color: ticketColor }}>
                          {getModeIcon(ticketMode)}
                        </div>
                        <div>
                          <h3 className="operator-name">{label}</h3>
                          {subLabel && <span className="operator-type">{subLabel}</span>}
                        </div>
                      </div>
                      <div className="card-price">
                        <span className="price-value">{price}</span>
                        <span className="price-label">per person</span>
                      </div>
                    </div>

                    {/* Card Timeline */}
                    <div className="card-timeline">
                      <div className="timeline-point">
                        <span className="time-value">{departure}</span>
                        <span className="time-label">Departure</span>
                      </div>
                      <div className="timeline-line">
                        <div className="duration-badge">
                          <Clock size={12} />
                          {duration}
                        </div>
                      </div>
                      <div className="timeline-point">
                        <span className="time-value">{arrival}</span>
                        <span className="time-label">Arrival</span>
                      </div>
                    </div>

                    {/* Quick Info Chips */}
                    <div className="card-chips">
                      {ticket.seats && ticket.seats !== '--' && (
                        <span className="info-chip">{ticket.seats}</span>
                      )}
                      {ticket.rating && ticket.rating !== '--' && (
                        <span className="info-chip rating-chip">
                          <Star size={12} /> {ticket.rating}
                        </span>
                      )}
                      {ticket.stops && ticket.stops !== '--' && (
                        <span className="info-chip">{ticket.stops}</span>
                      )}
                      {intent?.mode === 'all' && (
                        <span className="info-chip" style={{ background: `${ticketColor}15`, color: ticketColor, fontWeight: 600, border: `1px solid ${ticketColor}25` }}>
                          {ticketMode.toUpperCase()}
                        </span>
                      )}
                    </div>

                    {/* Expand Indicator */}
                    <div className="expand-indicator">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      <span>{isExpanded ? 'Less details' : 'View details & book'}</span>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="card-expanded">
                        <div className="expanded-divider" />

                        {/* Full Details Grid */}
                        <div className="details-grid">
                          {Object.entries(ticket).map(([key, value]) => {
                            if (key === 'booking_url' || key === 'mode' || !value || value === '--') return null;
                            const labelMap: Record<string, string> = {
                              operator: '🚌 Operator', airline: '✈️ Airline', train: '🚆 Train',
                              type: '📋 Type', number: '#️⃣ Number', departure: '🕐 Departure',
                              arrival: '🕐 Arrival', duration: '⏱️ Duration', price: '💰 Price',
                              seats: '💺 Seats', rating: '⭐ Rating', stops: '🔄 Stops',
                              fare: '💰 Fare',
                            };
                            return (
                              <div key={key} className="detail-item">
                                <span className="detail-label">{labelMap[key] || key}</span>
                                <span className="detail-value">{value}</span>
                              </div>
                            );
                          })}
                        </div>

                        {/* Travel Tips */}
                        <div className="travel-tips">
                          <h4>💡 Travel Tips</h4>
                          <ul>
                            <li>Carry a valid government photo ID</li>
                            <li>Arrive at the station/airport at least 30 minutes early</li>
                            <li>Download the {ticketSource} app for e-tickets</li>
                          </ul>
                        </div>

                        {/* Booking Button */}
                        {ticket.booking_url && (
                          <a
                            href={ticket.booking_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="book-button"
                            style={{ background: `linear-gradient(135deg, ${ticketColor}, ${ticketColor}cc)` }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            Book on {ticketSource}
                            <ExternalLink size={16} />
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
