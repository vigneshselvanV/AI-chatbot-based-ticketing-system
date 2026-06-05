import React from 'react';
import { Bus, Calendar, Clock, MapPin, ArrowRight, X as XIcon } from 'lucide-react';
import type { Booking, MonthlyStats } from '../hooks/useBookingHistory';
interface BookingHistoryProps {
  upcoming: Booking[];
  past: Booking[];
  monthlyStats: MonthlyStats;
  onCancel: (bookingId: string) => void;
  onRebook: (booking: Booking) => void;
  onRate: (booking: Booking) => void;
  hasReviewed: (bookingId: string) => boolean;
  onClose: () => void;
}

export const BookingHistory: React.FC<BookingHistoryProps> = ({
  upcoming,
  past,
  monthlyStats,
  onCancel,
  onRebook,
  onRate,
  hasReviewed,
  onClose,
}) => {
  return (
    <div className="booking-dashboard">
      <div className="bd-header">
        <h2>📋 Your Booking History</h2>
        <button className="bd-close" onClick={onClose}>
          <XIcon size={20} />
        </button>
      </div>

      {/* Monthly Stats */}
      {monthlyStats.totalTrips > 0 && (
        <div className="bd-stats">
          <h4>💰 Monthly Summary — {monthlyStats.month}</h4>
          <div className="bd-stats-grid">
            <div className="bd-stat-item">
              <span className="bd-stat-value">{monthlyStats.totalTrips}</span>
              <span className="bd-stat-label">Total Trips</span>
            </div>
            <div className="bd-stat-item">
              <span className="bd-stat-value">₹{monthlyStats.totalSpent.toLocaleString('en-IN')}</span>
              <span className="bd-stat-label">Total Spent</span>
            </div>
            <div className="bd-stat-item bd-stat-wide">
              <span className="bd-stat-value bd-stat-route">{monthlyStats.mostTakenRoute}</span>
              <span className="bd-stat-label">Most Taken</span>
            </div>
          </div>
        </div>
      )}

      {/* Upcoming Trips */}
      <div className="bd-section">
        <h3 className="bd-section-title">📅 Upcoming Trips ({upcoming.length})</h3>
        {upcoming.length === 0 ? (
          <div className="bd-empty">No upcoming trips. Search for a bus to get started! 🚌</div>
        ) : (
          <div className="bd-cards">
            {upcoming.map(booking => (
              <div key={booking.id} className="booking-card booking-confirmed">
                <div className="bc-header">
                  <span className="bc-id">🎫 {booking.id}</span>
                  <span className="bc-status bc-status-confirmed">✅ CONFIRMED</span>
                </div>
                <div className="bc-operator">
                  <Bus size={14} />
                  <span>{booking.operator}</span>
                  <span className="bc-type">{booking.busType}</span>
                </div>
                <div className="bc-route">
                  <MapPin size={14} />
                  <span>{booking.from}</span>
                  <ArrowRight size={12} />
                  <span>{booking.to}</span>
                </div>
                <div className="bc-details">
                  <span><Calendar size={12} /> {booking.date}</span>
                  <span><Clock size={12} /> {booking.departureTime}</span>
                  <span>💺 Seat: {booking.seatNumbers.join(', ') || 'N/A'}</span>
                  <span className="bc-price">💰 ₹{booking.totalAmount.toLocaleString('en-IN')}</span>
                </div>
                <div className="bc-actions">
                  <button className="bc-action-btn bc-view" onClick={() => {
                    if (booking.bookingUrl) window.open(booking.bookingUrl, '_blank');
                  }}>
                    📄 View Ticket
                  </button>
                  <button className="bc-action-btn bc-cancel" onClick={() => onCancel(booking.id)}>
                    ❌ Cancel
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Past Trips */}
      <div className="bd-section">
        <h3 className="bd-section-title">🕐 Past Trips ({past.length})</h3>
        {past.length === 0 ? (
          <div className="bd-empty">No past trips yet.</div>
        ) : (
          <div className="bd-cards">
            {past.map(booking => (
              <div key={booking.id} className={`booking-card ${booking.status === 'cancelled' ? 'booking-cancelled' : 'booking-completed'}`}>
                <div className="bc-header">
                  <span className="bc-id">🎫 {booking.id}</span>
                  <span className={`bc-status ${booking.status === 'cancelled' ? 'bc-status-cancelled' : 'bc-status-completed'}`}>
                    {booking.status === 'cancelled' ? '❌ CANCELLED' : '✅ COMPLETED'}
                  </span>
                </div>
                <div className="bc-operator">
                  <Bus size={14} />
                  <span>{booking.operator}</span>
                  <span className="bc-type">{booking.busType}</span>
                </div>
                <div className="bc-route">
                  <MapPin size={14} />
                  <span>{booking.from}</span>
                  <ArrowRight size={12} />
                  <span>{booking.to}</span>
                </div>
                <div className="bc-details">
                  <span><Calendar size={12} /> {booking.date}</span>
                  <span><Clock size={12} /> {booking.departureTime}</span>
                  <span>💺 Seat: {booking.seatNumbers.join(', ') || 'N/A'}</span>
                  <span className="bc-price">💰 ₹{booking.totalAmount.toLocaleString('en-IN')}</span>
                </div>
                <div className="bc-actions">
                  {booking.status !== 'cancelled' && (
                    <>
                      <button className="bc-action-btn bc-rebook" onClick={() => onRebook(booking)}>
                        🔁 Rebook
                      </button>
                      {!hasReviewed(booking.id) && (
                        <button className="bc-action-btn bc-rate" onClick={() => onRate(booking)}>
                          ⭐ Rate Trip
                        </button>
                      )}
                      {hasReviewed(booking.id) && (
                        <span className="bc-reviewed">⭐ Reviewed</span>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
