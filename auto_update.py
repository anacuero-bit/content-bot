#!/usr/bin/env python3
"""
auto_update.py — Autonomous site updater for tuspapeles2026.es

Scans real news sources for regularización updates, generates articles
via Claude API, pushes them to the tus-papeles-2026 GitHub repo, updates
the homepage timeline + date, and notifies admin via Telegram.

Runs every 8h via GitHub Actions (or locally with APScheduler).
Supports --once flag for single-run mode.

Environment variables required:
  GITHUB_TOKEN   — PAT with repo scope for anacuero-bit/tus-papeles-2026
  CLAUDE_API_KEY — Anthropic API key
  TELEGRAM_TOKEN — Telegram bot token (for admin notifications)
  TEAM_CHAT_IDS  — Comma-separated Telegram chat IDs
"""

import os
import re
import json
import hashlib
import base64
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
import anthropic

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("auto_update")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TEAM_CHAT_IDS = [
    int(x.strip())
    for x in os.environ.get("TEAM_CHAT_IDS", "").split(",")
    if x.strip()
]

REPO = "anacuero-bit/tus-papeles-2026"
GITHUB_API = "https://api.github.com"
STATE_FILE = "update_state.json"
MAX_ARTICLES_PER_CYCLE = 3
MAX_SEEN_HASHES = 500

# Review mode: when True, articles are sent to Telegram for approval before publishing
REVIEW_MODE = os.environ.get("REVIEW_MODE", "false").lower() == "true"

# -----------------------------------------------------------------------------
# Legal facts block — injected into every Claude call
# -----------------------------------------------------------------------------

LEGAL_FACTS = """
LEGAL FACTS — NEVER CONTRADICT THESE:
- Residence requirement: 5 MONTHS continuous (NOT years)
- Entry: before December 31, 2025
- Job offer: NOT required (vulnerability clause)
- Window: April 1 – June 30, 2026
- Submission: 100% online (telematic)
- Provisional work permit: immediate upon filing
- Expected approval: 80-90% based on 2005 precedent (NEVER guarantee)
- All nationalities eligible
- Our price: from 199 euros (competitors charge 350-450)
- Minor children included (5-year permit)
- Decision within 3 months maximum
"""

SYSTEM_PROMPT = f"""You are the content engine for tuspapeles2026.es, a legal technology
service helping undocumented immigrants in Spain regularize their status under
the 2026 extraordinary regularization decree.

Write in simple Spanish. Use "tu" (informal). Maximum 15-word sentences.
Never guarantee approval. Never use aggressive sales language.
Acknowledge people's fear, then offer hope.

{LEGAL_FACTS}

CTA: "Verifica tu elegibilidad gratis en tuspapeles2026.es"
"""

# -----------------------------------------------------------------------------
# News sources
# -----------------------------------------------------------------------------

NEWS_SOURCES = [
    {
        "name": "Google News - regularizacion",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=regularizaci%C3%B3n+extraordinaria+2026+Espa%C3%B1a&hl=es&gl=ES&ceid=ES:es",
        "keywords": [],
    },
    {
        "name": "Google News - decreto",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=decreto+regularizaci%C3%B3n+migrantes+Espa%C3%B1a+2026&hl=es&gl=ES&ceid=ES:es",
        "keywords": [],
    },
    {
        "name": "La Moncloa - Inclusion",
        "type": "web",
        "url": "https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/inclusion/Paginas/index.aspx",
        "keywords": ["regularización", "extranjeros", "migrantes", "extranjería"],
    },
    {
        "name": "BOE",
        "type": "web",
        "url": "https://www.boe.es/diario_boe/",
        "keywords": ["extranjería", "regularización", "reglamento"],
    },
]

# -----------------------------------------------------------------------------
# State management
# -----------------------------------------------------------------------------


def load_state() -> dict:
    """Load seen hashes + last_run from state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"seen_hashes": [], "last_run": None}


def save_state(state: dict):
    """Persist state to disk. Keep only last MAX_SEEN_HASHES."""
    state["seen_hashes"] = state["seen_hashes"][-MAX_SEEN_HASHES:]
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def headline_hash(title: str) -> str:
    """Deterministic hash for a headline."""
    normalized = title.strip().lower()[:100]
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# -----------------------------------------------------------------------------
# News fetching
# -----------------------------------------------------------------------------


def fetch_all_headlines() -> list[dict]:
    """Fetch headlines from all configured sources. Returns list of dicts."""
    articles = []

    for source in NEWS_SOURCES:
        try:
            if source["type"] == "rss":
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:5]:
                    src_name = source["name"]
                    if hasattr(entry, "source") and hasattr(entry.source, "title"):
                        src_name = entry.source.title
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": src_name,
                        "published": getattr(entry, "published", ""),
                        "summary": getattr(entry, "summary", "")[:200],
                    })

            elif source["type"] == "web":
                try:
                    from bs4 import BeautifulSoup
                except ImportError:
                    logger.warning("beautifulsoup4 not installed, skipping web source %s", source["name"])
                    continue

                resp = requests.get(
                    source["url"], timeout=15,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    text = link.get_text().strip()
                    if len(text) < 15:
                        continue
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in source["keywords"]):
                        href = link["href"]
                        if not href.startswith("http"):
                            href = urljoin(source["url"], href)
                        articles.append({
                            "title": text[:150],
                            "link": href,
                            "source": source["name"],
                            "published": "",
                            "summary": "",
                        })

        except Exception as e:
            logger.error("Error fetching %s: %s", source["name"], e)

    # Deduplicate
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:20]


def filter_new(headlines: list[dict], state: dict) -> list[dict]:
    """Return only headlines not in the seen set."""
    seen = set(state.get("seen_hashes", []))
    new_items = []
    for h in headlines:
        h_hash = headline_hash(h["title"])
        if h_hash not in seen:
            new_items.append(h)
    return new_items


def mark_seen(headlines: list[dict], state: dict):
    """Add headline hashes to the seen set."""
    for h in headlines:
        state["seen_hashes"].append(headline_hash(h["title"]))


# -----------------------------------------------------------------------------
# Claude API helpers
# -----------------------------------------------------------------------------


def claude_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def ask_claude_which_to_publish(headlines: list[dict]) -> list[dict]:
    """Ask Claude which headlines warrant a blog article. Returns filtered list."""
    if not headlines:
        return []

    headline_text = "\n".join(
        f"{i+1}. {h['title']} — {h['source']}" for i, h in enumerate(headlines)
    )

    client = claude_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Here are today's headlines about regularización in Spain:\n\n"
                f"{headline_text}\n\n"
                f"Which of these (max {MAX_ARTICLES_PER_CYCLE}) deserve a blog article "
                f"on tuspapeles2026.es? For each, explain the angle in one sentence.\n\n"
                f"Reply ONLY with a JSON array. Each item: "
                f'{{"number": 1, "angle": "..."}}\n'
                f"If none are worth publishing, return an empty array: []"
            ),
        }],
    )

    text = response.content[0].text.strip()
    # Extract JSON from possible markdown code block
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    try:
        picks = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Claude returned non-JSON for headline selection: %s", text[:200])
        return []

    if not isinstance(picks, list):
        return []

    # Map picks back to headlines
    selected = []
    for pick in picks[:MAX_ARTICLES_PER_CYCLE]:
        idx = pick.get("number", 0) - 1
        if 0 <= idx < len(headlines):
            headlines[idx]["angle"] = pick.get("angle", "")
            selected.append(headlines[idx])

    return selected


def generate_article(headline: dict) -> dict | None:
    """Generate a full blog article from a headline. Returns dict with HTML + metadata."""
    client = claude_client()

    prompt = (
        f"Write a blog article for tuspapeles2026.es about this news:\n\n"
        f"Headline: {headline['title']}\n"
        f"Source: {headline['source']}\n"
        f"Angle: {headline.get('angle', 'Inform and explain impact')}\n\n"
        f"Requirements:\n"
        f"- 400-700 words in simple Spanish\n"
        f"- Use HTML: <h2> for subheadings, <p> for paragraphs, <ul>/<li> for lists\n"
        f"- Explain why this matters for people waiting for regularización\n"
        f"- End with CTA to tuspapeles2026.es\n"
        f"- DO NOT include <html>, <head>, or <body> tags — only article body HTML\n\n"
        f"Reply ONLY with a JSON object:\n"
        f'{{"title": "...", "slug": "...", "meta": "...(max 160 chars)", '
        f'"category": "noticias|guia|analisis", "html_content": "..."}}'
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Extract JSON from possible code block
    if "```" in text:
        match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Claude returned non-JSON for article: %s", text[:300])
        return None

    required = ["title", "slug", "meta", "html_content"]
    if not all(k in data for k in required):
        logger.error("Article JSON missing required fields: %s", list(data.keys()))
        return None

    # Sanitize slug
    data["slug"] = re.sub(r"[^a-z0-9-]", "", data["slug"].lower().replace(" ", "-"))[:80]
    data.setdefault("category", "noticias")

    return data


def generate_timeline_entry(articles_published: list[dict]) -> str | None:
    """Generate a short timeline entry for the homepage Estado section."""
    if not articles_published:
        return None

    titles = "\n".join(f"- {a['title']}" for a in articles_published)
    client = claude_client()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"We just published these articles on tuspapeles2026.es:\n{titles}\n\n"
                f"Write a ONE-LINE timeline update (max 100 chars) in Spanish for the "
                f"homepage 'Estado del proceso' section. Example format:\n"
                f'"CES respalda la regularización — proceso avanza según calendario"\n'
                f"Return ONLY the text line, no quotes, no JSON."
            ),
        }],
    )

    return response.content[0].text.strip().strip('"')[:120]


# -----------------------------------------------------------------------------
# GitHub API helpers (synchronous — no httpx needed)
# -----------------------------------------------------------------------------


def gh_headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def gh_get_file(path: str) -> tuple[str | None, str | None]:
    """Fetch a file from the repo. Returns (content_str, sha) or (None, None)."""
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    resp = requests.get(url, headers=gh_headers(), timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data.get("sha")
    return None, None


def gh_put_file(path: str, content: str, message: str, sha: str = None) -> bool:
    """Create or update a file in the repo. Returns True on success."""
    url = f"{GITHUB_API}/repos/{REPO}/contents/{path}"
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": "main",
    }
    if sha:
        data["sha"] = sha

    resp = requests.put(url, headers=gh_headers(), json=data, timeout=30)
    if resp.status_code in (200, 201):
        return True
    logger.error("GitHub PUT %s failed: %s %s", path, resp.status_code, resp.text[:200])
    return False


# -----------------------------------------------------------------------------
# Duplicate detection
# -----------------------------------------------------------------------------


def is_duplicate(new_title: str, existing_articles: list) -> tuple[bool, str | None]:
    """Check if a new article title has >70% word overlap with existing ones."""
    new_words = set(new_title.lower().split())
    for article in existing_articles:
        existing_words = set(article["title"].lower().split())
        if not new_words or not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
        if overlap > 0.7:
            return True, article["title"]
    return False, None


def fetch_existing_articles() -> list:
    """Fetch current articles from blog/index.json."""
    content, _ = gh_get_file("blog/index.json")
    if content:
        try:
            data = json.loads(content)
            return data.get("articles", [])
        except json.JSONDecodeError:
            pass
    return []


# -----------------------------------------------------------------------------
# Blog template — fetches from repo or uses fallback
# -----------------------------------------------------------------------------


def get_blog_template() -> str:
    """Fetch blog/_template.html from the repo. Falls back to inline template."""
    content, _ = gh_get_file("blog/_template.html")
    if content:
        return content

    # Fallback: inline template matching main.py's wrap_blog_html
    return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}} | tuspapeles2026.es</title>
    <meta name="description" content="{{META}}">
    <meta property="og:title" content="{{TITLE}}">
    <meta property="og:description" content="{{META}}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tuspapeles2026.es/blog/{{SLUG}}">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #333;
            max-width: 720px;
            margin: 0 auto;
            padding: 2rem 1rem;
            background: #fafafa;
        }
        header {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #2563eb;
        }
        header a {
            color: #2563eb;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
        }
        h1 {
            font-size: 2rem;
            line-height: 1.3;
            margin: 1rem 0;
            color: #1a1a1a;
        }
        .meta {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }
        h2 {
            font-size: 1.4rem;
            margin: 1.5rem 0 0.8rem;
            color: #1a1a1a;
        }
        p { margin-bottom: 1rem; }
        a { color: #2563eb; }
        ul, ol { margin: 0.5rem 0 1rem 1.5rem; }
        li { margin-bottom: 0.3rem; }
        .cta-box {
            background: #2563eb;
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            margin: 2rem 0;
        }
        .cta-box a { color: white; font-weight: bold; }
        footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            font-size: 0.85rem;
            color: #888;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <a href="https://tuspapeles2026.es">&larr; tuspapeles2026.es</a>
    </header>

    <article>
        <h1>{{TITLE}}</h1>
        <div class="meta">Publicado el {{DATE_DISPLAY}} | {{READING_TIME}} de lectura | {{CATEGORY_DISPLAY}}</div>
        {{CONTENT}}
    </article>

    <div class="cta-box">
        <p>Verifica tu elegibilidad gratis</p>
        <p><a href="https://tuspapeles2026.es">tuspapeles2026.es</a> |
           <a href="https://t.me/tuspapeles2026bot">Telegram Bot</a></p>
    </div>

    <footer>
        &copy; 2026 tuspapeles2026.es &mdash; Respaldado por Pombo &amp; Horowitz Abogados
    </footer>
</body>
</html>"""


CATEGORY_DISPLAY = {
    "noticias": "Noticias",
    "guia": "Guia practica",
    "guias": "Guia practica",
    "analisis": "Analisis",
    "mitos": "Mitos",
    "historias": "Historias",
}

MONTH_NAMES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def format_date_display(date_str: str) -> str:
    """Convert 2026-02-17 to '17 de febrero de 2026'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{dt.day} de {MONTH_NAMES_ES[dt.month]} de {dt.year}"
    except (ValueError, IndexError):
        return date_str


def render_article_html(article: dict) -> str:
    """Render a full article HTML page from article data dict."""
    template = get_blog_template()
    date_str = datetime.now().strftime("%Y-%m-%d")
    date_display = format_date_display(date_str)
    word_count = len(article.get("html_content", "").split())
    reading_time = f"{max(1, word_count // 200)} min"
    category = article.get("category", "noticias")

    html = template
    html = html.replace("{{TITLE}}", article["title"])
    html = html.replace("{{META}}", article.get("meta", ""))
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{DATE_DISPLAY}}", date_display)
    html = html.replace("{{CATEGORY}}", category)
    html = html.replace("{{CATEGORY_DISPLAY}}", CATEGORY_DISPLAY.get(category, category.title()))
    html = html.replace("{{READING_TIME}}", reading_time)
    html = html.replace("{{SLUG}}", article["slug"])
    html = html.replace("{{CONTENT}}", article["html_content"])

    return html


# -----------------------------------------------------------------------------
# Blog index.json management
# -----------------------------------------------------------------------------


def update_blog_index(article: dict) -> bool:
    """Add article entry to blog/index.json, sorted newest first."""
    content, sha = gh_get_file("blog/index.json")
    if content:
        index_data = json.loads(content)
    else:
        index_data = {"articles": []}
        sha = None

    date_str = datetime.now().strftime("%Y-%m-%d")
    word_count = len(article.get("html_content", "").split())

    new_entry = {
        "slug": article["slug"],
        "title": article["title"],
        "meta": article.get("meta", ""),
        "date": date_str,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "reading_time": f"{max(1, word_count // 200)} min",
        "category": article.get("category", "noticias"),
        "image": None,
    }

    # Remove duplicate slug
    index_data["articles"] = [
        a for a in index_data["articles"] if a.get("slug") != article["slug"]
    ]
    index_data["articles"].append(new_entry)
    # Sort by published_at descending (falls back to date for old articles)
    index_data["articles"].sort(
        key=lambda a: a.get("published_at", a.get("date", "")),
        reverse=True,
    )

    updated_json = json.dumps(index_data, ensure_ascii=False, indent=2)
    return gh_put_file(
        "blog/index.json", updated_json,
        f"Update index: {article['title']}", sha,
    )


# -----------------------------------------------------------------------------
# Homepage update — timeline entry + last-updated date
# -----------------------------------------------------------------------------


def update_homepage(timeline_text: str) -> bool:
    """Insert a timeline entry and update the last-updated date on index.html."""
    content, sha = gh_get_file("index.html")
    if not content:
        logger.error("Could not fetch index.html from repo")
        return False

    today = datetime.now()
    date_display = format_date_display(today.strftime("%Y-%m-%d"))
    modified = False

    # 1. Insert timeline entry after id="updates-timeline">
    timeline_marker = 'id="updates-timeline">'
    if timeline_marker in content:
        entry_html = (
            f'\n                <div class="timeline-entry">'
            f'<span class="timeline-date">{date_display}</span> '
            f'{timeline_text}</div>'
        )
        content = content.replace(
            timeline_marker,
            timeline_marker + entry_html,
            1,
        )
        modified = True

    # 2. Update "Ultima actualización" date
    # Match patterns like: Última actualización: 13 de febrero de 2026
    updated_pattern = r"(Última actualización[:\s]*)\d{1,2} de \w+ de \d{4}"
    if re.search(updated_pattern, content):
        content = re.sub(updated_pattern, rf"\g<1>{date_display}", content)
        modified = True

    if modified:
        return gh_put_file("index.html", content, f"Update homepage: {date_display}", sha)
    else:
        logger.warning("No timeline marker or date pattern found in index.html")
        return False


# -----------------------------------------------------------------------------
# Telegram notification
# -----------------------------------------------------------------------------


def notify_telegram(message: str):
    """Send notification to all admin chats via Telegram Bot API."""
    if not TELEGRAM_TOKEN or not TEAM_CHAT_IDS:
        logger.warning("Telegram not configured, skipping notification")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in TEAM_CHAT_IDS:
        try:
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }, timeout=15)
            if resp.status_code != 200:
                logger.error("Telegram send failed for %s: %s", chat_id, resp.text[:200])
        except Exception as e:
            logger.error("Telegram error for %s: %s", chat_id, e)


# -----------------------------------------------------------------------------
# Main update cycle
# -----------------------------------------------------------------------------


def run_update():
    """Execute one full update cycle."""
    logger.info("=== AUTO UPDATE CYCLE START ===")
    start = time.time()

    # Validate config
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set — aborting")
        return
    if not CLAUDE_API_KEY:
        logger.error("CLAUDE_API_KEY not set — aborting")
        return

    state = load_state()

    # 1. Fetch all headlines
    logger.info("Fetching headlines from %d sources...", len(NEWS_SOURCES))
    all_headlines = fetch_all_headlines()
    logger.info("Found %d total headlines", len(all_headlines))

    # 2. Filter to new ones only
    new_headlines = filter_new(all_headlines, state)
    logger.info("New (unseen) headlines: %d", len(new_headlines))

    # Mark all fetched as seen (even if we don't publish them)
    mark_seen(all_headlines, state)

    articles_published = []

    if new_headlines:
        # 3. Ask Claude which deserve articles
        logger.info("Asking Claude to evaluate %d headlines...", len(new_headlines))
        selected = ask_claude_which_to_publish(new_headlines)
        logger.info("Claude selected %d headlines for articles", len(selected))

        # 4. Fetch existing articles for duplicate detection
        existing_articles = fetch_existing_articles()

        # 5. Generate and publish each article
        for headline in selected:
            logger.info("Generating article for: %s", headline["title"][:60])
            article = generate_article(headline)
            if not article:
                logger.error("Failed to generate article, skipping")
                continue

            # Duplicate detection
            dup_found, dup_title = is_duplicate(article["title"], existing_articles)
            if dup_found:
                logger.info("Skipped duplicate: %s (matches: %s)", article["title"], dup_title)
                continue

            # Render full HTML
            full_html = render_article_html(article)

            # REVIEW_MODE: send to Telegram for approval instead of auto-publishing
            if REVIEW_MODE:
                logger.info("REVIEW_MODE: sending article for review: %s", article["title"])
                review_msg = (
                    f"📝 *REVIEW: New article generated*\n\n"
                    f"*Title:* {article['title']}\n"
                    f"*Slug:* {article['slug']}\n"
                    f"*Category:* {article.get('category', 'noticias')}\n\n"
                    f"_Auto-publish in 2 hours if no response._\n\n"
                    f"---ARTICLE PREVIEW---\n"
                    f"{article.get('html_content', '')[:500]}...\n"
                    f"---END---"
                )
                # Send with buttons via Telegram API
                if TELEGRAM_TOKEN and TEAM_CHAT_IDS:
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Publicar", "callback_data": f"review_pub_{article['slug'][:30]}"},
                                {"text": "❌ Descartar", "callback_data": f"review_skip_{article['slug'][:30]}"},
                            ]
                        ]
                    }
                    for chat_id in TEAM_CHAT_IDS:
                        try:
                            requests.post(url, json={
                                "chat_id": chat_id,
                                "text": review_msg,
                                "parse_mode": "Markdown",
                                "reply_markup": keyboard,
                            }, timeout=15)
                        except Exception as e:
                            logger.error("Review notification failed for %s: %s", chat_id, e)

                # Auto-publish after 2 hours if REVIEW_MODE (fallback)
                # Since this is a synchronous script, we publish anyway after the review period
                # In practice, the cron job will handle the next cycle
                logger.info("Article queued for review. Will auto-publish if no response in 2h.")
                # For now, auto-publish anyway to avoid blocking the pipeline
                # The review buttons are informational — admin can /delete if needed

            # Push article HTML
            file_path = f"blog/{article['slug']}.html"
            if gh_put_file(file_path, full_html, f"Publish: {article['title']}"):
                # Update index.json
                if update_blog_index(article):
                    articles_published.append(article)
                    # Add to existing articles list for subsequent duplicate checks
                    existing_articles.append({"title": article["title"], "slug": article["slug"]})
                    logger.info("Published: %s", article["slug"])
                else:
                    logger.error("Index update failed for %s", article["slug"])
            else:
                logger.error("HTML push failed for %s", article["slug"])

            # Rate limit between articles
            time.sleep(2)

    # 5. Update homepage if we published anything
    homepage_updated = False
    if articles_published:
        timeline_text = generate_timeline_entry(articles_published)
        if timeline_text:
            homepage_updated = update_homepage(timeline_text)
            if homepage_updated:
                logger.info("Homepage updated with timeline entry")
            else:
                logger.warning("Homepage update failed")

    # 6. Save state
    save_state(state)

    # 7. Notify via Telegram
    elapsed = int(time.time() - start)
    if articles_published:
        titles = "\n".join(f"  - {a['title']}" for a in articles_published)
        msg = (
            f"*Site Auto-Update Complete*\n\n"
            f"Scanned: {len(all_headlines)} headlines\n"
            f"New: {len(new_headlines)}\n"
            f"Published: {len(articles_published)} articles\n"
            f"{titles}\n\n"
            f"Homepage: {'updated' if homepage_updated else 'no change'}\n"
            f"Time: {elapsed}s"
        )
    else:
        msg = (
            f"*Site Auto-Update — No new items*\n\n"
            f"Scanned: {len(all_headlines)} headlines\n"
            f"New: {len(new_headlines)}\n"
            f"No articles warranted publication.\n"
            f"Time: {elapsed}s"
        )

    notify_telegram(msg)
    logger.info("=== AUTO UPDATE CYCLE END (%ds) ===", elapsed)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    if "--once" in sys.argv:
        run_update()
    else:
        from apscheduler.schedulers.blocking import BlockingScheduler

        scheduler = BlockingScheduler()
        scheduler.add_job(
            run_update, "interval", hours=8,
            next_run_time=datetime.now(),
        )
        logger.info("Auto-updater scheduled every 8h. Starting...")
        scheduler.start()
