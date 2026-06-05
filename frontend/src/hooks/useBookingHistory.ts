import { useState, useCallback, useEffect } from 'react';

export interface Booking {
  id: string;
  operator: string;
  busType: string;
  from: string;
  to: string;
  date: string;
  departureTime: string;
  arrivalTime: string;
  duration: string;
  seatNumbers: string[];
  price: number;
  totalAmount: number;
  status: 'confirmed' | 'cancelled' | 'completed';
  bookingUrl: string;
  createdAt: string;
  passengerName?: string;
  passengerPhone?: string;
  passengerEmail?: string;
}

export interface MonthlyStats {
  month: string;
  totalTrips: number;
  totalSpent: number;
  mostTakenRoute: string;
}

const STORAGE_KEY = 'travel_ai_bookings';

function generateBookingId(): string {
  const year = new Date().getFullYear();
  const seq = Math.floor(Math.random() * 900) + 100;
  return `BUS-${year}-${seq}`;
}

function loadBookings(): Booking[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Error loading bookings', e);
  }
  return [];
}

function saveBookings(bookings: Booking[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookings));
}

export function useBookingHistory() {
  const [bookings, setBookings] = useState<Booking[]>(loadBookings);

  useEffect(() => {
    saveBookings(bookings);
  }, [bookings]);

  const addBooking = useCallback((
    ticket: {
      operator: string;
      type?: string;
      departure?: string;
      arrival?: string;
      duration?: string;
      price?: string;
      booking_url?: string;
    },
    from: string,
    to: string,
    date: string,
    selectedSeats: string[],
    totalAmount: number,
  ): Booking => {
    const priceNum = parseInt((ticket.price || '0').replace(/[^\d]/g, ''), 10);
    const newBooking: Booking = {
      id: generateBookingId(),
      operator: ticket.operator || 'Unknown',
      busType: ticket.type || 'Standard',
      from,
      to,
      date,
      departureTime: ticket.departure || '--',
      arrivalTime: ticket.arrival || '--',
      duration: ticket.duration || '--',
      seatNumbers: selectedSeats,
      price: priceNum,
      totalAmount,
      status: 'confirmed',
      bookingUrl: ticket.booking_url || '',
      createdAt: new Date().toISOString(),
    };

    setBookings(prev => [newBooking, ...prev]);
    return newBooking;
  }, []);

  const cancelBooking = useCallback((bookingId: string) => {
    setBookings(prev =>
      prev.map(b => b.id === bookingId ? { ...b, status: 'cancelled' as const } : b)
    );
  }, []);

  const completeBooking = useCallback((bookingId: string) => {
    setBookings(prev =>
      prev.map(b => b.id === bookingId ? { ...b, status: 'completed' as const } : b)
    );
  }, []);

  const getUpcoming = useCallback((): Booking[] => {
    return bookings.filter(b => b.status === 'confirmed');
  }, [bookings]);

  const getPast = useCallback((): Booking[] => {
    return bookings.filter(b => b.status === 'completed' || b.status === 'cancelled');
  }, [bookings]);

  const getMonthlyStats = useCallback((): MonthlyStats => {
    const now = new Date();
    const monthStr = now.toLocaleString('en-US', { month: 'long', year: 'numeric' });
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

    const thisMonth = bookings.filter(b => {
      const created = new Date(b.createdAt);
      return created >= monthStart && b.status !== 'cancelled';
    });

    // Find most taken route
    const routeCounts: Record<string, number> = {};
    thisMonth.forEach(b => {
      const route = `${b.from} → ${b.to}`;
      routeCounts[route] = (routeCounts[route] || 0) + 1;
    });
    const mostTaken = Object.entries(routeCounts).sort((a, b) => b[1] - a[1])[0];

    return {
      month: monthStr,
      totalTrips: thisMonth.length,
      totalSpent: thisMonth.reduce((sum, b) => sum + b.totalAmount, 0),
      mostTakenRoute: mostTaken ? mostTaken[0] : 'N/A',
    };
  }, [bookings]);

  const getBookingById = useCallback((id: string): Booking | undefined => {
    return bookings.find(b => b.id === id);
  }, [bookings]);

  const clearBookings = useCallback(() => {
    setBookings([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    bookings,
    addBooking,
    cancelBooking,
    completeBooking,
    getUpcoming,
    getPast,
    getMonthlyStats,
    getBookingById,
    clearBookings,
  };
}
