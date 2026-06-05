export const OPERATOR_LOGOS: Record<string, string> = {
  // Major operators with real logo URLs
  'SRS Travels':     'https://i.redbus.in/profile/logo/SRS.png',
  'KSRTC':           'https://i.redbus.in/profile/logo/KSRTC.png',
  'KPN Travels':     'https://i.redbus.in/profile/logo/KPN.png',
  'SETC':            'https://i.redbus.in/profile/logo/SETC.png',
  'Parveen Travels': 'https://i.redbus.in/profile/logo/Parveen.png',
  'Orange Travels':  'https://i.redbus.in/profile/logo/Orange.png',
  'VRL Travels':     'https://i.redbus.in/profile/logo/VRL.png',
  'Chartered Bus':   'https://i.redbus.in/profile/logo/Chartered.png',
  'IntrCity':        'https://i.redbus.in/profile/logo/IntrCity.png',
};

export function getOperatorDisplay(operatorName?: string) {
  if (!operatorName) return { type: 'avatar', text: '?', color: '#6366f1' };

  // Check if we have a real logo
  const logoUrl = OPERATOR_LOGOS[operatorName];
  if (logoUrl) return { type: 'logo', url: logoUrl };

  // Generate consistent color from name
  const colors = [
    '#ef4444','#f97316','#eab308','#22c55e',
    '#06b6d4','#6366f1','#a855f7','#ec4899'
  ];
  let sum = 0;
  for(let i=0; i<operatorName.length; i++) {
    sum += operatorName.charCodeAt(i);
  }
  const colorIndex = sum % colors.length;
  const initials = operatorName
    .split(' ')
    .filter(w => w.length > 0)
    .map(w => w[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  return {
    type: 'avatar',
    text: initials || '?',
    color: colors[colorIndex]
  };
}
