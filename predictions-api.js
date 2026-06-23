'use strict';
require('dotenv').config({ path: '/opt/june-fury-api/.env' });
const express = require('express');
const { Pool } = require('pg');
const crypto = require('crypto');
const https = require('https');

const app = express();
app.use(express.json({ limit: '2mb' }));
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

const pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: false });
const SECRET = process.env.WC_SECRET || 'wc2026-jrobalshabab-secret';
const ADMIN_PHONE = process.env.WC_ADMIN_PHONE || '';
const ADMIN_PHONES_EXTRA = process.env.WC_ADMIN_PHONES_EXTRA || '99888188'; // extra admins
const FDO_KEY = process.env.FOOTBALL_DATA_KEY || '';
const ODDS_KEY = process.env.ODDS_API_KEY || '';

// Strip non-digits for loose phone comparison
function normalizePhone(p) { return p ? String(p).replace(/\D/g, '') : ''; }
function isAdminPhone(p) {
  const n = normalizePhone(p);
  const primaries = ADMIN_PHONE.split(',').map(normalizePhone).filter(Boolean);
  const extras = ADMIN_PHONES_EXTRA.split(',').map(normalizePhone).filter(Boolean);
  return [...primaries, ...extras].includes(n);
}

// ── Token helpers ──────────────────────────────────────────────────────────────
function makeToken(playerId) {
  const exp = Date.now() + 90 * 24 * 3600 * 1000; // 90 days
  const payload = `${playerId}:${exp}`;
  const sig = crypto.createHmac('sha256', SECRET).update(payload).digest('hex');
  return `${payload}:${sig}`;
}

function verifyToken(raw) {
  if (!raw) return null;
  const t = raw.startsWith('Bearer ') ? raw.slice(7) : raw;
  const parts = t.split(':');
  if (parts.length < 3) return null;
  const sig = parts[parts.length - 1];
  const rest = parts.slice(0, -1).join(':');
  const [playerId, exp] = rest.split(':');
  if (Date.now() > Number(exp)) return null;
  const expected = crypto.createHmac('sha256', SECRET).update(rest).digest('hex');
  return sig === expected ? Number(playerId) : null;
}

function auth(req, res, next) {
  const id = verifyToken(req.headers.authorization || '');
  if (!id) return res.status(401).json({ error: 'Unauthorized' });
  req.playerId = id;
  next();
}

async function getPlayer(id) {
  const { rows } = await pool.query('SELECT * FROM wc_players WHERE id=$1', [id]);
  return rows[0] || null;
}

async function getSetting(key, fallback) {
  const { rows } = await pool.query('SELECT value FROM wc_settings WHERE key=$1', [key]);
  return rows[0] ? rows[0].value : fallback;
}

// ── Seed data ──────────────────────────────────────────────────────────────────
const SEED_MATCHES = [
  // GROUP STAGE — times in UTC (Sky Sports BST - 1h)
  // ── Group A ──
  { id:'GA1', stage:'group', grp:'A', h:'Mexico',       hf:'🇲🇽', a:'South Africa',  af:'🇿🇦', ko:'2026-06-11T19:00:00Z', venue:'Mexico City',  ho:1.80, do:3.40, ao:4.50 },
  { id:'GA2', stage:'group', grp:'A', h:'South Korea',  hf:'🇰🇷', a:'Czechia',        af:'🇨🇿', ko:'2026-06-12T02:00:00Z', venue:'Zapopan',      ho:2.20, do:3.20, ao:3.10 },
  { id:'GA3', stage:'group', grp:'A', h:'Czechia',      hf:'🇨🇿', a:'South Africa',  af:'🇿🇦', ko:'2026-06-18T16:00:00Z', venue:'Atlanta',      ho:1.90, do:3.30, ao:4.00 },
  { id:'GA4', stage:'group', grp:'A', h:'Mexico',       hf:'🇲🇽', a:'South Korea',   af:'🇰🇷', ko:'2026-06-19T01:00:00Z', venue:'Zapopan',      ho:2.00, do:3.30, ao:3.50 },
  { id:'GA5', stage:'group', grp:'A', h:'South Africa', hf:'🇿🇦', a:'South Korea',   af:'🇰🇷', ko:'2026-06-25T01:00:00Z', venue:'Guadalajara',  ho:3.50, do:3.20, ao:2.10 },
  { id:'GA6', stage:'group', grp:'A', h:'Czechia',      hf:'🇨🇿', a:'Mexico',        af:'🇲🇽', ko:'2026-06-25T01:00:00Z', venue:'Mexico City',  ho:3.20, do:3.30, ao:2.10 },
  // ── Group B ──
  { id:'GB1', stage:'group', grp:'B', h:'Canada',       hf:'🇨🇦', a:'Bosnia & Herz.', af:'🇧🇦', ko:'2026-06-12T19:00:00Z', venue:'Toronto',     ho:2.10, do:3.20, ao:3.40 },
  { id:'GB2', stage:'group', grp:'B', h:'Qatar',        hf:'🇶🇦', a:'Switzerland',   af:'🇨🇭', ko:'2026-06-13T19:00:00Z', venue:'Santa Clara', ho:4.00, do:3.30, ao:1.90 },
  { id:'GB3', stage:'group', grp:'B', h:'Switzerland',  hf:'🇨🇭', a:'Bosnia & Herz.', af:'🇧🇦', ko:'2026-06-18T19:00:00Z', venue:'Los Angeles', ho:1.80, do:3.40, ao:4.20 },
  { id:'GB4', stage:'group', grp:'B', h:'Canada',       hf:'🇨🇦', a:'Qatar',         af:'🇶🇦', ko:'2026-06-18T22:00:00Z', venue:'Vancouver',   ho:1.60, do:3.60, ao:5.50 },
  { id:'GB5', stage:'group', grp:'B', h:'Switzerland',  hf:'🇨🇭', a:'Canada',        af:'🇨🇦', ko:'2026-06-24T19:00:00Z', venue:'Vancouver',   ho:1.90, do:3.30, ao:4.00 },
  { id:'GB6', stage:'group', grp:'B', h:'Bosnia & Herz.',hf:'🇧🇦', a:'Qatar',        af:'🇶🇦', ko:'2026-06-24T19:00:00Z', venue:'Seattle',     ho:1.90, do:3.20, ao:4.00 },
  // ── Group C ──
  { id:'GC1', stage:'group', grp:'C', h:'Brazil',       hf:'🇧🇷', a:'Morocco',       af:'🇲🇦', ko:'2026-06-13T22:00:00Z', venue:'New Jersey',  ho:1.50, do:4.00, ao:6.00 },
  { id:'GC2', stage:'group', grp:'C', h:'Haiti',        hf:'🇭🇹', a:'Scotland',      af:'🏴󠁧󠁢󠁳󠁣󠁴󠁿', ko:'2026-06-14T01:00:00Z', venue:'Foxborough',  ho:4.50, do:3.30, ao:1.70 },
  { id:'GC3', stage:'group', grp:'C', h:'Scotland',     hf:'🏴󠁧󠁢󠁳󠁣󠁴󠁿', a:'Morocco',      af:'🇲🇦', ko:'2026-06-19T22:00:00Z', venue:'Foxborough',  ho:2.50, do:3.20, ao:2.80 },
  { id:'GC4', stage:'group', grp:'C', h:'Brazil',       hf:'🇧🇷', a:'Haiti',         af:'🇭🇹', ko:'2026-06-20T00:30:00Z', venue:'Philadelphia',ho:1.20, do:7.00, ao:15.0 },
  { id:'GC5', stage:'group', grp:'C', h:'Morocco',      hf:'🇲🇦', a:'Haiti',         af:'🇭🇹', ko:'2026-06-24T22:00:00Z', venue:'Atlanta',     ho:1.60, do:3.50, ao:5.50 },
  { id:'GC6', stage:'group', grp:'C', h:'Scotland',     hf:'🏴󠁧󠁢󠁳󠁣󠁴󠁿', a:'Brazil',       af:'🇧🇷', ko:'2026-06-24T22:00:00Z', venue:'Miami',       ho:5.50, do:3.80, ao:1.50 },
  // ── Group D ──
  { id:'GD1', stage:'group', grp:'D', h:'USA',          hf:'🇺🇸', a:'Paraguay',      af:'🇵🇾', ko:'2026-06-13T01:00:00Z', venue:'Los Angeles', ho:1.90, do:3.30, ao:4.00 },
  { id:'GD2', stage:'group', grp:'D', h:'Australia',    hf:'🇦🇺', a:'Türkiye',       af:'🇹🇷', ko:'2026-06-14T04:00:00Z', venue:'Vancouver',   ho:2.80, do:3.20, ao:2.50 },
  { id:'GD3', stage:'group', grp:'D', h:'USA',          hf:'🇺🇸', a:'Australia',     af:'🇦🇺', ko:'2026-06-19T19:00:00Z', venue:'Seattle',     ho:1.70, do:3.50, ao:4.50 },
  { id:'GD4', stage:'group', grp:'D', h:'Türkiye',      hf:'🇹🇷', a:'Paraguay',      af:'🇵🇾', ko:'2026-06-20T03:00:00Z', venue:'Santa Clara', ho:1.90, do:3.30, ao:3.80 },
  { id:'GD5', stage:'group', grp:'D', h:'Türkiye',      hf:'🇹🇷', a:'USA',           af:'🇺🇸', ko:'2026-06-26T02:00:00Z', venue:'Los Angeles', ho:4.00, do:3.50, ao:1.80 },
  { id:'GD6', stage:'group', grp:'D', h:'Paraguay',     hf:'🇵🇾', a:'Australia',     af:'🇦🇺', ko:'2026-06-26T02:00:00Z', venue:'Santa Clara', ho:2.60, do:3.20, ao:2.70 },
  // ── Group E ──
  { id:'GE1', stage:'group', grp:'E', h:'Germany',      hf:'🇩🇪', a:'Curaçao',       af:'🇨🇼', ko:'2026-06-14T17:00:00Z', venue:'Houston',     ho:1.15, do:9.00, ao:18.0 },
  { id:'GE2', stage:'group', grp:'E', h:'Ivory Coast',  hf:'🇨🇮', a:'Ecuador',       af:'🇪🇨', ko:'2026-06-14T23:00:00Z', venue:'Philadelphia',ho:2.40, do:3.20, ao:2.90 },
  { id:'GE3', stage:'group', grp:'E', h:'Germany',      hf:'🇩🇪', a:'Ivory Coast',   af:'🇨🇮', ko:'2026-06-20T20:00:00Z', venue:'Toronto',     ho:1.60, do:3.60, ao:5.50 },
  { id:'GE4', stage:'group', grp:'E', h:'Ecuador',      hf:'🇪🇨', a:'Curaçao',       af:'🇨🇼', ko:'2026-06-21T00:00:00Z', venue:'Kansas City', ho:1.70, do:3.50, ao:5.00 },
  { id:'GE5', stage:'group', grp:'E', h:'Curaçao',      hf:'🇨🇼', a:'Ivory Coast',   af:'🇨🇮', ko:'2026-06-25T20:00:00Z', venue:'Philadelphia',ho:3.20, do:3.10, ao:2.10 },
  { id:'GE6', stage:'group', grp:'E', h:'Ecuador',      hf:'🇪🇨', a:'Germany',       af:'🇩🇪', ko:'2026-06-25T20:00:00Z', venue:'New Jersey',  ho:6.00, do:4.00, ao:1.40 },
  // ── Group F ──
  { id:'GF1', stage:'group', grp:'F', h:'Netherlands',  hf:'🇳🇱', a:'Japan',         af:'🇯🇵', ko:'2026-06-14T20:00:00Z', venue:'Arlington',   ho:1.90, do:3.30, ao:3.80 },
  { id:'GF2', stage:'group', grp:'F', h:'Sweden',       hf:'🇸🇪', a:'Tunisia',       af:'🇹🇳', ko:'2026-06-15T02:00:00Z', venue:'Guadalajara', ho:1.80, do:3.30, ao:4.50 },
  { id:'GF3', stage:'group', grp:'F', h:'Netherlands',  hf:'🇳🇱', a:'Sweden',        af:'🇸🇪', ko:'2026-06-20T17:00:00Z', venue:'Houston',     ho:1.70, do:3.40, ao:4.80 },
  { id:'GF4', stage:'group', grp:'F', h:'Tunisia',      hf:'🇹🇳', a:'Japan',         af:'🇯🇵', ko:'2026-06-21T04:00:00Z', venue:'Guadalajara', ho:3.20, do:3.10, ao:2.20 },
  { id:'GF5', stage:'group', grp:'F', h:'Tunisia',      hf:'🇹🇳', a:'Netherlands',   af:'🇳🇱', ko:'2026-06-25T23:00:00Z', venue:'Kansas City', ho:5.00, do:3.60, ao:1.60 },
  { id:'GF6', stage:'group', grp:'F', h:'Japan',        hf:'🇯🇵', a:'Sweden',        af:'🇸🇪', ko:'2026-06-25T23:00:00Z', venue:'Arlington',   ho:2.50, do:3.20, ao:2.80 },
  // ── Group G ──
  { id:'GG1', stage:'group', grp:'G', h:'Belgium',      hf:'🇧🇪', a:'Egypt',         af:'🇪🇬', ko:'2026-06-15T19:00:00Z', venue:'Seattle',     ho:1.60, do:3.50, ao:5.50 },
  { id:'GG2', stage:'group', grp:'G', h:'Iran',         hf:'🇮🇷', a:'New Zealand',   af:'🇳🇿', ko:'2026-06-16T01:00:00Z', venue:'Los Angeles', ho:2.10, do:3.20, ao:3.50 },
  { id:'GG3', stage:'group', grp:'G', h:'Belgium',      hf:'🇧🇪', a:'Iran',          af:'🇮🇷', ko:'2026-06-21T19:00:00Z', venue:'Los Angeles', ho:1.55, do:3.60, ao:5.50 },
  { id:'GG4', stage:'group', grp:'G', h:'New Zealand',  hf:'🇳🇿', a:'Egypt',         af:'🇪🇬', ko:'2026-06-22T01:00:00Z', venue:'Vancouver',   ho:2.50, do:3.20, ao:2.80 },
  { id:'GG5', stage:'group', grp:'G', h:'New Zealand',  hf:'🇳🇿', a:'Belgium',       af:'🇧🇪', ko:'2026-06-27T03:00:00Z', venue:'Vancouver',   ho:6.00, do:4.00, ao:1.45 },
  { id:'GG6', stage:'group', grp:'G', h:'Egypt',        hf:'🇪🇬', a:'Iran',          af:'🇮🇷', ko:'2026-06-27T03:00:00Z', venue:'Seattle',     ho:2.60, do:3.20, ao:2.60 },
  // ── Group H ──
  { id:'GH1', stage:'group', grp:'H', h:'Spain',        hf:'🇪🇸', a:'Cape Verde',    af:'🇨🇻', ko:'2026-06-15T16:00:00Z', venue:'Atlanta',     ho:1.20, do:8.00, ao:14.0 },
  { id:'GH2', stage:'group', grp:'H', h:'Saudi Arabia', hf:'🇸🇦', a:'Uruguay',       af:'🇺🇾', ko:'2026-06-15T22:00:00Z', venue:'Miami',       ho:3.20, do:3.30, ao:2.20 },
  { id:'GH3', stage:'group', grp:'H', h:'Spain',        hf:'🇪🇸', a:'Saudi Arabia',  af:'🇸🇦', ko:'2026-06-21T16:00:00Z', venue:'Atlanta',     ho:1.40, do:5.00, ao:8.00 },
  { id:'GH4', stage:'group', grp:'H', h:'Uruguay',      hf:'🇺🇾', a:'Cape Verde',    af:'🇨🇻', ko:'2026-06-21T22:00:00Z', venue:'Miami',       ho:1.40, do:4.50, ao:9.00 },
  { id:'GH5', stage:'group', grp:'H', h:'Cape Verde',   hf:'🇨🇻', a:'Saudi Arabia',  af:'🇸🇦', ko:'2026-06-27T00:00:00Z', venue:'Houston',     ho:3.50, do:3.10, ao:2.10 },
  { id:'GH6', stage:'group', grp:'H', h:'Uruguay',      hf:'🇺🇾', a:'Spain',         af:'🇪🇸', ko:'2026-06-27T00:00:00Z', venue:'Zapopan',     ho:5.50, do:3.80, ao:1.55 },
  // ── Group I ──
  { id:'GI1', stage:'group', grp:'I', h:'France',       hf:'🇫🇷', a:'Senegal',       af:'🇸🇳', ko:'2026-06-16T19:00:00Z', venue:'New Jersey',  ho:1.55, do:3.70, ao:5.50 },
  { id:'GI2', stage:'group', grp:'I', h:'Iraq',         hf:'🇮🇶', a:'Norway',        af:'🇳🇴', ko:'2026-06-16T22:00:00Z', venue:'Foxborough',  ho:4.00, do:3.20, ao:1.85 },
  { id:'GI3', stage:'group', grp:'I', h:'France',       hf:'🇫🇷', a:'Iraq',          af:'🇮🇶', ko:'2026-06-22T21:00:00Z', venue:'Philadelphia',ho:1.25, do:7.00, ao:12.0 },
  { id:'GI4', stage:'group', grp:'I', h:'Norway',       hf:'🇳🇴', a:'Senegal',       af:'🇸🇳', ko:'2026-06-23T00:00:00Z', venue:'Toronto',     ho:1.80, do:3.30, ao:4.50 },
  { id:'GI5', stage:'group', grp:'I', h:'Norway',       hf:'🇳🇴', a:'France',        af:'🇫🇷', ko:'2026-06-26T19:00:00Z', venue:'Foxborough',  ho:4.50, do:3.70, ao:1.70 },
  { id:'GI6', stage:'group', grp:'I', h:'Senegal',      hf:'🇸🇳', a:'Iraq',          af:'🇮🇶', ko:'2026-06-26T19:00:00Z', venue:'Toronto',     ho:1.70, do:3.30, ao:5.00 },
  // ── Group J ──
  { id:'GJ1', stage:'group', grp:'J', h:'Argentina',    hf:'🇦🇷', a:'Algeria',       af:'🇩🇿', ko:'2026-06-17T01:00:00Z', venue:'Kansas City', ho:1.40, do:4.80, ao:8.00 },
  { id:'GJ2', stage:'group', grp:'J', h:'Austria',      hf:'🇦🇹', a:'Jordan',        af:'🇯🇴', ko:'2026-06-17T04:00:00Z', venue:'Santa Clara', ho:1.75, do:3.40, ao:4.50 },
  { id:'GJ3', stage:'group', grp:'J', h:'Argentina',    hf:'🇦🇷', a:'Austria',       af:'🇦🇹', ko:'2026-06-22T17:00:00Z', venue:'Arlington',   ho:1.60, do:3.70, ao:5.50 },
  { id:'GJ4', stage:'group', grp:'J', h:'Jordan',       hf:'🇯🇴', a:'Algeria',       af:'🇩🇿', ko:'2026-06-23T03:00:00Z', venue:'Santa Clara', ho:2.80, do:3.10, ao:2.60 },
  { id:'GJ5', stage:'group', grp:'J', h:'Algeria',      hf:'🇩🇿', a:'Austria',       af:'🇦🇹', ko:'2026-06-28T02:00:00Z', venue:'Kansas City', ho:3.00, do:3.20, ao:2.40 },
  { id:'GJ6', stage:'group', grp:'J', h:'Jordan',       hf:'🇯🇴', a:'Argentina',     af:'🇦🇷', ko:'2026-06-28T02:00:00Z', venue:'Arlington',   ho:9.00, do:5.00, ao:1.30 },
  // ── Group K ──
  { id:'GK1', stage:'group', grp:'K', h:'Portugal',     hf:'🇵🇹', a:'DR Congo',      af:'🇨🇩', ko:'2026-06-17T17:00:00Z', venue:'Houston',     ho:1.50, do:4.00, ao:6.50 },
  { id:'GK2', stage:'group', grp:'K', h:'Uzbekistan',   hf:'🇺🇿', a:'Colombia',      af:'🇨🇴', ko:'2026-06-18T02:00:00Z', venue:'Mexico City', ho:3.50, do:3.20, ao:2.10 },
  { id:'GK3', stage:'group', grp:'K', h:'Portugal',     hf:'🇵🇹', a:'Uzbekistan',    af:'🇺🇿', ko:'2026-06-23T17:00:00Z', venue:'Houston',     ho:1.30, do:6.00, ao:9.00 },
  { id:'GK4', stage:'group', grp:'K', h:'Colombia',     hf:'🇨🇴', a:'DR Congo',      af:'🇨🇩', ko:'2026-06-24T02:00:00Z', venue:'Zapopan',     ho:1.60, do:3.50, ao:6.00 },
  { id:'GK5', stage:'group', grp:'K', h:'Colombia',     hf:'🇨🇴', a:'Portugal',      af:'🇵🇹', ko:'2026-06-27T23:30:00Z', venue:'Miami',       ho:3.80, do:3.40, ao:1.95 },
  { id:'GK6', stage:'group', grp:'K', h:'DR Congo',     hf:'🇨🇩', a:'Uzbekistan',    af:'🇺🇿', ko:'2026-06-27T23:30:00Z', venue:'Atlanta',     ho:2.40, do:3.10, ao:2.80 },
  // ── Group L ──
  { id:'GL1', stage:'group', grp:'L', h:'England',      hf:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', a:'Croatia',      af:'🇭🇷', ko:'2026-06-17T20:00:00Z', venue:'Arlington',   ho:1.70, do:3.50, ao:4.80 },
  { id:'GL2', stage:'group', grp:'L', h:'Ghana',        hf:'🇬🇭', a:'Panama',        af:'🇵🇦', ko:'2026-06-17T23:00:00Z', venue:'Toronto',     ho:2.50, do:3.20, ao:2.80 },
  { id:'GL3', stage:'group', grp:'L', h:'England',      hf:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', a:'Ghana',        af:'🇬🇭', ko:'2026-06-23T20:00:00Z', venue:'Foxborough',  ho:1.55, do:3.80, ao:5.50 },
  { id:'GL4', stage:'group', grp:'L', h:'Panama',       hf:'🇵🇦', a:'Croatia',       af:'🇭🇷', ko:'2026-06-24T23:00:00Z', venue:'Foxborough',  ho:3.50, do:3.20, ao:2.10 },
  { id:'GL5', stage:'group', grp:'L', h:'Panama',       hf:'🇵🇦', a:'England',       af:'🏴󠁧󠁢󠁥󠁮󠁧󠁿', ko:'2026-06-27T21:00:00Z', venue:'New Jersey',  ho:8.00, do:5.00, ao:1.35 },
  { id:'GL6', stage:'group', grp:'L', h:'Croatia',      hf:'🇭🇷', a:'Ghana',         af:'🇬🇭', ko:'2026-06-27T21:00:00Z', venue:'Philadelphia',ho:1.80, do:3.30, ao:4.50 },

  // ── ROUND OF 32 (knockout - teams TBD) ──
  { id:'R32_1', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-28T20:00:00Z', venue:'Los Angeles',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_2', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-29T17:00:00Z', venue:'Houston',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_3', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-29T21:30:00Z', venue:'Foxborough',   ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_4', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-30T01:00:00Z', venue:'Guadalajara',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_5', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-30T17:00:00Z', venue:'Arlington',    ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_6', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-06-30T21:00:00Z', venue:'New Jersey',   ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_7', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-01T01:00:00Z', venue:'Mexico City',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_8', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-01T17:00:00Z', venue:'Atlanta',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_9', stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-01T21:00:00Z', venue:'Seattle',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_10',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-02T01:00:00Z', venue:'Santa Clara',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_11',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-02T20:00:00Z', venue:'Los Angeles',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_12',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-03T00:00:00Z', venue:'Toronto',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_13',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-03T04:00:00Z', venue:'Vancouver',    ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_14',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-03T19:00:00Z', venue:'Arlington',    ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_15',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-03T23:00:00Z', venue:'Miami',        ho:1.90, do:3.30, ao:3.90 },
  { id:'R32_16',stage:'r32', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-04T02:30:00Z', venue:'Kansas City',  ho:1.90, do:3.30, ao:3.90 },

  // ── ROUND OF 16 ──
  { id:'R16_1', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-04T18:00:00Z', venue:'Houston',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_2', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-04T22:00:00Z', venue:'Philadelphia', ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_3', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-05T21:00:00Z', venue:'New Jersey',   ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_4', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-06T01:00:00Z', venue:'Mexico City',  ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_5', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-06T20:00:00Z', venue:'Arlington',    ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_6', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-07T01:00:00Z', venue:'Seattle',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_7', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-07T17:00:00Z', venue:'Atlanta',      ho:1.90, do:3.30, ao:3.90 },
  { id:'R16_8', stage:'r16', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-07T21:00:00Z', venue:'Vancouver',    ho:1.90, do:3.30, ao:3.90 },

  // ── QUARTER FINALS ──
  { id:'QF1', stage:'qf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-09T21:00:00Z', venue:'Foxborough',   ho:1.90, do:3.30, ao:3.90 },
  { id:'QF2', stage:'qf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-10T20:00:00Z', venue:'Los Angeles',  ho:1.90, do:3.30, ao:3.90 },
  { id:'QF3', stage:'qf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-11T22:00:00Z', venue:'Miami',        ho:1.90, do:3.30, ao:3.90 },
  { id:'QF4', stage:'qf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-12T02:00:00Z', venue:'Kansas City',  ho:1.90, do:3.30, ao:3.90 },

  // ── SEMI FINALS ──
  { id:'SF1', stage:'sf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-14T20:00:00Z', venue:'Arlington',    ho:1.90, do:3.30, ao:3.90 },
  { id:'SF2', stage:'sf', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-15T20:00:00Z', venue:'Atlanta',      ho:1.90, do:3.30, ao:3.90 },

  // ── 3RD PLACE + FINAL ──
  { id:'3RD', stage:'3rd', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-18T22:00:00Z', venue:'Miami',        ho:1.90, do:3.30, ao:3.90 },
  { id:'FINAL', stage:'final', grp:null, h:'TBD', hf:'🏳️', a:'TBD', af:'🏳️', ko:'2026-07-19T20:00:00Z', venue:'New Jersey',  ho:1.90, do:3.30, ao:3.90 },
];

// ── DB init ────────────────────────────────────────────────────────────────────
async function initDB() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS wc_players (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      phone TEXT UNIQUE NOT NULL,
      balance NUMERIC(10,2) DEFAULT 100.00,
      pin VARCHAR(6),
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ALTER TABLE wc_players ADD COLUMN IF NOT EXISTS pin VARCHAR(6);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_btts_yes NUMERIC(6,3);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_btts_no NUMERIC(6,3);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_over25 NUMERIC(6,3);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_under25 NUMERIC(6,3);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_dnb_home NUMERIC(6,3);
    ALTER TABLE wc_matches ADD COLUMN IF NOT EXISTS odds_dnb_away NUMERIC(6,3);
    ALTER TABLE wc_predictions DROP CONSTRAINT IF EXISTS wc_predictions_player_id_match_id_key;
    ALTER TABLE wc_predictions ADD CONSTRAINT wc_predictions_player_match_pred_key UNIQUE (player_id, match_id, prediction);
    CREATE TABLE IF NOT EXISTS wc_matches (
      id TEXT PRIMARY KEY,
      stage TEXT NOT NULL,
      grp TEXT,
      home_team TEXT NOT NULL,
      away_team TEXT NOT NULL,
      home_flag TEXT DEFAULT '',
      away_flag TEXT DEFAULT '',
      kickoff TIMESTAMPTZ NOT NULL,
      venue TEXT DEFAULT '',
      home_odds NUMERIC(6,2) DEFAULT 2.00,
      draw_odds NUMERIC(6,2) DEFAULT 3.20,
      away_odds NUMERIC(6,2) DEFAULT 3.50,
      home_score INT,
      away_score INT,
      result TEXT,
      settled BOOLEAN DEFAULT FALSE
    );
    CREATE TABLE IF NOT EXISTS wc_predictions (
      id SERIAL PRIMARY KEY,
      player_id INT REFERENCES wc_players(id),
      match_id TEXT REFERENCES wc_matches(id),
      prediction TEXT NOT NULL,
      stake NUMERIC(10,2) NOT NULL,
      payout NUMERIC(10,2),
      settled BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      UNIQUE(player_id, match_id)
    );
    CREATE TABLE IF NOT EXISTS wc_settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
    INSERT INTO wc_settings (key,value) VALUES
      ('stake_per_match','5.00'),
      ('starting_balance','100.00'),
      ('group_name','جروب الشباب')
    ON CONFLICT (key) DO NOTHING;
    CREATE TABLE IF NOT EXISTS wc_player_odds (
      match_id TEXT NOT NULL REFERENCES wc_matches(id) ON DELETE CASCADE,
      player_name TEXT NOT NULL,
      market TEXT NOT NULL,
      odds NUMERIC(6,3) NOT NULL,
      updated_at TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (match_id, player_name, market)
    );
    CREATE TABLE IF NOT EXISTS wc_match_goals (
      id SERIAL PRIMARY KEY,
      match_id TEXT NOT NULL REFERENCES wc_matches(id) ON DELETE CASCADE,
      minute INTEGER,
      scorer_name TEXT NOT NULL,
      team TEXT,
      is_own_goal BOOLEAN DEFAULT FALSE,
      is_penalty BOOLEAN DEFAULT FALSE
    );
  `);

  await pool.query(`GRANT SELECT, INSERT, UPDATE ON TABLE wc_player_odds TO urbanpadel_app`);
  await pool.query(`GRANT SELECT, INSERT, UPDATE ON TABLE wc_match_goals TO urbanpadel_app`);
  await pool.query(`GRANT USAGE, SELECT ON SEQUENCE wc_match_goals_id_seq TO urbanpadel_app`);

  const { rows } = await pool.query('SELECT COUNT(*) FROM wc_matches');
  if (rows[0].count === '0') {
    for (const m of SEED_MATCHES) {
      await pool.query(
        `INSERT INTO wc_matches (id,stage,grp,home_team,away_team,home_flag,away_flag,kickoff,venue,home_odds,draw_odds,away_odds)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) ON CONFLICT DO NOTHING`,
        [m.id, m.stage, m.grp, m.h, m.a, m.hf, m.af, m.ko, m.venue, m.ho, m.do, m.ao]
      );
    }
    console.log('Seeded', SEED_MATCHES.length, 'matches');
  }
}

// ── Routes ────────────────────────────────────────────────────────────────────

// Register / login  (multi-step: phone → name? → pin)
app.post('/wc/auth', async (req, res) => {
  try {
    const { phone, name, pin } = req.body;
    if (!phone || !phone.trim()) return res.status(400).json({ error: 'Phone required' });
    const phoneClean = phone.trim();

    const existing = await pool.query('SELECT * FROM wc_players WHERE phone=$1', [phoneClean]);

    if (existing.rows.length > 0) {
      const player = existing.rows[0];

      // Step: PIN provided — verify or set
      if (pin !== undefined && pin !== null) {
        const pinStr = String(pin).trim();
        if (!player.pin) {
          // First-time PIN setup for this existing user
          await pool.query('UPDATE wc_players SET pin=$1 WHERE id=$2', [pinStr, player.id]);
          const isAdmin = isAdminPhone(phoneClean);
          return res.json({ player: { ...player, pin: pinStr }, token: makeToken(player.id), isAdmin });
        }
        if (pinStr !== String(player.pin)) {
          return res.status(401).json({ error: 'Wrong PIN' });
        }
        // PIN correct
        const isAdmin = isAdminPhone(phoneClean);
        return res.json({ player, token: makeToken(player.id), isAdmin });
      }

      // Step: only phone — ask for PIN
      return res.json({ needsPin: true, setupPin: !player.pin });
    }

    // New player
    if (pin !== undefined && pin !== null && name && name.trim()) {
      // Full registration: name + PIN together
      const startBal = await getSetting('starting_balance', '100.00');
      const { rows } = await pool.query(
        'INSERT INTO wc_players (name,phone,balance,pin) VALUES ($1,$2,$3,$4) RETURNING *',
        [name.trim(), phoneClean, parseFloat(startBal), String(pin).trim()]
      );
      const player = rows[0];
      const isAdmin = isAdminPhone(phoneClean);
      return res.json({ player, token: makeToken(player.id), isAdmin });
    }

    if (name && name.trim()) {
      // Name registered but no PIN yet — save player (no PIN), then ask for PIN setup
      const startBal = await getSetting('starting_balance', '100.00');
      await pool.query(
        'INSERT INTO wc_players (name,phone,balance) VALUES ($1,$2,$3) ON CONFLICT (phone) DO NOTHING',
        [name.trim(), phoneClean, parseFloat(startBal)]
      );
      return res.json({ needsPin: true, setupPin: true });
    }

    // No name provided for new player
    return res.status(400).json({ error: 'Name required for registration', needsName: true });

  } catch (e) {
    console.error(e);
    res.status(500).json({ error: e.message });
  }
});

// Get all matches
app.get('/wc/matches', async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM wc_matches ORDER BY kickoff ASC');
    res.json(rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get player info + predictions
app.get('/wc/me', auth, async (req, res) => {
  try {
    const player = await getPlayer(req.playerId);
    if (!player) return res.status(404).json({ error: 'Not found' });
    const { rows: preds } = await pool.query(
      'SELECT * FROM wc_predictions WHERE player_id=$1', [req.playerId]
    );
    const isAdmin = isAdminPhone(player.phone);
    res.json({ player, predictions: preds, isAdmin });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Submit prediction
app.post('/wc/predict', auth, async (req, res) => {
  try {
    const { matchId, prediction } = req.body;
    const KO_MARKETS = ['BTTS-Y','BTTS-N','OVER2.5','UNDER2.5','DNB1','DNB2'];
    const isKOMarket = KO_MARKETS.includes(prediction) || prediction.startsWith('ANYTIME:') || prediction.startsWith('FIRST:');
    const validStandard = ['1','X','2','1X','X2','12'].includes(prediction);
    if (!validStandard && !isKOMarket) return res.status(400).json({ error: 'Invalid prediction' });

    const { rows: mRows } = await pool.query('SELECT * FROM wc_matches WHERE id=$1', [matchId]);
    if (!mRows.length) return res.status(404).json({ error: 'Match not found' });
    const match = mRows[0];

    // Deadline = 5 min before kickoff
    const deadline = new Date(match.kickoff).getTime() - 5 * 60 * 1000;
    if (Date.now() > deadline) return res.status(400).json({ error: 'Prediction deadline passed' });

    const stake = parseFloat(await getSetting('stake_per_match', '5.00'));
    const player = await getPlayer(req.playerId);
    if (player.balance < stake) return res.status(400).json({ error: 'Insufficient balance' });

    const bh = parseFloat(match.home_odds), bd = parseFloat(match.draw_odds), ba = parseFloat(match.away_odds);
    const oddsAtBet = {
      '1': bh, 'X': bd, '2': ba,
      '1X': parseFloat(match.odds_1x) || (bh*bd)/(bh+bd),
      'X2': parseFloat(match.odds_x2) || (bd*ba)/(bd+ba),
      '12': (bh*ba)/(bh+ba),
      'BTTS-Y': parseFloat(match.odds_btts_yes) || 1.85,
      'BTTS-N': parseFloat(match.odds_btts_no) || 1.85,
      'OVER2.5': parseFloat(match.odds_over25) || 1.85,
      'UNDER2.5': parseFloat(match.odds_under25) || 1.85,
      'DNB1': parseFloat(match.odds_dnb_home) || bh,
      'DNB2': parseFloat(match.odds_dnb_away) || ba,
    };
    let oddsLocked = oddsAtBet[prediction];
    if (oddsLocked == null && (prediction.startsWith('ANYTIME:') || prediction.startsWith('FIRST:'))) {
      const market = prediction.startsWith('ANYTIME:') ? 'anytime' : 'first';
      const playerName = prediction.split(':').slice(1).join(':');
      const { rows: poRows } = await pool.query(
        'SELECT odds FROM wc_player_odds WHERE match_id=$1 AND player_name=$2 AND market=$3',
        [matchId, playerName, market]
      );
      oddsLocked = poRows.length ? parseFloat(poRows[0].odds) : 5.0;
    }
    if (!oddsLocked) oddsLocked = bh;

    // For KO markets, upsert by (player_id, match_id, prediction)
    const existing = await pool.query(
      'SELECT * FROM wc_predictions WHERE player_id=$1 AND match_id=$2 AND prediction=$3',
      [req.playerId, matchId, prediction]
    );

    if (existing.rows.length > 0) {
      if (existing.rows[0].settled) return res.status(400).json({ error: 'Match already settled' });
      await pool.query(
        'UPDATE wc_predictions SET odds_locked=$1 WHERE player_id=$2 AND match_id=$3 AND prediction=$4',
        [oddsLocked, req.playerId, matchId, prediction]
      );
    } else {
      await pool.query('UPDATE wc_players SET balance=balance-$1 WHERE id=$2', [stake, req.playerId]);
      await pool.query(
        'INSERT INTO wc_predictions (player_id,match_id,prediction,stake,odds_locked) VALUES ($1,$2,$3,$4,$5)',
        [req.playerId, matchId, prediction, stake, oddsLocked]
      );
    }

    const { rows: updated } = await pool.query('SELECT balance FROM wc_players WHERE id=$1', [req.playerId]);
    res.json({ ok: true, newBalance: updated[0].balance });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: e.message });
  }
});

// Leaderboard
app.get('/wc/leaderboard', async (req, res) => {
  try {
    const { rows: sRows } = await pool.query("SELECT value FROM wc_settings WHERE key='starting_balance'");
    const startBal = parseFloat(sRows[0]?.value || '100');
    const { rows } = await pool.query(`
      SELECT id, name,
        ROUND(balance,2) as balance,
        ROUND(balance - $1, 2) as profit,
        (SELECT COUNT(*) FROM wc_predictions p WHERE p.player_id=pl.id AND p.settled=true AND p.payout>0) as wins,
        (SELECT COUNT(*) FROM wc_predictions p WHERE p.player_id=pl.id AND p.settled=true) as played,
        (SELECT COUNT(*) FROM wc_predictions p WHERE p.player_id=pl.id) as total,
        COALESCE((SELECT SUM(payout - stake) FROM wc_predictions p WHERE p.player_id=pl.id AND p.settled=true AND p.payout>0),0) as winnings
      FROM wc_players pl
      ORDER BY winnings DESC, balance DESC, name ASC
    `, [startBal]);
    res.json(rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Public: player's confirmed bets for past-deadline matches (transparency)
app.get('/wc/player/:id/predictions', async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT p.match_id, p.prediction, p.settled, p.payout, p.stake,
             m.home_team, m.away_team, m.kickoff, m.result,
             m.home_score, m.away_score, m.stage
      FROM wc_predictions p
      JOIN wc_matches m ON m.id = p.match_id
      WHERE p.player_id = $1
        AND (m.settled = true OR m.kickoff <= NOW() + INTERVAL '5 minutes')
      ORDER BY m.kickoff ASC
    `, [req.params.id]);
    res.json(rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── ADMIN routes ──────────────────────────────────────────────────────────────
function adminAuth(req, res, next) {
  const id = verifyToken(req.headers.authorization || '');
  if (!id) return res.status(401).json({ error: 'Unauthorized' });
  req.playerId = id;
  // Check if admin
  pool.query('SELECT phone FROM wc_players WHERE id=$1', [id]).then(({ rows }) => {
    if (!rows.length || !isAdminPhone(rows[0].phone)) {
      return res.status(403).json({ error: 'Admin only' });
    }
    next();
  }).catch(e => res.status(500).json({ error: e.message }));
}

// Set match result & settle predictions
app.post('/wc/admin/result', adminAuth, async (req, res) => {
  try {
    const { matchId, homeScore, awayScore, homeTeam, awayTeam } = req.body;
    if (homeScore == null || awayScore == null) return res.status(400).json({ error: 'Scores required' });
    const info = await settleMatchById(matchId, homeScore, awayScore, homeTeam, awayTeam);
    res.json({ ok: true, ...info });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: e.message });
  }
});

// Update match (teams, odds, kickoff)
app.put('/wc/admin/match/:id', adminAuth, async (req, res) => {
  try {
    const { homeTeam, awayTeam, homeFlag, awayFlag, homeOdds, drawOdds, awayOdds, kickoff, venue } = req.body;
    await pool.query(
      `UPDATE wc_matches SET
        home_team=COALESCE($1,home_team), away_team=COALESCE($2,away_team),
        home_flag=COALESCE($3,home_flag), away_flag=COALESCE($4,away_flag),
        home_odds=COALESCE($5,home_odds), draw_odds=COALESCE($6,draw_odds), away_odds=COALESCE($7,away_odds),
        kickoff=COALESCE($8::timestamptz,kickoff), venue=COALESCE($9,venue)
       WHERE id=$10`,
      [homeTeam||null, awayTeam||null, homeFlag||null, awayFlag||null,
       homeOdds||null, drawOdds||null, awayOdds||null, kickoff||null, venue||null, req.params.id]
    );
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get all players (admin)
app.get('/wc/admin/players', adminAuth, async (req, res) => {
  try {
    const { rows } = await pool.query(`
      SELECT pl.*,
        (SELECT COUNT(*) FROM wc_predictions p WHERE p.player_id=pl.id) as pred_count,
        (SELECT COUNT(*) FROM wc_predictions p WHERE p.player_id=pl.id AND p.settled=true AND p.payout>0) as wins
      FROM wc_players pl ORDER BY balance DESC
    `);
    res.json(rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Adjust player balance / name / pin
app.put('/wc/admin/player/:id', adminAuth, async (req, res) => {
  try {
    const { balance, name, pin } = req.body;
    await pool.query(
      'UPDATE wc_players SET balance=COALESCE($1,balance), name=COALESCE($2,name), pin=COALESCE($3,pin) WHERE id=$4',
      [balance != null ? parseFloat(balance) : null, name||null, pin != null ? String(pin) : null, req.params.id]
    );
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Delete player
app.delete('/wc/admin/player/:id', adminAuth, async (req, res) => {
  try {
    await pool.query('DELETE FROM wc_predictions WHERE player_id=$1', [req.params.id]);
    await pool.query('DELETE FROM wc_players WHERE id=$1', [req.params.id]);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Public settings (stake_per_match, starting_balance)
app.get("/wc/settings", async (req, res) => {
  try {
    const { rows } = await pool.query("SELECT key,value FROM wc_settings WHERE key IN ('stake_per_match','starting_balance')");
    const s = {}; rows.forEach(r => s[r.key] = r.value);
    res.json(s);
  } catch(e) { res.status(500).json({error:e.message}); }
});

// Get / update settings
app.get('/wc/admin/settings', adminAuth, async (req, res) => {
  try {
    const { rows } = await pool.query('SELECT * FROM wc_settings');
    const s = {};
    rows.forEach(r => s[r.key] = r.value);
    res.json(s);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.put('/wc/admin/settings', adminAuth, async (req, res) => {
  try {
    for (const [key, value] of Object.entries(req.body)) {
      await pool.query(
        'INSERT INTO wc_settings (key,value) VALUES ($1,$2) ON CONFLICT (key) DO UPDATE SET value=$2',
        [key, String(value)]
      );
    }
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Reopen a settled match (undo result)
app.delete('/wc/admin/result/:matchId', adminAuth, async (req, res) => {
  try {
    const { matchId } = req.params;
    // Refund all settled predictions
    const { rows: preds } = await pool.query(
      'SELECT * FROM wc_predictions WHERE match_id=$1 AND settled=true', [matchId]
    );
    for (const p of preds) {
      if (p.payout > 0) {
        await pool.query('UPDATE wc_players SET balance=balance-$1 WHERE id=$2', [p.payout, p.player_id]);
      }
      // Refund original stake for losses
      if (!p.payout || p.payout === 0) {
        await pool.query('UPDATE wc_players SET balance=balance+$1 WHERE id=$2', [p.stake, p.player_id]);
      }
      await pool.query('UPDATE wc_predictions SET settled=false, payout=null WHERE id=$1', [p.id]);
    }
    await pool.query(
      'UPDATE wc_matches SET settled=false, result=null, home_score=null, away_score=null WHERE id=$1',
      [matchId]
    );
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── Auto-fetch results from football-data.org ─────────────────────────────────
// Map our team names → football-data.org names (where they differ)
const FDO_NAME_MAP = {
  'USA':             'United States',
  'Ivory Coast':     "Côte d'Ivoire",
  'Bosnia & Herz.':  'Bosnia and Herzegovina',
  'DR Congo':        'DR Congo',
  'South Korea':     'Korea Republic',
  'Czechia':         'Czech Republic',
  'Türkiye':         'Türkiye',
  'Cape Verde':      'Cabo Verde',
  'Curaçao':         'Curaçao',
};

function toFDOName(name) {
  return FDO_NAME_MAP[name] || name;
}

function fetchJSON(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch (e) { reject(new Error('JSON parse error: ' + data.slice(0, 200))); }
      });
    });
    req.on('error', reject);
    req.setTimeout(10000, () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// ── KO market settlement helper ───────────────────────────────────────────────
function settleKOPrediction(prediction, homeScore, awayScore, goalScorers = []) {
  const total = homeScore + awayScore;
  const homeScoredAny = homeScore > 0;
  const awayScoredAny = awayScore > 0;
  if (prediction === 'BTTS-Y') return { won: homeScoredAny && awayScoredAny, refund: false };
  if (prediction === 'BTTS-N') return { won: !(homeScoredAny && awayScoredAny), refund: false };
  if (prediction === 'OVER2.5') return { won: total > 2, refund: false };
  if (prediction === 'UNDER2.5') return { won: total < 3, refund: false };
  if (prediction === 'DNB1') {
    if (homeScore > awayScore) return { won: true, refund: false };
    if (homeScore === awayScore) return { won: false, refund: true };
    return { won: false, refund: false };
  }
  if (prediction === 'DNB2') {
    if (awayScore > homeScore) return { won: true, refund: false };
    if (homeScore === awayScore) return { won: false, refund: true };
    return { won: false, refund: false };
  }
  if (prediction.startsWith('ANYTIME:')) {
    const name = prediction.slice(8).toLowerCase().trim();
    return { won: goalScorers.some(g => !g.is_own_goal && g.scorer_name.toLowerCase().trim() === name), refund: false };
  }
  if (prediction.startsWith('FIRST:')) {
    const name = prediction.slice(6).toLowerCase().trim();
    const nonOG = goalScorers.filter(g => !g.is_own_goal).sort((a,b) => (a.minute||999)-(b.minute||999));
    return { won: nonOG.length > 0 && nonOG[0].scorer_name.toLowerCase().trim() === name, refund: false };
  }
  return null;
}

// Extracted settle logic (shared by admin route + auto-fetch)
async function settleMatchById(matchId, homeScore, awayScore, homeTeam, awayTeam) {
  const result = homeScore > awayScore ? '1' : awayScore > homeScore ? '2' : 'X';
  await pool.query(
    `UPDATE wc_matches SET home_score=$1, away_score=$2, result=$3, settled=true,
     home_team=COALESCE($4, home_team), away_team=COALESCE($5, away_team)
     WHERE id=$6`,
    [homeScore, awayScore, result, homeTeam || null, awayTeam || null, matchId]
  );
  const { rows: mRows } = await pool.query('SELECT * FROM wc_matches WHERE id=$1', [matchId]);
  const match = mRows[0];
  const h = parseFloat(match.home_odds), d = parseFloat(match.draw_odds), a = parseFloat(match.away_odds);
  // Double-chance odds computed from 1X2 (harmonic combination)
  const oddsMap = {
    '1': h, 'X': d, '2': a,
    '1X': (h * d) / (h + d),
    'X2': (d * a) / (d + a),
    '12': (h * a) / (h + a),
  };
  function isWon(pred, res) {
    if (pred === res) return true;
    if (pred === '1X') return res === '1' || res === 'X';
    if (pred === 'X2') return res === 'X' || res === '2';
    if (pred === '12') return res === '1' || res === '2';
    return false;
  }
  const { rows: preds } = await pool.query(
    'SELECT * FROM wc_predictions WHERE match_id=$1 AND settled=false', [matchId]
  );
  const KO_MARKETS_SET = ['BTTS-Y','BTTS-N','OVER2.5','UNDER2.5','DNB1','DNB2'];
  const { rows: goals } = await pool.query('SELECT * FROM wc_match_goals WHERE match_id=$1 ORDER BY minute ASC', [matchId]);
  for (const p of preds) {
    const isPKOMarket = KO_MARKETS_SET.includes(p.prediction) || p.prediction.startsWith('ANYTIME:') || p.prediction.startsWith('FIRST:');
    if (isPKOMarket) {
      const koResult = settleKOPrediction(p.prediction, homeScore, awayScore, goals);
      if (!koResult) continue;
      const betOdds = parseFloat(p.odds_locked) || 1.85;
      let payout;
      if (koResult.refund) {
        payout = parseFloat(p.stake);
      } else {
        payout = koResult.won ? parseFloat(p.stake) * betOdds : 0;
      }
      await pool.query('UPDATE wc_predictions SET settled=true, payout=$1 WHERE id=$2', [payout, p.id]);
      if (payout > 0) {
        await pool.query('UPDATE wc_players SET balance=balance+$1 WHERE id=$2', [payout, p.player_id]);
      }
    } else {
      const won = isWon(p.prediction, result);
      const betOdds = parseFloat(p.odds_locked) || oddsMap[p.prediction] || oddsMap[result];
      const payout = won ? parseFloat(p.stake) * betOdds : 0;
      await pool.query('UPDATE wc_predictions SET settled=true, payout=$1 WHERE id=$2', [payout, p.id]);
      if (won) {
        await pool.query('UPDATE wc_players SET balance=balance+$1 WHERE id=$2', [payout, p.player_id]);
      }
    }
  }
  return { result, settled: preds.length };
}

async function autoFetchResults() {
  if (!FDO_KEY) return; // No key configured — skip silently
  try {
    // Find group-stage matches that ended 120+ mins ago and aren't settled
    const cutoff = new Date(Date.now() - 120 * 60 * 1000).toISOString();
    const { rows: pending } = await pool.query(
      `SELECT * FROM wc_matches WHERE settled=false AND kickoff < $1 ORDER BY kickoff ASC`,
      [cutoff]
    );
    if (!pending.length) return;

    // Fetch all finished WC2026 matches from football-data.org
    const url = 'https://api.football-data.org/v4/competitions/WC/matches?season=2026&status=FINISHED';
    const { status, body } = await fetchJSON(url, { 'X-Auth-Token': FDO_KEY });
    if (status !== 200) {
      console.warn(`[auto-fetch] football-data.org returned ${status}:`, body?.message || '');
      return;
    }

    const fdoMatches = body.matches || [];

    for (const pm of pending) {
      const koTime = new Date(pm.kickoff).getTime();
      const homeNameFDO = toFDOName(pm.home_team);
      const awayNameFDO = toFDOName(pm.away_team);

      // Match by kickoff date + team names
      const fdoMatch = fdoMatches.find(fm => {
        if (fm.status !== 'FINISHED') return false;
        const fdoKo = new Date(fm.utcDate).getTime();
        // Within 3 hours of our stored kickoff (handles schedule adjustments)
        if (Math.abs(fdoKo - koTime) > 3 * 3600 * 1000) return false;
        const fh = fm.homeTeam?.name || '';
        const fa = fm.awayTeam?.name || '';
        return (fh.includes(homeNameFDO) || homeNameFDO.includes(fh) ||
                fh.toLowerCase() === homeNameFDO.toLowerCase()) &&
               (fa.includes(awayNameFDO) || awayNameFDO.includes(fa) ||
                fa.toLowerCase() === awayNameFDO.toLowerCase());
      });

      if (!fdoMatch) continue;

      const hs = fdoMatch.score?.fullTime?.home;
      const as_ = fdoMatch.score?.fullTime?.away;
      if (hs == null || as_ == null) continue;

      const info = await settleMatchById(pm.id, hs, as_, pm.home_team, pm.away_team);
      console.log(`[auto-fetch] Settled ${pm.id} (${pm.home_team} ${hs}-${as_} ${pm.away_team}) → ${info.result}, ${info.settled} predictions`);

      // If KO match, fetch goal events from football-data.org
      if (pm.stage !== 'group' && FDO_KEY) {
        try {
          const detail = await fetchJSON(`https://api.football-data.org/v4/matches/${fdoMatch.id}`, {'X-Auth-Token': FDO_KEY});
          if (detail.status === 200 && detail.body.goals) {
            await pool.query('DELETE FROM wc_match_goals WHERE match_id=$1', [pm.id]);
            for (const g of detail.body.goals) {
              await pool.query(
                'INSERT INTO wc_match_goals (match_id, minute, scorer_name, team, is_own_goal, is_penalty) VALUES ($1,$2,$3,$4,$5,$6)',
                [pm.id, g.minute, g.scorer?.name || 'Unknown', g.team?.name || '', g.type === 'OWN', g.type === 'PENALTY']
              );
            }
          }
        } catch (goalErr) {
          console.warn(`[auto-fetch] Goal fetch failed for ${pm.id}:`, goalErr.message);
        }
      }
    }
  } catch (e) {
    console.error('[auto-fetch] Error:', e.message);
  }
}

// ── Auto-fetch odds from The Odds API ─────────────────────────────────────────
// Map Odds API team names → our DB names (where they differ)
const ODDS_NAME_MAP = {
  'United States':             'USA',
  "Côte d'Ivoire":             'Ivory Coast',
  'Cote d\'Ivoire':            'Ivory Coast',
  'Korea Republic':            'South Korea',
  'Republic of Korea':         'South Korea',
  'Bosnia and Herzegovina':    'Bosnia & Herz.',
  'Turkey':                    'Türkiye',
  'Curacao':                   'Curaçao',
  'Cape Verde Islands':        'Cape Verde',
  'Congo DR':                  'DR Congo',
  'Congo - Kinshasa':          'DR Congo',
  'New Zealand':               'New Zealand',
  'Saudi Arabia':              'Saudi Arabia',
};

function fromOddsName(n) { return ODDS_NAME_MAP[n] || n; }

function teamsMatch(dbName, apiName) {
  if (!dbName || !apiName) return false;
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  const a = norm(dbName), b = norm(fromOddsName(apiName));
  return a === b || a.includes(b) || b.includes(a);
}

async function autoFetchOdds() {
  if (!ODDS_KEY) return;
  try {
    const url = `https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/?apiKey=${ODDS_KEY}&regions=eu,uk&markets=h2h&oddsFormat=decimal&dateFormat=iso`;
    const { status, body } = await fetchJSON(url, {});
    if (status !== 200) {
      console.warn(`[odds-fetch] The Odds API returned ${status}:`, body?.message || JSON.stringify(body).slice(0,120));
      return;
    }
    if (!body || !body.length) {
      console.log('[odds-fetch] No upcoming matches with odds yet');
      return;
    }

    const { rows: dbMatches } = await pool.query(
      'SELECT * FROM wc_matches WHERE settled=false ORDER BY kickoff ASC'
    );

    let updated = 0;
    for (const event of body) {
      if (!event.bookmakers?.length) continue;
      const eventTime = new Date(event.commence_time).getTime();

      // Find matching DB match: kickoff within ±3h + both team names match
      const match = dbMatches.find(m => {
        const diff = Math.abs(new Date(m.kickoff).getTime() - eventTime);
        if (diff > 3 * 3600 * 1000) return false;
        return (teamsMatch(m.home_team, event.home_team) && teamsMatch(m.away_team, event.away_team))
            || (teamsMatch(m.home_team, event.away_team) && teamsMatch(m.away_team, event.home_team));
      });
      if (!match) continue;

      // Determine orientation (API home might be our away)
      const flipped = teamsMatch(match.home_team, event.away_team);

      // Collect odds from all bookmakers, average them
      const homeArr = [], drawArr = [], awayArr = [];
      for (const bm of event.bookmakers) {
        const h2h = bm.markets?.find(m => m.key === 'h2h');
        if (!h2h) continue;
        for (const outcome of h2h.outcomes) {
          if (outcome.name === 'Draw') {
            drawArr.push(outcome.price);
          } else if (teamsMatch(flipped ? match.away_team : match.home_team, outcome.name)) {
            homeArr.push(outcome.price);
          } else {
            awayArr.push(outcome.price);
          }
        }
      }
      if (!homeArr.length || !drawArr.length || !awayArr.length) continue;

      const avg = arr => (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
      await pool.query(
        'UPDATE wc_matches SET home_odds=$1, draw_odds=$2, away_odds=$3 WHERE id=$4',
        [avg(homeArr), avg(drawArr), avg(awayArr), match.id]
      );
      updated++;

      // For KO matches, also fetch event-specific markets
      if (match.stage !== 'group' && event.id) {
        try {
          const evUrl = `https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events/${event.id}/odds/?apiKey=${ODDS_KEY}&regions=eu,uk&markets=btts,totals,draw_no_bet,double_chance,player_goal_scorer_anytime,player_first_goal_scorer&oddsFormat=decimal`;
          const evRes = await fetchJSON(evUrl, {});
          if (evRes.status === 200 && evRes.body.bookmakers) {
            const bms = evRes.body.bookmakers;
            // BTTS
            const bttsY = [], bttsN = [];
            // Totals 2.5
            const over25 = [], under25 = [];
            // DNB
            const dnbHome = [], dnbAway = [];
            // Player markets
            const playerAnytime = {}, playerFirst = {};

            for (const bm of bms) {
              for (const mkt of (bm.markets || [])) {
                if (mkt.key === 'btts') {
                  for (const o of mkt.outcomes) {
                    if (o.name === 'Yes') bttsY.push(o.price);
                    else if (o.name === 'No') bttsN.push(o.price);
                  }
                } else if (mkt.key === 'totals') {
                  // Find outcomes closest to 2.5
                  const line25 = mkt.outcomes.filter(o => Math.abs((o.point||0) - 2.5) < 0.01);
                  for (const o of line25) {
                    if (o.name === 'Over') over25.push(o.price);
                    else if (o.name === 'Under') under25.push(o.price);
                  }
                  // fallback: if no exact 2.5, find closest
                  if (!line25.length) {
                    const points = [...new Set(mkt.outcomes.map(o => o.point||0))];
                    const closest = points.reduce((a, b) => Math.abs(b-2.5) < Math.abs(a-2.5) ? b : a, points[0]);
                    for (const o of mkt.outcomes.filter(o => (o.point||0) === closest)) {
                      if (o.name === 'Over') over25.push(o.price);
                      else if (o.name === 'Under') under25.push(o.price);
                    }
                  }
                } else if (mkt.key === 'draw_no_bet') {
                  for (const o of mkt.outcomes) {
                    if (teamsMatch(flipped ? match.away_team : match.home_team, o.name)) dnbHome.push(o.price);
                    else if (teamsMatch(flipped ? match.home_team : match.away_team, o.name)) dnbAway.push(o.price);
                  }
                } else if (mkt.key === 'player_goal_scorer_anytime') {
                  for (const o of mkt.outcomes) {
                    const pname = o.description || o.name;
                    if (!playerAnytime[pname]) playerAnytime[pname] = [];
                    playerAnytime[pname].push(o.price);
                  }
                } else if (mkt.key === 'player_first_goal_scorer') {
                  for (const o of mkt.outcomes) {
                    const pname = o.description || o.name;
                    if (!playerFirst[pname]) playerFirst[pname] = [];
                    playerFirst[pname].push(o.price);
                  }
                }
              }
            }

            const avg = arr => arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : null;
            const avgBttsY = avg(bttsY), avgBttsN = avg(bttsN);
            const avgOver = avg(over25), avgUnder = avg(under25);
            const avgDnbH = avg(dnbHome), avgDnbA = avg(dnbAway);

            // Update match odds columns
            await pool.query(
              `UPDATE wc_matches SET
                odds_btts_yes=COALESCE($1,odds_btts_yes),
                odds_btts_no=COALESCE($2,odds_btts_no),
                odds_over25=COALESCE($3,odds_over25),
                odds_under25=COALESCE($4,odds_under25),
                odds_dnb_home=COALESCE($5,odds_dnb_home),
                odds_dnb_away=COALESCE($6,odds_dnb_away)
              WHERE id=$7`,
              [
                avgBttsY ? avgBttsY.toFixed(3) : null,
                avgBttsN ? avgBttsN.toFixed(3) : null,
                avgOver ? avgOver.toFixed(3) : null,
                avgUnder ? avgUnder.toFixed(3) : null,
                avgDnbH ? avgDnbH.toFixed(3) : null,
                avgDnbA ? avgDnbA.toFixed(3) : null,
                match.id
              ]
            );

            // Upsert player odds — delete old then insert new
            if (Object.keys(playerAnytime).length || Object.keys(playerFirst).length) {
              await pool.query('DELETE FROM wc_player_odds WHERE match_id=$1', [match.id]);
              for (const [pname, prices] of Object.entries(playerAnytime)) {
                const avgPrice = avg(prices);
                if (avgPrice) {
                  await pool.query(
                    'INSERT INTO wc_player_odds (match_id, player_name, market, odds) VALUES ($1,$2,$3,$4) ON CONFLICT (match_id,player_name,market) DO UPDATE SET odds=$4, updated_at=NOW()',
                    [match.id, pname, 'anytime', avgPrice.toFixed(3)]
                  );
                }
              }
              for (const [pname, prices] of Object.entries(playerFirst)) {
                const avgPrice = avg(prices);
                if (avgPrice) {
                  await pool.query(
                    'INSERT INTO wc_player_odds (match_id, player_name, market, odds) VALUES ($1,$2,$3,$4) ON CONFLICT (match_id,player_name,market) DO UPDATE SET odds=$4, updated_at=NOW()',
                    [match.id, pname, 'first', avgPrice.toFixed(3)]
                  );
                }
              }
            }
          }
        } catch (evErr) {
          console.warn(`[odds-fetch] Event odds failed for ${match.id}:`, evErr.message);
        }
      }
    }

    // Store last update timestamp
    await pool.query(
      "INSERT INTO wc_settings (key,value) VALUES ('odds_last_updated',$1) ON CONFLICT (key) DO UPDATE SET value=$1",
      [new Date().toISOString()]
    );
    console.log(`[odds-fetch] Updated odds for ${updated}/${body.length} matches (${body.length - updated} unmatched)`);
  } catch (e) {
    console.error('[odds-fetch] Error:', e.message);
  }
}

// Get player scorer odds for a match
app.get('/wc/matches/:id/players', async (req, res) => {
  try {
    const { rows } = await pool.query(
      'SELECT player_name, market, odds FROM wc_player_odds WHERE match_id=$1 ORDER BY market, odds ASC',
      [req.params.id]
    );
    res.json(rows);
  } catch(e) { res.status(500).json({error:e.message}); }
});

// ── Start ─────────────────────────────────────────────────────────────────────
initDB().then(() => {
  const PORT = 3002;
  app.listen(PORT, '127.0.0.1', () => {
    console.log(`WC Predictions API on port ${PORT}`);
    if (FDO_KEY) {
      console.log('[auto-fetch] football-data.org key configured — auto-settling results every 5 min');
      autoFetchResults();
      setInterval(autoFetchResults, 5 * 60 * 1000);
    } else {
      console.log('[auto-fetch] No FOOTBALL_DATA_KEY in .env — results must be entered manually');
    }
    if (ODDS_KEY) {
      console.log('[odds-fetch] The Odds API key configured — syncing odds every 6h');
      autoFetchOdds();
      setInterval(autoFetchOdds, 6 * 60 * 60 * 1000);
    } else {
      console.log('[odds-fetch] No ODDS_API_KEY in .env — odds must be set manually');
    }
  });
}).catch(e => {
  console.error('DB init failed:', e);
  process.exit(1);
});
