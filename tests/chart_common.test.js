// Run by tests/test_chart_common.py; loads chart-common.js with a stub Chart global.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const stub = { defaults: { font: {}, scale: { title: {} }, plugins: { legend: { labels: {} }, tooltip: {} } } };
const ctx = vm.createContext({ Chart: stub });
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'app', 'static', 'chart-common.js'), 'utf8'), ctx);
const { chartConfig, tickLabel, tooltipTitle } = ctx;

const keys = ['2026-08-31', '2026-09-01'];
const pollen = { kind: 'pollen', label: 'Ambrozija', byKey: { '2026-08-31': 3, '2026-09-01': 4 } };

// Ticks show day and month for full dates and month-day keys alike.
assert.equal(tickLabel('2026-08-31'), '31.8.');
assert.equal(tickLabel('09-01'), '1.9.');
assert.equal(tooltipTitle('2026-09-01'), '1.9.2026.');
assert.equal(tooltipTitle('09-01'), '1.9.');

// Nothing to draw.
assert.equal(chartConfig(keys, []), null);
assert.equal(chartConfig(keys, [{ kind: 'pollen', label: 'x', byKey: {} }]), null);

// Each overlay kind always gets the same axis, whichever page draws it.
const all = chartConfig(keys, [
  pollen,
  { kind: 'rain', label: 'r', byKey: { '2026-09-01': 2 } },
  { kind: 'air', label: 'a', byKey: { '2026-09-01': 20 } },
  { kind: 'cams', label: 'c', byKey: { '2026-09-01': 5 } }
]);
assert.deepEqual(all.data.datasets.map(d => d.yAxisID), ['y', 'rain', 'temp', 'cams']);
assert.deepEqual(Object.keys(all.options.scales).sort(), ['cams', 'rain', 'temp', 'x', 'y']);
assert.equal(all.options.scales.y.position, 'left');
assert.equal(all.options.scales.cams.position, 'right');
assert.equal(all.data.datasets[1].type, 'bar');
assert.ok(all.data.datasets[3].borderDash, 'overlay lines are dashed');

// Empty overlays are dropped, an empty pollen series keeps its legend entry.
const sparse = chartConfig(keys, [
  pollen,
  { kind: 'pollen', label: 'Split', byKey: {} },
  { kind: 'cams', label: 'old year', byKey: {} }
]);
assert.deepEqual(sparse.data.datasets.map(d => d.label), ['Ambrozija', 'Split']);
assert.equal(sparse.options.scales.cams, undefined);

// Without pollen the first kind is primary: solid lines on the left axis.
const temps = chartConfig(keys, [
  { kind: 'air', label: 'air', byKey: { '2026-09-01': 20 } },
  { kind: 'sea', label: 'sea', byKey: { '2026-09-01': 18 } }
]);
assert.equal(temps.options.scales.temp.position, 'left');
assert.ok(temps.data.datasets.every(d => !d.borderDash));

// Colours follow the series' own colour, else its index within the kind.
const coloured = chartConfig(keys, [{ ...pollen, color: '#123456' }, { ...pollen, label: 'b' }]);
assert.equal(coloured.data.datasets[0].borderColor, '#123456');
assert.equal(coloured.data.datasets[1].borderColor, '#d4a843'); // PALETTE[1]

// Same-kind overlays share a colour, so their dashes differ.
const twoCams = chartConfig(keys, [
  pollen,
  { kind: 'cams', label: 'c1', byKey: { '2026-09-01': 1 } },
  { kind: 'cams', label: 'c2', byKey: { '2026-09-01': 2 } }
]);
assert.notDeepEqual(twoCams.data.datasets[1].borderDash, twoCams.data.datasets[2].borderDash);

console.log('chart-common ok');
