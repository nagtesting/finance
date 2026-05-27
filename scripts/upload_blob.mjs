#!/usr/bin/env node
/**
 * upload_blob.mjs ─ private Vercel Blob uploader for the market-video pipeline
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Why this exists:
 *   The Python vercel_blob SDK (v0.4.x) hardcodes `access: public` and cannot
 *   upload to a private Blob store. @vercel/blob (TS/JS) is the only client
 *   that natively supports `access: private`. So we do a hybrid: Python builds
 *   the MP4, this Node helper uploads it, and Python writes the Supabase row.
 *
 * Invocation (from the GitHub Actions workflow):
 *   node scripts/upload_blob.mjs \
 *        --file /tmp/moneyveda-2026-05-27-pre.mp4 \
 *        --path market-pulse/2026-05-27/pre.mp4
 *
 * Required env vars:
 *   BLOB_READ_WRITE_TOKEN
 *
 * Output (stdout):
 *   A single line of JSON: {"url":"…","downloadUrl":"…","pathname":"…",…}
 *   So the wrapping Python step can capture-and-parse it cleanly.
 *
 * Errors go to stderr, non-zero exit code.
 */

import { readFile } from "node:fs/promises";
import { put } from "@vercel/blob";

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--file") out.file = argv[++i];
    else if (a === "--path") out.path = argv[++i];
    else if (a === "--content-type") out.contentType = argv[++i];
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.file || !args.path) {
    console.error(
      "Usage: node upload_blob.mjs --file <local-path> --path <blob-path> [--content-type video/mp4]"
    );
    process.exit(2);
  }
  if (!process.env.BLOB_READ_WRITE_TOKEN) {
    console.error("BLOB_READ_WRITE_TOKEN env var is not set");
    process.exit(2);
  }

  const contentType = args.contentType || "video/mp4";
  const bytes = await readFile(args.file);

  console.error(
    `[upload_blob] Uploading ${(bytes.length / 1024 / 1024).toFixed(2)} MB ` +
      `to '${args.path}' (access=private)…`
  );

  // @vercel/blob picks up BLOB_READ_WRITE_TOKEN from env automatically.
  const blob = await put(args.path, bytes, {
    access: "private",        // ← the entire point of this script
    contentType,
    addRandomSuffix: true,    // unguessable filename; defense in depth
    cacheControlMaxAge: 604800, // 7 days
  });

  console.error(`[upload_blob] ✅ Uploaded → ${blob.url}`);
  // stdout: machine-readable single-line JSON for the Python wrapper
  process.stdout.write(JSON.stringify(blob) + "\n");
}

main().catch((err) => {
  console.error(`[upload_blob] FATAL: ${err && err.message ? err.message : err}`);
  if (err && err.stack) console.error(err.stack);
  process.exit(1);
});
