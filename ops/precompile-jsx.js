// Compile a page's <script type="text/babel"> block ONCE, at build time.
//   node ops/precompile-jsx.js < page.html > page.compiled.html
//
// Every volume since July Heat shipped its JSX raw and let @babel/standalone
// (3.1MB) compile ~900KB of it on the phone, on every open, before the first
// frame. Same compiler, same preset ("react", as the tag's data-presets asks),
// run here instead: the output is what the phone was producing for itself.
// The Babel CDN tag is removed with it, so the page no longer depends on unpkg
// serving a 7.x Babel (the lesson in CLAUDE.md, "ALWAYS pin to @7").
const fs = require('fs'), vm = require('vm'), path = require('path');
const ctx = { console }; ctx.window = ctx; ctx.self = ctx; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'vendor', 'babel-standalone-7.29.12.min.js'), 'utf8'), ctx);
const Babel = ctx.Babel;
let html = fs.readFileSync(0, 'utf8');
const re = /<script type="text\/babel"([^>]*)>([\s\S]*?)<\/script>/g;
let n = 0;
html = html.replace(re, (m, attrs, code) => {
  const presets = ((/data-presets="([^"]*)"/.exec(attrs) || [])[1] || 'react').split(',').map(s => s.trim()).filter(Boolean);
  const out = Babel.transform(code, { presets, sourceType: 'script', compact: false, comments: false, retainLines: false }).code;
  n++;
  return `<script>\n${out}\n</script>`;
});
if (n !== 1) { console.error(`precompile: expected 1 text/babel block, found ${n}`); process.exit(1); }
const before = html.length;
html = html.replace(/<script src="https:\/\/unpkg\.com\/@babel\/standalone@7\/babel\.min\.js"[^>]*><\/script>\s*/, '');
if (html.length === before) { console.error('precompile: Babel CDN tag not found'); process.exit(1); }
if (/text\/babel/.test(html)) { console.error('precompile: a text/babel reference survived'); process.exit(1); }
process.stdout.write(html);
