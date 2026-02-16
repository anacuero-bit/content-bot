# Content Bot v3.0

AI Content Factory for [tuspapeles2026.es](https://tuspapeles2026.es) — a team-only Telegram bot that generates marketing content via Claude API.

## Features

- **7 content types:** blog, tiktok, carousel, caption, whatsapp, fbpost, story
- **Batch commands:** `/tiktok5`, `/carousel3`, `/captions10`, `/whatsapp5`, `/fbpost5`, `/stories7`
- **Weekly mega-batch:** `/weekly` generates ~46 pieces in one go
- **News monitoring:** `/news` scans Google News RSS for regularización updates
- **One-tap publishing:** Push blog articles to PH-Site or tuspapeles2026 via GitHub API
- **Phase-aware:** Auto-adjusts tone based on campaign phase (pre-BOE / BOE week / apps open / final push)
- **Team-only access:** Restricted to configured Telegram user IDs

## Setup

### 1. Environment Variables

Copy `.env.example` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather |
| `CLAUDE_API_KEY` | API key from console.anthropic.com |
| `TEAM_CHAT_IDS` | Comma-separated Telegram user IDs |
| `GITHUB_TOKEN` | Personal access token with `repo` scope |
| `GITHUB_REPO_PH` | GitHub repo for PH-Site (default: `anacuero-bit/PH-Site`) |
| `GITHUB_REPO_TP` | GitHub repo for tuspapeles2026 (default: `anacuero-bit/tus-papeles-2026`) |

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python main.py
```

### 4. Deploy to Railway

1. Connect this GitHub repo to Railway
2. Add all environment variables from `.env.example`
3. Deploy — the `Procfile` tells Railway to run `python main.py`

## Commands

### Single Generation
| Command | Description |
|---------|-------------|
| `/blog [topic]` | SEO blog article (suggests topics if none given) |
| `/tiktok [topic]` | TikTok script |
| `/carousel [topic]` | Instagram carousel (6-8 slides) |
| `/caption [ig\|fb] [topic]` | Social media caption |
| `/whatsapp [type]` | WhatsApp broadcast message |
| `/fbpost [topic]` | Facebook group post |
| `/story [type]` | Instagram Story concept |

### Batch Generation
| Command | Description |
|---------|-------------|
| `/tiktok5` | 5 TikTok scripts |
| `/carousel3` | 3 carousel sets |
| `/captions10` | 10 social captions |
| `/whatsapp5` | 5 WhatsApp messages |
| `/fbpost5` | 5 Facebook posts |
| `/stories7` | 7 Story concepts |
| `/weekly` | Full weekly pack (~46 pieces) |

### Tools
| Command | Description |
|---------|-------------|
| `/news` | Latest regularización news + content ideas |
| `/topics` | 10 AI-generated topic suggestions |
| `/stats` | Generation statistics |
| `/phase [phase]` | Override campaign phase |
| `/help` | Show all commands |
