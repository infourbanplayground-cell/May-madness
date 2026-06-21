require('dotenv').config();
const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

const MATCHPOINT_BASE = 'https://urbanplayground.matchpoint.com.es/api/query';
const API_TOKEN = process.env.MATCHPOINT_API_TOKEN;

if (!API_TOKEN) {
  console.error('MATCHPOINT_API_TOKEN environment variable is required');
  process.exit(1);
}

app.use(cors());
app.use(express.json());

async function proxyToMatchPoint(path, queryParams, res) {
  const url = new URL(`${MATCHPOINT_BASE}${path}`);
  for (const [key, value] of Object.entries(queryParams)) {
    if (value !== undefined && value !== '') {
      url.searchParams.set(key, value);
    }
  }

  try {
    const response = await fetch(url.toString(), {
      headers: { 'X-Api-Token': API_TOKEN }
    });

    const data = await response.json();

    if (response.status === 429) {
      return res.status(429).json({ ok: false, error: 'Daily request limit exceeded' });
    }
    if (response.status === 401) {
      return res.status(401).json({ ok: false, error: 'Invalid or unauthorized API token' });
    }
    if (response.status === 400) {
      return res.status(400).json(data);
    }

    return res.status(response.status).json(data);
  } catch (err) {
    return res.status(502).json({ ok: false, error: 'Failed to reach upstream API' });
  }
}

// GET /api/query/bookings
app.get('/api/query/bookings', async (req, res) => {
  const { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit } = req.query;

  if (!dateFrom || !dateTo) {
    return res.status(400).json({ ok: false, error: 'dateFrom and dateTo are required' });
  }

  await proxyToMatchPoint('/bookings', { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit }, res);
});

// GET /api/query/matches
app.get('/api/query/matches', async (req, res) => {
  const { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit } = req.query;

  if (!dateFrom || !dateTo) {
    return res.status(400).json({ ok: false, error: 'dateFrom and dateTo are required' });
  }

  await proxyToMatchPoint('/matches', { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit }, res);
});

// GET /api/query/activities
app.get('/api/query/activities', async (req, res) => {
  const { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit } = req.query;

  if (!dateFrom || !dateTo) {
    return res.status(400).json({ ok: false, error: 'dateFrom and dateTo are required' });
  }

  await proxyToMatchPoint('/activities', { dateFrom, dateTo, canceled, createdFrom, createdTo, offset, limit }, res);
});

// GET /api/query/customers
app.get('/api/query/customers', async (req, res) => {
  const { entryDateFrom, entryDateTo, offset, limit } = req.query;

  await proxyToMatchPoint('/customers', { entryDateFrom, entryDateTo, offset, limit }, res);
});

// GET /api/query/sales
app.get('/api/query/sales', async (req, res) => {
  const { dateFrom, dateTo, payDateFrom, payDateTo, offset, limit } = req.query;

  if (!dateFrom || !dateTo) {
    return res.status(400).json({ ok: false, error: 'dateFrom and dateTo are required' });
  }

  await proxyToMatchPoint('/sales', { dateFrom, dateTo, payDateFrom, payDateTo, offset, limit }, res);
});

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'urban-padel-api' });
});

app.listen(PORT, () => {
  console.log(`Urban Padel API proxy running on port ${PORT}`);
});
