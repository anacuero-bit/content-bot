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
from datetime import datetime, timezone, timedelta
from time import mktime

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


def resolve_google_news_url(google_url: str) -> str:
    """Extract the real article URL from a Google News RSS redirect link."""
    if "news.google.com" not in google_url:
        return google_url
    try:
        resp = httpx.get(
            google_url, follow_redirects=True, timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code == 200 and "news.google.com" not in str(resp.url):
            return str(resp.url)
    except Exception:
        pass
    try:
        path = google_url.split("/articles/")[-1].split("?")[0]
        decoded = base64.urlsafe_b64decode(path + "==").decode("utf-8", errors="ignore")
        http_pos = decoded.find("http")
        if http_pos >= 0:
            url = decoded[http_pos:]
            for end_char in ['"', "'", " ", "\n", "\x00"]:
                end_pos = url.find(end_char)
                if end_pos > 0:
                    url = url[:end_pos]
            return url
    except Exception:
        pass
    return google_url


def fetch_headlines():
    """Fetch headlines from RSS feeds. Only items from last 24 hours."""
    headlines = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    for source in NEWS_SOURCES:
        try:
            feed = feedparser.parse(source)
            for entry in feed.entries[:8]:
                # 24-hour filter
                pub_parsed = getattr(entry, "published_parsed", None)
                if pub_parsed:
                    try:
                        pub_dt = datetime.fromtimestamp(mktime(pub_parsed), tz=timezone.utc)
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass

                link = resolve_google_news_url(getattr(entry, "link", ""))
                headlines.append({
                    "title": entry.title.strip(),
                    "link": link,
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


def wrap_blog_html(title, html_content, meta_desc, date_str, slug="article", category="noticias"):
    """Wrap article content in the full site template (nav, ticker, share, footer)."""
    safe_title = html_mod.escape(title)
    safe_meta = html_mod.escape(meta_desc)
    cat_display_map = {
        "noticias": "Noticias", "guia": "Gu&iacute;a pr&aacute;ctica",
        "guias": "Gu&iacute;a pr&aacute;ctica", "mitos": "Mitos",
        "analisis": "An&aacute;lisis", "historias": "Historias",
        "documentos": "Documentos", "proceso": "Proceso",
    }
    cat_display = cat_display_map.get(category, category.title())
    word_count = len(html_content.split())
    reading_time = f"{max(1, word_count // 200)} min"
    return f"""<!-- Generated by Content Bot Auto-Updater -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title} | tuspapeles2026</title>
    <meta name="description" content="{safe_meta}">
    <meta property="og:title" content="{safe_title} | tuspapeles2026">
    <meta property="og:description" content="{safe_meta}">
    <meta property="og:type" content="article">
    <meta property="og:locale" content="es_ES">
    <meta property="og:url" content="https://tuspapeles2026.es/blog/{slug}.html">
    <link rel="icon" type="image/png" href="/tp26sqlogo.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --navy: #1E3A5F; --navy-light: #2C4A6E; --navy-dark: #152B48;
            --gold: #E8D4A8; --gold-dark: #D4C494; --gold-light: #F0E0BE;
            --charcoal: #4D4D4D; --gray-light: #E8E8E8; --white: #FFFFFF; --black: #1A1A1A;
            --success: #22C55E; --warning: #F59E0B; --error: #EF4444; --info: #3B82F6;
            --gray-50: #F9FAFB; --gray-100: #F3F4F6; --gray-200: #E5E7EB;
            --gray-300: #D1D5DB; --gray-400: #9CA3AF; --gray-500: #6B7280;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Inter', sans-serif; color: var(--charcoal); line-height: 1.6; background: var(--white); }}
        h1, h2, h3, h4 {{ font-family: 'Playfair Display', serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        .ticker-bar {{ background: var(--navy); color: white; font-size: 0.85rem; overflow: hidden; height: 40px; }}
        .ticker-track {{ display: flex; animation: ticker-scroll 25s linear infinite; white-space: nowrap; height: 100%; }}
        .ticker-track:hover {{ animation-play-state: paused; }}
        .ticker-content {{ display: flex; align-items: center; flex-shrink: 0; height: 100%; }}
        .ticker-item {{ display: inline-flex; align-items: center; gap: 8px; font-weight: 600; padding: 0 10px; }}
        .ticker-separator {{ color: var(--gold); opacity: 0.5; padding: 0 8px; font-size: 0.75rem; }}
        @keyframes ticker-scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
        .header {{ background: white; padding: 12px 0; border-bottom: 1px solid var(--gray-200); position: sticky; top: 0; z-index: 100; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .header-inner {{ display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ display: flex; align-items: center; gap: 10px; text-decoration: none; }}
        .header-right {{ display: flex; align-items: center; gap: 25px; }}
        .nav {{ display: flex; gap: 25px; align-items: center; }}
        .nav a {{ color: var(--charcoal); text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: color 0.2s; }}
        .nav a:hover {{ color: var(--navy); }}
        .btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; border-radius: 8px; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.95rem; text-decoration: none; cursor: pointer; border: none; transition: all 0.3s; }}
        .btn-gold {{ background: var(--gold); color: var(--navy); box-shadow: 0 4px 15px rgba(232,212,168,0.4); }}
        .btn-gold:hover {{ background: var(--gold-dark); transform: translateY(-2px); }}
        .btn-sm {{ padding: 8px 16px; font-size: 0.85rem; }}
        .breadcrumb {{ padding: 16px 0; font-family: 'Inter', sans-serif; font-size: 0.85rem; color: var(--gray-500); }}
        .breadcrumb a {{ color: var(--navy); text-decoration: none; }}
        .breadcrumb a:hover {{ color: var(--gold-dark); }}
        .breadcrumb span {{ margin: 0 8px; }}
        .article-container {{ max-width: 780px; margin: 0 auto; padding: 0 20px 80px; }}
        .article-category-badge {{ display: inline-block; font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 12px; border-radius: 50px; margin-bottom: 16px; }}
        .badge-guia {{ background: #E8D4A8; color: #1E3A5F; }}
        .badge-noticias {{ background: #3B82F6; color: white; }}
        .badge-mitos {{ background: #EF4444; color: white; }}
        .badge-documentos {{ background: #22C55E; color: white; }}
        .badge-proceso {{ background: #8B5CF6; color: white; }}
        .badge-historias {{ background: #F59E0B; color: white; }}
        .badge-analisis {{ background: #8B5CF6; color: white; }}
        .article-container h1 {{ font-size: 2.4rem; color: var(--navy); line-height: 1.25; margin-bottom: 16px; }}
        .article-meta-line {{ font-family: 'Inter', sans-serif; font-size: 0.9rem; color: var(--gray-500); margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--gray-200); }}
        .article-body h2 {{ font-family: 'Playfair Display', serif; color: var(--navy); margin: 2em 0 0.8em; font-size: 1.6rem; }}
        .article-body p {{ margin-bottom: 1.2em; font-size: 1.05rem; line-height: 1.8; color: var(--charcoal); }}
        .article-body ul, .article-body ol {{ margin: 1em 0 1.5em 1.5em; }}
        .article-body li {{ margin-bottom: 0.5em; line-height: 1.7; }}
        .article-body strong {{ color: var(--navy); }}
        .article-body a {{ color: var(--navy); transition: color 0.2s; }}
        .article-body a:hover {{ color: var(--gold-dark); }}
        .article-share {{ display: flex; align-items: center; gap: 12px; padding: 12px 0; margin-bottom: 24px; border-bottom: 1px solid #e5e7eb; }}
        .share-label {{ font-size: 14px; color: #666; }}
        .share-btn {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 13px; text-decoration: none; transition: opacity 0.2s; }}
        .share-btn:hover {{ opacity: 0.8; }}
        .share-whatsapp {{ background: #25D366; color: white; }}
        .share-twitter {{ background: #000; color: white; }}
        .share-facebook {{ background: #1877F2; color: white; }}
        .footer {{ background: var(--navy-dark); color: white; padding: 60px 0 30px; }}
        .footer-grid {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1.5fr; gap: 40px; margin-bottom: 40px; }}
        .footer h4 {{ font-family: 'Inter', sans-serif; font-size: 1rem; font-weight: 700; margin-bottom: 20px; color: var(--gold); }}
        .footer p {{ font-size: 0.9rem; opacity: 0.7; line-height: 1.8; }}
        .footer-brand {{ font-family: 'Inter', sans-serif; }}
        .footer-links {{ list-style: none; }}
        .footer-links li {{ margin-bottom: 10px; }}
        .footer-links a {{ color: rgba(255,255,255,0.7); text-decoration: none; font-size: 0.9rem; transition: color 0.2s; }}
        .footer-links a:hover {{ color: var(--gold); }}
        .footer-disclaimer {{ border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; margin-bottom: 20px; font-family: 'Inter', sans-serif; font-size: 0.75rem; opacity: 0.5; line-height: 1.7; max-width: 700px; }}
        .footer-bottom {{ border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px; display: flex; justify-content: space-between; font-size: 0.85rem; opacity: 0.6; }}
        .footer-bottom a {{ color: var(--gold); text-decoration: none; }}
        @media (max-width: 768px) {{
            .nav {{ display: none; }}
            .header-inner {{ justify-content: center; }}
            .header-right {{ display: none; }}
            .article-container h1 {{ font-size: 1.8rem; }}
            .footer-grid {{ grid-template-columns: 1fr; }}
            .footer-bottom {{ flex-direction: column; gap: 10px; text-align: center; }}
        }}
        @media (max-width: 420px) {{
            .article-container h1 {{ font-size: 1.5rem; }}
            .article-body h2 {{ font-size: 1.3rem; }}
            .article-body p {{ font-size: 0.95rem; }}
        }}
    </style>
</head>
<body>
    <div class="ticker-bar">
        <div class="ticker-track">
            <div class="ticker-content">
                <div class="ticker-item">&#128202; <span>3.127</span> personas prepar&aacute;ndose</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#128220; Real Decreto en fase de informes preceptivos</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#9203; Apertura prevista: 1 abril 2026</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#9989; Comenzar gratis &mdash; No cobramos hasta que el proceso sea oficial</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
            </div>
            <div class="ticker-content" aria-hidden="true">
                <div class="ticker-item">&#128202; <span>3.127</span> personas prepar&aacute;ndose</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#128220; Real Decreto en fase de informes preceptivos</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#9203; Apertura prevista: 1 abril 2026</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
                <div class="ticker-item">&#9989; Comenzar gratis &mdash; No cobramos hasta que el proceso sea oficial</div>
                <span class="ticker-separator">&bull;&bull;&bull;</span>
            </div>
        </div>
    </div>
    <header class="header">
        <div class="container">
            <div class="header-inner">
                <a href="/" class="logo">
                    <img src="/tp2026logo.svg" alt="tuspapeles2026" style="height:36px;width:auto;">
                </a>
                <div class="header-right">
                    <nav class="nav">
                        <a href="/informacion.html">Informaci&oacute;n</a>
                        <a href="/#estado">Estado</a>
                        <a href="/#requisitos">Requisitos</a>
                        <a href="/#documentos">Documentos</a>
                        <a href="/#como-funciona">Servicio</a>
                        <a href="/#preguntas">FAQ</a>
                        <a href="https://t.me/TusPapeles2026Bot" target="_blank" rel="noopener noreferrer" title="Telegram" style="display:inline-flex;align-items:center;"><img src="https://telegram.org/img/t_logo.svg" alt="Telegram" style="width:22px;height:22px;"></a>
                        <a href="/verificar.html" class="btn btn-gold btn-sm">Comenzar gratis</a>
                    </nav>
                </div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="breadcrumb">
            <a href="/">Inicio</a> <span>&rsaquo;</span> <a href="/informacion.html">Informaci&oacute;n</a> <span>&rsaquo;</span> {safe_title}
        </div>
    </div>
    <main class="article-container">
        <span class="article-category-badge badge-{category}">{cat_display}</span>
        <h1>{safe_title}</h1>
        <div class="article-meta-line">{date_str} &middot; {reading_time} de lectura</div>
        <div class="article-share">
            <span class="share-label">Compartir:</span>
            <a href="#" class="share-btn share-whatsapp" aria-label="WhatsApp">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                WhatsApp
            </a>
            <a href="#" class="share-btn share-twitter" aria-label="X/Twitter">&#120143;</a>
            <a href="#" class="share-btn share-facebook" aria-label="Facebook">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                Facebook
            </a>
        </div>
        <div class="article-body">
            {html_content}
        </div>
        <div id="article-nav" style="display:flex;justify-content:space-between;align-items:center;padding:20px 0;margin:30px 0;border-top:1px solid #E5E7EB;border-bottom:1px solid #E5E7EB;font-family:Inter,sans-serif;">
            <a id="prev-article" href="#" style="display:none;text-decoration:none;color:#1E3A5F;font-size:0.9rem;max-width:45%;">
                <span style="font-size:0.75rem;color:#9CA3AF;display:block;">&larr; Anterior</span>
                <span id="prev-title" style="font-weight:600;"></span>
            </a>
            <div style="flex:1;"></div>
            <a id="next-article" href="#" style="display:none;text-decoration:none;color:#1E3A5F;font-size:0.9rem;text-align:right;max-width:45%;">
                <span style="font-size:0.75rem;color:#9CA3AF;display:block;">Siguiente &rarr;</span>
                <span id="next-title" style="font-weight:600;"></span>
            </a>
        </div>
        <div style="background:linear-gradient(135deg,#1E3A5F 0%,#2C4A6E 100%);border-radius:16px;padding:40px;text-align:center;margin:40px 0;color:white;font-family:Inter,sans-serif;">
            <h3 style="font-size:1.5rem;margin:0 0 16px 0;font-weight:700;">&iquest;Quieres saber si cumples los requisitos?</h3>
            <p style="margin:0 0 24px 0;opacity:0.85;font-size:0.95rem;">Comprueba tu elegibilidad gratis en 2 minutos. Sin compromiso.</p>
            <a href="https://t.me/TusPapeles2026Bot" target="_blank" rel="noopener noreferrer" style="display:inline-block;background:#E8D4A8;color:#1E3A5F;padding:14px 32px;border-radius:8px;font-weight:700;font-size:1rem;text-decoration:none;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 4px 15px rgba(0,0,0,0.2);">Verificar elegibilidad gratis</a>
            <p style="margin:16px 0 0 0;font-size:0.8rem;opacity:0.6;">tuspapeles2026.es &middot; Abogados colegiados + tecnolog&iacute;a legal</p>
        </div>
    </main>
    <footer class="footer">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-brand">
                    <img src="/tp2026logo.svg" alt="tuspapeles2026" style="height:30px;width:auto;margin-bottom:15px;filter:brightness(0) invert(1);">
                    <p>Servicio de regularizaci&oacute;n extraordinaria 2026, en colaboraci&oacute;n con abogados de extranjer&iacute;a colegiados en Espa&ntilde;a. Te acompa&ntilde;amos desde la verificaci&oacute;n de elegibilidad hasta la presentaci&oacute;n de tu solicitud.</p>
                </div>
                <div>
                    <h4>Navegaci&oacute;n</h4>
                    <ul class="footer-links">
                        <li><a href="/#requisitos">Requisitos</a></li>
                        <li><a href="/#como-funciona">C&oacute;mo funciona</a></li>
                        <li><a href="/#documentos">Documentos</a></li>
                        <li><a href="/#preguntas">Preguntas</a></li>
                        <li><a href="/#estado">Novedades</a></li>
                        <li><a href="/informacion.html">Informaci&oacute;n</a></li>
                    </ul>
                </div>
                <div>
                    <h4>Legal</h4>
                    <ul class="footer-links">
                        <li><a href="/privacidad">Pol&iacute;tica de privacidad</a></li>
                        <li><a href="/terminos">T&eacute;rminos de servicio</a></li>
                        <li><a href="#">Aviso legal</a></li>
                        <li><a href="#">Cookies</a></li>
                        <li><a href="/referidos-terminos.html">Programa de Referidos</a></li>
                    </ul>
                </div>
                <div>
                    <h4>Contacto</h4>
                    <ul class="footer-links">
                        <li><a href="https://t.me/TusPapeles2026Bot"><img src="https://telegram.org/img/t_logo.svg" alt="Telegram" style="width:16px;height:16px;vertical-align:middle;margin-right:4px;filter:brightness(0) invert(1);"> Telegram (principal)</a></li>
                        <li>&#9993; info@tuspapeles2026.es</li>
                    </ul>
                </div>
            </div>
            <div class="footer-disclaimer">
                Pombo, Horowitz &amp; Espinosa &middot; Abogados de extranjer&iacute;a &middot; Madrid
            </div>
            <div class="footer-bottom">
                <div>&copy; 2026 tuspapeles2026.es</div>
                <div>Informaci&oacute;n oficial: <a href="https://www.inclusion.gob.es">Ministerio de Inclusi&oacute;n</a></div>
            </div>
        </div>
    </footer>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var title = encodeURIComponent(document.title);
        var url = encodeURIComponent(window.location.href);
        var shares = document.querySelectorAll('.article-share a');
        if (shares[0]) shares[0].href = 'https://wa.me/?text=' + title + '%20' + url;
        if (shares[1]) shares[1].href = 'https://twitter.com/intent/tweet?text=' + title + '&url=' + url;
        if (shares[2]) shares[2].href = 'https://www.facebook.com/sharer/sharer.php?u=' + url;
        var path = window.location.pathname;
        var currentSlug = path.split('/').pop().replace('.html', '');
        fetch('/blog/index.json')
            .then(function(r) {{ return r.json(); }})
            .then(function(data) {{
                var articles = data.articles || [];
                var idx = -1;
                for (var i = 0; i < articles.length; i++) {{
                    if (articles[i].slug === currentSlug) {{ idx = i; break; }}
                }}
                if (idx === -1) return;
                if (idx > 0) {{
                    var prev = articles[idx - 1];
                    var el = document.getElementById('prev-article');
                    el.href = '/blog/' + prev.slug + '.html';
                    document.getElementById('prev-title').textContent = prev.title;
                    el.style.display = 'block';
                }}
                if (idx < articles.length - 1) {{
                    var next = articles[idx + 1];
                    var el2 = document.getElementById('next-article');
                    el2.href = '/blog/' + next.slug + '.html';
                    document.getElementById('next-title').textContent = next.title;
                    el2.style.display = 'block';
                }}
            }})
            .catch(function(e) {{ console.log('Nav load error:', e); }});
    }});
    </script>
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
        full_html = wrap_blog_html(title, html_content, meta, date_str, slug=slug, category=category)

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
