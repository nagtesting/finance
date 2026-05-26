// /api/videos.js
// ────────────────────────────────────────────────────────────────────────────
// Returns today's pre-market and post-market videos for the
// market-pulse.html download UI to render.
//
// ZERO npm DEPENDENCIES — uses the built-in fetch() against Supabase's PostgREST
// API directly, so this works on a Vercel project that has no package.json
// (i.e. a Python-primary repo).
//
// Past videos are auto-deleted by the Render `market-video` cron after
// 4 trading days; this endpoint only reports TODAY.
//
// Required env vars on the Vercel project:
//   SUPABASE_URL          — e.g. https://<project>.supabase.co
//   SUPABASE_SECRET_KEY   — service_role key (or SUPABASE_ANON_KEY — SELECT
//                           on market_videos is allowed under the public RLS
//                           policy, so anon works too)
// ────────────────────────────────────────────────────────────────────────────

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY;

// IST date as YYYY-MM-DD. videos are keyed by IST date so this needs to be
// timezone-correct even when Vercel runs us in a non-IST region.
function todayIST() {
  const now = new Date();
  // 5h30 = 330 min offset from UTC to IST
  const istMs = now.getTime() + (now.getTimezoneOffset() + 330) * 60_000;
  return new Date(istMs).toISOString().slice(0, 10);
}

export default async function handler(req, res) {
  res.setHeader(
    "Cache-Control",
    "s-maxage=60, max-age=30, stale-while-revalidate=120"
  );
  res.setHeader("Content-Type", "application/json; charset=utf-8");

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    return res.status(500).json({
      status: "error",
      message:
        "Supabase env vars not configured on Vercel (SUPABASE_URL and " +
        "SUPABASE_SECRET_KEY/SUPABASE_ANON_KEY required)",
    });
  }

  const today = todayIST();

  // Direct PostgREST query. Same as the Supabase client would issue under the
  // hood. select=cols&filter=eq.value is the standard PostgREST query syntax.
  // Endpoint: GET <SUPABASE_URL>/rest/v1/market_videos?video_date=eq.<today>
  const cols =
    "video_type,video_date,video_url,download_url,duration_s,size_bytes,generated_at";
  const url =
    `${SUPABASE_URL}/rest/v1/market_videos` +
    `?select=${encodeURIComponent(cols)}` +
    `&video_date=eq.${encodeURIComponent(today)}`;

  try {
    const r = await fetch(url, {
      method: "GET",
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        // Accept compact JSON, no count header (we don't need a count)
        Accept: "application/json",
      },
    });

    if (!r.ok) {
      const body = await r.text();
      return res.status(500).json({
        status: "error",
        message: `Supabase responded ${r.status}: ${body.slice(0, 300)}`,
      });
    }

    const rows = await r.json(); // PostgREST returns an array
    const safeRows = Array.isArray(rows) ? rows : [];
    const pre = safeRows.find((x) => x.video_type === "pre") || null;
    const post = safeRows.find((x) => x.video_type === "post") || null;

    return res.status(200).json({
      status: "success",
      today: { pre, post },
    });
  } catch (err) {
    return res.status(500).json({
      status: "error",
      message: (err && err.message) || "Internal error",
    });
  }
}
