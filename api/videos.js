// /api/videos.js
// ────────────────────────────────────────────────────────────────────────────
// Returns today's pre-market and post-market videos for the
// market-pulse.html download UI to render.
//
// ZERO npm DEPENDENCIES — uses the built-in fetch() against Supabase's PostgREST
// API directly, so this works on a Vercel project that has no package.json
// (i.e. a Python-primary repo).
//
// PRIVATE BLOB STORE: the raw video_url from Supabase is NOT accessible
// without an auth token, so we return a download_url that points at
// /api/video-download — a server-side proxy that fetches the private blob
// using the BLOB_READ_WRITE_TOKEN and streams it to the user.
//
// Required env vars on Vercel:
//   SUPABASE_URL
//   SUPABASE_SECRET_KEY (or SUPABASE_ANON_KEY)
// ────────────────────────────────────────────────────────────────────────────

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY;

function todayIST() {
  const now = new Date();
  const istMs = now.getTime() + (now.getTimezoneOffset() + 330) * 60_000;
  return new Date(istMs).toISOString().slice(0, 10);
}

// Rewrite the raw private blob URL to our public proxy route. The website
// shows this URL as the Download MP4 / Preview link, so the user never
// touches the private blob URL directly.
function buildDownloadUrl(videoType, videoDate) {
  return `/api/video-download?mode=${encodeURIComponent(videoType)}&date=${encodeURIComponent(videoDate)}`;
}

function shapeRow(row) {
  if (!row) return null;
  return {
    video_type:   row.video_type,
    video_date:   row.video_date,
    // Rewrite — original `video_url` would be the private blob, useless to
    // browsers. Replace both fields with the public proxy URL so the
    // website's Download and Preview buttons both go through /api/video-download.
    video_url:    buildDownloadUrl(row.video_type, row.video_date),
    download_url: buildDownloadUrl(row.video_type, row.video_date),
    duration_s:   row.duration_s,
    size_bytes:   row.size_bytes,
    generated_at: row.generated_at,
  };
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

    const rows = await r.json();
    const safeRows = Array.isArray(rows) ? rows : [];
    const pre = shapeRow(safeRows.find((x) => x.video_type === "pre"));
    const post = shapeRow(safeRows.find((x) => x.video_type === "post"));

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
