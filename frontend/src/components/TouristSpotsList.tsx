// @ts-ignore
import type { PlaceItem } from './InteractiveMap';

const TYPE_ICONS: Record<string, string> = {
  'Religious': '🛕',
  'Temple': '🛕',
  'Beach': '🏖️',
  'Landmark': '🏛️',
  'Museum': '🏛️',
  'Nature': '🌿',
  'Park': '🌳',
  'Historical': '🏰',
  'Shopping': '🛍️',
  'Food': '🍽️',
  'Adventure': '⛰️',
  'Waterfall': '💧',
  'Fort': '🏰',
  'Palace': '👑',
  'Hill': '⛰️',
  'Island': '🏝️',
  'Pilgrimage': '🛕',
  'Scenic': '🌄',
  'Coastal': '🌊',
  'Bridge': '🌉',
  'default': '📍',
};

const PLACE_COLORS = [
  '#6366f1', '#ef4444', '#f97316', '#22c55e',
  '#06b6d4', '#a855f7', '#ec4899', '#eab308',
  '#14b8a6', '#f43f5e',
];

interface TouristSpotsListProps {
  places: PlaceItem[];
  selectedPlace: PlaceItem | null;
  onPlaceSelect: (place: PlaceItem) => void;
  destination: string;
}

export default function TouristSpotsList({ places, selectedPlace, onPlaceSelect, destination }: TouristSpotsListProps) {
  const allMapsUrl = `https://www.google.com/maps/search/tourist+places+in+${encodeURIComponent(destination)}`;

  return (
    <div className="spots-list-container">
      {/* ── Header ── */}
      <div className="spots-list-header">
        <h3 className="spots-title">
          📍 Tourist Spots
          <span className="spots-count">{places?.length || 0}</span>
        </h3>
        <p className="spots-subtitle">👆 Click any place to zoom the map</p>
      </div>

      {/* ── Scrollable list ── */}
      <div className="spots-scroll">
        {places?.map((place, index) => {
          const isSelected = selectedPlace?.name === place.name;
          const color = PLACE_COLORS[index % PLACE_COLORS.length];
          const icon = TYPE_ICONS[place.type] ?? TYPE_ICONS['default'];

          return (
            <div
              key={index}
              id={`spot-card-${index}`}
              className={`spot-card ${isSelected ? 'spot-card-active' : ''}`}
              style={isSelected ? {
                borderColor: color,
                boxShadow: `0 0 0 1px ${color}44, 0 4px 24px ${color}22`,
              } : {}}
              onClick={() => onPlaceSelect(place)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onPlaceSelect(place)}
            >
              {/* Number badge */}
              <div className="spot-left">
                <div className="spot-number" style={{ background: color }}>
                  {isSelected ? '✓' : index + 1}
                </div>
              </div>

              {/* Details */}
              <div className="spot-content">
                <div className="spot-top-row">
                  <span className="spot-icon">{icon}</span>
                  <span className="spot-name">{place.name}</span>
                  {isSelected && (
                    <span className="spot-active-badge">viewing</span>
                  )}
                </div>

                <div className="spot-type-row">
                  {place.type && <span className="spot-type">{place.type}</span>}
                  {place.distance_from_center && (
                    <span className="spot-distance">📍 {place.distance_from_center}</span>
                  )}
                </div>

                <div className="spot-meta-row">
                  {place.entry_fee && <span className="spot-fee">🎟️ {place.entry_fee}</span>}
                  {place.duration && <span className="spot-dur">⏱️ {place.duration}</span>}
                </div>

                {/* Expanded tip when selected */}
                {isSelected && place.tips && (
                  <div className="spot-tip-expanded">
                    💡 {place.tips}
                  </div>
                )}

                {/* Description preview when not selected */}
                {!isSelected && place.description && (
                  <div className="spot-desc-preview">{place.description}</div>
                )}
              </div>

              {/* Arrow */}
              <div className="spot-arrow" style={isSelected ? { color } : {}}>
                {isSelected ? '›' : '›'}
              </div>
            </div>
          );
        })}

        {(!places || places.length === 0) && (
          <div style={{ textAlign: 'center', color: '#6b7280', padding: '30px 16px', fontSize: '13px' }}>
            No tourist spots available
          </div>
        )}
      </div>

      {/* ── View all on Maps button ── */}
      <a
        href={allMapsUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="view-all-maps-btn"
      >
        🗺️ View All on Google Maps
      </a>
    </div>
  );
}
