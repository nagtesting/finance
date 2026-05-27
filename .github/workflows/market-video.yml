# .github/workflows/market-video.yml
# ────────────────────────────────────────────────────────────────────────────
# MoneyVeda Market Pulse — daily 60-second video Shorts pipeline
# ────────────────────────────────────────────────────────────────────────────
# GitHub-hosted ubuntu-latest runners have 7GB RAM, so the full-quality
# 1080×1920 pipeline runs comfortably (Render Starter's 512MB ceiling OOM'd).
#
# Pipeline: Python builds the MP4, a tiny Node helper uploads it to the
# PRIVATE Vercel Blob store (because the Python vercel_blob SDK hardcodes
# access:public and can't talk to private stores), Python writes the row
# to Supabase market_videos and runs retention cleanup.
#
# Schedule:
#   • Cron expression is UTC. Two daily ticks Mon-Fri:
#       02:45 UTC = 08:15 IST  → publishes pre-market video (auto-detected)
#       11:45 UTC = 17:15 IST  → publishes post-market video (auto-detected)
#   • 15 min AFTER each Render commentary cron, giving commentary time to
#     save to Supabase before the video reads it.
#
# Manual trigger: workflow_dispatch — fire from GitHub UI to test on demand.

name: market-video

on:
  schedule:
    # Pre-market: 08:15 IST = 02:45 UTC
    # Post-market: 17:15 IST = 11:45 UTC
    - cron: '45 2,11 * * 1-5'
  workflow_dispatch:        # manual "Run workflow" button in GitHub UI
    inputs:
      mode:
        description: 'Mode to publish (pre/post/auto)'
        required: false
        default: 'auto'
        type: choice
        options:
          - auto
          - pre
          - post
      date:
        description: 'Commentary date YYYY-MM-DD (blank = today IST)'
        required: false
        default: ''

# Don't allow two video runs to overlap if a previous one is still going
concurrency:
  group: market-video
  cancel-in-progress: false

jobs:
  publish-video:
    runs-on: ubuntu-latest
    timeout-minutes: 8        # videos finish in 90-120s; abort if much slower

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Set up Node.js (for @vercel/blob private uploads)
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install ffmpeg (not pre-installed on current ubuntu-latest)
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq ffmpeg
          which ffmpeg
          ffmpeg -version | head -1

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          # Only what video_publisher.py + render_frames.py need.
          # No yfinance / pandas / etc — commentary stack stays on Render.
          pip install \
            supabase \
            google-generativeai \
            python-dotenv \
            requests \
            Pillow \
            qrcode \
            vercel_blob
          # Note: vercel_blob is still needed for the delete() call in
          # retention cleanup. The upload uses @vercel/blob (Node) instead
          # because the Python SDK can't write to private stores.

      - name: Install @vercel/blob (Node SDK for private blob uploads)
        run: |
          npm install --silent --no-save --no-package-lock @vercel/blob
          # Verify the install
          node -e "const b = require('@vercel/blob'); console.log('@vercel/blob put fn:', typeof b.put);"

      - name: Build and publish video
        env:
          SUPABASE_URL:           ${{ secrets.SUPABASE_URL }}
          SUPABASE_SECRET_KEY:    ${{ secrets.SUPABASE_SECRET_KEY }}
          GEMINI_API_KEY:         ${{ secrets.GEMINI_API_KEY }}
          BLOB_READ_WRITE_TOKEN:  ${{ secrets.BLOB_READ_WRITE_TOKEN }}
          PUBLIC_SITE_URL:        https://www.moneyveda.org
        run: |
          # Build the mode/date args from the manual-dispatch inputs (if any).
          # Schedule-triggered runs use auto-detect from IST time.
          ARGS=""
          MODE='${{ github.event.inputs.mode }}'
          DATE='${{ github.event.inputs.date }}'
          if [ -n "$MODE" ] && [ "$MODE" != "auto" ]; then
            ARGS="$ARGS --mode $MODE"
          fi
          if [ -n "$DATE" ]; then
            ARGS="$ARGS --date $DATE"
          fi
          echo "Running: python video_publisher.py $ARGS"
          python video_publisher.py $ARGS
