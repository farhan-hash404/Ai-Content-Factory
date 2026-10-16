#!/usr/bin/env bash
# One-time setup for a Codespaces / Dev Containers checkout of the FULL system
# (the real multi-agent backend, not the recorded demo). ffmpeg is needed for
# audio/video; the Python and Node deps are the project's own.
set -euo pipefail

sudo apt-get update -y
sudo apt-get install -y --no-install-recommends ffmpeg

echo "Installing backend dependencies (this includes torch/whisper — a few minutes)…"
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing frontend dependencies…"
npm --prefix frontend ci || npm --prefix frontend install

cat <<'MSG'

────────────────────────────────────────────────────────────────────────
  Setup complete. To run the FULL live system:

  1. Add your free Gemini key (no card):  https://aistudio.google.com/apikey
       cp .env.example .env
       # edit .env and set GOOGLE_API_KEY=...

  2. Start the backend:
       cd Agents_backend && uvicorn api:app --host 0.0.0.0 --port 8000

  3. In a second terminal, start the frontend:
       cd frontend && npm run dev

  4. Open the forwarded port 3000.

  Free-tier note: Gemini allows 20 requests/day/model; one full run uses
  most of that. See README for details.
────────────────────────────────────────────────────────────────────────
MSG
