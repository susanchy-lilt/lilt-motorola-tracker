# Lilt · Motorola Query Tracker

Auto-updating Discourse tracker. Syncs every 4 hours via GitHub Actions.

## Files

- `index.html` — the dashboard (auto-fetches data.json on load)
- `sync.py` — Python script run by GitHub Actions to pull Discourse data
- `data.json` — generated automatically, do not edit by hand
- `.github/workflows/sync.yml` — the schedule that runs sync.py
- `vercel.json` — Vercel hosting config

## Setup (one time)

### 1. Create a GitHub repo
- Go to github.com → New repository
- Name it `lilt-motorola-tracker` (or anything)
- Set it to **Public** (required for free Vercel hosting)
- Upload all these files into the repo

### 2. Add your API credentials as secrets
- In your GitHub repo → Settings → Secrets and variables → Actions
- Click "New repository secret" and add:
  - `DISCOURSE_API_KEY` — your Discourse API key
  - `DISCOURSE_API_USER` — your Discourse username

### 3. Deploy to Vercel
- Go to vercel.com → Add New Project → Import your GitHub repo
- Click Deploy (no config needed)
- You'll get a URL like `https://lilt-motorola-tracker.vercel.app`

### 4. Run the first sync manually
- In your GitHub repo → Actions → "Sync Discourse data" → Run workflow
- This populates data.json immediately (don't wait 4 hours)

### 5. Share the URL with your customer
That's it. The tracker will auto-update every 4 hours from then on.

## Changing the sync frequency
Edit `.github/workflows/sync.yml` and change the cron line:
- Every 4 hours: `0 */4 * * *`
- Every 2 hours: `0 */2 * * *`
- Daily at 9am UTC: `0 9 * * *`
