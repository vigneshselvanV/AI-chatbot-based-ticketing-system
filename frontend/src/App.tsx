import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Plane, Bus, Train, Calendar, MapPin, Loader2, ExternalLink, Clock, Star, ArrowRight, Sparkles, ChevronDown, ChevronUp, LogOut, Bookmark, Menu, Plus, MessageSquare } from 'lucide-react';
import './index.css';
import { AuthModal } from './components/AuthModal';
import type { User as AuthUser } from './components/AuthModal';

interface Message {
  id: string;
  type: 'user' | 'bot';
  text: string;
  isMarkdown?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
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
  ai_recommendation?: string;
}

const initialMessages: Message[] = [
  {
    id: 'init', type: 'bot',
    text: '👋 Hello! I\'m your AI travel assistant.\n\nI can help you find live tickets for:\n🚌 **Buses** — from RedBus\n✈️ **Flights** — from Google Flights\n🚆 **Trains** — from MakeMyTrip\n\nJust type something like:\n*"Check bus for Coimbatore to Rameswaram"*',
    isMarkdown: true
  }
];

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tickets, setTickets] = useState<TicketResult[]>([]);
  const [intent, setIntent] = useState<IntentData | null>(null);
  const [bookingUrl, setBookingUrl] = useState<string>('');
  const [dataSource, setDataSource] = useState<string>('');
  const [searchSummary, setSearchSummary] = useState<SearchSummary | null>(null);
  const [expandedTicket, setExpandedTicket] = useState<number | null>(null);
  const [conversationContext, setConversationContext] = useState<Record<string, string | null>>({});
  const [activeTab, setActiveTab] = useState<'all' | 'flight' | 'train' | 'bus' | 'saved'>('all');
  const [savedTickets, setSavedTickets] = useState<TicketResult[]>([]);
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    "Bus from Chennai to Madurai tomorrow",
    "Flights from Delhi to Mumbai",
    "Train from Coimbatore to Rameswaram"
  ]);

  // Auth State
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Sidebar & History State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  const handleNewChat = () => {
    const id = Date.now().toString();
    const newSession: ChatSession = { id, title: 'New Chat', messages: initialMessages, updatedAt: Date.now() };
    setChatSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(id);
    setMessages(initialMessages);
    setTickets([]);
    setIntent(null);
    setSearchSummary(null);
    setConversationContext({});
    if (window.innerWidth < 900) setIsSidebarOpen(false);
  };

  const loadSession = (id: string) => {
    const session = chatSessions.find(s => s.id === id);
    if (session) {
      setCurrentSessionId(id);
      setMessages(session.messages);
      setTickets([]);
      setIntent(null);
      setSearchSummary(null);
      setConversationContext({});
      if (window.innerWidth < 900) setIsSidebarOpen(false);
    }
  };

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
    
    setIsCheckingAuth(false);

    const savedSessions = localStorage.getItem('travel_ai_sessions');
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        setChatSessions(parsed);
        if (parsed.length > 0) {
          setCurrentSessionId(parsed[0].id);
          setMessages(parsed[0].messages);
        } else {
          handleNewChat();
        }
      } catch (e) { handleNewChat(); }
    } else {
      const savedMessages = localStorage.getItem('travel_ai_messages');
      if (savedMessages) {
        try { 
          const parsed = JSON.parse(savedMessages);
          const newSession = { id: Date.now().toString(), title: 'Legacy Chat', messages: parsed, updatedAt: Date.now() };
          setChatSessions([newSession]);
          setCurrentSessionId(newSession.id);
          setMessages(parsed);
        } catch (e) { handleNewChat(); }
      } else {
        handleNewChat();
      }
    }

    const savedTks = localStorage.getItem('travel_ai_saved_tickets');
    if (savedTks) {
      try { setSavedTickets(JSON.parse(savedTks)); } catch (e) {}
    }
  }, []);

  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setChatSessions(prev => prev.map(session => {
        if (session.id === currentSessionId) {
           let title = session.title;
           if (title === 'New Chat' && messages.length > 1) {
             const firstUserMsg = messages.find(m => m.type === 'user');
             if (firstUserMsg) title = firstUserMsg.text.slice(0, 25) + '...';
           }
           return { ...session, title, messages, updatedAt: Date.now() };
        }
        return session;
      }));
    }
  }, [messages, currentSessionId]);

  useEffect(() => {
    if (chatSessions.length > 0) {
      localStorage.setItem('travel_ai_sessions', JSON.stringify(chatSessions));
    }
  }, [chatSessions]);

  useEffect(() => {
    localStorage.setItem('travel_ai_saved_tickets', JSON.stringify(savedTickets));
  }, [savedTickets]);

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
        body: JSON.stringify({ query: queryText, context: conversationContext, history: messages.slice(-6) })
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

  const toggleSaveTicket = (ticket: TicketResult) => {
    const isSaved = savedTickets.some(t => t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator);
    if (isSaved) {
      setSavedTickets(savedTickets.filter(t => !(t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator)));
    } else {
      setSavedTickets([...savedTickets, ticket]);
    }
  };

  const filteredTickets = activeTab === 'saved' ? savedTickets : tickets.filter(ticket => {
    if (activeTab === 'all') return true;
    const ticketMode = ticket.mode || intent?.mode || 'bus';
    return ticketMode === activeTab;
  });

  const hasResults = tickets.length > 0 || savedTickets.length > 0;
  const intentSource = intent?.source || intent?.origin || null;
  const modeColor = getModeColor(intent?.mode);

  if (isCheckingAuth) {
    return (
      <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#f9fafb' }}>
        <Loader2 className="animate-spin" size={40} color="#4f46e5" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <header className="header" style={{ position: 'relative', zIndex: 10 }}>
          <div className="header-left">
            <Bot className="header-icon" size={28} />
            <h1>AI Travel Assistant</h1>
          </div>
          <div className="header-right" style={{ marginLeft: 'auto' }}>
            <button onClick={() => setShowAuthModal(true)} className="login-btn">
              <User size={16} />
              <span>Sign In</span>
            </button>
          </div>
        </header>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%)', padding: '20px', textAlign: 'center' }}>
          <div style={{ background: 'white', padding: '40px', borderRadius: '24px', boxShadow: '0 20px 40px rgba(0,0,0,0.05)', maxWidth: '500px', width: '100%' }}>
            <Bot size={64} color="#4f46e5" style={{ margin: '0 auto 20px auto' }} />
            <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#1f2937', marginBottom: '16px' }}>Welcome to AI Travel Assistant</h2>
            <p style={{ fontSize: '16px', color: '#6b7280', marginBottom: '32px', lineHeight: 1.5 }}>
              Sign in to start chatting with your personal AI travel agent. Discover the best routes, cheapest flights, and fastest trains across India.
            </p>
            <button 
              onClick={() => setShowAuthModal(true)}
              className="send-button"
              style={{ width: '100%', padding: '16px', fontSize: '16px', fontWeight: 600, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', borderRadius: '12px' }}
            >
              <Sparkles size={20} />
              Get Started Now
            </button>
          </div>
        </div>

        <AuthModal 
          isOpen={showAuthModal} 
          onClose={() => setShowAuthModal(false)} 
          onLogin={(newUser) => {
            setUser(newUser);
            setShowAuthModal(false);
          }} 
        />
      </div>
    );
  }

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

      {/* Sidebar Overlay */}
      <div 
        className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
        onClick={() => setIsSidebarOpen(false)}
      />

      {/* Sidebar */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'white', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <Bot size={24} color="#a5b4fc" /> TicketBot
          </h2>
        </div>
        <div className="sidebar-content">
          <button className="sidebar-btn new-chat-btn" onClick={handleNewChat}>
            <Plus size={18} /> New Search
          </button>
          <button 
            className={`sidebar-btn ${activeTab === 'saved' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('saved');
              setIntent(null);
              setTickets([]);
              if (window.innerWidth < 900) setIsSidebarOpen(false);
            }}
          >
            <Bookmark size={18} fill={activeTab === 'saved' ? "currentColor" : "none"} /> Saved Tickets ({savedTickets.length})
          </button>

          <div style={{ marginTop: '1rem' }}>
            <h3 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>History</h3>
            <div className="history-list">
              {chatSessions.map(session => (
                <div 
                  key={session.id} 
                  className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
                  onClick={() => loadSession(session.id)}
                >
                  <MessageSquare size={14} />
                  {session.title}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="sidebar-footer">
          {user && (
            <div className="user-settings">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(to right, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 'bold', color: 'white' }}>
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: '500', color: 'white', lineHeight: 1 }}>{user.name}</span>
                  <span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>Traveler</span>
                </div>
              </div>
              <button onClick={handleLogout} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', padding: '4px' }} title="Log out">
                <LogOut size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="header">
        <div className="header-left">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', marginRight: '12px' }}
          >
            <Menu size={24} />
          </button>
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
                  {activeTab === 'saved' && <span> (Showing Saved Tickets)</span>}
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

            {/* AI Recommendation Box */}
            {searchSummary?.ai_recommendation && intent?.mode === 'all' && (
              <div className="ai-recommendation-box" style={{ background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)', padding: '20px', borderRadius: '16px', marginBottom: '24px', border: '1px solid rgba(124, 58, 237, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Bot size={20} color="#7c3aed" />
                  <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#a5b4fc', margin: 0 }}>AI Recommendation</h3>
                </div>
                <p style={{ fontSize: '0.95rem', color: 'rgba(255, 255, 255, 0.85)', lineHeight: 1.6, margin: 0 }}>
                  {renderText(searchSummary.ai_recommendation)}
                </p>
              </div>
            )}

            {/* Filter Tabs */}
            {(intent?.mode === 'all' || savedTickets.length > 0) && (
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
                {savedTickets.length > 0 && (
                  <button
                    className={`tab-btn ${activeTab === 'saved' ? 'active' : ''}`}
                    onClick={() => { setActiveTab('saved'); setExpandedTicket(null); }}
                  >
                    🔖 Saved ({savedTickets.length})
                  </button>
                )}
              </div>
            )}

            {/* Content Switch: Table View for 'All' vs Card View for individual modes */}
            {activeTab === 'all' && intent?.mode === 'all' ? (
              <div className="modern-table-container">
                <table className="modern-table">
                  <thead>
                    <tr>
                      <th>Mode</th>
                      <th>Operator / Details</th>
                      <th>Departure</th>
                      <th>Duration</th>
                      <th>Arrival</th>
                      <th>Price</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTickets.map((ticket, idx) => {
                      const ticketMode = ticket.mode || 'bus';
                      const ticketColor = getModeColor(ticketMode);
                      return (
                        <tr key={idx}>
                          <td>
                            <div className="table-mode-tag" style={{ background: `${ticketColor}20`, color: ticketColor }}>
                              {getModeIcon(ticketMode)} {ticketMode.toUpperCase()}
                            </div>
                          </td>
                          <td>
                            <div style={{ fontWeight: 600, color: 'rgba(255, 255, 255, 0.95)' }}>{getTicketLabel(ticket)}</div>
                            <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.5)' }}>{getTicketSubLabel(ticket)}</div>
                          </td>
                          <td style={{ fontWeight: 500, color: 'rgba(255, 255, 255, 0.85)' }}>{getTicketDeparture(ticket)}</td>
                          <td style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem' }}><Clock size={12} style={{ display: 'inline', marginRight: '4px' }}/>{getTicketDuration(ticket)}</td>
                          <td style={{ fontWeight: 500, color: 'rgba(255, 255, 255, 0.85)' }}>{getTicketArrival(ticket)}</td>
                          <td>
                            <div style={{ fontWeight: 700, color: ticketColor, fontSize: '1.05rem' }}>{getTicketPrice(ticket)}</div>
                          </td>
                          <td>
                            <a href={ticket.booking_url || bookingUrl || '#'} target="_blank" rel="noopener noreferrer" className="table-book-btn" style={{ background: ticketColor }}>
                              Book <ExternalLink size={12} style={{ marginLeft: '4px' }} />
                            </a>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
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
                const isSaved = savedTickets.some(t => t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator);

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
                      <div className="card-price" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                        <div>
                          <span className="price-value">{price}</span>
                          <span className="price-label">per person</span>
                        </div>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleSaveTicket(ticket);
                          }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: isSaved ? ticketColor : '#9ca3af', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: 500 }}
                          title={isSaved ? "Remove saved ticket" : "Save ticket"}
                        >
                          <Bookmark size={14} fill={isSaved ? ticketColor : "none"} />
                          {isSaved ? "Saved" : "Save"}
                        </button>
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
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
