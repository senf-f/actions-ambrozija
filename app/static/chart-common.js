// Shared Chart.js look and series colours for the graph, compare and temps pages.
Chart.defaults.font.family = 'Outfit';
Chart.defaults.font.size = 11;
Chart.defaults.color = '#6b6b6b';
Chart.defaults.scale.title.font = { size: 12, weight: '500' };
Chart.defaults.plugins.legend.labels.font = { size: 12 };
Object.assign(Chart.defaults.plugins.tooltip, {
  backgroundColor: '#1a3a2a',
  titleFont: { weight: '500' },
  cornerRadius: 8,
  padding: 12
});

const PALETTE = [
  '#2d5a42','#d4a843','#c0392b','#2980b9','#7c3aed',
  '#0891b2','#be185d','#92400e','#16a34a','#1a3a2a'
];

const RAIN_COLORS = ['#2980b9', '#5dade2', '#85c1e9'];
const TEMP_COLORS = { air: '#e67e22', sea: '#0891b2' };
const CAMS_COLOR = '#7c3aed';

function pad(n) {
  return String(n).padStart(2, '0');
}

function formatDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
