#!/usr/bin/env node
// MUSCAT HEIST — the portrait automation.
//
//   npm run heist -- --limit 3          a test batch of three
//   npm run heist                       everyone the brief still lists
//   npm run heist -- --only "Hamed Amri,p_mptqpbkf_hp51i"
//   npm run heist -- --no-upload        generate only (review first)
//   npm run heist -- --upload-only      upload what is generated, generate nothing
//   npm run heist -- --retry-failed     only the players whose last run failed
//   npm run heist -- --dry-run          read the brief, fetch the photos, spend nothing
//   npm run heist -- --force --only X   regenerate AND replace an existing portrait
//
// The pipeline, per player, one at a time so faces never mix:
//   brief (https://heist.urbanpadel.om/api/brief)   who still needs one, their
//     photo link and the exact file name — the SAME page ChatGPT reads, so the
//     style prompt and the to-do list are never typed twice
//   -> source photo (/api/ref/<id>)
//   -> OpenAI image edit, the photo as the reference, input_fidelity high
//   -> <out>/<exact file name from the brief>.png   (the full generated image)
//   -> 4:5 crop anchored high (face in the top third), 1080x1350 JPEG — the only
//      thing the upload API accepts
//   -> POST /api/photo/<id> with a token from POST /api/login {pin: HEIST_PIN}
//   -> verify: the API says ok, the served file is BYTE-IDENTICAL to the one sent,
//      and the roster now reports the portrait.
//
// progress.json records every player as pending / generated / uploaded / failed,
// so a re-run never regenerates an image it already paid for. Existing portraits
// are never replaced without --force.
//
// env: OPENAI_API_KEY, HEIST_PIN (never printed). Optional: HEIST_IMAGE_MODEL
// (default gpt-image-1), HEIST_IMAGE_QUALITY (default high), HEIST_OUT.
import fs from 'fs';
import path from 'path';
import sharp from 'sharp';

const HOST = process.env.HEIST_HOST || 'https://heist.urbanpadel.om';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const OUT = path.resolve(process.env.HEIST_OUT || path.join(ROOT, 'brand/heist/portraits'));
const PROG = path.join(OUT, 'progress.json');
const MODEL = process.env.HEIST_IMAGE_MODEL || 'gpt-image-1';
const QUALITY = process.env.HEIST_IMAGE_QUALITY || 'high';
const GEN = { w: 1024, h: 1536 };          // the model's vertical size, 2:3
const UP = { w: 1080, h: 1350 };           // what the upload API accepts, 4:5
const HEAD_BIAS = 0.3;                     // of the spare height, how much is cut from the TOP

// ── arguments ──────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const flag = f => argv.includes(f);
const opt = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : undefined; };
const A = {
  limit: opt('--limit') ? +opt('--limit') : Infinity,
  only: (opt('--only') || '').split(',').map(s => s.trim()).filter(Boolean),
  force: flag('--force'), dry: flag('--dry-run'), noUpload: flag('--no-upload'),
  uploadOnly: flag('--upload-only'), retryFailed: flag('--retry-failed'), all: flag('--all'),
};
if (flag('--help') || flag('-h')) { console.log(fs.readFileSync(new URL(import.meta.url), 'utf8').split('\n').slice(1, 12).join('\n')); process.exit(0); }

// ── secrets: read, never echoed; anything that looks like one is masked ──────
const mask = s => String(s).replace(/sk-[A-Za-z0-9_-]{8,}/g, 'sk-***')
  .replace(new RegExp((process.env.HEIST_PIN || '\u0000').replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), '***');
function need(v, why) {
  if (!process.env[v]) { console.error(`!! ${v} is not set — ${why}`); process.exit(2); }
}

// ── progress ───────────────────────────────────────────────────────────────
fs.mkdirSync(OUT, { recursive: true });
const prog = fs.existsSync(PROG) ? JSON.parse(fs.readFileSync(PROG, 'utf8')) : {};
function save() { const t = PROG + '.tmp'; fs.writeFileSync(t, JSON.stringify(prog, null, 2)); fs.renameSync(t, PROG); }
function mark(p, status, extra = {}) {
  prog[p.id] = { ...(prog[p.id] || {}), name: p.name, file: p.file, ...extra, status, at: new Date().toISOString() };
  if (status !== 'failed') delete prog[p.id].error;
  save();
  console.log(`  [${status}] ${p.name}${extra.error ? ' — ' + extra.error : ''}`);
}

// ── HTTP ───────────────────────────────────────────────────────────────────
async function http(url, init = {}, tries = 3) {
  for (let i = 1; ; i++) {
    try {
      const r = await fetch(url, { ...init, signal: AbortSignal.timeout(init.timeout || 60000) });
      if ((r.status === 429 || r.status >= 500) && i < tries) { await sleep(4000 * i); continue; }
      return r;
    } catch (e) { if (i >= tries) throw e; await sleep(3000 * i); }
  }
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ── the brief ──────────────────────────────────────────────────────────────
async function readBrief() {
  const r = await http(`${HOST}/api/brief${A.all ? '?all' : ''}`);
  if (!r.ok) throw new Error(`brief: HTTP ${r.status}`);
  const text = await r.text();
  const sec = name => { const m = text.match(new RegExp(`^## ${name}[^\\n]*\\n([\\s\\S]*?)(?=^## |$(?![\\s\\S]))`, 'm')); return m ? m[1].trim() : ''; };
  const style = sec('Style prompt');
  if (!style) throw new Error('brief: no "## Style prompt" section — the brief format changed');
  const players = [];
  for (const line of text.split('\n')) {
    const m = line.match(/^\d+\.\s+(.+?)\s+—\s+photo:\s+(\S+\/api\/ref\/([\w-]+))\s+—\s+save as:\s+(.+?)\s*$/);
    if (m) players.push({ name: m[1], ref: m[2], id: m[3], file: m[4] });
  }
  const todoHead = text.match(/^## To do — (\d+) players/m);
  if (todoHead && +todoHead[1] !== players.length)
    throw new Error(`brief: header says ${todoHead[1]} players, parsed ${players.length} — the line format changed`);
  return { style, players };
}
async function rosterNow() {
  const r = await http(`${HOST}/api/roster`);
  if (!r.ok) throw new Error(`roster: HTTP ${r.status}`);
  return new Map((await r.json()).players.map(p => [p.id, p]));
}
// the brief's own file-name rule, for players it no longer lists (--force)
const fname = (p, roster) => (p.sameName ? p.id : p.name.replace(/[\\/:*?"<>|]+/g, '').trim()) + '.png';

// ── generate ───────────────────────────────────────────────────────────────
function promptFor(style) {
  return `${style}

The attached image is the ONLY reference for this person's identity. Match their facial structure, eyes, nose, mouth, jawline, skin tone, hairline, hair and facial hair exactly; keep their age and build. If the photo is a group or action shot, portray only the most prominent person.`;
}
async function generate(p, style) {
  const src = await http(p.ref);
  if (!src.ok) throw new Error(`source photo: HTTP ${src.status}`);
  // normalised to a PNG no larger than the model works at; also strips odd formats
  const ref = await sharp(Buffer.from(await src.arrayBuffer())).rotate()
    .resize({ width: 1536, height: 1536, fit: 'inside', withoutEnlargement: true }).png().toBuffer();
  fs.writeFileSync(path.join(OUT, 'sources', p.id + '.png'), ref);
  if (A.dry) return null;
  const fd = new FormData();
  fd.append('model', MODEL);
  fd.append('image', new Blob([ref], { type: 'image/png' }), 'reference.png');
  fd.append('prompt', promptFor(style));
  fd.append('size', `${GEN.w}x${GEN.h}`);
  fd.append('quality', QUALITY);
  fd.append('input_fidelity', 'high');
  fd.append('n', '1');
  const r = await http('https://api.openai.com/v1/images/edits', {
    method: 'POST', body: fd, timeout: 300000,
    headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`OpenAI ${r.status}: ${mask((j.error && j.error.message) || 'no message')}`);
  const b64 = j.data && j.data[0] && j.data[0].b64_json;
  if (!b64) throw new Error('OpenAI returned no image');
  const png = Buffer.from(b64, 'base64');
  fs.writeFileSync(path.join(OUT, p.file), png);
  return png;
}

// 2:3 -> 4:5, cut mostly from the bottom so the head keeps its room, then 1080x1350
async function toUpload(png) {
  const m = await sharp(png).metadata();
  const h = Math.min(m.height, Math.round(m.width * UP.h / UP.w));
  const w = Math.round(h * UP.w / UP.h);
  const left = Math.round((m.width - w) / 2), top = Math.round((m.height - h) * HEAD_BIAS);
  return sharp(png).extract({ left, top, width: w, height: h }).resize(UP.w, UP.h)
    .jpeg({ quality: 90, mozjpeg: true }).toBuffer();
}

// ── upload ─────────────────────────────────────────────────────────────────
let token = null;
async function login() {
  const r = await http(`${HOST}/api/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin: process.env.HEIST_PIN }) }, 1);
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.token) throw new Error(`sign-in refused (${r.status}${j.error ? ': ' + j.error : ''})`);
  token = j.token;
}
async function upload(p, jpg) {
  const r = await http(`${HOST}/api/photo/${encodeURIComponent(p.id)}`, {
    method: 'POST', timeout: 120000,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ image: 'data:image/jpeg;base64,' + jpg.toString('base64') }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.ok) throw new Error(`upload ${r.status}: ${j.error || 'no ok'}`);
  // verify by the bytes actually served, at the cache-busted URL the API returned
  const got = await http(HOST + j.url, { headers: { 'Cache-Control': 'no-cache' } });
  const buf = Buffer.from(await got.arrayBuffer());
  if (!got.ok || !buf.equals(jpg)) throw new Error(`verify: served file differs (HTTP ${got.status}, ${buf.length} vs ${jpg.length} bytes)`);
  const now = (await rosterNow()).get(p.id);
  if (!now || !now.heist) throw new Error('verify: roster does not report the portrait');
  return j.url;
}

// ── a review sheet: source beside portrait, for each player in this run ─────
async function sheet(batch) {
  const rows = [];
  for (const p of batch) {
    const srcF = path.join(OUT, 'sources', p.id + '.png'), outF = path.join(OUT, 'upload', p.id + '.jpg');
    if (!fs.existsSync(srcF) || !fs.existsSync(outF)) continue;
    const a = await sharp(srcF).resize(432, 540, { fit: 'contain', background: '#0F1B2B' }).toBuffer();
    const b = await sharp(outF).resize(432, 540).toBuffer();
    const label = Buffer.from(`<svg width="884" height="44"><rect width="884" height="44" fill="#0F1B2B"/><text x="12" y="29" font-family="sans-serif" font-size="22" font-weight="700" fill="#FFF4E8">${p.name.replace(/[<&>]/g, '')} — ${prog[p.id]?.status || ''}</text></svg>`);
    rows.push(await sharp({ create: { width: 884, height: 584, channels: 3, background: '#0F1B2B' } })
      .composite([{ input: label, top: 0, left: 0 }, { input: a, top: 44, left: 0 }, { input: b, top: 44, left: 452 }]).png().toBuffer());
  }
  if (!rows.length) return null;
  const f = path.join(OUT, `sheet-${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}.jpg`);
  await sharp({ create: { width: 884, height: 584 * rows.length, channels: 3, background: '#0F1B2B' } })
    .composite(rows.map((input, i) => ({ input, top: i * 584, left: 0 }))).jpeg({ quality: 85 }).toFile(f);
  return f;
}

// ── run ────────────────────────────────────────────────────────────────────
async function main() {
  fs.mkdirSync(path.join(OUT, 'sources'), { recursive: true });
  fs.mkdirSync(path.join(OUT, 'upload'), { recursive: true });
  const { style, players } = await readBrief();
  const roster = await rosterNow();
  let pool = players;
  if (A.force && A.only.length) {            // the brief omits anyone already done; find them on the roster
    for (const r of roster.values()) if (r.ref && !pool.some(p => p.id === r.id))
      pool.push({ name: r.name, id: r.id, ref: `${HOST}/api/ref/${r.id}`, file: fname(r) });
  }
  if (A.only.length) {
    const want = new Set(A.only.map(s => s.toLowerCase()));
    pool = pool.filter(p => want.has(p.id.toLowerCase()) || want.has(p.name.toLowerCase()));
  }
  if (A.retryFailed) pool = pool.filter(p => prog[p.id]?.status === 'failed');
  if (A.uploadOnly) pool = pool.filter(p => prog[p.id]?.status === 'generated');
  // already uploaded by THIS tool, or a portrait exists on the site: skip unless --force
  pool = pool.filter(p => A.force || (prog[p.id]?.status !== 'uploaded' && !(roster.get(p.id) || {}).heist));
  const batch = pool.slice(0, A.limit);

  console.log(`brief: ${players.length} to do · this run: ${batch.length}${A.dry ? ' (dry run)' : ''} · model ${MODEL}/${QUALITY} · out ${path.relative(ROOT, OUT)}`);
  if (!batch.length) { console.log('nothing to do'); return; }
  const generating = !A.uploadOnly && !A.dry && batch.some(p => A.force || !['generated'].includes(prog[p.id]?.status));
  const uploading = !A.noUpload && !A.dry;
  if (generating) need('OPENAI_API_KEY', 'needed to generate portraits');
  if (uploading) need('HEIST_PIN', 'needed to upload (or pass --no-upload)');
  if (uploading) await login();

  for (const p of batch) {
    console.log(`\n${p.name}  (${p.id})  ->  ${p.file}`);
    if (!prog[p.id] || A.force) mark(p, 'pending');
    try {
      let png = null;
      const have = path.join(OUT, p.file);
      if (!A.force && ['generated', 'uploaded'].includes(prog[p.id]?.status) && fs.existsSync(have)) png = fs.readFileSync(have);
      else if (A.uploadOnly) throw new Error('nothing generated to upload');
      else {
        png = await generate(p, style);
        if (A.dry) { console.log('  dry run — source photo fetched, nothing generated'); continue; }
        mark(p, 'generated', { model: MODEL, quality: QUALITY });
      }
      const jpg = await toUpload(png);
      fs.writeFileSync(path.join(OUT, 'upload', p.id + '.jpg'), jpg);
      if (!uploading) continue;
      // re-check right before replacing anything: somebody may have uploaded by hand
      if (!A.force && (await rosterNow()).get(p.id)?.heist) { mark(p, 'generated', { note: 'a portrait already exists on the site — not replaced' }); continue; }
      const url = await upload(p, jpg);
      mark(p, 'uploaded', { url });
    } catch (e) {
      mark(p, 'failed', { error: mask(e.message) });
    }
  }

  // the report
  const rows = batch.map(p => {
    const s = prog[p.id] || {};
    const made = fs.existsSync(path.join(OUT, p.file));
    const gen = made ? 'generated' : s.status === 'failed' ? 'failed' : A.dry ? 'skipped (dry run)' : 'pending';
    const up = s.status === 'uploaded' ? 'uploaded + verified' : !uploading ? 'skipped'
      : s.status === 'failed' && made ? 'failed' : 'not uploaded';
    return { name: p.name, file: p.file, gen, up, err: s.error || s.note || '', failed: s.status === 'failed' };
  });
  const md = ['| Player | Output file | Generation | Upload | Errors |', '|---|---|---|---|---|',
    ...rows.map(r => `| ${r.name} | ${r.file} | ${r.gen} | ${r.up} | ${r.err.replace(/\|/g, '/')} |`)].join('\n');
  fs.writeFileSync(path.join(OUT, 'REPORT.md'), `# Heist portraits — last run ${new Date().toISOString()}\n\n${md}\n`);
  console.log('\n' + md);
  const sh = await sheet(batch);
  if (sh) console.log(`\nreview sheet: ${sh}`);
  process.exitCode = rows.some(r => r.failed) ? 1 : 0;
}
main().catch(e => { console.error('!! ' + mask(e.message)); process.exit(1); });
