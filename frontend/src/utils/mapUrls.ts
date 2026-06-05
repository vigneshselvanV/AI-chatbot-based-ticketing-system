// ── Utility: Free Google Maps iframe URLs ──
// No API key. No JS SDK. Just URLs.

export function getPlaceZoomUrl(place: { maps_query?: string; name: string }, destination: string): string {
  const query = place.maps_query || `${place.name} ${destination} India`;
  return `https://maps.google.com/maps?q=${encodeURIComponent(query)}&z=16&output=embed`;
}

export function getOverviewUrl(destination: string, zoom = 13): string {
  return `https://maps.google.com/maps?q=${encodeURIComponent(`tourist places in ${destination} India`)}&z=${zoom}&output=embed`;
}

export function getGoogleMapsLink(place: { maps_query?: string; name: string }, destination: string): string {
  const query = place.maps_query || `${place.name} ${destination}`;
  return `https://www.google.com/maps/search/${encodeURIComponent(query)}`;
}

export function getDestinationMapsLink(destination: string): string {
  return `https://www.google.com/maps/search/tourist+places+in+${encodeURIComponent(destination)}`;
}
