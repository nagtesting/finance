// /api/video-download.js
// ────────────────────────────────────────────────────────────────────────────
// Streams a market-pulse video from the PRIVATE Vercel Blob store to the
// end user, after validating that the requested (date, mode) pair has a row
// in the `market_videos` Supabase table.
//
// Why this exists:
//   The Vercel Blob store is configured as PRIVATE — raw blob URLs cannot be
//   opened directly. This route fetches the file server-side using the
//   BLOB_READ_WRITE_TOKEN (which only Vercel functions can access) and pipes
//   the bytes back to the user as a video/mp4 download.
//
// URL shape:
//   /api/video-download?mode=pre&date=2026-05-27
//   /api/video-download?mode=post           (defaults date to today IST)
//
// Required env vars on Vercel:
//   SUPABASE_URL
//   SUPABASE_SECRET_KEY  (or SUPABASE_ANON_KEY)
//   BLOB_READ_WRITE_TOKEN
// ────────────────────────────────────────────────────────────────────────────

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY =
  process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_ANON_KEY;
const BLOB_TOKEN = process.env.BLOB_READ_WRITE_TOKEN;

function todayIST() {
  const now = new Date();
  const istMs = now.getTime() + (now.getTimezoneOffset() + 330) * 60_000;
  return new Date(istMs).toISOString().slice(0, 10);
}

export default async function handler(req, res) {
  if (!SUPABASE_URL || !SUPABASE_KEY || !BLOB_TOKEN) {
    return res.status(500).json({
      status: "error",
      message:
        "Server config missing (SUPABASE_URL, SUPABASE_SECRET_KEY, " +
        "BLOB_READ_WRITE_TOKEN all required)",
    });
  }

  // Parse query
  const mode = (req.query.mode || "").toLowerCase();
  if (mode !== "pre" && mode !== "post") {
    return res
      .status(400)
      .json({ status: "error", message: "mode must be 'pre' or 'post'" });
  }
  const date = (req.query.date || todayIST()).trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return res
      .status(400)
      .json({ status: "error", message: "date must be YYYY-MM-DD" });
  }

  // Look up the video_url in market_videos
  const cols = "video_url";
  const supabaseQueryUrl =
    `${SUPABASE_URL}/rest/v1/market_videos` +
    `?select=${encodeURIComponent(cols)}` +
    `&video_type=eq.${encodeURIComponent(mode)}` +
    `&video_date=eq.${encodeURIComponent(date)}` +
    `&limit=1`;

  let blobUrl;
  try {
    const sb = await fetch(supabaseQueryUrl, {
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        Accept: "application/json",
      },
    });
    if (!sb.ok) {
      const body = await sb.text();
      return res.status(502).json({
        status: "error",
        message: `Supabase responded ${sb.status}: ${body.slice(0, 200)}`,
      });
    }
    const rows = await sb.json();
    if (!Array.isArray(rows) || rows.length === 0 || !rows[0].video_url) {
      return res.status(404).json({
        status: "error",
        message: `No ${mode} video found for ${date}`,
      });
    }
    blobUrl = rows[0].video_url;
  } catch (err) {
    return res.status(500).json({
      status: "error",
      message: `Supabase lookup error: ${err.message || err}`,
    });
  }

  // Fetch the private blob with the auth token, stream bytes back to client
  try {
    const blobResp = await fetch(blobUrl, {
      headers: {
        // Vercel Blob's private read API accepts the read-write token in the
        // Authorization header (Bearer scheme).
        Authorization: `Bearer ${BLOB_TOKEN}`,
      },
    });
    if (!blobResp.ok || !blobResp.body) {
      const body = await blobResp.text().catch(() => "");
      return res.status(502).json({
        status: "error",
        message: `Blob fetch failed ${blobResp.status}: ${body.slice(0, 200)}`,
      });
    }

    // Forward the file as a downloadable MP4
    const fileName = `moneyveda-${date}-${mode}.mp4`;
    res.setHeader("Content-Type", "video/mp4");
    res.setHeader(
      "Content-Disposition",
      `attachment; filename="${fileName}"`
    );
    // Forward content-length if upstream provided one
    const cl = blobResp.headers.get("content-length");
    if (cl) res.setHeader("Content-Length", cl);
    // Allow CDN caching — the (mode, date) pair is immutable once written
    res.setHeader(
      "Cache-Control",
      "public, s-maxage=604800, stale-while-revalidate=86400"
    );

    // Pipe the upstream response body to the client. The Web Streams API is
    // available on Vercel Node 20+; readable.pipe is the legacy fallback.
    if (typeof blobResp.body.pipe === "function") {
      // Node-style stream
      blobResp.body.pipe(res);
    } else {
      // Web ReadableStream — drain and write
      const reader = blobResp.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!res.write(Buffer.from(value))) {
          // backpressure: wait for drain
          await new Promise((resolve) => res.once("drain", resolve));
        }
      }
      res.end();
    }
  } catch (err) {
    return res.status(500).json({
      status: "error",
      message: `Stream error: ${err.message || err}`,
    });
  }
}
