import React from 'react';
import { Bus, Clock, ArrowRight } from 'lucide-react';

interface LegData {
  operator: string;
  type: string;
  departure: string;
  arrival: string;
  duration: string;
  price: string;
  seats: string;
  booking_url?: string;
}

interface ConnectingRouteProps {
  source: string;
  intermediate: string;
  destination: string;
  leg1: LegData;
  leg2: LegData;
  totalDuration: string;
  totalCost: string;
  onBookBoth: () => void;
}

export const ConnectingRoute: React.FC<ConnectingRouteProps> = ({
  source,
  intermediate,
  destination,
  leg1,
  leg2,
  totalDuration,
  totalCost,
  onBookBoth,
}) => {
  return (
    <div className="connecting-route-card">
      {/* Header Warning */}
      <div className="cr-header">
        <div className="cr-warning">
          <span className="cr-warning-icon">⚠️</span>
          <span>No direct bus available for this route</span>
        </div>
        <h3 className="cr-title">
          <span className="cr-brain">🧠</span> Smart Route Suggestion
        </h3>
      </div>

      {/* Route Visual */}
      <div className="cr-route-visual">
        <div className="cr-stop">
          <div className="cr-dot cr-dot-start"></div>
          <span className="cr-stop-name">{source}</span>
        </div>
        <div className="cr-connector">
          <div className="cr-line"></div>
          <ArrowRight size={14} className="cr-arrow" />
        </div>
        <div className="cr-stop">
          <div className="cr-dot cr-dot-mid"></div>
          <span className="cr-stop-name cr-stop-mid">{intermediate}</span>
          <span className="cr-transfer-badge">🔄 Transfer</span>
        </div>
        <div className="cr-connector">
          <div className="cr-line"></div>
          <ArrowRight size={14} className="cr-arrow" />
        </div>
        <div className="cr-stop">
          <div className="cr-dot cr-dot-end"></div>
          <span className="cr-stop-name">{destination}</span>
        </div>
      </div>

      {/* Leg 1 */}
      <div className="cr-leg">
        <div className="cr-leg-header">
          <span className="cr-leg-label">Leg 1</span>
          <span className="cr-leg-route">{source} → {intermediate}</span>
        </div>
        <div className="cr-leg-details">
          <div className="cr-leg-operator">
            <Bus size={14} />
            <span>{leg1.operator}</span>
            <span className="cr-leg-type">{leg1.type}</span>
          </div>
          <div className="cr-leg-info">
            <span><Clock size={12} /> {leg1.departure} → {leg1.arrival}</span>
            <span className="cr-leg-duration">{leg1.duration}</span>
            <span className="cr-leg-price">{leg1.price}</span>
          </div>
          {leg1.seats && leg1.seats !== '--' && (
            <span className="cr-leg-seats">💺 {leg1.seats}</span>
          )}
        </div>
      </div>

      {/* Leg 2 */}
      <div className="cr-leg">
        <div className="cr-leg-header">
          <span className="cr-leg-label">Leg 2</span>
          <span className="cr-leg-route">{intermediate} → {destination}</span>
        </div>
        <div className="cr-leg-details">
          <div className="cr-leg-operator">
            <Bus size={14} />
            <span>{leg2.operator}</span>
            <span className="cr-leg-type">{leg2.type}</span>
          </div>
          <div className="cr-leg-info">
            <span><Clock size={12} /> {leg2.departure} → {leg2.arrival}</span>
            <span className="cr-leg-duration">{leg2.duration}</span>
            <span className="cr-leg-price">{leg2.price}</span>
          </div>
          {leg2.seats && leg2.seats !== '--' && (
            <span className="cr-leg-seats">💺 {leg2.seats}</span>
          )}
        </div>
      </div>

      {/* Total Summary */}
      <div className="cr-summary">
        <div className="cr-summary-item">
          <Clock size={14} />
          <span>Total Duration: <strong>{totalDuration}</strong></span>
        </div>
        <div className="cr-summary-item">
          <span>💰 Total Cost: <strong className="cr-total-price">{totalCost}</strong></span>
        </div>
      </div>

      {/* Book Button */}
      <button className="cr-book-btn" onClick={onBookBoth}>
        ✅ Book Both Legs Together
      </button>
    </div>
  );
};
