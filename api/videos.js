// /api/videos.js
//
// Returns today's pre-market and post-market videos for the
// market-pulse.html download UI to render.
//
// Past videos are auto-deleted by the video pipeline after
// RETENTION_TRADING_DAYS (4 trading days) so this endpoint only
// reports today.
//
// Cached via Vercel's CDN for 60s — videos publish at most twice a day.

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY;

const supabase = (SUPABASE_URL && SUPABASE_KEY)
  ? createClient(SUPABASE_URL, SUPABASE_KEY)
  : null;

function todayIST() {
  const now = new Date();
  const ist = new Date(now.getTime() + (now.getTimezoneOffset() + 330) * 60_000);
  return ist.toISOString().slice(0, 10);
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=60, max-age=30, stale-while-revalidate=120');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  if (!supabase) {
    return res.status(500).json({
      status: 'error',
      message: 'Supabase not configured (SUPABASE_URL / SUPABASE_SECRET_KEY missing)',
    });
  }

  try {
    const today = todayIST();

    const { data, error } = await supabase
      .from('market_videos')
      .select('video_type, video_date, video_url, download_url, duration_s, size_bytes, generated_at')
      .eq('video_date', today);

    if (error) throw error;

    const rows = data || [];
    const pre  = rows.find(r => r.video_type === 'pre')  || null;
    const post = rows.find(r => r.video_type === 'post') || null;

    return res.status(200).json({
      status: 'success',
      today:  { pre, post },
    });
  } catch (err) {
    return res.status(500).json({
      status: 'error',
      message: err.message || 'Internal error',
    });
  }
}
