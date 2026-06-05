import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, Bus, Calendar, MapPin, Loader2, ExternalLink, ArrowRight, Sparkles, LogOut, Bookmark, Menu, Plus, MessageSquare, Mic, MicOff, History, Map } from 'lucide-react';
import './index.css';
import { AuthModal } from './components/AuthModal';
import { TicketCard } from './components/TicketCard';
import { ConnectingRoute } from './components/ConnectingRoute';
import { BookingHistory } from './components/BookingHistory';
import { ReviewModal } from './components/ReviewModal';
import { TravelGuidePanel } from './components/TravelGuidePanel';
import type { TravelGuideData } from './components/TravelGuidePanel';
// ThemeToggle removed — dark mode only
import { useVoiceInput } from './hooks/useVoiceInput';
import { useUserPreferences } from './hooks/useUserPreferences';
import { useBookingHistory } from './hooks/useBookingHistory';
import { useReviews } from './hooks/useReviews';
import type { Booking } from './hooks/useBookingHistory';
import type { User as AuthUser } from './components/AuthModal';

interface Message {
  id: string;
  type: 'user' | 'bot';
  text: string | React.ReactNode;
  isMarkdown?: boolean;
  showExploreBtn?: boolean;
  exploreDest?: string;
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
  preference?: string | null;
  seatType?: string | null;
  operator?: string | null;
}

interface TicketResult {
  operator: string;
  type?: string;
  departure?: string;
  arrival?: string;
  duration?: string;
  price?: string;
  booking_url?: string;
  [key: string]: any;
}

interface SearchSummary {
  mode: string;
  source: string;
  destination: string;
  date: string;
  total_results: number;
  ai_recommendation?: string;
  provider_info?: string;
}

// ═══════════════════════════════════════════
// NEW SEARCH DETECTION — Bug Fix
// ═══════════════════════════════════════════
function cleanCityName(name: string): string {
  return name.trim().replace(/[^a-zA-Z\s]/g, '').trim();
}

function detectNewSearch(
  userMessage: string,
  currentState: Record<string, string | null>
): { isNewSearch: boolean; from_city?: string; to_city?: string } {
  const msg = userMessage.toLowerCase().trim();

  // Pattern 1: Full route "X to Y"
  const routePattern = /([a-zA-Z\s]{2,})\s+to\s+([a-zA-Z\s]{2,})/i;
  const routeMatch = msg.match(routePattern);

  // Pattern 2: Search intent keywords
  const searchKeywords = [
    'search', 'find', 'check', 'show', 'book',
    'want to travel', 'going to', 'i want to go',
    'bus from', 'ticket from', 'travelling from',
    'travel from', 'buses from'
  ];
  const hasSearchKeyword = searchKeywords.some(k => msg.includes(k));

  // Pattern 3: "new search", "search again", "another search"
  const resetKeywords = ['new search', 'search again', 'another search', 'different route', 'another route'];
  const isResetRequest = resetKeywords.some(k => msg.includes(k));

  if (isResetRequest) {
    return { isNewSearch: true };
  }

  if (routeMatch) {
    const detectedFrom = cleanCityName(routeMatch[1]).toLowerCase();
    const detectedTo = cleanCityName(routeMatch[2]).toLowerCase();

    // Check if cities are actually different from what we have
    const currentFrom = (currentState?.from_city || '').toLowerCase();
    const currentTo = (currentState?.to_city || '').toLowerCase();

    const newCitiesDetected =
      detectedFrom !== currentFrom ||
      detectedTo !== currentTo;

    // Trigger new search if:
    // - Has search keyword with route, OR
    // - Completely new cities detected, OR
    // - We don't have cities yet and route is given
    if (hasSearchKeyword || newCitiesDetected || (!currentFrom && !currentTo)) {
      return {
        isNewSearch: true,
        from_city: cleanCityName(routeMatch[1]),
        to_city: cleanCityName(routeMatch[2]),
      };
    }
  }

  return { isNewSearch: false };
}

const initialMessages: Message[] = [
  {
    id: 'init', type: 'bot',
    text: "👋 **Hey! Ready to find your perfect bus?**\n\nJust tell me where you want to go!\n\nTry: *Coimbatore to Chennai*",
    isMarkdown: true
  }
];

type ResultPanelTab = 'buses' | 'guide';

function App() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tickets, setTickets] = useState<TicketResult[]>([]);
  const [intent, setIntent] = useState<IntentData | null>(null);
  const [bookingUrl, setBookingUrl] = useState<string>('');
  const [, setDataSource] = useState<string>('');
  const [searchSummary, setSearchSummary] = useState<SearchSummary | null>(null);
  const [expandedTicket, setExpandedTicket] = useState<number | null>(null);
  const [conversationContext, setConversationContext] = useState<Record<string, string | null>>({});
  const [activeTab, setActiveTab] = useState<'all' | 'saved'>('all');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<string>('departure_asc');
  // Use sortBy to avoid TS error
  console.debug("Active Sort:", sortBy);
  const [savedTickets, setSavedTickets] = useState<TicketResult[]>([]);
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([
    "Tomorrow 📅",
    "Day after tomorrow",
    "AC Bus ❄️",
    "Sleeper 🛏️",
    "Cheapest 💰"
  ]);

  // Auth State
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Sidebar & History State
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  // Feature State
  const [connectingRouteData, setConnectingRouteData] = useState<any>(null);
  const [showBookingHistory, setShowBookingHistory] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewBooking, setReviewBooking] = useState<Booking | null>(null);
  // BUG FIX: use a ref instead of state to prevent StrictMode double-fire of the greeting
  const greetingShownRef = useRef(false);

  // ── Travel Guide State ──
  const [resultPanelTab, setResultPanelTab] = useState<ResultPanelTab>('buses');
  const [travelGuideData, setTravelGuideData] = useState<TravelGuideData | null>(null);
  const [isLoadingGuide, setIsLoadingGuide] = useState(false);
  const [currentGuideDest, setCurrentGuideDest] = useState<string>('');

  // Hooks
  const voice = useVoiceInput();
  const prefs = useUserPreferences();
  const bookingHistory = useBookingHistory();
  const reviews = useReviews();

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
    setConnectingRouteData(null);
    setShowBookingHistory(false);
    setTravelGuideData(null);
    setResultPanelTab('buses');
    setCurrentGuideDest('');
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
      setConnectingRouteData(null);
      setShowBookingHistory(false);
      setTravelGuideData(null);
      setResultPanelTab('buses');
      if (window.innerWidth < 900) setIsSidebarOpen(false);
    }
  };

  // ── Fetch travel guide ──
  const fetchTravelGuide = useCallback(async (destination: string) => {
    if (!destination) return;
    const dest = destination.trim();
    if (dest.toLowerCase() === currentGuideDest.toLowerCase() && travelGuideData) return; // already loaded

    setIsLoadingGuide(true);
    setCurrentGuideDest(dest);
    setTravelGuideData(null);

    // Abort after 25 seconds so spinner never hangs forever
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);

    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(
        `${apiBase}/api/travel-guide?destination=${encodeURIComponent(dest)}`,
        { signal: controller.signal }
      );
      const json = await res.json();
      if (json.data) {
        setTravelGuideData(json.data as TravelGuideData);
      }
    } catch (e: unknown) {
      if ((e as Error).name === 'AbortError') {
        // Timed out — fetch a second time with no timeout to get fallback fast
        try {
          const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          const res2 = await fetch(
            `${apiBase}/api/travel-guide?destination=${encodeURIComponent(dest)}&fallback=1`
          );
          const json2 = await res2.json();
          if (json2.data) setTravelGuideData(json2.data as TravelGuideData);
        } catch (_) { /* ignore */ }
      } else {
        console.error('Travel guide fetch error:', e);
      }
    } finally {
      clearTimeout(timeout);
      setIsLoadingGuide(false);
    }
  }, [currentGuideDest, travelGuideData]);


  useEffect(() => {
    const savedUser = localStorage.getItem('travel_ai_user');
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)); } catch (e) {}
    }
    setIsCheckingAuth(false);

    const savedTheme = localStorage.getItem('busbot-theme');
    const theme = savedTheme || 'dark';
    document.documentElement.setAttribute('data-theme', theme);

    const savedSessions = localStorage.getItem('travel_ai_sessions');
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        if (savedSessions.includes('_owner') || savedSessions.includes('"type":"div"')) {
          localStorage.removeItem('travel_ai_sessions');
          handleNewChat();
        } else {
          setChatSessions(parsed);
          if (parsed.length > 0) {
            setCurrentSessionId(parsed[0].id);
            setMessages(parsed[0].messages);
          } else { handleNewChat(); }
        }
      } catch (e) { handleNewChat(); }
    } else { handleNewChat(); }

    const savedTks = localStorage.getItem('travel_ai_saved_tickets');
    if (savedTks) { try { setSavedTickets(JSON.parse(savedTks)); } catch (e) {} }
  }, []);

  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setChatSessions(prev => prev.map(session => {
        if (session.id === currentSessionId) {
          let title = session.title;
          if (title === 'New Chat' && messages.length > 1) {
            const firstUserMsg = messages.find(m => m.type === 'user');
            if (firstUserMsg && typeof firstUserMsg.text === 'string') title = firstUserMsg.text.slice(0, 25) + '...';
          }
          return { ...session, title, messages, updatedAt: Date.now() };
        }
        return session;
      }));
    }
  }, [messages, currentSessionId]);

  useEffect(() => {
    if (chatSessions.length > 0) localStorage.setItem('travel_ai_sessions', JSON.stringify(chatSessions));
  }, [chatSessions]);

  useEffect(() => {
    localStorage.setItem('travel_ai_saved_tickets', JSON.stringify(savedTickets));
  }, [savedTickets]);

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('travel_ai_user');
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); };
  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    setSuggestedQueries([]);
  };

  useEffect(() => { if (voice.transcript) setInput(voice.transcript); }, [voice.transcript]);

  useEffect(() => {
    // BUG FIX: Use ref guard to prevent StrictMode double-fire from adding greeting twice
    if (user && !greetingShownRef.current) {
      const greeting = prefs.getPersonalizedGreeting(user.name);
      if (greeting) {
        greetingShownRef.current = true;
        setMessages(prev => [...prev, { id: `greeting-${Date.now()}`, type: 'bot', text: greeting, isMarkdown: true }]);
        const topRoute = prefs.getMostFrequentRoute();
        if (topRoute) setSuggestedQueries([`Bus from ${topRoute.from} to ${topRoute.to} tomorrow`, "Tomorrow 📅", "AC Bus ❄️"]);
      }
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), type: 'user', text: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    const queryText = input.trim();
    setInput('');
    setIsLoading(true);
    setSuggestedQueries([]);
    setShowBookingHistory(false);

    // ══════════════════════════════════════
    // 🐛 BUG FIX: New Search Detection
    // ══════════════════════════════════════
    const searchDetection = detectNewSearch(queryText, conversationContext);

    let effectiveContext = conversationContext;

    if (searchDetection.isNewSearch) {
      // Full state reset with new route pre-filled
      const newCtx: Record<string, string | null> = {
        from_city: searchDetection.from_city || null,
        to_city: searchDetection.to_city || null,
        date: null,
        passengers: '1',
      };
      setConversationContext(newCtx);
      effectiveContext = newCtx;

      // If BOTH cities detected → just ask for date, don't restart
      if (searchDetection.from_city && searchDetection.to_city) {
        // Don't inject context — let query carry the full route naturally
        // The backend AI / rule-based will parse the full route from the query
        effectiveContext = {}; // Let backend parse fresh from query text
      } else {
        // Partial reset (e.g., "new search") → clear everything
        setConversationContext({});
        effectiveContext = {};
      }

      // Reset results panel
      setTickets([]);
      setConnectingRouteData(null);
      setIntent(null);
      setSearchSummary(null);
      setResultPanelTab('buses');
    }
    // ══════════════════════════════════════

    try {
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiBase}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, context: effectiveContext, history: messages.slice(-6) })
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      if (data.type === 'chat') {
        setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', text: data.message, isMarkdown: true }]);
        setTickets([]);
        setIntent(null);
        setSearchSummary(null);
        setConnectingRouteData(null);

      } else if (data.type === 'ask_details') {
        setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', text: data.message, isMarkdown: true }]);
        if (data.partial_intent) setConversationContext(data.partial_intent);
        if (data.quick_replies && data.quick_replies.length > 0) setSuggestedQueries(data.quick_replies);

      } else if (data.type === 'connecting_route') {
        setConnectingRouteData(data);
        setTickets([]);
        setIntent(data.intent);
        setSearchSummary(null);
        setConversationContext({});
        setMessages(prev => [...prev, {
          id: Date.now().toString(), type: 'bot',
          text: `🧠 No direct bus found for **${data.source} → ${data.destination}**. But I found a smart connecting route!\n\n🚌 **${data.source} → ${data.intermediate} → ${data.destination}**\n\n⏱️ Total: ${data.total_duration} | 💰 ${data.total_cost}\n\nCheck the route details on the right! 👉`,
          isMarkdown: true
        }]);

      } else if (data.type === 'tickets') {
        setConnectingRouteData(null);
        setIntent(data.intent);
        setActiveFilter(data.active_filter || data.intent?.filter || null);
        setSortBy(data.sort_by || data.intent?.sort_by || 'departure_asc');
        setTickets(data.data || []);
        setBookingUrl(data.booking_url || '');
        setDataSource(data.data_source || '');
        setSearchSummary(data.search_summary || null);
        setConversationContext({});
        setExpandedTicket(null);
        setActiveTab('all');
        setResultPanelTab('buses');

        if (data.search_summary?.source && data.search_summary?.destination) {
          prefs.logSearch(data.search_summary.source, data.search_summary.destination, data.search_summary.date || '', data.intent?.preference || undefined);
        }

        if (!data.data || data.data.length === 0) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(), type: 'bot',
            text: 'No direct buses found for this route.\nTry checking RedBus or AbhiBus directly.\n\n[🔴 RedBus](https://www.redbus.in) | [🟠 AbhiBus](https://www.abhibus.com) | [🔵 MakeMyTrip](https://www.makemytrip.com)',
            isMarkdown: true
          }]);
        } else {
          const sourceLabel = data.search_summary?.source || '';
          const destLabel = data.search_summary?.destination || '';
          const dateLabel = data.search_summary?.date || '';
          const count = data.data.length;

          // Message 1: Bus results
          setMessages(prev => [...prev, {
            id: Date.now().toString(), type: 'bot',
            text: `✅ Found **${count} buses** from ${sourceLabel} to ${destLabel} on ${dateLabel}! 🚌\n\n👆 Tap any bus to book directly.`,
            isMarkdown: true
          }]);

          // Message 2: Travel guide teaser (2s delay)
          if (destLabel) {
            setTimeout(() => {
              setMessages(prev => [...prev, {
                id: `guide-teaser-${Date.now()}`,
                type: 'bot',
                text: `🗺️ Planning to explore **${destLabel}**? Here's what you can see there! 👇`,
                isMarkdown: true,
                showExploreBtn: true,
                exploreDest: destLabel
              }]);
            }, 2000);
          }
        }
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), type: 'bot',
        text: '⚠️ Slight hiccup! Retrying...',
        isMarkdown: true
      }]);
      setTimeout(async () => {
        try {
          const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          const res = await fetch(`${apiBase}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: queryText, context: effectiveContext, history: messages.slice(-6) })
          });
          const data = await res.json();
          if (data.type === 'tickets') {
            setTickets(data.data || []);
            setSearchSummary(data.search_summary || null);
            setMessages(prev => [...prev.slice(0, -1), {
              id: Date.now().toString(), type: 'bot',
              text: `✅ Found **${data.data.length} buses**.\n\n👆 Tap any bus to book directly.`,
              isMarkdown: true
            }]);
          } else {
            setMessages(prev => [...prev.slice(0, -1), { id: Date.now().toString(), type: 'bot', text: 'No direct buses found.\n[🔴 RedBus](https://www.redbus.in) | [🟠 AbhiBus](https://www.abhibus.com)', isMarkdown: true }]);
          }
        } catch (e) {
          setMessages(prev => [...prev.slice(0, -1), { id: Date.now().toString(), type: 'bot', text: '🚨 Server unreachable. Please ensure the backend is running.', isMarkdown: true }]);
        }
      }, 2000);
    } finally {
      setIsLoading(false);
    }
  };

  const getModeColor = (_mode: string | null | undefined): string => '#34d399';

  const renderText = (text: string) => {
    const parts = text.split('\n');
    return parts.map((line, i) => {
      let rendered = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      rendered = rendered.replace(/\*(.+?)\*/g, '<em>$1</em>');
      // BUG FIX: render markdown links [text](url) as real clickable anchor tags
      rendered = rendered.replace(
        /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:#a5b4fc;text-decoration:underline;text-underline-offset:2px;">$1</a>'
      );
      return <span key={i} dangerouslySetInnerHTML={{ __html: rendered + (i < parts.length - 1 ? '<br/>' : '') }} />;
    });
  };

  const toggleSaveTicket = (ticket: TicketResult) => {
    const isSaved = savedTickets.some(t => t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator);
    if (isSaved) {
      setSavedTickets(savedTickets.filter(t => !(t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator)));
    } else {
      setSavedTickets([...savedTickets, ticket]);
    }
  };

  const applyFilters = (tks: TicketResult[]) => {
    // The backend now handles the smart filters. We just return the tickets here.
    return tks;
  };

  const getFilterLabel = (f: string) => {
    const labels: Record<string,string> = {
      cheapest: '💰 Cheapest First',
      ac:       '❄️ AC Buses Only',
      sleeper:  '🛏️ Sleepers Only',
      non_ac:   '🚌 Non-AC Only',
      volvo:    '✨ Volvo/Luxury',
      fastest:  '⚡ Fastest First',
      night:    '🌙 Night Buses Only',
    };
    return labels[f] || f;
  };

  const filteredTickets = activeTab === 'saved' ? savedTickets : applyFilters(tickets);
  const hasResults = tickets.length > 0 || savedTickets.length > 0 || connectingRouteData;
  const intentSource = intent?.source || intent?.origin || null;
  const modeColor = getModeColor(intent?.mode);

  // Handle "Explore {destination}" button click from chat
  const handleExploreDestination = (dest: string) => {
    setResultPanelTab('guide');
    fetchTravelGuide(dest);
    // If no results panel open, open it
    if (!hasResults) {
      // Just show the guide panel by triggering a dummy ticket state
      // We'll handle this by having a travelGuide-only mode
    }
  };

  if (isCheckingAuth) {
    return <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: '#f9fafb' }}><Loader2 className="animate-spin" size={40} color="#4f46e5" /></div>;
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
            <p style={{ fontSize: '16px', color: '#6b7280', marginBottom: '32px', lineHeight: 1.5 }}>Sign in to start chatting with your smart bus booking companion.</p>
            <button onClick={() => setShowAuthModal(true)} className="send-button" style={{ width: '100%', padding: '16px', fontSize: '16px', fontWeight: 600, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px', borderRadius: '12px' }}>
              <Sparkles size={20} />
              Get Started Now
            </button>
          </div>
        </div>
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} onLogin={(newUser) => { setUser(newUser); setShowAuthModal(false); }} />
      </div>
    );
  }

  // Whether to show the results section (bus results OR travel guide)
  // BUG FIX: added parentheses to fix operator precedence (&&  binds tighter than ||)
  const showResultsPanel = hasResults || ((isLoadingGuide || travelGuideData) && resultPanelTab === 'guide');

  return (
    <div className="app-container">
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} onLogin={(newUser) => { setUser(newUser); setShowAuthModal(false); }} />
      <div className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`} onClick={() => setIsSidebarOpen(false)} />
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header"><h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'white', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}><Bus size={24} color="#34d399" /> AI Travel Assistant 🚌</h2></div>
        <div className="sidebar-content">
          <button className="sidebar-btn new-chat-btn" onClick={handleNewChat}><Plus size={18} /> New Search</button>
          <button className={`sidebar-btn ${showBookingHistory ? 'active' : ''}`} onClick={() => { setShowBookingHistory(true); setTickets([]); setConnectingRouteData(null); setIntent(null); if (window.innerWidth < 900) setIsSidebarOpen(false); }}>
            <History size={18} /> My Bookings 📋 ({bookingHistory.bookings.length})
          </button>
          <button className={`sidebar-btn ${activeTab === 'saved' ? 'active' : ''}`} onClick={() => { setActiveTab('saved'); setIntent(null); setTickets([]); if (window.innerWidth < 900) setIsSidebarOpen(false); }}>
            <Bookmark size={18} fill={activeTab === 'saved' ? 'currentColor' : 'none'} /> Saved Tickets ({savedTickets.length})
          </button>
          <div style={{ marginTop: '1rem' }}><h3 style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)', marginBottom: '0.5rem', letterSpacing: '0.05em' }}>History</h3><div className="history-list">{chatSessions.map(session => (<div key={session.id} className={`history-item ${session.id === currentSessionId ? 'active' : ''}`} onClick={() => loadSession(session.id)}><MessageSquare size={14} />{session.title}</div>))}</div></div>
        </div>
        <div className="sidebar-footer">
          {user && (
            <div className="user-settings">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(to right, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 'bold', color: 'white' }}>{user.name.charAt(0).toUpperCase()}</div><div style={{ display: 'flex', flexDirection: 'column' }}><span style={{ fontSize: '0.85rem', fontWeight: '500', color: 'white', lineHeight: 1 }}>{user.name}</span><span style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>Traveler</span></div></div>
              <button onClick={handleLogout} style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.5)', cursor: 'pointer', padding: '4px' }} title="Log out"><LogOut size={16} /></button>
            </div>
          )}
        </div>
      </div>

      <header className="app-header">
        <div className="logo-area">
          <button onClick={() => setIsSidebarOpen(true)} style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}><Menu size={24} /></button>
          <div className="logo-icon">🚌</div>
          <span className="logo-text">AI Bus Assistant</span>
        </div>
        <div className="header-right">
          {searchSummary && (<div className="route-pill"><strong>{searchSummary.source}</strong> → <strong>{searchSummary.destination}</strong></div>)}

        </div>
      </header>

      <main className="main-content">
        <section className={`chat-section ${showResultsPanel || showBookingHistory ? 'has-results' : ''}`}>
          <div className="chat-messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message ${msg.type}`}>
                <div className="avatar">{msg.type === 'user' ? <User size={20} color="white" /> : <Bot size={20} color="#a5b4fc" />}</div>
                <div className="message-bubble">
                  {msg.isMarkdown && typeof msg.text === 'string' ? renderText(msg.text) : msg.text}
                  {msg.showExploreBtn && msg.exploreDest && (
                    <div>
                      <button
                        className="explore-dest-btn"
                        onClick={() => handleExploreDestination(msg.exploreDest!)}
                        id={`explore-btn-${msg.id}`}
                      >
                        <Map size={16} />
                        🗺️ Explore {msg.exploreDest}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {suggestedQueries.length > 0 && !isLoading && (<div className="suggestions-container">{suggestedQueries.map((suggestion, idx) => (<button key={idx} className="suggestion-chip" onClick={() => handleSuggestionClick(suggestion)}><Sparkles size={14} />{suggestion}</button>))}</div>)}
            {isLoading && (<div className="message bot"><div className="avatar"><Bot size={20} color="#a5b4fc" /></div><div className="message-bubble loading-bubble"><div className="loading-dots"><div className="dot"></div><div className="dot"></div><div className="dot"></div></div><div className="loading-text">🔍 Scanning live websites...</div></div></div>)}
            <div ref={messagesEndRef} />
          </div>
          <div className="input-area">
            <form onSubmit={handleSubmit} className="input-container">
              <input type="text" className="chat-input" placeholder="Search for bus tickets... 🚌" value={input} onChange={(e) => setInput(e.target.value)} disabled={isLoading} />
              {voice.isSupported && (<button type="button" className={`mic-button ${voice.isListening ? 'listening' : ''}`} onClick={() => { if (voice.isListening) { voice.stopListening(); } else { voice.clearTranscript(); voice.startListening(); } }} disabled={isLoading} title={voice.isListening ? 'Stop listening' : 'Start voice input'}>{voice.isListening ? <MicOff size={18} /> : <Mic size={18} />}</button>)}
              <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>{isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}</button>
            </form>
            {(voice.isListening || voice.interimTranscript) && (<div className="transcript-preview"><Mic size={14} className={voice.isListening ? 'animate-pulse' : ''} /><span>{voice.interimTranscript || 'Listening...'}</span></div>)}
          </div>
        </section>

        {showBookingHistory ? (
          <section className="results-section">
            <BookingHistory
              upcoming={bookingHistory.getUpcoming()}
              past={bookingHistory.getPast()}
              monthlyStats={bookingHistory.getMonthlyStats()}
              onCancel={(id) => bookingHistory.cancelBooking(id)}
              onRebook={(booking) => { setShowBookingHistory(false); setInput(`Bus from ${booking.from} to ${booking.to} tomorrow`); }}
              onRate={(booking) => { setReviewBooking(booking); setShowReviewModal(true); }}
              hasReviewed={(id) => reviews.hasReviewed(id)}
              onClose={() => setShowBookingHistory(false)}
            />
          </section>
        ) : connectingRouteData ? (
          <section className="results-section">
            <ConnectingRoute
              source={connectingRouteData.source}
              intermediate={connectingRouteData.intermediate}
              destination={connectingRouteData.destination}
              leg1={connectingRouteData.leg1}
              leg2={connectingRouteData.leg2}
              totalDuration={connectingRouteData.total_duration}
              totalCost={connectingRouteData.total_cost}
              onBookBoth={() => { if (connectingRouteData.leg1?.booking_url) window.open(connectingRouteData.leg1.booking_url, '_blank'); if (connectingRouteData.leg2?.booking_url) window.open(connectingRouteData.leg2.booking_url, '_blank'); }}
            />
          </section>
        ) : (hasResults || isLoadingGuide || travelGuideData) && (
          <section className="results-section">
            {/* ── Panel Tabs ── */}
            <div className="results-panel-tabs">
              <button
                id="bus-results-tab"
                className={`panel-tab-btn ${resultPanelTab === 'buses' ? 'active' : ''}`}
                onClick={() => setResultPanelTab('buses')}
              >
                <Bus size={15} /> Bus Results {tickets.length > 0 && `(${tickets.length})`}
              </button>
              <button
                id="travel-guide-tab"
                className={`panel-tab-btn ${resultPanelTab === 'guide' ? 'guide-active' : ''}`}
                onClick={() => {
                  setResultPanelTab('guide');
                  const dest = searchSummary?.destination || currentGuideDest;
                  if (dest) fetchTravelGuide(dest);
                }}
              >
                <Map size={15} /> 🗺️ Travel Guide {currentGuideDest && `· ${currentGuideDest}`}
              </button>
            </div>

            {/* ── Bus Results Tab ── */}
            {resultPanelTab === 'buses' && (
              <>
                <div className="results-header">
                  <div><h2><Bus size={20} /> Available Bus Options</h2><p className="results-subtitle">{tickets.length} results found{activeTab === 'saved' && <span> (Showing Saved Tickets)</span>}</p></div>
                  {bookingUrl && (<a href={bookingUrl} target="_blank" rel="noopener noreferrer" className="view-all-btn">View all on Booking Site <ExternalLink size={14} /></a>)}
                </div>
                {intent && (<div className="intent-badges">{intentSource && intent.destination && (<div className="badge route-badge" style={{ borderColor: `${modeColor}40` }}><MapPin size={14} style={{ color: modeColor }} />{intentSource} <ArrowRight size={12} /> {intent.destination}</div>)}{intent.date && (<div className="badge date-badge" style={{ borderColor: `${modeColor}40` }}><Calendar size={14} style={{ color: modeColor }} />{intent.date}</div>)}</div>)}
                {savedTickets.length > 0 && (<div className="filter-tabs"><button className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`} onClick={() => { setActiveTab('all'); setExpandedTicket(null); }}>🚌 Results ({tickets.length})</button><button className={`tab-btn ${activeTab === 'saved' ? 'active' : ''}`} onClick={() => { setActiveTab('saved'); setExpandedTicket(null); }}>🔖 Saved ({savedTickets.length})</button></div>)}
                {activeTab === 'all' && activeFilter && (
                  <div className="filter-active-badge" data-filter={activeFilter}>
                    {getFilterLabel(activeFilter)}
                    <span className="result-count">{tickets.length} buses</span>
                    <button className="clear-filter-btn" onClick={() => { setActiveFilter(null); setSortBy('departure_asc'); }}>✕ Clear</button>
                  </div>
                )}
                <div className="ticket-cards">
                  {filteredTickets.map((ticket, idx) => (
                    <TicketCard
                      key={idx}
                      ticket={ticket}
                      activeFilter={activeFilter}
                      cardIndex={idx}
                      intentSource={searchSummary?.source || ''}
                      intentDest={searchSummary?.destination || ''}
                      isExpanded={expandedTicket === idx}
                      onToggleExpand={() => setExpandedTicket(expandedTicket === idx ? null : idx)}
                      isSaved={savedTickets.some(t => t.price === ticket.price && t.departure === ticket.departure && t.operator === ticket.operator)}
                      onToggleSave={() => toggleSaveTicket(ticket)}
                      operatorRating={reviews.getOperatorRating(ticket.operator || '')}
                      onBook={(selectedSeats, totalAmount) => {
                        const booking = bookingHistory.addBooking(ticket, searchSummary?.source || '', searchSummary?.destination || '', searchSummary?.date || '', selectedSeats, totalAmount);
                        prefs.logBooking(searchSummary?.source || '', searchSummary?.destination || '', ticket.operator || '', totalAmount);
                        setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', text: `🎫 **Booking Confirmed!** ${booking.id}\n\n🚌 ${booking.operator} • ${booking.busType}\n📍 ${booking.from} → ${booking.to}\n📅 ${booking.date} | ⏰ ${booking.departureTime}\n💺 Seat: ${booking.seatNumbers.join(', ')}\n💰 ₹${booking.totalAmount.toLocaleString('en-IN')}\n\nStatus: ✅ CONFIRMED`, isMarkdown: true }]);
                      }}
                    />
                  ))}
                </div>

                {/* Explore button at bottom of bus results */}
                {searchSummary?.destination && (
                  <div style={{ marginTop: '16px', textAlign: 'center' }}>
                    <button
                      id="explore-destination-bottom-btn"
                      className="explore-dest-btn"
                      style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => {
                        setResultPanelTab('guide');
                        fetchTravelGuide(searchSummary.destination);
                      }}
                    >
                      <Map size={18} /> 🗺️ Explore {searchSummary.destination} — Travel Guide
                    </button>
                  </div>
                )}
              </>
            )}

            {/* ── Travel Guide Tab ── */}
            {resultPanelTab === 'guide' && (
              <TravelGuidePanel
                destination={currentGuideDest || searchSummary?.destination || ''}
                data={travelGuideData}
                isLoading={isLoadingGuide}
              />
            )}
          </section>
        )}
      </main>

      {reviewBooking && (
        <ReviewModal
          isOpen={showReviewModal}
          onClose={() => { setShowReviewModal(false); setReviewBooking(null); }}
          bookingId={reviewBooking.id}
          operator={reviewBooking.operator}
          route={`${reviewBooking.from} → ${reviewBooking.to}`}
          userName={user?.name || 'Traveler'}
          onSubmit={(bookingId, operator, route, rating, aspects, comment, userName) => {
            reviews.addReview(bookingId, operator, route, rating, aspects, comment, userName);
            bookingHistory.completeBooking(bookingId);
          }}
        />
      )}
    </div>
  );
}

export default App;
