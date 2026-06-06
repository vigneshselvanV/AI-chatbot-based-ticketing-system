import React from 'react';
import type { OperatorRating } from '../hooks/useReviews';
import { getOperatorDisplay } from '../utils/operatorLogos';

interface TicketCardProps {
  ticket: any;
  intentSource: string;
  intentDest: string;
  isExpanded: boolean;
  onToggleExpand: () => void;
  isSaved: boolean;
  onToggleSave: () => void;
  operatorRating?: OperatorRating;
  onBook?: (selectedSeats: string[], totalAmount: number) => void;
  activeFilter?: string | null;
  cardIndex?: number;
}

const OperatorLogo: React.FC<{ name: string }> = ({ name }) => {
  const display = getOperatorDisplay(name);
  if (display.type === 'logo') {
    return (
      <img
        src={display.url}
        alt={name}
        className="operator-logo"
        onError={(e: any) => {
          e.target.style.display = 'none';
          if (e.target.nextSibling) {
            e.target.nextSibling.style.display = 'flex';
          }
        }}
      />
    );
  }
  return (
    <div
      className="operator-avatar"
      style={{ backgroundColor: display.color }}
    >
      {display.text}
    </div>
  );
};

export const TicketCard: React.FC<TicketCardProps> = ({ 
  ticket, 
  intentSource, 
  intentDest,
  activeFilter,
  cardIndex
}) => {
  const getRedbusUrl = (from: string, to: string, date: string) => {
    if (ticket.booking_url) return ticket.booking_url;
    const fromSlug = (from || '').toLowerCase().replace(/ /g, '-');
    const toSlug = (to || '').toLowerCase().replace(/ /g, '-');
    
    let formattedDate = date || '04-Jun-2026';
    if (date && date.includes('-')) {
      const parts = date.split('-');
      if (parts.length === 3) {
        const monthMap: Record<string, string> = {
          '01': 'Jan', '1': 'Jan', '02': 'Feb', '2': 'Feb', '03': 'Mar', '3': 'Mar',
          '04': 'Apr', '4': 'Apr', '05': 'May', '5': 'May', '06': 'Jun', '6': 'Jun',
          '07': 'Jul', '7': 'Jul', '08': 'Aug', '8': 'Aug', '09': 'Sep', '9': 'Sep',
          '10': 'Oct', '11': 'Nov', '12': 'Dec'
        };
        formattedDate = `${parts[0]}-${monthMap[parts[1]] || 'Jun'}-${parts[2]}`;
      }
    }

    return `https://www.redbus.in/bus-tickets/${fromSlug}-to-${toSlug}?doj=${formattedDate}`;
  };

  const amenitiesList: string[] = [];
  if (ticket.amenities?.ac) amenitiesList.push("A/C");
  if (ticket.amenities?.sleeper) amenitiesList.push("Sleeper");
  if (ticket.amenities?.wifi) amenitiesList.push("WiFi");
  if (ticket.amenities?.charging) amenitiesList.push("Charging");
  if (ticket.amenities?.live_tracking) amenitiesList.push("Live Tracking");
  if (ticket.amenities && Array.isArray(ticket.amenities)) {
    amenitiesList.push(...ticket.amenities.filter((a: string) => !amenitiesList.includes(a)));
  }
  if (amenitiesList.length === 0) amenitiesList.push("Standard");

  // Format price if it's not a number
  const formattedPrice = ticket.price?.toString().replace(/\D/g, '') || '0';

  return (
    <div className="bus-card">
      {cardIndex === 0 && activeFilter === 'cheapest' && (
        <div className="cheapest-badge">🏆 CHEAPEST</div>
      )}
      {cardIndex === 0 && activeFilter === 'ac' && (
        <div className="best-match-badge">❄️ BEST AC BUS</div>
      )}
      {cardIndex === 0 && activeFilter === 'sleeper' && (
        <div className="best-match-badge">🛏️ BEST SLEEPER</div>
      )}
      {cardIndex === 0 && activeFilter === 'fastest' && (
        <div className="best-match-badge">⚡ FASTEST</div>
      )}
      {cardIndex === 0 && activeFilter === 'night' && (
        <div className="best-match-badge">🌙 FIRST NIGHT BUS</div>
      )}
      
      <div className="bus-card-header">
        <div className="operator-left">
          <OperatorLogo name={ticket.operator || 'Unknown Operator'} />
          <div className="operator-details">
            <h4 className="operator-name">
              {ticket.operator || 'Unknown Operator'}
            </h4>
            <span className="bus-type">{ticket.bus_type || ticket.type || 'Standard Bus'}</span>
          </div>
        </div>
        <div className="price-right">
          {ticket.rating > 0 && (
            <div className="rating-badge">
              ⭐ {ticket.rating.toFixed(1)}
            </div>
          )}
          <div className="price-amount">
            ₹{parseInt(formattedPrice).toLocaleString('en-IN') || 'N/A'}
          </div>
          <div className="price-label">per person</div>
        </div>
      </div>

      {amenitiesList.length > 0 && (
        <div className="amenities-row">
          {amenitiesList.slice(0, 4).map((a, i) => (
            <span key={i} className="amenity-chip">{a}</span>
          ))}
        </div>
      )}

      <div className="journey-timeline">
        <div className="time-block">
          <span className="time-value">{ticket.departure || '--:--'}</span>
          <span className="stop-name">
            {ticket.boarding_point || 'Main Boarding'}
          </span>
        </div>
        <div className="duration-center">
          <span className="duration-text">{ticket.duration || '--'}</span>
          <div className="timeline-bar">
            <div className="dot dot-start"></div>
            <div className="line"></div>
            <div className="dot dot-end"></div>
          </div>
        </div>
        <div className="time-block right">
          <span className="time-value">
            {ticket.arrival || '--:--'}
            {ticket.arrival_next_day &&
              <sup className="next-day">+1</sup>
            }
          </span>
          <span className="stop-name">
            {ticket.dropping_point || 'Main Dropping'}
          </span>
        </div>
      </div>

      <div className="bus-card-footer">
        <div className="footer-badges">
          {ticket.seats_available > 0 ? (
            <span className={`seats-badge ${
              ticket.seats_available <= 5 ? 'urgent' : ''
            }`}>
              🪑 {ticket.seats_available} seats left
            </span>
          ) : (
            <span className="seats-badge full">
              ❌ Sold Out
            </span>
          )}
          {(ticket.cancellation !== false) && (
            <span className="cancel-badge">
              ✅ Free Cancellation
            </span>
          )}
          {ticket.live_tracking && (
            <span className="tracking-badge">
              📍 Live Tracking
            </span>
          )}
        </div>
      </div>

      <a
        href={ticket.booking_url || getRedbusUrl(intentSource, intentDest, ticket.date)}
        target="_blank"
        rel="noopener noreferrer"
        className="book-now-btn"
      >
        🔗 Book on {ticket.source ? ticket.source.charAt(0).toUpperCase() + ticket.source.slice(1) : 'RedBus'}
      </a>
    </div>
  );
};

