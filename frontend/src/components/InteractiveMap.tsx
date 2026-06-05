import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { TouristPlace } from '../data/touristPlaces';

// ── Fix Leaflet default icon paths (must be inline here too for safety) ──
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow });

// ── Marker colors for up to 10 places ──
const MARKER_COLORS = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4',
  '#6366f1', '#a855f7', '#ec4899', '#14b8a6', '#f43f5e',
];

// ── Create a numbered colored circle icon ──
function createNumberedIcon(number: number, color: string, isActive: boolean): L.DivIcon {
  const size = isActive ? 44 : 34;
  return L.divIcon({
    className: '',
    html: `<div style="
      width:${size}px;height:${size}px;
      background:${color};
      border:${isActive ? 3 : 2}px solid white;
      border-radius:50%;
      display:flex;align-items:center;justify-content:center;
      font-size:${isActive ? 16 : 13}px;
      font-weight:800;color:white;font-family:sans-serif;
      box-shadow:0 3px ${isActive ? 16 : 8}px rgba(0,0,0,${isActive ? 0.6 : 0.4});
      transition:all 0.3s;
      ${isActive ? 'transform:scale(1.15);' : ''}
    ">${number}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -(size / 2 + 4)],
  });
}

// ── Controller: flies map to selected place ──
function MapController({ selectedPlace }: { selectedPlace: TouristPlace | null }) {
  const map = useMap();
  useEffect(() => {
    if (!selectedPlace?.lat || !selectedPlace?.lng) return;
    map.flyTo([Number(selectedPlace.lat), Number(selectedPlace.lng)], 16, { animate: true, duration: 1.2 });
  }, [selectedPlace, map]);
  return null;
}

// ── Props ──
interface InteractiveMapProps {
  destination: string;
  places: TouristPlace[];
  selectedPlace: TouristPlace | null;
  onPlaceSelect: (place: TouristPlace) => void;
}

export default function InteractiveMap({ places, selectedPlace, onPlaceSelect }: InteractiveMapProps) {
  // Determine initial center from first place with coords, fallback to India center
  const center: [number, number] =
    places?.[0]?.lat ? [Number(places[0].lat), Number(places[0].lng)] : [20.5937, 78.9629];

  return (
    <div className="map-wrapper">
      <MapContainer
        center={center}
        zoom={13}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
        scrollWheelZoom={true}
      >
        {/* ── OpenStreetMap tiles — 100% free, no API key ── */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* ── Fly-to controller ── */}
        <MapController selectedPlace={selectedPlace} />

        {/* ── Numbered colored markers ── */}
        {places?.map((place, index) => {
          if (!place.lat || !place.lng) return null;
          const isActive = selectedPlace?.name === place.name;
          const color = MARKER_COLORS[index % MARKER_COLORS.length];

          return (
            <Marker
              key={`${place.name}-${index}`}
              position={[Number(place.lat), Number(place.lng)]}
              icon={createNumberedIcon(index + 1, color, isActive)}
              eventHandlers={{ click: () => onPlaceSelect(place) }}
              zIndexOffset={isActive ? 1000 : 0}
            >
              <Popup className="custom-popup" maxWidth={280} autoPan={true}>
                <div className="popup-content">
                  <div className="popup-header">
                    <span className="popup-num" style={{ background: color }}>{index + 1}</span>
                    <span className="popup-name">{place.name}</span>
                  </div>
                  <span className="popup-type">{place.type}</span>
                  <p className="popup-desc">{place.description}</p>
                  <div className="popup-chips">
                    {place.entry_fee && <span className="popup-chip green">🎟️ {place.entry_fee}</span>}
                    {place.duration && <span className="popup-chip blue">⏱️ {place.duration}</span>}
                    {place.best_time && <span className="popup-chip yellow">🕐 {place.best_time}</span>}
                  </div>
                  {place.tips && <div className="popup-tip">💡 {place.tips}</div>}
                  <a
                    href={`https://www.google.com/maps/search/${encodeURIComponent(place.maps_query || place.name)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="popup-maps-btn"
                  >
                    📍 Open in Google Maps
                  </a>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* ── Selected place bottom overlay bar ── */}
      {selectedPlace && (
        <div className="map-bottom-bar">
          <div className="map-place-info">
            <span className="map-place-name">{selectedPlace.name}</span>
            <div className="map-place-chips">
              {selectedPlace.entry_fee && <span className="map-chip green">🎟️ {selectedPlace.entry_fee}</span>}
              {selectedPlace.duration && <span className="map-chip blue">⏱️ {selectedPlace.duration}</span>}
              {selectedPlace.best_time && <span className="map-chip yellow">🕐 {selectedPlace.best_time}</span>}
            </div>
          </div>
          <a
            href={`https://www.google.com/maps/search/${encodeURIComponent(selectedPlace.maps_query || selectedPlace.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="map-directions-btn"
          >
            📍 Open in Maps
          </a>
        </div>
      )}
    </div>
  );
}
