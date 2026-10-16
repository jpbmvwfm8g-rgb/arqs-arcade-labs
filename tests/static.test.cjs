// ARQS Arcade Labs — static checks (no dependencies). Run: node tests/static.test.cjs
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const root = path.join(__dirname, '..');
const pages = ['index.html', 'paddle-lab.html', 'break-lab.html', 'drop-lab.html', 'snake-lab.html', 'risk-pulse.html', 'cost-estimator.html'];
let pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); pass++; console.log('PASS ', name); }
  catch (e) { fail++; console.log('FAIL ', name, '—', e.message); }
}

for (const p of pages) {
  const html = fs.readFileSync(path.join(root, p), 'utf8');
  t(`${p}: doctype, lang, charset, viewport, title`, () => {
    assert(/^<!DOCTYPE html>/i.test(html.trim()), 'doctype');
    assert(/<html[^>]*lang="en"/i.test(html), 'lang');
    assert(/<meta charset="UTF-8">/i.test(html), 'charset');
    assert(/name="viewport"/i.test(html), 'viewport');
    assert(/<title>[^<]+<\/title>/i.test(html), 'title');
    assert(/<\/html>\s*$/i.test(html), 'closing html');
  });
  t(`${p}: inline scripts compile`, () => {
    const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
    scripts.forEach((src, i) => { new vm.Script(src, { filename: `${p}#script${i}` }); });
  });
  t(`${p}: no external script loads, no secrets`, () => {
    assert(!/<script[^>]+src=/i.test(html), 'external <script src>');
    assert(!/(sk_live_|rk_live_|pk_live_|AC[0-9a-f]{32})/.test(html), 'credential-like string');
  });
  if (p !== 'index.html') t(`${p}: localStorage only via guarded access`, () => {
    const code = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
    const lines = code.split('\n');
    // Direct localStorage use is allowed only inside the store shim or within a try block (checked 10 lines back).
    const unguarded = lines.filter((l, i) => /localStorage\.(get|set|remove)Item/.test(l)
      && !/const store =/.test(l) && !/try\s*\{/.test(l)
      && !lines.slice(Math.max(0, i - 10), i).some(p => /try\s*\{/.test(p)));
    assert.strictEqual(unguarded.length, 0, unguarded.join(' | '));
  });
}

const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
t('index: every local link resolves to a file', () => {
  const links = [...index.matchAll(/href="([^"#:]+\.html)"/g)].map(m => m[1]);
  assert(links.length >= 6, `expected >=6 lab links, got ${links.length}`);
  links.forEach(l => assert(fs.existsSync(path.join(root, l)), `missing ${l}`));
});
t('index: every lab page is linked from index', () => {
  pages.filter(p => p !== 'index.html').forEach(p => assert(index.includes(`href="${p}"`), `${p} not linked`));
});
t('index: How to Play covers every lab', () => {
  ['Paddle Lab', 'Break Lab', 'Drop Lab', 'Snake Lab', 'Risk Pulse', 'Cost Estimator'].forEach(n => assert(index.includes(`<td>${n}</td>`), n));
});
t('index: no draft-PR status labels left on release candidate', () => {
  assert(!index.includes('Improved in draft PRs'));
});
t('no stray duplicate lab variants in repo root', () => {
  const extra = fs.readdirSync(root).filter(f => /-(enhanced|v2)\.html$/.test(f));
  assert.strictEqual(extra.length, 0, extra.join(','));
});

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
