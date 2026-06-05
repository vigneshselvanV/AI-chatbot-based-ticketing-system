import { useState, useCallback, useEffect } from 'react';

export interface FrequentRoute {
  from: string;
  to: string;
  frequency: number;
  preferredDay: string | null;
  preferredTime: string | null;
  preferredType: string | null;
  avgSpend: number;
  lastSearched: string;
}

export interface UserPreferences {
  frequentRoutes: FrequentRoute[];
  preferredOperators: string[];
  preferredSeat: string | null;
  lastBooking: string | null;
  totalSearches: number;
  totalBookings: number;
}

const STORAGE_KEY = 'travel_ai_preferences';
const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function getDefaultPrefs(): UserPreferences {
  return {
    frequentRoutes: [],
    preferredOperators: [],
    preferredSeat: null,
    lastBooking: null,
    totalSearches: 0,
    totalBookings: 0,
  };
}

function loadPrefs(): UserPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Error loading preferences', e);
  }
  return getDefaultPrefs();
}

function savePrefs(prefs: UserPreferences) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
}

export function useUserPreferences() {
  const [preferences, setPreferences] = useState<UserPreferences>(loadPrefs);

  useEffect(() => {
    savePrefs(preferences);
  }, [preferences]);

  const logSearch = useCallback((from: string, to: string, date: string, busType?: string) => {
    setPreferences(prev => {
      const updated = { ...prev, totalSearches: prev.totalSearches + 1 };
      const routes = [...updated.frequentRoutes];
      const existing = routes.find(
        r => r.from.toLowerCase() === from.toLowerCase() && r.to.toLowerCase() === to.toLowerCase()
      );

      const dayOfWeek = date ? DAY_NAMES[new Date(date.split('-').reverse().join('-')).getDay()] || null : null;

      if (existing) {
        existing.frequency += 1;
        existing.lastSearched = new Date().toISOString();
        if (dayOfWeek) existing.preferredDay = dayOfWeek;
        if (busType) existing.preferredType = busType;
      } else {
        routes.push({
          from: from.trim().replace(/^\w/, c => c.toUpperCase()),
          to: to.trim().replace(/^\w/, c => c.toUpperCase()),
          frequency: 1,
          preferredDay: dayOfWeek,
          preferredTime: null,
          preferredType: busType || null,
          avgSpend: 0,
          lastSearched: new Date().toISOString(),
        });
      }

      updated.frequentRoutes = routes.sort((a, b) => b.frequency - a.frequency);
      return updated;
    });
  }, []);

  const logBooking = useCallback((from: string, to: string, operator: string, price: number, seat?: string) => {
    setPreferences(prev => {
      const updated = {
        ...prev,
        totalBookings: prev.totalBookings + 1,
        lastBooking: new Date().toISOString(),
      };

      // Update preferred operators
      const ops = [...updated.preferredOperators];
      if (!ops.includes(operator)) {
        ops.push(operator);
      }
      updated.preferredOperators = ops;

      // Update seat preference
      if (seat) updated.preferredSeat = seat;

      // Update avg spend for route
      const routes = [...updated.frequentRoutes];
      const route = routes.find(
        r => r.from.toLowerCase() === from.toLowerCase() && r.to.toLowerCase() === to.toLowerCase()
      );
      if (route) {
        const totalSpent = route.avgSpend * (route.frequency - 1) + price;
        route.avgSpend = Math.round(totalSpent / route.frequency);
      }
      updated.frequentRoutes = routes;

      return updated;
    });
  }, []);

  const getTopRoutes = useCallback((limit = 3): FrequentRoute[] => {
    return preferences.frequentRoutes.slice(0, limit);
  }, [preferences.frequentRoutes]);

  const getMostFrequentRoute = useCallback((): FrequentRoute | null => {
    return preferences.frequentRoutes.length > 0 ? preferences.frequentRoutes[0] : null;
  }, [preferences.frequentRoutes]);

  const getPersonalizedGreeting = useCallback((userName: string): string | null => {
    const topRoute = getMostFrequentRoute();
    if (!topRoute || topRoute.frequency < 2) return null;

    let greeting = `Welcome back, ${userName}! 🚌\n\n`;
    greeting += `🔁 Based on your travel history:\n`;
    greeting += `You usually travel **${topRoute.from} → ${topRoute.to}**`;
    if (topRoute.preferredDay) greeting += ` on **${topRoute.preferredDay}s**`;
    if (topRoute.preferredType) greeting += ` via **${topRoute.preferredType}**`;
    greeting += `.\n\n`;
    if (topRoute.avgSpend > 0) {
      greeting += `📅 Shall I book your usual trip? (₹${topRoute.avgSpend} approx.)`;
    } else {
      greeting += `📅 Shall I search for your usual route?`;
    }
    return greeting;
  }, [getMostFrequentRoute]);

  const clearPreferences = useCallback(() => {
    setPreferences(getDefaultPrefs());
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    preferences,
    logSearch,
    logBooking,
    getTopRoutes,
    getMostFrequentRoute,
    getPersonalizedGreeting,
    clearPreferences,
  };
}
