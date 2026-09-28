// Shared Chart.js look, and how each kind of series is drawn, for the graph,
// compare and temps pages.
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

// Every page draws a series of a given kind the same way, on the same axis.
// The axis of the first drawn series is primary: solid lines on the left.
// Every other axis is an overlay: dashed lines, or bars, on the right.
const SERIES_KINDS = {
  pollen: { axis: 'y', title: 'Koncentracija', unit: '', beginAtZero: true, keepEmpty: true,
            color: i => PALETTE[i % PALETTE.length] },
  rain: { axis: 'rain', title: 'Oborine (mm)', unit: ' mm', beginAtZero: true, bar: true,
          color: i => RAIN_COLORS[i % RAIN_COLORS.length], axisColor: RAIN_COLORS[0] },
  air: { axis: 'temp', title: 'Temperatura (°C)', unit: ' °C', dash: [6, 4],
         color: () => TEMP_COLORS.air, axisColor: TEMP_COLORS.air },
  sea: { axis: 'temp', title: 'Temperatura (°C)', unit: ' °C', dash: [2, 3],
         color: () => TEMP_COLORS.sea, axisColor: TEMP_COLORS.air },
  cams: { axis: 'cams', title: 'Ambrozija CAMS (zrnaca/m³)', unit: ' zrnaca/m³', beginAtZero: true,
          dash: [6, 4], color: () => CAMS_COLOR, axisColor: CAMS_COLOR }
};

// Keys are 'YYYY-MM-DD' or 'MM-DD'; ticks always show day and month.
function tickLabel(key) {
  const [m, d] = key.split('-').slice(-2);
  return `${parseInt(d, 10)}.${parseInt(m, 10)}.`;
}

function tooltipTitle(key) {
  return key.length > 5 ? `${tickLabel(key)}${key.slice(0, 4)}.` : tickLabel(key);
}

// series: [{ kind, label, byKey: { key: value }, color? }]. Returns null when
// nothing in `keys` has a value. Empty overlays are dropped, but an empty
// pollen series keeps its legend entry so a missing city is still visible.
function chartConfig(keys, series, { legend = true } = {}) {
  const perKind = {};
  const drawn = series.map(s => {
    const index = perKind[s.kind] = (perKind[s.kind] ?? -1) + 1;
    return { ...s, index, data: keys.map(k => s.byKey[k] ?? null) };
  }).filter(s => SERIES_KINDS[s.kind].keepEmpty || s.data.some(v => v !== null));
  if (!drawn.some(s => s.data.some(v => v !== null))) return null;

  const primary = SERIES_KINDS[drawn[0].kind].axis;
  const scales = {
    x: {
      type: 'category',
      title: { display: true, text: 'Datum' },
      grid: { display: false },
      ticks: { callback(value) { return tickLabel(this.getLabelForValue(value)); } }
    }
  };

  const datasets = drawn.map(s => {
    const kind = SERIES_KINDS[s.kind];
    const color = s.color || kind.color(s.index);
    const isPrimary = kind.axis === primary;
    if (!scales[kind.axis]) {
      scales[kind.axis] = isPrimary
        ? { axis: 'y', position: 'left', beginAtZero: !!kind.beginAtZero,
            title: { display: true, text: kind.title },
            grid: { color: 'rgba(0,0,0,0.04)' } }
        : { axis: 'y', position: 'right', beginAtZero: !!kind.beginAtZero,
            title: { display: true, text: kind.title, color: kind.axisColor },
            grid: { drawOnChartArea: false },
            ticks: { color: kind.axisColor } };
    }
    const base = { label: s.label, data: s.data, yAxisID: kind.axis, unit: kind.unit };
    if (kind.bar) {
      return { ...base, type: 'bar', backgroundColor: color + '66', borderColor: color,
               borderWidth: 1, order: 2 };
    }
    const line = { ...base, borderColor: color, tension: 0.35, spanGaps: true };
    if (isPrimary) {
      return { ...line, backgroundColor: color + '18', pointRadius: 3, pointHoverRadius: 6,
               borderWidth: 2.5, order: 1 };
    }
    // Same-kind overlays share a colour, so their dash gaps widen to tell them apart.
    return { ...line, backgroundColor: 'transparent', borderDash: [kind.dash[0], kind.dash[1] * (s.index + 1)],
             pointRadius: 0, pointHoverRadius: 5, borderWidth: 2, order: 0 };
  });

  return {
    type: 'line',
    data: { labels: keys, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: legend },
        tooltip: {
          callbacks: {
            title: items => (items.length ? tooltipTitle(items[0].label) : ''),
            label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y}${ctx.dataset.unit}`
          }
        }
      },
      scales
    }
  };
}

// The canvas's parent is the chart card, shown only while a chart is drawn.
function clearChart(canvas) {
  Chart.getChart(canvas)?.destroy();
  canvas.parentElement.style.display = 'none';
}

// Returns false, leaving the card hidden, when there was nothing to draw.
function drawSeries(canvas, keys, series, options) {
  clearChart(canvas);
  const config = chartConfig(keys, series, options);
  if (!config) return false;
  canvas.parentElement.style.display = '';
  new Chart(canvas, config);
  return true;
}
