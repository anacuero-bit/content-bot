#!/usr/bin/env python3
"""
Auto-Update Script — runs via GitHub Actions every 8 hours.
Scans news, generates articles, publishes to tuspapeles2026.es autonomously.
"""

import os
import sys
import json
import base64
import hashlib
import re
import html as html_mod
from datetime import datetime, timezone

import httpx
import feedparser

# === Config ===
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TEAM_CHAT_IDS = [int(x.strip()) for x in os.environ.get("TEAM_CHAT_IDS", "").split(",") if x.strip()]
REPO = os.environ.get("GITHUB_REPO_TP", "anacuero-bit/tus-papeles-2026")
STATE_FILE = "update_state.json"
MAX_ARTICLES_PER_RUN = 2

# RSS Sources
NEWS_SOURCES = [
    "https://news.google.com/rss/search?q=regularizaci%C3%B3n+extraordinaria+Espa%C3%B1a&hl=es&gl=ES&ceid=ES:es",
    "https://news.google.com/rss/search?q=papeles+inmigrantes+Espa%C3%B1a+2026&hl=es&gl=ES&ceid=ES:es",
]

LEGAL_FACTS = """
LEGAL FACTS — NEVER GET THESE WRONG:
- Residence requirement: 5 MONTHS (not years)
- Job offer: NOT REQUIRED (vulnerability clause)
- Application window: April 1 – June 30, 2026
- Process: 100% online
- Price: from €199 (competitors €350-450)
- Approval rate: 80-90% EXPECTED (never say guaranteed)
- All nationalities eligible
- Cutoff: must be in Spain before December 31, 2025
"""

MONTHS_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MONTHS_SHORT = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def load_state():
    """Load state from GitHub repo (seen headlines)."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    resp = httpx.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        content = json.loads(base64.b64decode(data["content"]).decode())
        return content, data.get("sha")
    return {"seen_hashes": [], "last_run": ""}, None


def save_state(state, sha=None):
    """Save state back to GitHub repo."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/{STATE_FILE}"
    encoded = base64.b64encode(json.dumps(state, indent=2).encode()).decode()
    data = {"message": "Update auto-updater state", "content": encoded, "branch": "main"}
    if sha:
        data["sha"] = sha
    resp = httpx.put(url, headers=headers, json=data, timeout=15)
    return resp.status_code in (200, 201)


def fetch_headlines():
    """Fetch headlines from RSS feeds."""
    headlines = []
    for source in NEWS_SOURCES:
        try:
            feed = feedparser.parse(source)
            for entry in feed.entries[:8]:
                headlines.append({
                    "title": entry.title.strip(),
                    "link": getattr(entry, "link", ""),
                    "summary": getattr(entry, "summary", "")[:300],
                    "hash": hashlib.md5(entry.title.strip().lower()[:80].encode()).hexdigest(),
                })
        except Exception as e:
            print(f"RSS error: {e}")
    return headlines


def filter_new(headlines, seen_hashes):
    """Filter out already-seen headlines."""
    return [h for h in headlines if h["hash"] not in seen_hashes]


def is_duplicate(new_title, existing_articles):
    """Check if a new article title has >70% word overlap with existing ones."""
    new_words = set(new_title.lower().split())
    for article in existing_articles:
        existing_words = set(article.get("title", "").lower().split())
        if not new_words or not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
        if overlap > 0.7:
            return True, article["title"]
    return False, None


def ask_claude_evaluate(headlines):
    """Ask Claude to pick which headlines deserve a blog article."""
    if not headlines:
        return []

    headlines_text = "\n".join(
        f"{i+1}. {h['title']} — {h['summary'][:100]}"
        for i, h in enumerate(headlines[:10])
    )

    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "system": (
                "You evaluate news headlines about Spain's 2026 regularización extraordinaria. "
                "Pick ONLY headlines that are genuinely new, relevant, and would interest "
                "undocumented immigrants in Spain. Respond with ONLY a JSON array of the "
                "headline numbers worth covering (e.g. [1, 3]). If none are worth it, respond []. "
                "Max 2 picks per batch. Skip duplicates, opinion pieces, and non-Spain news."
            ),
            "messages": [{"role": "user", "content": headlines_text}],
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"Claude evaluate error: {resp.status_code}")
        return []

    text = resp.json()["content"][0]["text"].strip()
    # Extract JSON array
    match = re.search(r'\[[\d\s,]*\]', text)
    if not match:
        return []

    try:
        picks = json.loads(match.group())
        return [headlines[i-1] for i in picks if 1 <= i <= len(headlines)]
    except (json.JSONDecodeError, IndexError):
        return []


def generate_article(headline):
    """Generate a full blog article via Claude API."""
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": (
                "You write blog articles for tuspapeles2026.es, a Spanish legal service helping "
                "undocumented immigrants with Spain's 2026 regularización extraordinaria. "
                "Write in Castilian Spanish. Professional but warm tone. "
                f"{LEGAL_FACTS}\n"
                "Respond with a JSON object with these fields:\n"
                "- title: Article title (Spanish)\n"
                "- slug: URL-friendly slug (lowercase, hyphens, no accents)\n"
                "- meta_description: SEO meta description (150 chars max)\n"
                "- category: one of: noticias, guia, mitos, analisis, historias\n"
                "- summary: 1-2 sentence summary for the Estado timeline\n"
                "- html_content: The article body as HTML (h2, h3, p, ul, li, strong, em tags only). "
                "500-800 words. Include practical implications for readers.\n"
                "Respond ONLY with the JSON object, no markdown fences."
            ),
            "messages": [{"role": "user", "content": (
                f"Write a blog article about this news:\n\n"
                f"Headline: {headline['title']}\n"
                f"Summary: {headline['summary']}\n"
                f"Source: {headline['link']}\n\n"
                f"Make it informative and practical for our audience."
            )}],
        },
        timeout=60,
    )

    if resp.status_code != 200:
        print(f"Claude generate error: {resp.status_code}")
        return None

    text = resp.json()["content"][0]["text"].strip()
    # Clean potential markdown fences
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None


def wrap_blog_html(title, html_content, meta_desc, date_str):
    """Wrap article content in full blog HTML template."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_mod.escape(title)} | tuspapeles2026</title>
    <meta name="description" content="{html_mod.escape(meta_desc)}">
    <link rel="icon" type="image/png" href="/tp26sqlogo.png">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; color: #1A1A1A; line-height: 1.7; background: #FAFAFA; }}
        .article-container {{ max-width: 720px; margin: 0 auto; padding: 40px 20px; }}
        .article-header {{ margin-bottom: 30px; }}
        .article-header .back {{ color: #1E3A5F; text-decoration: none; font-size: 0.9rem; }}
        .article-header h1 {{ font-family: 'Playfair Display', serif; font-size: 2rem; margin: 20px 0 10px; color: #1E3A5F; }}
        .article-header .meta {{ color: #6B7280; font-size: 0.85rem; }}
        .article-body h2 {{ font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1E3A5F; margin: 30px 0 12px; }}
        .article-body h3 {{ font-size: 1.1rem; color: #1E3A5F; margin: 24px 0 10px; }}
        .article-body p {{ margin-bottom: 16px; color: #374151; }}
        .article-body ul, .article-body ol {{ margin: 0 0 16px 24px; color: #374151; }}
        .article-body li {{ margin-bottom: 6px; }}
        .article-body strong {{ color: #1A1A1A; }}
        .article-cta {{ background: linear-gradient(135deg, #1E3A5F 0%, #2C4A6E 100%); border-radius: 16px; padding: 40px; text-align: center; margin: 40px 0; color: white; }}
        .article-cta h3 {{ font-size: 1.5rem; margin: 0 0 16px 0; font-weight: 700; }}
        .article-cta p {{ margin: 0 0 24px 0; opacity: 0.85; font-size: 0.95rem; color: white; }}
        .article-cta a {{ display: inline-block; background: #E8D4A8; color: #1E3A5F; padding: 14px 32px; border-radius: 8px; font-weight: 700; text-decoration: none; }}
        .article-cta .sub {{ margin: 16px 0 0 0; font-size: 0.8rem; opacity: 0.6; }}
    </style>
</head>
<body>
    <div class="article-container">
        <div class="article-header">
            <a class="back" href="/informacion.html">&larr; Volver a Informaci&oacute;n</a>
            <h1>{html_mod.escape(title)}</h1>
            <p class="meta">{date_str} &middot; tuspapeles2026.es</p>
        </div>
        <div class="article-body">
            {html_content}
        </div>
        <div class="article-cta">
            <h3>&iquest;Quieres saber si cumples los requisitos?</h3>
            <p>Comprueba tu elegibilidad gratis en 2 minutos. Sin compromiso.</p>
            <a href="https://t.me/TusPapeles2026Bot" target="_blank">Verificar elegibilidad gratis</a>
            <p class="sub">tuspapeles2026.es &middot; Abogados colegiados + tecnolog&iacute;a legal</p>
        </div>
    </div>
</body>
</html>"""


def publish_file(file_path, content, commit_msg):
    """Push a file to GitHub."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"

    # Check if exists
    resp = httpx.get(url, headers=headers, timeout=15)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    encoded = base64.b64encode(content.encode()).decode()
    data = {"message": commit_msg, "content": encoded, "branch": "main"}
    if sha:
        data["sha"] = sha

    resp = httpx.put(url, headers=headers, json=data, timeout=15)
    return resp.status_code in (200, 201)


def update_blog_index(slug, title, meta, category, html_content):
    """Add article to blog/index.json."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/blog/index.json"

    resp = httpx.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        current = json.loads(base64.b64decode(data["content"]).decode())
        sha = data.get("sha")
    else:
        current = {"articles": []}
        sha = None

    now = datetime.now(timezone.utc)
    new_entry = {
        "slug": slug,
        "title": title,
        "meta": meta,
        "date": now.strftime("%Y-%m-%d"),
        "published_at": now.isoformat(),
        "category": category,
        "preview": re.sub(r'<[^>]+>', '', html_content)[:200],
    }

    current["articles"].insert(0, new_entry)
    # Sort by published_at descending
    current["articles"].sort(
        key=lambda x: x.get("published_at", x.get("date", "")),
        reverse=True
    )

    updated = json.dumps(current, ensure_ascii=False, indent=2)
    return publish_file("blog/index.json", updated, f"Index: {title[:50]}")


def fetch_existing_articles():
    """Fetch current articles from blog/index.json for duplicate detection."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/blog/index.json"
    resp = httpx.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        content = json.loads(base64.b64decode(data["content"]).decode())
        return content.get("articles", [])
    return []


def update_estado_timeline(title, summary, category):
    """Inject Estado timeline entry into index.html."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{REPO}/contents/index.html"

    resp = httpx.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        print("Failed to fetch index.html")
        return False

    data = resp.json()
    page_html = base64.b64decode(data["content"]).decode()

    # Map category to tag
    tag_map = {
        "noticias": ("oficial", "Oficial"),
        "guia": ("tramitacion", "Tramitaci&oacute;n"),
        "mitos": ("tramitacion", "Tramitaci&oacute;n"),
        "analisis": ("tramitacion", "Tramitaci&oacute;n"),
        "historias": ("beneficio", "Beneficio"),
    }
    tag_class, tag_label = tag_map.get(category, ("tramitacion", "Tramitaci&oacute;n"))

    now = datetime.now()
    day = f"{now.day:02d}"
    month_year = f"{MONTHS_SHORT[now.month]} {now.year}"
    today_full = f"{now.day} de {MONTHS_ES[now.month]} de {now.year}"

    safe_title = html_mod.escape(title)
    safe_summary = html_mod.escape(summary[:200]) if summary else safe_title

    new_entry = (
        f'\n                <!-- {day} {month_year} - AUTO -->\n'
        f'                <div class="update-item">\n'
        f'                    <div class="update-date-badge">\n'
        f'                        <div class="update-date-day">{day}</div>\n'
        f'                        <div class="update-date-month">{month_year}</div>\n'
        f'                    </div>\n'
        f'                    <div class="update-card">\n'
        f'                        <div class="update-card-top">\n'
        f'                            <span class="update-tag {tag_class}">{tag_label}</span>\n'
        f'                        </div>\n'
        f'                        <h4>{safe_title}</h4>\n'
        f'                        <p>{safe_summary}</p>\n'
        f'                    </div>\n'
        f'                </div>\n'
    )

    # Insert after the updates-timeline marker, before the first <!-- comment
    marker = '<div class="updates-timeline" id="updates-timeline">'
    pos = page_html.find(marker)
    if pos == -1:
        print("Could not find updates-timeline in index.html")
        return False

    after = page_html[pos:]
    first_comment = re.search(r'\n(\s*<!-- \d+ )', after)
    if first_comment:
        insert_pos = pos + first_comment.start()
        updated = page_html[:insert_pos] + new_entry + page_html[insert_pos:]
    else:
        # Fallback: insert after the marker line
        end_of_marker_line = page_html.find('\n', pos + len(marker))
        next_line_end = page_html.find('\n', end_of_marker_line + 1)
        insert_pos = next_line_end
        updated = page_html[:insert_pos] + new_entry + page_html[insert_pos:]

    # Update the timeline-entry date text
    updated = re.sub(
        r'(<span class="timeline-date">)[^<]+(</span>)',
        f'\\g<1>{today_full}\\g<2>',
        updated,
        count=1,
    )

    return publish_file("index.html", updated, f"Estado: {title[:50]}")


def send_telegram(message):
    """Send notification to team via Telegram."""
    if not TELEGRAM_TOKEN or not TEAM_CHAT_IDS:
        return
    for chat_id in TEAM_CHAT_IDS:
        try:
            httpx.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10,
            )
        except Exception as e:
            print(f"Telegram error: {e}")


def main():
    print(f"=== Auto-Update Run: {datetime.now(timezone.utc).isoformat()} ===")

    if not GITHUB_TOKEN or not CLAUDE_API_KEY:
        print("ERROR: Missing GITHUB_TOKEN or CLAUDE_API_KEY")
        sys.exit(1)

    # Load state
    state, state_sha = load_state()
    seen_hashes = set(state.get("seen_hashes", []))

    # Fetch and filter headlines
    all_headlines = fetch_headlines()
    print(f"Found {len(all_headlines)} total headlines")

    new_headlines = filter_new(all_headlines, seen_hashes)
    print(f"After filtering: {len(new_headlines)} new headlines")

    if not new_headlines:
        print("No new headlines. Exiting.")
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        save_state(state, state_sha)
        return

    # Fetch existing articles for duplicate detection
    existing_articles = fetch_existing_articles()

    # Ask Claude which ones to cover
    picks = ask_claude_evaluate(new_headlines)
    print(f"Claude picked {len(picks)} headlines to cover")

    published = 0
    for headline in picks[:MAX_ARTICLES_PER_RUN]:
        print(f"\nGenerating article for: {headline['title']}")

        article = generate_article(headline)
        if not article:
            print("Failed to generate article")
            continue

        title = article.get("title", "")
        slug = article.get("slug", "")
        meta = article.get("meta_description", "")
        category = article.get("category", "noticias")
        summary = article.get("summary", meta)
        html_content = article.get("html_content", "")

        if not title or not slug or not html_content:
            print("Article missing required fields")
            continue

        # Duplicate detection
        dup_found, dup_title = is_duplicate(title, existing_articles)
        if dup_found:
            print(f"Skipped duplicate: {title} (matches: {dup_title})")
            continue

        # Build full HTML
        date_str = f"{datetime.now().day} de {MONTHS_ES[datetime.now().month]} de {datetime.now().year}"
        full_html = wrap_blog_html(title, html_content, meta, date_str)

        # Publish
        print(f"Publishing: blog/{slug}.html")
        if publish_file(f"blog/{slug}.html", full_html, f"Auto-publish: {title}"):
            update_blog_index(slug, title, meta, category, html_content)
            update_estado_timeline(title, summary, category)
            existing_articles.append({"title": title, "slug": slug})
            send_telegram(
                f"🤖 *Auto-publicado:*\n\n"
                f"📰 {title}\n"
                f"🏷️ {category}\n"
                f"🔗 https://tuspapeles2026.es/blog/{slug}.html"
            )
            published += 1
            print("✅ Published successfully")
        else:
            print("❌ Publish failed")

        # Mark as seen
        seen_hashes.add(headline["hash"])

    # Mark ALL new headlines as seen (even unpicked ones)
    for h in new_headlines:
        seen_hashes.add(h["hash"])

    # Trim seen_hashes to last 500
    state["seen_hashes"] = list(seen_hashes)[-500:]
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_published"] = published
    save_state(state, state_sha)

    print(f"\n=== Done. Published {published} articles. ===")


if __name__ == "__main__":
    main()
