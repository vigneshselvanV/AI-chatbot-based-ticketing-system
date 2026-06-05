import { useState, useMemo } from 'react';
import {
  Star, ExternalLink, Utensils, Building2,
  Calendar, Lightbulb, Map, ChevronDown, ChevronUp
} from 'lucide-react';
import InteractiveMap from './InteractiveMap';
import TouristSpotsList from './TouristSpotsList';
import { getPlacesForCity } from '../data/touristPlaces';
import type { TouristPlace } from '../data/touristPlaces';

// Re-export PlaceItem as alias for backward compatibility
export type PlaceItem = TouristPlace;

// ── Data types ──
export interface TravelGuideData {
  destination: string;
  tagline: string;
  best_time_to_visit: string;
  ideal_duration: string;
  budget_summary: {
    budget_per_day: string;
    midrange_per_day: string;
    luxury_per_day: string;
  };
  must_visit_places: PlaceItem[];
  hotels: Array<{
    name: string;
    category: string;
    price_per_night: string;
    rating: number;
    amenities: string[];
    maps_query: string;
    booking_tip: string;
  }>;
  food: Array<{
    name: string;
    type: string;
    avg_meal_cost: string;
    must_try: string[];
    maps_query: string;
  }>;
  day_plan: Array<{
    day: number;
    title: string;
    schedule: Array<{
      time: string;
      activity: string;
      cost: string;
      duration: string;
    }>;
    total_cost_estimate: string;
  }>;
  total_trip_estimate: {
    '2_days_budget': string;
    '2_days_midrange': string;
    '2_days_luxury': string;
    includes: string;
    excludes: string;
  };
  travel_tips: string[];
  google_maps_places: Array<{ name: string; query: string }>;
}

interface TravelGuidePanelProps {
  destination: string;
  data: TravelGuideData | null;
  isLoading: boolean;
}

// ── Helpers ──
function getPlaceMapLink(q: string) {
  return `https://www.google.com/maps/search/${encodeURIComponent(q)}`;
}
function getDayRouteUrl(dest: string, places: string[]) {
  if (places.length < 2) return `https://www.google.com/maps/search/tourist+places+in+${encodeURIComponent(dest)}`;
  return `https://www.google.com/maps/dir/${places.map(encodeURIComponent).join('/')}`;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
      {[1,2,3,4,5].map(i => (
        <Star key={i} size={12} fill={i <= Math.round(rating) ? '#f59e0b' : 'none'} color={i <= Math.round(rating) ? '#f59e0b' : '#4b5563'} />
      ))}
      <span style={{ fontSize: '12px', color: '#9ca3af', marginLeft: '4px' }}>{rating?.toFixed(1)}</span>
    </div>
  );
}

// ══════════════════════════════════════════════════════
//  MAIN PANEL
// ══════════════════════════════════════════════════════
export function TravelGuidePanel({ destination, data, isLoading }: TravelGuidePanelProps) {
  const [openDay, setOpenDay]             = useState<number | null>(0);
  const [selectedPlace, setSelectedPlace] = useState<TouristPlace | null>(null);

  // ── Always use REAL verified places from our database ──
  // Fall back to AI places only if database has no entry (very rare)
  const realPlaces = useMemo(() => {
    const dbPlaces = getPlacesForCity(destination || data?.destination || '');
    // If DB returned real places (not the Chennai default for an unknown city)
    // use them; else try AI places as last resort
    return dbPlaces.length > 0 ? dbPlaces : (data?.must_visit_places || []);
  }, [destination, data?.destination, data?.must_visit_places]);

  const handlePlaceSelect = (place: TouristPlace) => {
    setSelectedPlace(prev => prev?.name === place.name ? null : place);
  };

  // ── Loading state ──
  if (isLoading) {
    return (
      <div className="travel-guide-panel">
        <div className="guide-loading">
          <div className="guide-loading-spinner" />
          <p>Generating travel guide for <strong>{destination}</strong>...</p>
          <p className="guide-loading-sub">Fetching places, hotels, food & day plans 🗺️</p>
        </div>
      </div>
    );
  }
  if (!data) return null;

  return (
    <div className="travel-guide-panel">

      {/* ── Guide Header ── */}
      <div className="guide-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div className="guide-dest-icon">📍</div>
          <div>
            <div className="guide-title">{data.destination.toUpperCase()} TRAVEL GUIDE</div>
            <div className="guide-tagline">"{data.tagline}"</div>
          </div>
        </div>
        <div className="guide-meta">
          <span>🗓️ Best: {data.best_time_to_visit}</span>
          <span>⏱️ {data.ideal_duration}</span>
        </div>
      </div>

      {/* ── Budget Card ── */}
      <div className="budget-card">
        <div className="budget-title">💰 ESTIMATED TOTAL TRIP BUDGET</div>
        <div className="budget-row">
          <span className="budget-label">🎒 Budget</span>
          <span className="budget-value">{data.budget_summary.budget_per_day} /day</span>
        </div>
        <div className="budget-row">
          <span className="budget-label">⭐ Mid-range</span>
          <span className="budget-value">{data.budget_summary.midrange_per_day} /day</span>
        </div>
        <div className="budget-row">
          <span className="budget-label">✨ Luxury</span>
          <span className="budget-value">{data.budget_summary.luxury_per_day} /day</span>
        </div>
        {data.total_trip_estimate && (
          <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: '11px', color: '#86efac', fontWeight: 700, marginBottom: '6px' }}>2-DAY TOTAL ESTIMATE</div>
            <div className="budget-row">
              <span className="budget-label">Budget trip</span>
              <span className="budget-value">{data.total_trip_estimate['2_days_budget']}</span>
            </div>
            <div className="budget-row">
              <span className="budget-label">Mid-range</span>
              <span className="budget-value">{data.total_trip_estimate['2_days_midrange']}</span>
            </div>
            <div className="budget-row">
              <span className="budget-label">Luxury</span>
              <span className="budget-value">{data.total_trip_estimate['2_days_luxury']}</span>
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '6px' }}>
              ✅ Includes: {data.total_trip_estimate.includes}
            </div>
          </div>
        )}
      </div>

      {/* ════════════════════════════════════════════
           INTERACTIVE MAP SECTION
          ════════════════════════════════════════════ */}
      <div className="map-section-header">
        <div>
          <span className="guide-section-title" style={{ border: 'none', paddingBottom: 0, marginBottom: 0 }}>
            <Map size={16} /> EXPLORE ON MAPS
          </span>
        </div>
        {data.must_visit_places?.length > 0 && (
          <span className="map-hint">👆 Click any spot to zoom the map</span>
        )}
      </div>

      {/* Side-by-side: spots list LEFT, map RIGHT */}
      <div className="map-spots-container">

        {/* LEFT — Real tourist spots list */}
        <TouristSpotsList
          places={realPlaces as any}
          selectedPlace={selectedPlace as any}
          onPlaceSelect={handlePlaceSelect as any}
          destination={data.destination}
        />

        {/* RIGHT — Leaflet map with real GPS markers */}
        <InteractiveMap
          destination={data.destination}
          places={realPlaces}
          selectedPlace={selectedPlace}
          onPlaceSelect={handlePlaceSelect}
        />
      </div>

      {/* ── Where To Stay ── */}
      {data.hotels?.length > 0 && (
        <div className="guide-section">
          <div className="guide-section-title"><Building2 size={16} /> WHERE TO STAY</div>
          <div className="hotels-grid">
            {data.hotels.map((hotel, idx) => (
              <div key={idx} className="hotel-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <div className="hotel-name">{hotel.name}</div>
                    <span className={`hotel-category hotel-cat-${hotel.category?.toLowerCase().replace(/[^a-z]/g, '')}`}>
                      {hotel.category}
                    </span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="hotel-price">{hotel.price_per_night}</div>
                    <div style={{ fontSize: '10px', color: '#6b7280' }}>per night</div>
                  </div>
                </div>
                <StarRating rating={hotel.rating} />
                <div className="hotel-amenities">
                  {hotel.amenities?.map((a, i) => <span key={i} className="amenity-tag">{a}</span>)}
                </div>
                {hotel.booking_tip && <div className="place-tip" style={{ marginTop: '8px' }}>💡 {hotel.booking_tip}</div>}
                <a href={getPlaceMapLink(hotel.maps_query)} target="_blank" rel="noopener noreferrer" className="maps-btn" style={{ marginTop: '8px' }}>
                  <ExternalLink size={12} /> Find on Maps
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Food & Dining ── */}
      {data.food?.length > 0 && (
        <div className="guide-section">
          <div className="guide-section-title"><Utensils size={16} /> FOOD & DINING</div>
          <div className="food-grid">
            {data.food.map((spot, idx) => (
              <div key={idx} className="food-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div>
                    <div className="food-name">{spot.name}</div>
                    <div className="food-type">{spot.type}</div>
                  </div>
                  <div className="food-cost">{spot.avg_meal_cost}</div>
                </div>
                {spot.must_try?.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '8px' }}>
                    {spot.must_try.map((dish, i) => <span key={i} className="must-try-tag">🍽️ {dish}</span>)}
                  </div>
                )}
                <a href={getPlaceMapLink(spot.maps_query)} target="_blank" rel="noopener noreferrer" className="maps-btn">
                  <ExternalLink size={12} /> Find on Maps
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Day Plan ── */}
      {data.day_plan?.length > 0 && (
        <div className="guide-section">
          <div className="guide-section-title"><Calendar size={16} /> VISIT PLAN</div>
          {data.day_plan.map((day, dayIdx) => {
            const dayPlaces = day.schedule.map(s => `${s.activity} ${destination}`);
            return (
              <div key={dayIdx} className="day-plan-block">
                <div className="day-header" onClick={() => setOpenDay(openDay === dayIdx ? null : dayIdx)} style={{ cursor: 'pointer' }}>
                  <div>
                    <span className="day-badge">Day {day.day}</span>
                    <span className="day-title">{day.title}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="day-cost">{day.total_cost_estimate}</span>
                    {openDay === dayIdx ? <ChevronUp size={16} color="#6b7280" /> : <ChevronDown size={16} color="#6b7280" />}
                  </div>
                </div>
                {openDay === dayIdx && (
                  <div className="day-timeline">
                    {day.schedule.map((item, iIdx) => (
                      <div key={iIdx} className="timeline-item">
                        <div className="timeline-time">{item.time}</div>
                        <div className="timeline-connector">
                          <div className="timeline-dot" />
                          {iIdx < day.schedule.length - 1 && <div className="timeline-line-v" />}
                        </div>
                        <div className="timeline-content">
                          <div className="timeline-activity">{item.activity}</div>
                          <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                            <span className="timeline-cost">💰 {item.cost}</span>
                            <span className="timeline-duration">⏱️ {item.duration}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    <a
                      href={getDayRouteUrl(destination, dayPlaces)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="maps-btn full-width-btn"
                      style={{ display: 'flex', justifyContent: 'center', marginTop: '12px' }}
                    >
                      <Map size={14} /> 🗺️ View Day {day.day} Route on Maps
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Travel Tips ── */}
      {data.travel_tips?.length > 0 && (
        <div className="guide-section">
          <div className="guide-section-title"><Lightbulb size={16} /> TRAVEL TIPS</div>
          <div className="tips-list">
            {data.travel_tips.map((tip, idx) => (
              <div key={idx} className="tip-item">
                <span className="tip-icon">💡</span>
                <span className="tip-text">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ height: '24px' }} />
    </div>
  );
}
