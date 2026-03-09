# CLAUDE.md

## What This Is
AI-powered Telegram bot that generates marketing content for tuspapeles2026.es (Spain's 2026 extraordinary regularization). Team-only access (restricted to configured Telegram user IDs).

## Features
- 7+ content types: blog articles, video scripts, carousels, images, reels, memes, quotes, WhatsApp messages, Facebook posts
- Batch generation commands (`/video5`, `/carousel3`, `/weekly`)
- Predis.ai integration for branded visuals
- Google News RSS monitoring for regularization updates
- One-tap publishing to tuspapeles2026.es via GitHub API
- Auto-updater via GitHub Actions every 8 hours
- Phase-aware tone and content angle system

## Stack
- Python 3.13
- python-telegram-bot 21.5
- Anthropic Claude API
- Predis.ai (branded content generation)
- Pillow / numpy / ffmpeg (image & video rendering)
- feedparser / beautifulsoup4 / httpx (RSS & scraping)
- APScheduler (scheduled auto-generation)
- Docker (Railway deploy)

## Hosting
- Railway (worker dyno)
- Procfile: `worker: python main.py`

## Env Vars
| Variable | Required | Notes |
|----------|----------|-------|
| TELEGRAM_TOKEN | Yes | Bot token from @BotFather |
| CLAUDE_API_KEY | Yes | Anthropic API key |
| TEAM_CHAT_IDS | Yes | Comma-separated Telegram user IDs |
| GITHUB_TOKEN | Optional | For publishing articles to GitHub repos |
| GITHUB_REPO_PH | Optional | PH-Site repo (default: anacuero-bit/PH-Site) |
| GITHUB_REPO_TP | Optional | tus-papeles-2026 repo (default: anacuero-bit/tus-papeles-2026) |
| CHANNEL_ID | Optional | Telegram channel (default: @tuspapeles2026) |
| PREDIS_API_KEY | Optional | Predis.ai API key |
| PREDIS_BRAND_ID | Optional | Predis.ai brand ID |

## Key Files
| File | Purpose |
|------|---------|
| `main.py` | Bot application (long-running) |
| `auto_update.py` | Autonomous news scanner/article generator (GitHub Actions) |
| `requirements.txt` | Python dependencies |
| `Procfile` | Railway deployment |
| `Dockerfile` | Docker build config |
| `nixpacks.toml` | System packages (ffmpeg, fonts) |
