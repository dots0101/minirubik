/* Browser-free verification of the exported viewer. No native/browser UI access. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const elements = new Map();
class Element {
  constructor(id = '') { this.id = id; this.children = []; this.textContent = ''; this.value = 0; this.listeners = {}; this.draws = []; }
  append(item) { this.children.push(item); }
  replaceChildren(...items) { this.children = items; }
  addEventListener(type, callback) { this.listeners[type] = callback; }
  getContext(type) {
    assert.strictEqual(type, '2d');
    const owner = this;
    return { fillStyle: '', fillRect(x, y, w, h) { owner.draws.push([x, y, w, h, this.fillStyle]); } };
  }
}
const document = {
  getElementById(id) { if (!elements.has(id)) elements.set(id, new Element(id)); return elements.get(id); },
  createElement(tag) { return new Element(tag); },
};
const callbacks = new Map(); let timerId = 0;
const context = vm.createContext({ document, setInterval(callback) { callbacks.set(++timerId, callback); return timerId; }, clearInterval(id) { callbacks.delete(id); } });
const script = fs.readFileSync(path.join(root, 'build/report_script.js'), 'utf8');
vm.runInContext(script, context);
for (let cycle = 0; cycle <= 616; cycle++) {
  context.renderCycle(cycle);
  assert.strictEqual(elements.get('stages').children.length, 5);
  assert.strictEqual(Number(elements.get('cycle').value), cycle);
}
const stage = name => elements.get('stages').children[['IF', 'ID', 'EX', 'MEM', 'WB'].indexOf(name)];
context.renderCycle(604);
assert.match(stage('ID').children[2].textContent, /clear: 1/);
assert.match(stage('MEM').children[2].textContent, /MemWrite=1/);
context.renderCycle(605);
assert.match(stage('IF').children[1].textContent, /held/);
assert.match(stage('ID').children[1].textContent, /held/);
assert.match(stage('EX').children[1].textContent, /bubble/);
assert.match(stage('WB').children[2].textContent, /RegWrite=0/);
context.renderCycle(606);
assert.match(stage('EX').children[2].textContent, /Forward A\/B: WB \(3\)/);
assert.match(stage('WB').children[2].textContent, /MEMREAD/);
context.renderCycle(608);
assert.match(stage('WB').children[2].textContent, /value=6/);
context.renderCycle(-10); assert.strictEqual(Number(elements.get('cycle').value), 0);
context.renderCycle(1000); assert.strictEqual(Number(elements.get('cycle').value), 616);
context.renderCycle(615); context.play(); assert.strictEqual(callbacks.size, 1);
Array.from(callbacks.values())[0](); assert.strictEqual(callbacks.size, 0);
const led = JSON.parse(fs.readFileSync(path.join(root, 'evidence/led_geometry.json')));
for (let frame = 0; frame < 12; frame++) {
  const canvas = elements.get('led'); canvas.draws = [];
  context.renderLed(frame);
  assert.strictEqual(canvas.draws.length, 875);
  canvas.draws.forEach((draw, i) => {
    assert.deepStrictEqual(draw, [(i % 35) * 10, Math.floor(i / 35) * 10, 10, 10, '#' + led.frames[frame].pixels[i].toString(16).padStart(6, '0')]);
  });
}
const result = { status: 'PASS', scope: 'Node VM with a DOM/canvas stub; JavaScript and recorded data verification, not visual browser QA or live Ripes ports.', cycles: 617, frames: 12, pixels_per_frame: 875, hazard_cycles: [604, 605, 606, 608], playback_and_bounds: 'PASS' };
fs.writeFileSync(path.join(root, 'evidence/report_logic_check.json'), JSON.stringify(result, null, 2) + '\n');
process.stdout.write('PASS: all 617 viewer cycles, hazard controls, playback/bounds and 12 x 875 recorded pixels.\n');
