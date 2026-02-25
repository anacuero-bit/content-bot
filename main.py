#!/usr/bin/env python3
"""
================================================================================
Content Bot v4.0 — AI Content Factory for tuspapeles2026
================================================================================
Repository: github.com/anacuero-bit/content-bot
Updated:    2026-02-16

Team-only Telegram bot that generates marketing content via Claude API.
Supports one-tap blog publishing to pombohorowitz.es and tuspapeles2026.es.

CHANGELOG:
----------
v4.1.0 (2026-02-23)
  - ADD: /daily command — generates full day's content from weekly calendar
  - ADD: DAILY_CONTENT_PLAN — weekly calendar mapping day→angle→funnel→themes
  - ADD: Scheduled auto-generation at 7:30am Madrid (Predis only)
  - ADD: /daily force — override daily limit
  - UPDATE: /help with automation section

v4.1.0-alpha (2026-02-23)
  - ADD: Smart topic engine with 60+ themes, file-based persistence
  - ADD: Least-recently-used topic selection (no repeats across restarts)
  - ADD: SEO keyword per topic for better search optimization
  - REMOVE: Old in-memory RECENT_TOPICS system

v4.0.0 (2026-02-22)
  - REPLACE: /help with full V4 command listing (angles, Predis, InVideo, text, planning, tools)
  - ADD: /ideas — example commands per media type with different angles
  - ADD: /predis — test Predis API connection, show brand_id and post count
  - REPLACE: /stats — content_log-based stats (7 days, by type, by angle, Predis approval, least used)
  - REWRITE: /weekly — 25 pieces with angle rotation (11 Claude text + 14 Predis in batches of 3)
  - 19 CommandHandlers: start, help, ideas, blog, video, carousel, image, reel, meme, quote,
    whatsapp, fbtext, video5, weekly, news, stats, predis, articles, delete

v4.0.0-rc1 (2026-02-22)
  - RENAME: /tiktok → /video with angle support + ad tier (_generate_premium_video)
  - RENAME: /carousel → uses V4 Predis pipeline (cmd_carousel → cmd_carousel)
  - RENAME: /fbpost → /fbtext with angle support
  - RENAME: /tiktok5 → /video5
  - ADD: _generate_premium_video() — 5 ad styles (testimonio, contraste, cuenta_atrás, cascada, mini_película)
  - ADD: handle_all_callbacks() — unified callback router (pa_/pr_ approval + legacy)
  - ADD: Angle support for /whatsapp
  - DEL: /caption, /story, /scan, /topics, /phase, /backfill batch commands
  - DEL: /branded, /branded_image, /branded_video, /branded_ideas, /predis_setup, /predis_posts
  - DEL: /carousel3, /captions10, /whatsapp5, /fbpost5, /stories7

v4.0.0-beta (2026-02-22)
  - ADD: send_predis_approval() — unified Predis approval workflow with review checklist
  - ADD: _predis_command_handler() — shared pipeline: angle → prompt → Claude → Predis → review
  - ADD: 5 prompt templates: CAROUSEL_PROMPT_V4, IMAGE_PROMPT_V4, REEL_PROMPT_V4, MEME_PROMPT_V4, QUOTE_PROMPT_V4
  - ADD: 5 new commands: /cr (carousel v4), /image, /reel, /meme, /quote
  - ADD: Topic pools for image, reel, meme, quote content types
  - ADD: generate_content override_prompt parameter for raw-text generation
  - ADD: video_duration + post_type params for predis_create_content

v4.0.0-alpha (2026-02-22)
  - ADD: Angle system — VALID_ANGLES, ANGLE_INSTRUCTIONS, parse_angle_and_topic(), get_angle_instruction()
  - ADD: SEO_KEYWORDS list + get_seo_keywords() helper for regularización keywords
  - ADD: Content tracking — content_log in-memory + content_log.json persistence
  - ADD: log_content() records media_type, angle, topic, tool, predis_post_id, approved

v3.3.0 (2026-02-20)
  - ADD: Predis.ai API integration — generate branded carousels, images, and videos
  - ADD: /predis_setup command — verify Predis connection, show brand info + credits
  - ADD: /branded [topic] command — generate branded carousel via Claude + Predis AI
  - ADD: /branded_image [topic] command — generate branded single image via Predis AI
  - ADD: /branded_video [topic] command — generate branded short video via Predis AI
  - ADD: /predis_posts command — list recent Predis-generated content with status
  - ADD: Review queue — branded content previewed in Telegram with approve/reject
  - ADD: "Brand It" button on /carousel output to render via Predis
  - ADD: Auto-updater branded content — published articles also generate branded carousel
  - ADD: PREDIS_API_KEY, PREDIS_BRAND_ID env vars
  - ADD: Brand color injection (Deep Blue #1B3A5C, Gold #D4A843, White #FFFFFF)

v3.2.0 (2026-02-20)
  - ADD: carousel_renderer.py — Pillow-based branded slide generator (1080x1350px)
  - ADD: Auto-render carousel slides as PNG images + MP4 video + PDF
  - ADD: Send rendered media group + video + PDF in Telegram after /carousel
  - ADD: Logo auto-download from GitHub at startup (ensure_logos)
  - ADD: nixpacks.toml for ffmpeg + fonts-dejavu-core system packages
  - ADD: Pillow + numpy to requirements.txt

v3.1.1 (2026-02-20)
  - FIX: Channel publish — CHANNEL_ID from env, return error detail to user
  - FIX: Google News RSS links — resolve redirect URLs to real article URLs
  - ADD: resolve_google_news_url() helper (httpx follow_redirects + base64 fallback)
  - ADD: 24-hour filter on RSS news scanner — skip items older than 24h
  - ADD: Clickable source link in news alert messages
  - UPD: auto_update.py — same URL resolution + 24h filter

v3.1.0 (2026-02-18)
  - ADD: Telegram channel publishing to @tuspapeles2026
  - ADD: post_to_channel() function for sending content to channel
  - ADD: Channel formatters for all 7 content types (blog, tiktok, carousel, caption, whatsapp, fbpost, story)
  - ADD: "📢 Canal" button on all blog publish dialogs
  - ADD: "📢 Publicar en canal" button on all non-blog content outputs
  - ADD: "📢 Canal" button on news alerts (both /news and auto-scan)
  - ADD: pub_ch_, chpost_, news_chan_ callback handlers
  - REM: Removed PH-Site publish buttons (consolidated to web + channel)

v3.0.9 (2026-02-18)
  - UPD: wrap_blog_html() now outputs full site template: nav, ticker, share bar,
    category badge, prev/next JS navigation, navy CTA box, 4-column footer
  - UPD: auto_update.py template matches main.py (identical output)

v3.0.8 (2026-02-17)
  - ADD: Auto-update Estado timeline on every blog publish
  - ADD: auto_update.py — autonomous news scanning + article publishing via GitHub Actions
  - ADD: GitHub Actions workflow for auto-update every 8h (httpx + feedparser)

v3.0.7 (2026-02-17)
  - FIX: /delete crash — httpx delete() doesn't support json kwarg, use request() instead
  - FIX: Same-day article sorting — add published_at ISO timestamp, sort by it

v3.0.6 (2026-02-17)
  - ADD: /articles command — list all published articles from blog/index.json
  - ADD: /delete command — remove articles via numbered list or slug, with confirmation
  - ADD: Duplicate detection (>70% title word overlap) on blog publish + auto_update
  - ADD: REVIEW_MODE env var for auto_update.py — sends articles for Telegram approval

v3.0.5 (2026-02-17)
  - ADD: /backfill command — generates and publishes 7 backdated launch articles
    to tuspapeles2026 repo (Jan 27 – Feb 17 timeline) via Claude API + GitHub API
  - ADD: Multi-source /news — fetches from Google News RSS, La Moncloa, BOE
    with web scraping via BeautifulSoup; shows action buttons per article
  - ADD: beautifulsoup4 dependency for web scraping news sources
  - FIX: update_blog_index supports date_override for historical dates
  - FIX: index.json sorted by date descending (newest first)

v3.0.4 (2026-02-17)
  - FIX: Blog publish now updates blog/index.json (noticias listing page)
  - FIX: Legal facts block injected into system prompt (5 MONTHS not years)
  - FIX: Blog articles always sent as HTML file attachment (no truncation)
  - ADD: Categorized /blog topics (noticias, guias, mitos, analisis, historias)
  - ADD: /blog noticias — filter by category
  - ADD: Article category auto-detection for publish
  - ADD: /scan — force immediate news scan
  - ADD: Scheduled news auto-scan every 6h (6am/12pm/6pm/midnight Madrid)
  - ADD: News alert buttons (Blog/TikTok/WhatsApp/Ignore) for team

v3.0.3 (2026-02-17)
  - UPDATED: Simplified topic rotation — plain string pools, cleaner pick functions
  - UPDATED: TikTok InVideo prompt — European Spanish voice, color-coded overlays,
    scene descriptions, documentary music, structured ---INVIDEO PROMPT--- block
  - UPDATED: Story output — structured fields (type/topic/background/label/stat/
    title/body/sticker/cta) for instant visual generation
  - UPDATED: Carousel output — standardized slide format with title/bullets/tip_box,
    cover and CTA slide rules, label prefixes (OJO:/IMPORTANTE:/TIP:/DATO:)

v3.0.2 (2026-02-16)
  - ADD: Topic rotation system to prevent content repetition
    30+ topics per content type, pillar-weighted distribution for /weekly
    (40% educational, 25% emotional, 20% news, 10% social proof, 5% behind scenes)

v3.0.1 (2026-02-16)
  - ADD: InVideo AI ready-to-paste prompts in all TikTok script outputs
    (single /tiktok, batch /tiktok5, and /weekly)

v3.0.0 (2026-02-16)
  - NEW: Built from scratch per v3.0 spec
  - Content generation: blog, tiktok, carousel, caption, whatsapp, fbpost, story
  - Batch commands: /tiktok5, /carousel3, /captions10, /whatsapp5, /fbpost5, /stories7
  - Weekly mega-batch: /weekly (generates ~46 pieces)
  - News monitoring: /news (Google News RSS scan)
  - Direct publishing: one-tap blog publish to PH-Site and tuspapeles2026 via GitHub API
  - Phase-aware: auto-adjusts tone based on campaign phase (pre-BOE/BOE/open/final)
  - Team-agnostic: all members have equal access to all commands
"""

# ==============================================================================
# IMPORTS + CONFIG
# ==============================================================================

import os
import json
import logging
import asyncio
import re
import html as html_mod
import random
import hashlib
import base64
import uuid
import io
from datetime import datetime, timedelta, timezone

from typing import Optional
from functools import wraps

import anthropic
import httpx
import feedparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Config from environment
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
TEAM_CHAT_IDS = [
    int(x.strip())
    for x in os.environ.get("TEAM_CHAT_IDS", "").split(",")
    if x.strip()
]
# Keke added to team
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO_PH = os.environ.get("GITHUB_REPO_PH", "anacuero-bit/PH-Site")
GITHUB_REPO_TP = os.environ.get("GITHUB_REPO_TP", "anacuero-bit/tus-papeles-2026")
TELEGRAM_CHANNEL = os.environ.get("CHANNEL_ID", os.environ.get("TELEGRAM_CHANNEL", "@tuspapeles2026"))

# ==============================================================================
# PREDIS.AI API CLIENT
# ==============================================================================

PREDIS_BASE = "https://brain.predis.ai/predis_api/v1"
PREDIS_API_KEY = os.getenv("PREDIS_API_KEY", "")
PREDIS_BRAND_ID = os.getenv("PREDIS_BRAND_ID", "")

# ==============================================================================
# ANGLE SYSTEM — emotional angle selection for content generation
# ==============================================================================

VALID_ANGLES = {"fear", "hope", "urgency", "proof", "humor", "curiosity", "ad"}

ANGLE_INSTRUCTIONS = {
    "fear": "ÁNGULO: MIEDO → ALIVIO. Empieza con el miedo real, luego ofrece solución. Tono: empático, tranquilizador.",
    "hope": "ÁNGULO: ESPERANZA. Pinta el futuro positivo con papeles. Tono: inspirador, cálido.",
    "urgency": "ÁNGULO: URGENCIA. El tiempo se acaba. Fechas, plazos. Tono: directo, firme. NO alarmista.",
    "proof": "ÁNGULO: PRUEBA SOCIAL. Miles ya se preparan. Datos, números. Tono: confiable.",
    "humor": "ÁNGULO: HUMOR CÓMPLICE. Situaciones que todo inmigrante reconoce. Tono: ligero, cercano, viral.",
    "curiosity": "ÁNGULO: CURIOSIDAD. Pregunta o dato sorprendente. '¿Sabías que...?' Tono: intrigante.",
    "ad": "ÁNGULO: ANUNCIO DIRECTO. Presenta el servicio con beneficios claros. Tono: profesional, persuasivo.",
}


def parse_angle_and_topic(args: list) -> tuple:
    """Parse angle and topic from command arguments.

    If the first arg is a valid angle, return (angle, remaining args as topic).
    Otherwise return (None, all args as topic).
    """
    if args and args[0].lower() in VALID_ANGLES:
        angle = args[0].lower()
        topic = " ".join(args[1:]) if len(args) > 1 else ""
        return (angle, topic)
    return (None, " ".join(args) if args else "")


def get_angle_instruction(angle) -> str:
    """Return the instruction string for a given angle, or a default."""
    if angle and angle in ANGLE_INSTRUCTIONS:
        return ANGLE_INSTRUCTIONS[angle] + "\n\n"
    return "Elige el ángulo emocional más efectivo.\n\n"


# ==============================================================================
# SEO KEYWORDS
# ==============================================================================

SEO_KEYWORDS = [
    "regularización extraordinaria 2026",
    "papeles España 2026",
    "arraigo social España",
    "permiso residencia sin papeles",
    "trámite extranjería 2026",
    "documentación inmigrantes España",
    "legalización inmigrantes 2026",
]


def get_seo_keywords(count=3) -> str:
    """Return a random sample of SEO keywords as an instruction string."""
    sample = random.sample(SEO_KEYWORDS, min(count, len(SEO_KEYWORDS)))
    return "KEYWORDS SEO (incluir de forma natural): " + ", ".join(sample) + "\n\n"


# ==============================================================================
# CONTENT TRACKING
# ==============================================================================

content_log: list = []


def load_content_log():
    """Load content log from content_log.json if it exists."""
    global content_log
    try:
        with open("content_log.json", "r", encoding="utf-8") as f:
            content_log = json.load(f)
        logger.info(f"Loaded {len(content_log)} entries from content_log.json")
    except FileNotFoundError:
        content_log = []
        logger.info("No content_log.json found, starting fresh")
    except Exception as e:
        content_log = []
        logger.error(f"Error loading content_log.json: {e}")


def save_content_log():
    """Save content log to content_log.json."""
    try:
        with open("content_log.json", "w", encoding="utf-8") as f:
            json.dump(content_log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving content_log.json: {e}")


def log_content(media_type, angle, topic, tool, predis_post_id=None, approved=None):
    """Append a content entry to the log and save to file."""
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "media_type": media_type,
        "angle": angle,
        "topic": topic,
        "tool": tool,
        "predis_post_id": predis_post_id,
        "approved": approved,
    }
    content_log.append(entry)
    save_content_log()
    return entry


# ==============================================================================
# PERSISTENT TOPIC HISTORY
# ==============================================================================

TOPIC_HISTORY_FILE = "topic_history.json"


def load_topic_history() -> dict:
    try:
        with open(TOPIC_HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"used": {}, "last_daily": None}


def save_topic_history(history: dict):
    try:
        with open(TOPIC_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save topic history: {e}")


topic_history = {}


# ==============================================================================
# V4 PROMPT TEMPLATES — angle-aware, SEO-injected
# ==============================================================================

CAROUSEL_PROMPT_V4 = (
    "{angle_instruction}"
    "{seo_keywords}"
    "Genera texto para un CARRUSEL de redes sociales en español (España) sobre: {topic}\n\n"
    "CONTEXTO: tuspapeles2026.es ayuda a inmigrantes sin papeles en España con la regularización 2026. "
    "Desde €199 (competencia cobra €350-450). IA + abogados reales. Plazo: abril-junio 2026. "
    "Requisito: 5 MESES de residencia (NO años). No necesitas contrato de trabajo. "
    "Tasa de aprobación esperada: 80-90%.\n\n"
    "ESTRUCTURA: gancho → problema → solución → prueba social → llamada a acción.\n\n"
    "REGLAS:\n"
    "- Máximo 900 caracteres\n"
    "- Tono: cercano, empático, profesional\n"
    "- NO promesas de resultados garantizados\n"
    "- Termina con: tuspapeles2026.es | @tuspapeles2026\n"
    "- Incluir: #regularizacion2026 #sinpapeles #papeles2026 #tuspapeles2026\n"
    "- NO markdown (sin ** ni ##)\n"
    "- SOLO texto corrido, nada más"
)

IMAGE_PROMPT_V4 = (
    "{angle_instruction}"
    "{seo_keywords}"
    "Genera texto para UNA IMAGEN de redes sociales en español (España) sobre: {topic}\n\n"
    "CONTEXTO: tuspapeles2026.es — regularización 2026 para inmigrantes en España. "
    "Desde €199. IA + abogados reales. 5 MESES residencia, no necesitas contrato. "
    "80-90% aprobación esperada. Plazo abril-junio.\n\n"
    "REGLAS:\n"
    "- Máximo 400 caracteres\n"
    "- UNA sola idea impactante\n"
    "- Tono cercano y empático\n"
    "- Termina con: tuspapeles2026.es | @tuspapeles2026\n"
    "- 3-4 hashtags relevantes\n"
    "- NO markdown\n"
    "- SOLO texto"
)

REEL_PROMPT_V4 = (
    "{angle_instruction}"
    "{seo_keywords}"
    "Genera texto para un REEL/VÍDEO CORTO en español (España) sobre: {topic}\n\n"
    "CONTEXTO: tuspapeles2026.es — regularización 2026 para inmigrantes en España. "
    "Desde €199. IA + abogados reales. 5 MESES residencia, no contrato. "
    "80-90% aprobación. Abril-junio.\n\n"
    "ESTRUCTURA hablada: gancho 2s → desarrollo 8-12s → cierre 3s.\n\n"
    "REGLAS:\n"
    "- Máximo 500 caracteres\n"
    "- Lenguaje hablado, natural\n"
    "- Tono cercano y directo\n"
    "- Termina con: tuspapeles2026.es | @tuspapeles2026\n"
    "- 3-4 hashtags\n"
    "- NO markdown\n"
    "- SOLO texto"
)

MEME_PROMPT_V4 = (
    "{seo_keywords}"
    "Genera texto para un MEME en español (España) sobre: {topic}\n\n"
    "ÁNGULO: HUMOR CÓMPLICE. Situaciones que todo inmigrante en España reconoce.\n\n"
    "REGLAS:\n"
    "- Máximo 300 caracteres\n"
    "- Humor cercano, cómplice, NUNCA ofensivo\n"
    "- Situación relatable + remate\n"
    "- Termina con: @tuspapeles2026\n"
    "- NO markdown\n"
    "- SOLO texto"
)

QUOTE_PROMPT_V4 = (
    "{seo_keywords}"
    "Genera texto para una FRASE MOTIVACIONAL en español (España) sobre: {topic}\n\n"
    "TEMAS: esperanza, resiliencia, pertenencia, futuro con papeles.\n\n"
    "REGLAS:\n"
    "- Máximo 300 caracteres\n"
    "- Puede ser frase inventada atribuida a \"Comunidad tuspapeles2026\" o frase histórica real\n"
    "- Tono inspirador y cálido\n"
    "- Termina con: @tuspapeles2026\n"
    "- NO markdown\n"
    "- SOLO texto"
)

# Map content types to their V4 prompt templates
V4_PROMPT_MAP = {
    "carousel": CAROUSEL_PROMPT_V4,
    "image": IMAGE_PROMPT_V4,
    "reel": REEL_PROMPT_V4,
    "meme": MEME_PROMPT_V4,
    "quote": QUOTE_PROMPT_V4,
}


# Claude prompts for Predis content generation (conversion-focused)
BRANDED_PROMPT = """Genera un texto breve para crear un carrusel de redes sociales en español (España) sobre: {topic}

CONTEXTO: Somos tuspapeles2026.es, una plataforma que ayuda a inmigrantes sin papeles en España a tramitar su regularización 2026. Nuestro servicio cuesta desde €199 (la competencia cobra €350-450). Usamos IA para validar documentos 24/7 y abogados reales para la presentación.

OBJETIVO: Convertir visualizaciones en clics a tuspapeles2026.es

CATEGORÍAS DE CONTENIDO (elige la más relevante al tema):

1. QUIÉNES SOMOS: Plataforma online respaldada por abogados reales. Proceso 100% digital. Asistente 24/7 por Telegram. Desde €199.

2. MIEDOS DEL PÚBLICO: ¿Es una estafa? No — somos un despacho registrado. ¿Me deportarán? No — el proceso está diseñado para protegerte. ¿Es demasiado caro? Desde €199, menos que cualquier competidor. ¿Es complicado? Nosotros lo hacemos por ti.

3. DIFERENCIADORES: Precio más bajo del mercado. IA que revisa documentos al instante. Sin colas ni oficinas. Abogados que hablan tu idioma. Te acompañamos hasta la resolución.

4. URGENCIA Y ACCIÓN: La ventana se abre en abril. Preparar documentos lleva tiempo. No esperes al último momento. Verifica gratis si cumples requisitos.

5. TESTIMONIAL/SOCIAL PROOF: Miles de personas ya están preparándose. Únete a nuestra comunidad en Telegram. No estás solo en esto.

REGLAS:
- Máximo 900 caracteres
- Tono: cercano, empático, profesional. Como un amigo que te ayuda.
- NO lenguaje agresivo de ventas
- NO promesas de resultados garantizados
- Termina siempre con: tuspapeles2026.es | @tuspapeles2026
- Incluir: #regularizacion2026 #sinpapeles #papeles2026 #tuspapeles2026
- NO usar formato markdown (sin ** ni ##)
- NO usar marcadores de diapositiva
- Escribe SOLO el texto, nada más"""

BRANDED_IMAGE_PROMPT = """Genera un texto muy breve para una imagen de redes sociales en español (España) sobre: {topic}

CONTEXTO: tuspapeles2026.es ayuda a inmigrantes sin papeles en España con la regularización 2026. Desde €199. Abogados reales + IA.

REGLAS:
- Máximo 500 caracteres
- Una idea central, directa, impactante
- Tono cercano y empático
- Termina con: tuspapeles2026.es | @tuspapeles2026
- Incluir 3-4 hashtags relevantes
- NO markdown, NO marcadores
- Escribe SOLO el texto"""

BRANDED_VIDEO_PROMPT = """Genera un texto breve para un vídeo corto de redes sociales en español (España) sobre: {topic}

CONTEXTO: tuspapeles2026.es ayuda a inmigrantes sin papeles en España con la regularización 2026. Desde €199. Proceso 100% online con abogados reales.

REGLAS:
- Máximo 600 caracteres
- Estructura: gancho + problema + solución + llamada a acción
- Tono: cercano, directo, esperanzador
- Termina con: tuspapeles2026.es | @tuspapeles2026
- Incluir 3-4 hashtags
- NO markdown
- Escribe SOLO el texto"""


async def predis_create_content(
    text: str,
    media_type: str = "carousel",
    model_version: str = "4",
    n_posts: int = 1,
    video_duration: str = None,
    post_type: str = None,
) -> dict:
    """Create branded content via Predis.ai API.

    Args:
        text: Topic/prompt text (min 20 chars, 3 words)
        media_type: "single_image", "carousel", or "video"
        model_version: "4" (best quality, carousel+image) or "2" (all types including video)
        n_posts: Number of variations to generate (1-10)
        video_duration: Optional video duration ("short", "medium", "long")
        post_type: Optional post type hint ("generic", "meme", "quotes", etc.)

    Returns:
        dict with post_ids and post_status
    """
    payload = {
        "brand_id": PREDIS_BRAND_ID,
        "text": text,
        "media_type": media_type,
        "model_version": model_version if media_type != "video" else "2",
        "n_posts": str(n_posts),
        "input_language": "spanish",
        "output_language": "spanish",
        "color_palette_type": "brand",
    }

    if post_type:
        payload["post_type"] = post_type

    # Video-specific settings
    if media_type == "video":
        payload["video_duration"] = video_duration or "short"
        payload["model_version"] = "2"  # v4 doesn't support video

    headers = {"Authorization": PREDIS_API_KEY}

    logger.info(f"Predis API request payload: {json.dumps(payload, indent=2, default=str)}")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PREDIS_BASE}/create_content/",
            data=payload,
            headers=headers,
        )

    logger.info(f"Predis API response: {resp.status_code} {resp.text[:1000]}")

    if resp.status_code >= 400:
        logger.error(f"Predis API error {resp.status_code}: {resp.text[:500]}")
        return {"ok": False, "error": resp.text[:200], "status_code": resp.status_code}

    result = resp.json()
    result["ok"] = "post_ids" in result and len(result.get("post_ids", [])) > 0
    return result


async def predis_get_posts(page: int = 1) -> dict:
    """Get all generated posts from Predis.ai."""
    headers = {"Authorization": PREDIS_API_KEY}
    params = {"brand_id": PREDIS_BRAND_ID, "page": page}

    logger.info(f"Predis get_posts request: params={json.dumps(params, default=str)}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{PREDIS_BASE}/get_posts/",
            headers=headers,
            params=params,
        )

    logger.info(f"Predis get_posts response: {resp.status_code} {resp.text[:1000]}")

    if resp.status_code >= 400:
        logger.error(f"Predis get_posts error {resp.status_code}: {resp.text[:500]}")
        return {"ok": False, "error": resp.text[:200]}

    result = resp.json()
    result["ok"] = "posts" in result
    return result


async def predis_get_templates(media_type: str = None, page: int = 1) -> dict:
    """Get available templates from Predis.ai."""
    headers = {"Authorization": PREDIS_API_KEY}
    params = {"brand_id": PREDIS_BRAND_ID, "page": page}
    if media_type:
        params["media_type"] = media_type

    logger.info(f"Predis get_templates request: params={json.dumps(params, default=str)}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{PREDIS_BASE}/get_templates/",
            headers=headers,
            params=params,
        )

    logger.info(f"Predis get_templates response: {resp.status_code} {resp.text[:1000]}")

    if resp.status_code >= 400:
        return {"ok": False, "error": resp.text[:200]}

    result = resp.json()
    result["ok"] = "templates" in result
    return result


async def predis_poll_until_complete(post_id: str, max_wait: int = 180, interval: int = 5) -> dict:
    """Poll Predis.ai until a specific post is completed or errors out.

    Args:
        post_id: The post ID to wait for
        max_wait: Maximum seconds to wait
        interval: Seconds between polls

    Returns:
        dict with post data including urls, caption, media_type
        or {"ok": False, "error": "timeout"} if max_wait exceeded
    """
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval

        result = await predis_get_posts(page=1)
        if not result.get("ok"):
            continue

        for post in result.get("posts", []):
            if post.get("post_id") == post_id:
                # Check if post has URLs (means it's completed)
                urls = post.get("urls", [])
                if urls and len(urls) > 0:
                    post["ok"] = True
                    post["status"] = "completed"
                    return post

        logger.info(f"Predis poll: waiting for {post_id}... ({elapsed}s/{max_wait}s)")

    return {"ok": False, "error": "timeout", "post_id": post_id}


# Claude client
claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Phase detection dates
BOE_DATE = None  # Set when BOE publishes — None means pre-BOE
APPS_OPEN_DATE = datetime(2026, 4, 1)
DEADLINE_DATE = datetime(2026, 6, 30)

# Manual phase override (set via /phase command)
phase_override: Optional[str] = None

# In-memory article cache for publish buttons
pending_articles: dict = {}

# In-memory cache for channel publish buttons (non-blog content)
pending_channel_posts: dict = {}

# In-memory store for carousel text pending Predis rendering
pending_branded: dict = {}

# In-memory Predis review queue: {telegram_msg_id: {post_id, caption, media_urls, ...}}
predis_review_queue: dict = {}

PREDIS_APPROVE = "predis_approve"
PREDIS_REJECT = "predis_reject"

# Generation stats (resets on restart)
gen_stats = {
    "total": 0,
    "by_type": {},
    "by_date": {},
    "last_weekly": None,
}

# Telegram max message length
TG_MAX_LEN = 4096

# News auto-scan sources
NEWS_SCAN_SOURCES = [
    "https://news.google.com/rss/search?q=regularizaci%C3%B3n+2026+Espa%C3%B1a&hl=es&gl=ES&ceid=ES:es",
    "https://news.google.com/rss/search?q=decreto+extranjer%C3%ADa+2026&hl=es&gl=ES&ceid=ES:es",
    "https://news.google.com/rss/search?q=regularizaci%C3%B3n+extraordinaria+Espa%C3%B1a&hl=es&gl=ES&ceid=ES:es",
]

# In-memory set of seen headline keys (resets on restart)
seen_headlines: set = set()

# Logo directory for carousel rendering
LOGO_DIR = "/tmp/tp26_logos"
os.makedirs(LOGO_DIR, exist_ok=True)


async def ensure_logos():
    """Download brand logos from GitHub if not already cached."""
    for name in ["tp2026.png", "tp26sqlogo.png"]:
        path = os.path.join(LOGO_DIR, name)
        if not os.path.exists(path):
            url = f"https://raw.githubusercontent.com/anacuero-bit/tus-papeles-2026/main/{name}"
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(resp.content)
                        logger.info(f"Downloaded logo: {name}")
                    else:
                        logger.warning(f"Logo download failed ({resp.status_code}): {name}")
            except Exception as e:
                logger.warning(f"Logo download error for {name}: {e}")


# ==============================================================================
# TOPIC ROTATION POOL
# ==============================================================================

# Topic pools per content type (plain strings — simple and effective)
TOPIC_POOLS = {
    "tiktok": [
        # Myths (bust them)
        "mito: necesitas oferta de trabajo",
        "mito: cuesta miles de euros",
        "mito: te pueden deportar por intentarlo",
        "mito: solo funciona si hablas español perfecto",
        "mito: necesitas antecedentes penales limpios en todo",
        "mito: es solo para latinoamericanos",
        "mito: si te deniegan no puedes volver a intentar",
        # Documents
        "documento: pasaporte vigente",
        "documento: certificado de antecedentes penales",
        "documento: empadronamiento histórico",
        "documento: certificado médico",
        "documento: fotos biométricas",
        "documento: prueba de arraigo social",
        # Educational
        "qué es la cláusula de vulnerabilidad",
        "diferencia entre regularización 2005 y 2026",
        "timeline completo del proceso",
        "qué pasa cuando se publica el BOE",
        "cuánto tiempo tarda el proceso completo",
        "qué significa arraigo social vs arraigo laboral",
        "proceso digital vs presencial en 2026",
        # Emotional
        "el miedo de vivir sin papeles",
        "imagina tener papeles: qué cambia",
        "reunificación familiar después de regularizar",
        "historias de esperanza: la regularización de 2005",
        "por qué este momento es diferente",
        # Urgency
        "solo 1000 plazas disponibles con nosotros",
        "prepárate ahora antes de que abra el plazo",
        "lo que puedes hacer HOY mientras esperas el BOE",
        "por qué esperar es un error",
        # Social proof
        "miles de personas ya se están preparando",
        "80-90% tasa de aprobación esperada",
        # Pricing / service
        "199 euros vs 350-450 de la competencia",
        "cómo funciona nuestro servicio paso a paso",
        "nuestro bot te ayuda 24/7",
        "sistema de referidos: sube de nivel",
    ],
    "carousel": [
        "8 documentos que necesitas preparar YA",
        "mitos vs realidad de la regularización",
        "timeline: qué esperar mes a mes",
        "5 errores que te pueden costar la aprobación",
        "cláusula de vulnerabilidad explicada",
        "empadronamiento: tu documento más importante",
        "guía paso a paso del proceso",
        "qué hacer mientras esperas el BOE",
        "comparación 2005 vs 2026",
        "derechos que obtienes con la regularización",
        "cómo preparar tu certificado de antecedentes",
        "preguntas frecuentes respondidas",
        "costos reales del proceso completo",
        "qué pasa si te deniegan (y cómo evitarlo)",
        "5 razones para empezar HOY",
    ],
    "story": [
        "tip: empadronamiento es gratuito",
        "tip: pasaporte tarda 2-3 meses renovar",
        "tip: antecedentes deben estar apostillados",
        "tip: certificado médico cuesta 50-80€",
        "stat: 80-90% tasa de aprobación",
        "stat: 500.000+ personas elegibles",
        "stat: 199€ nuestro precio total",
        "poll: ¿ya tienes empadronamiento?",
        "poll: ¿cuántos años llevas en España?",
        "poll: ¿conoces la cláusula de vulnerabilidad?",
        "quiz: ¿cuánto sabes sobre la regularización?",
        "countdown: fecha estimada del BOE",
        "quote: testimonio esperanza",
        "quote: testimonio miedo superado",
        "mito: necesitas oferta de trabajo",
    ],
    "whatsapp": [
        "recordatorio de documentos",
        "actualización sobre el BOE",
        "tip educativo semanal",
        "push de referidos",
        "re-engagement mensaje motivacional",
        "urgencia: plazas limitadas",
        "nuevo artículo en el blog",
        "evento o fecha importante",
    ],
    "fbpost": [
        "guía educativa documentos",
        "mito vs realidad",
        "historia de esperanza",
        "actualización proceso",
        "consejo práctico",
        "pregunta a la comunidad",
        "recurso gratuito compartido",
    ],
    # V4 content type pools
    "image": [
        "5 meses, no 5 años — la verdad sobre el requisito",
        "desde €199: el proceso más accesible del mercado",
        "no necesitas contrato de trabajo para aplicar",
        "80-90% tasa de aprobación esperada en 2026",
        "tu empadronamiento es tu documento más valioso",
        "abril 2026: se abre la ventana de oportunidad",
        "IA + abogados reales = tu mejor combinación",
        "prepárate hoy, no esperes al último momento",
        "qué derechos obtienes con la regularización",
        "miles ya se están preparando — únete",
        "certificado de antecedentes: cómo conseguirlo",
        "el proceso es 100% digital, sin colas",
    ],
    "reel": [
        "3 cosas que NO necesitas para regularizarte",
        "así funciona el proceso paso a paso en 60 segundos",
        "el mito del contrato de trabajo desmontado",
        "¿5 meses o 5 años? la verdad te sorprenderá",
        "qué pasa después de enviar tu solicitud",
        "documentos que debes tener ANTES de abril",
        "por qué este momento es histórico para inmigrantes",
        "errores que te pueden costar la aprobación",
        "cómo funciona tuspapeles2026 en 15 segundos",
        "testimonio: preparándose para la regularización",
        "la cláusula de vulnerabilidad explicada rápido",
        "desde €199 vs €450 de la competencia",
    ],
    "meme": [
        "cuando te dicen que necesitas 5 años y son solo 5 meses",
        "yo preparando mis documentos vs mis amigos que no saben",
        "cuando descubres que no necesitas contrato de trabajo",
        "el grupo de WhatsApp cuando sale una noticia del BOE",
        "yo buscando mi empadronamiento de hace 3 años",
        "cuando tu amigo te dice que conoce a alguien que cobra €100",
        "esperando el BOE como quien espera los resultados de la lotería",
        "cuando llevas toda la documentación y te piden una foto más",
        "yo explicando la regularización en la cena familiar",
        "cuando te enteras que el proceso es 100% online",
    ],
    "quote": [
        "el valor de tener papeles y vivir sin miedo",
        "la esperanza de un futuro legal en España",
        "resiliencia: lo que nos hace fuertes como comunidad",
        "pertenecer: más que un papel, un derecho",
        "el coraje de dar el primer paso",
        "construir un futuro para nuestras familias",
        "la fuerza de una comunidad que se apoya",
        "de la incertidumbre a la tranquilidad",
        "cada documento es un paso hacia la libertad",
        "juntos somos más fuertes — comunidad inmigrante",
    ],
}

# ==============================================================================
# CONTENT_THEMES — unified theme-based topic list (60+ entries)
# ==============================================================================

CONTENT_THEMES = [
    # ── EDUCATIONAL (~15) ─────────────────────────────────────────────
    {"id": "edu_5months", "theme": "educational", "text": "Solo necesitas 5 meses de residencia, no años", "seo": "5 meses residencia regularización"},
    {"id": "edu_no_contract", "theme": "educational", "text": "No necesitas contrato de trabajo para aplicar", "seo": "regularización sin contrato trabajo"},
    {"id": "edu_vulnerability", "theme": "educational", "text": "La cláusula de vulnerabilidad explicada paso a paso", "seo": "cláusula vulnerabilidad regularización"},
    {"id": "edu_timeline", "theme": "educational", "text": "Timeline completo del proceso: del BOE a tus papeles", "seo": "plazo regularización extraordinaria 2026"},
    {"id": "edu_boe", "theme": "educational", "text": "Qué pasa cuando se publica el BOE y qué significa", "seo": "BOE regularización 2026"},
    {"id": "edu_8docs", "theme": "educational", "text": "Los 8 documentos que necesitas preparar ya", "seo": "documentos regularización extraordinaria"},
    {"id": "edu_empadronamiento", "theme": "educational", "text": "Empadronamiento: tu documento más importante y cómo conseguirlo", "seo": "empadronamiento regularización España"},
    {"id": "edu_antecedentes", "theme": "educational", "text": "Certificado de antecedentes penales: guía completa", "seo": "antecedentes penales regularización"},
    {"id": "edu_digital", "theme": "educational", "text": "El proceso es 100% digital, sin colas ni citas presenciales", "seo": "proceso digital regularización 2026"},
    {"id": "edu_2005vs2026", "theme": "educational", "text": "Regularización 2005 vs 2026: las 7 diferencias clave", "seo": "regularización 2005 2026 diferencias"},
    {"id": "edu_arraigo", "theme": "educational", "text": "Arraigo social vs arraigo laboral: cuál te conviene", "seo": "arraigo social laboral España"},
    {"id": "edu_rights", "theme": "educational", "text": "Derechos que obtienes con la regularización: sanidad, trabajo, vivienda", "seo": "derechos regularización España"},
    {"id": "edu_medical", "theme": "educational", "text": "Certificado médico para la regularización: qué piden y cuánto cuesta", "seo": "certificado médico regularización"},
    {"id": "edu_passport", "theme": "educational", "text": "Pasaporte vigente: cómo renovarlo a tiempo para el plazo", "seo": "renovar pasaporte regularización"},
    {"id": "edu_costs", "theme": "educational", "text": "Costos reales del proceso completo de regularización", "seo": "precio regularización extraordinaria 2026"},

    # ── FEARS (~10) ───────────────────────────────────────────────────
    {"id": "fear_deportation", "theme": "fears", "text": "Mito: te pueden deportar por intentar regularizarte", "seo": "deportación regularización mito"},
    {"id": "fear_expensive", "theme": "fears", "text": "Mito: la regularización cuesta miles de euros", "seo": "coste regularización España"},
    {"id": "fear_spanish", "theme": "fears", "text": "Mito: necesitas hablar español perfecto para aplicar", "seo": "idioma regularización requisito"},
    {"id": "fear_denied", "theme": "fears", "text": "¿Qué pasa si te deniegan? Opciones y recursos disponibles", "seo": "denegación regularización recurso"},
    {"id": "fear_latin_only", "theme": "fears", "text": "Mito: la regularización es solo para latinoamericanos", "seo": "regularización todas nacionalidades"},
    {"id": "fear_data_safety", "theme": "fears", "text": "¿Es seguro dar mis datos? Protección de información en el proceso", "seo": "seguridad datos regularización"},
    {"id": "fear_money_risk", "theme": "fears", "text": "¿Puedo perder mi dinero si no me aprueban?", "seo": "riesgo dinero regularización"},
    {"id": "fear_wait_vs_act", "theme": "fears", "text": "Esperar vs prepararte ahora: qué pierdes si no actúas", "seo": "prepararse regularización 2026"},
    {"id": "fear_no_job", "theme": "fears", "text": "Mito: sin trabajo no puedes regularizarte", "seo": "regularización sin empleo"},
    {"id": "fear_criminal", "theme": "fears", "text": "Mito: cualquier antecedente penal te descalifica", "seo": "antecedentes penales requisito regularización"},

    # ── URGENCY (~7) ──────────────────────────────────────────────────
    {"id": "urg_april", "theme": "urgency", "text": "Abril se acerca: ¿tienes todo listo para la apertura?", "seo": "plazo abril regularización 2026"},
    {"id": "urg_docs_weeks", "theme": "urgency", "text": "Los documentos tardan semanas en llegar, empieza ya", "seo": "tiempo documentos regularización"},
    {"id": "urg_passport", "theme": "urgency", "text": "Renovar tu pasaporte puede tardar 2-3 meses", "seo": "renovar pasaporte plazo regularización"},
    {"id": "urg_waiting_error", "theme": "urgency", "text": "Esperar al último momento es el error más común", "seo": "prepararse antes regularización"},
    {"id": "urg_limited", "theme": "urgency", "text": "Plazas limitadas para asesoría — no esperes más", "seo": "plazas limitadas regularización"},
    {"id": "urg_june_deadline", "theme": "urgency", "text": "Junio 2026: la ventana se cierra, no hay prórroga", "seo": "fecha límite junio regularización 2026"},
    {"id": "urg_3_things_today", "theme": "urgency", "text": "3 cosas que puedes hacer HOY para prepararte", "seo": "preparar regularización hoy"},

    # ── PROOF (~7) ────────────────────────────────────────────────────
    {"id": "proof_thousands", "theme": "proof", "text": "Miles de personas ya se están preparando con nosotros", "seo": "comunidad regularización 2026"},
    {"id": "proof_2005_rate", "theme": "proof", "text": "En 2005 se aprobó el 83% de solicitudes presentadas", "seo": "tasa aprobación regularización 2005"},
    {"id": "proof_price_compare", "theme": "proof", "text": "Desde €199 vs €350-450 de la competencia", "seo": "precio regularización comparación"},
    {"id": "proof_real_lawyers", "theme": "proof", "text": "Abogados reales revisan cada expediente personalmente", "seo": "abogados regularización España"},
    {"id": "proof_ai_verify", "theme": "proof", "text": "IA verifica tus documentos 24/7 antes de enviar", "seo": "verificación documentos IA regularización"},
    {"id": "proof_community", "theme": "proof", "text": "Nuestra comunidad crece cada día — no estás solo", "seo": "comunidad inmigrantes regularización"},
    {"id": "proof_referral", "theme": "proof", "text": "Sistema de referidos: recomienda y sube de nivel", "seo": "referidos tuspapeles2026"},

    # ── HOPE (~6) ─────────────────────────────────────────────────────
    {"id": "hope_imagine", "theme": "hope", "text": "Imagina tener papeles: qué cambia en tu vida desde el día uno", "seo": "vida con papeles España"},
    {"id": "hope_family", "theme": "hope", "text": "Reunificación familiar: el primer paso es tu regularización", "seo": "reunificación familiar regularización"},
    {"id": "hope_rights", "theme": "hope", "text": "Sanidad, trabajo, vivienda: los derechos que vas a recuperar", "seo": "derechos regularización inmigrantes"},
    {"id": "hope_2005_stories", "theme": "hope", "text": "Historias reales de la regularización de 2005: sí se puede", "seo": "historias éxito regularización 2005"},
    {"id": "hope_first_step", "theme": "hope", "text": "El primer paso es el más difícil — pero ya lo estás dando", "seo": "primer paso regularización"},
    {"id": "hope_children", "theme": "hope", "text": "Tus hijos merecen estabilidad — esto es por ellos también", "seo": "hijos regularización estabilidad"},

    # ── HUMOR (~8) ────────────────────────────────────────────────────
    {"id": "humor_extranjeria", "theme": "humor", "text": "Las colas de extranjería: una experiencia que nos une a todos", "seo": "extranjería colas España"},
    {"id": "humor_nie", "theme": "humor", "text": "Cuando te piden el NIE para absolutamente TODO en España", "seo": "NIE España trámites"},
    {"id": "humor_empadronamiento", "theme": "humor", "text": "Conseguir cita para empadronarte: misión imposible nivel experto", "seo": "cita empadronamiento España"},
    {"id": "humor_job_situation", "theme": "humor", "text": "Cuando preguntan tu situación laboral y no sabes qué decir", "seo": "trabajo sin papeles España"},
    {"id": "humor_papers_question", "theme": "humor", "text": "Cuando alguien pregunta '¿ya tienes papeles?' por millonésima vez", "seo": "papeles España inmigrantes"},
    {"id": "humor_bureaucracy", "theme": "humor", "text": "La burocracia española: el jefe final que todos enfrentamos", "seo": "burocracia extranjería España"},
    {"id": "humor_working", "theme": "humor", "text": "Cuando trabajas más que nadie pero sin contrato oficial", "seo": "trabajar sin papeles realidad"},
    {"id": "humor_folder", "theme": "humor", "text": "Esa carpeta de documentos que pesa más que tu maleta al llegar", "seo": "documentos inmigrante España"},
]

THEMES_BY_ID = {t["id"]: t for t in CONTENT_THEMES}

# Angle → theme filter mapping for smart topic selection
ANGLE_THEME_MAP = {
    "fear": ["fears", "educational"],
    "hope": ["hope"],
    "urgency": ["urgency"],
    "proof": ["proof"],
    "humor": ["humor"],
    "curiosity": ["educational"],
}


# ==============================================================================
# DAILY CONTENT PLAN — weekly calendar (day_of_week → list of content slots)
# Each slot: (media_type, angle, funnel_stage, theme_filter_list)
# ==============================================================================

DAILY_CONTENT_PLAN = {
    # Monday (10 slots)
    0: [
        ("carousel", "fear", "tofu", ["fears", "educational"]),
        ("carousel", "proof", "mofu", ["proof"]),
        ("carousel", "urgency", "bofu", ["urgency"]),
        ("image", "urgency", "bofu", ["urgency"]),
        ("video", "curiosity", "tofu", ["educational"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("blog", None, "tofu", ["educational", "fears"]),
        ("whatsapp", "urgency", "bofu", ["urgency"]),
        ("fbtext", "curiosity", "tofu", ["educational"]),
    ],
    # Tuesday (9 slots)
    1: [
        ("carousel", "hope", "tofu", ["hope"]),
        ("carousel", "curiosity", "tofu", ["educational"]),
        ("carousel", "proof", "mofu", ["proof"]),
        ("image", "proof", "mofu", ["proof"]),
        ("video", "fear", "tofu", ["fears", "educational"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("whatsapp", None, None, None),
        ("fbtext", "proof", "mofu", ["proof"]),
    ],
    # Wednesday (10 slots)
    2: [
        ("carousel", "urgency", "bofu", ["urgency"]),
        ("carousel", "fear", "tofu", ["fears", "educational"]),
        ("carousel", "hope", "tofu", ["hope"]),
        ("image", "curiosity", "tofu", ["educational"]),
        ("video", "urgency", "bofu", ["urgency"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("blog", None, "tofu", ["educational", "fears"]),
        ("whatsapp", "hope", "tofu", ["hope"]),
        ("fbtext", "curiosity", "tofu", ["educational"]),
    ],
    # Thursday (7 slots)
    3: [
        ("carousel", "proof", "mofu", ["proof"]),
        ("carousel", "urgency", "bofu", ["urgency"]),
        ("image", "fear", "tofu", ["fears", "educational"]),
        ("video", "proof", "mofu", ["proof"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("fbtext", "fear", "tofu", ["fears", "educational"]),
    ],
    # Friday (9 slots)
    4: [
        ("carousel", "curiosity", "tofu", ["educational"]),
        ("carousel", "hope", "tofu", ["hope"]),
        ("carousel", "fear", "tofu", ["fears", "educational"]),
        ("image", "hope", "tofu", ["hope"]),
        ("video", "humor", "tofu", ["humor"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("whatsapp", "urgency", "bofu", ["urgency"]),
        ("fbtext", "proof", "mofu", ["proof"]),
    ],
    # Saturday (5 slots)
    5: [
        ("carousel", "proof", "mofu", ["proof"]),
        ("image", "hope", "tofu", ["hope"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("reel", "hope", "tofu", ["hope"]),
    ],
    # Sunday (4 slots)
    6: [
        ("image", "urgency", "bofu", ["urgency"]),
        ("meme", "humor", "tofu", ["humor"]),
        ("quote", "hope", "tofu", ["hope"]),
        ("reel", "curiosity", "tofu", ["educational"]),
    ],
}


# Blog topic pools by category (for /blog suggestions)
BLOG_TOPICS = {
    "noticias": [
        "Real Decreto en fase de informes: qué significa para ti",
        "Consejo de Estado revisa el texto — plazo se mantiene",
        "Audiencia pública cierra con más de 1.200 aportaciones",
        "Ministerio confirma apertura en abril: lo que sabemos",
        "Diferencias entre el borrador de enero y el texto actual",
        "¿Qué falta para la publicación en el BOE?",
        "Cronología completa: del anuncio al decreto",
        "Lo que dicen los expertos sobre el nuevo decreto",
    ],
    "guias": [
        "5 documentos que debes buscar AHORA para la regularización",
        "Empadronamiento histórico: cómo conseguirlo paso a paso",
        "Certificado de antecedentes penales: guía completa",
        "Cómo preparar tu certificado médico para la solicitud",
        "Guía completa de documentos para la regularización 2026",
        "Qué hacer si no tienes empadronamiento",
        "Cómo demostrar 5 meses de residencia sin padrón",
    ],
    "mitos": [
        "No, no necesitas oferta de trabajo — la cláusula de vulnerabilidad explicada",
        "Mito: solo pueden aplicar latinoamericanos",
        "Mito: te pueden deportar por intentar regularizarte",
        "Mito: necesitas hablar español perfecto",
        "5 mitos sobre la regularización que debes dejar de creer",
    ],
    "analisis": [
        "Regularización 2005 vs 2026: las 7 diferencias clave",
        "Por qué esta regularización tiene mayor tasa de aprobación esperada",
        "Qué pasa si te deniegan: opciones y recursos",
        "El impacto económico de regularizar 500.000 personas",
    ],
    "historias": [
        "Así cambió la vida de María después de la regularización de 2005",
        "De vivir con miedo a tener papeles: testimonios reales",
        "Lo que significa tener papeles: derechos que obtienes",
    ],
}

BLOG_CATEGORY_ICONS = {
    "noticias": "📰",
    "guias": "📋",
    "mitos": "❌",
    "analisis": "📊",
    "historias": "💬",
}

# Weights for random category selection (news-heavy)
BLOG_CATEGORY_WEIGHTS = {
    "noticias": 3, "guias": 2, "mitos": 1, "analisis": 2, "historias": 1,
}


def suggest_blog_topics(category_filter: str = None, count: int = 3) -> list[dict]:
    """Suggest blog topics from different categories, weighted toward news.

    Returns list of {"topic": str, "category": str}.
    """
    if category_filter and category_filter in BLOG_TOPICS:
        pool = BLOG_TOPICS[category_filter]
        chosen = random.sample(pool, min(count, len(pool)))
        return [{"topic": t, "category": category_filter} for t in chosen]

    suggestions = []
    used_cats = set()
    categories = list(BLOG_TOPICS.keys())

    for _ in range(count):
        available = [c for c in categories if c not in used_cats]
        if not available:
            available = categories
        weights = [BLOG_CATEGORY_WEIGHTS.get(c, 1) for c in available]
        cat = random.choices(available, weights=weights, k=1)[0]
        used_cats.add(cat)

        topic = random.choice(BLOG_TOPICS[cat])
        suggestions.append({"topic": topic, "category": cat})

    return suggestions


def smart_pick_topic(content_type: str = None, angle: str = None,
                     theme_filter: list = None, user_topic: str = None) -> dict:
    """Return {"text": str, "seo": str, "id": str} using least-recently-used algorithm."""
    global topic_history

    if user_topic:
        return {"text": user_topic, "seo": "", "id": f"custom_{hash(user_topic) % 10000}"}

    # Use angle→theme mapping if no explicit filter
    if theme_filter is None and angle and angle in ANGLE_THEME_MAP:
        theme_filter = ANGLE_THEME_MAP[angle]

    candidates = (
        [t for t in CONTENT_THEMES if t["theme"] in theme_filter]
        if theme_filter
        else list(CONTENT_THEMES)
    )
    if not candidates:
        candidates = list(CONTENT_THEMES)

    used = topic_history.get("used", {})
    now = datetime.now()
    scored = []
    for t in candidates:
        times_used = used.get(t["id"], {}).get("count", 0)
        last_str = used.get(t["id"], {}).get("last")
        days_ago = 999
        if last_str:
            try:
                days_ago = (now - datetime.fromisoformat(last_str)).days
            except Exception:
                pass
        score = (times_used * 50) - (days_ago * 10)
        scored.append((score, t))

    scored.sort(key=lambda x: x[0])
    chosen = random.choice([s[1] for s in scored[:5]])

    if chosen["id"] not in used:
        used[chosen["id"]] = {"count": 0, "last": None}
    used[chosen["id"]]["count"] += 1
    used[chosen["id"]]["last"] = now.isoformat()
    topic_history["used"] = used
    save_topic_history(topic_history)

    return chosen


def pick_topic(content_type, user_topic=None):
    """Pick a topic via smart engine, with TOPIC_POOLS fallback."""
    result = smart_pick_topic(content_type=content_type, user_topic=user_topic)
    if result and result["text"]:
        return result["text"]
    # Fallback to old pool
    pool = TOPIC_POOLS.get(content_type, [])
    return random.choice(pool) if pool else ""


def pick_multiple_topics(content_type, count):
    """Pick N different topics for batch commands."""
    topics = []
    for _ in range(count):
        topic = pick_topic(content_type)
        topics.append(topic)
    return topics


# ==============================================================================
# ACCESS CONTROL
# ==============================================================================


def team_only(func):
    """Decorator: restrict command to TEAM_CHAT_IDS only."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in TEAM_CHAT_IDS:
            await update.message.reply_text(
                "Este bot es privado. Para regularización, visita tuspapeles2026.es"
            )
            return
        return await func(update, context)

    return wrapper


async def handle_unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catch-all handler for non-team members."""
    if update.effective_user and update.effective_user.id not in TEAM_CHAT_IDS:
        await update.message.reply_text(
            "Este bot es privado. Para regularización, visita tuspapeles2026.es"
        )


# ==============================================================================
# PHASE DETECTION
# ==============================================================================


def get_current_phase() -> str:
    """Returns the current campaign phase.

    Returns one of: 'pre_boe', 'boe_week', 'apps_open', 'final_push'
    """
    global phase_override
    if phase_override:
        return phase_override

    now = datetime.now()
    if BOE_DATE and now < BOE_DATE + timedelta(days=7):
        return "boe_week"
    if now >= datetime(2026, 6, 1):
        return "final_push"
    if now >= APPS_OPEN_DATE:
        return "apps_open"
    return "pre_boe"


# ==============================================================================
# SYSTEM PROMPT (THE BRAIN)
# ==============================================================================


def get_system_prompt(content_type: str, phase: str) -> str:
    """Build the full system prompt for Claude based on content type and phase."""

    base = """You are the content engine for tuspapeles2026.es, a legal technology service helping undocumented immigrants in Spain regularize their status under the 2026 extraordinary regularization decree.

BRAND VOICE:
- Warm, professional, simple Spanish
- Maximum 15-word sentences
- No legal jargon unless you explain it immediately
- Never condescending — these people are scared and vulnerable
- Acknowledge their fear, then offer hope
- Use "tú" not "usted" (informal, like a trusted friend)

TARGET AUDIENCE:
- Undocumented immigrants in Spain (500,000-840,000 eligible)
- 90% Latin American, 35% Colombian
- Ages 25-50, low-medium digital literacy
- WhatsApp is their primary communication channel
- Their fears: scams, deportation, wasting money, rejection, missing deadline
- Their desires: legal status, work permit, travel home, security for family

KEY FACTS TO WEAVE IN NATURALLY (don't force all into every piece):
- Vulnerability clause: NO job offer needed (biggest difference from 2005)
- 80-90% approval expected based on 2005 precedent (NEVER guarantee)
- Price: €199 prepay or €247 by phases (€29 + €89 + €129) — competitors charge €350-450
- 1,000 slot capacity (creates urgency without being scammy)
- Backed by Pombo & Horowitz Abogados (25 years experience)
- AI-powered document validation — 24/7 availability via Telegram bot
- Digital submission confirmed — everything is online
- Cónsul/Embajador referral program — friends get €25 off

WHAT TO NEVER SAY:
- Never guarantee approval or use "100% success"
- Never use aggressive sales ("BUY NOW", "LIMITED TIME")
- Never be condescending about their education or situation
- Never use complex legal terms without explaining them
- Never make promises about timelines we can't control

CTAs (vary by content type):
- Blog: "Verifica tu elegibilidad gratis en tuspapeles2026.es"
- Social: "Link en bio → tuspapeles2026.es"
- WhatsApp: "Comparte con quien lo necesite"
- General: "Empieza gratis en t.me/tuspapeles2026bot"

SEO KEYWORDS (for blogs only):
regularización 2026, regularización extraordinaria España, papeles España 2026,
cómo regularizarse en España, documentos regularización, requisitos regularización

COMPETITORS (differentiate naturally, never attack):
- They charge €350-450 → we charge €199-247
- They process manually → we use AI document validation
- They work business hours → our bot works 24/7
- They have no referral program → we have Cónsul/Embajador tiers

LEGAL FACTS — NEVER CONTRADICT THESE. IF UNSURE, USE THESE EXACT FACTS:

ELIGIBILITY REQUIREMENTS:
- Entry: Must have entered Spain BEFORE December 31, 2025
- Residence: At least 5 MONTHS continuous stay (NOT years — FIVE MONTHS)
- Criminal record: No serious convictions (over 1 year sentence)
- Job offer: NOT REQUIRED — vulnerability clause presumes vulnerability
- Nationality: ALL nationalities eligible (not just Latin American)

APPLICATION:
- Window: April 1 – June 30, 2026 (3 months)
- Process: 100% online (telematic)
- Provisional work permit: Granted IMMEDIATELY upon filing
- Decision: Within 3 months maximum

KEY MESSAGES:
- Vulnerability clause = NO job offer needed (biggest difference from 2005)
- Expected approval rate: 80-90% based on 2005 precedent (NEVER guarantee)
- Our price: from €199 (competitors charge €350-450)
- Capacity: 1,000 clients
- Service backed by registered lawyers (abogados colegiados)

NEVER SAY:
- "Guaranteed approval" or "100%"
- "2 years" or "3 years" of residency — IT IS 5 MONTHS
- "You need a job offer"
- "Only for Latin Americans"
"""

    # Phase-specific instructions
    phase_prompts = {
        "pre_boe": (
            "\nCURRENT PHASE: PRE-BOE\n"
            "Content tone: educational, trust-building. Focus on 'get ready', "
            "'prepare your documents now', 'understand the process'. No hard sells. "
            "Build authority and trust."
        ),
        "boe_week": (
            "\nCURRENT PHASE: BOE WEEK (law just published)\n"
            "Content tone: URGENT but not panicky. 'It's official', "
            "'the law has been published', 'act now to secure your spot'. "
            "Heavy emphasis on the vulnerability clause and that no job offer is needed."
        ),
        "apps_open": (
            "\nCURRENT PHASE: APPLICATIONS OPEN\n"
            "Content tone: conversion-focused. Testimonials, social proof, scarcity "
            "('X slots remaining'). Emphasize that people who started early are already "
            "getting approvals. Fear of missing out."
        ),
        "final_push": (
            "\nCURRENT PHASE: FINAL PUSH (deadline approaching)\n"
            "Content tone: last chance. Daily countdown to June 30 deadline. "
            "'If you don't apply now, this opportunity may not come again for another "
            "20 years.' Maximum urgency."
        ),
    }

    # Content-type-specific instructions
    type_prompts = {
        "blog": (
            "\nCONTENT TYPE: BLOG ARTICLE\n"
            "Write a complete SEO blog article in Spanish. 600-900 words. "
            "Include: H2 subheadings (use <h2> tags), internal links to tuspapeles2026.es, "
            "a CTA paragraph at the end. Format the article body as clean HTML ready to embed.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"title": "string", "meta_description": "string (max 160 chars)", '
            '"slug": "string (url-friendly)", "html_content": "string (HTML)", '
            '"word_count": number}'
        ),
        "tiktok": (
            "\nCONTENT TYPE: VIDEO SCRIPT\n"
            "Write a script for an ad video for social media (TikTok/Instagram Reels) for 15-30 seconds.\n\n"
            "TARGET DURATION: 20-30 seconds (25 seconds ideal).\n"
            "SCRIPT LENGTH: Maximum 75 words of spoken text. Fewer is better.\n"
            "PACING: Hook in first 2 seconds. One clear idea per video. No rambling.\n\n"
            "Duration by format:\n"
            "- Myth-busting: 15-20 seconds (~40-50 words)\n"
            "- Document tip: 20-25 seconds (~50-60 words)\n"
            "- Educational explainer: 25-30 seconds (~60-75 words)\n"
            "- Emotional/story: 30 seconds max (~75 words)\n\n"
            "NEVER exceed 30 seconds or 75 words. Shorter = higher completion rate = more views.\n\n"
            "After the main JSON fields, also include a field called 'invideo_prompt' — "
            "this is a ready-to-paste prompt for InVideo AI. The prompt MUST follow this exact format:\n\n"
            "Create a [DURATION]-second vertical ad video for social media (TikTok/Instagram Reels) in European Spanish (Spain). "
            "(DURATION must be 15-30 seconds, never more.)\n\n"
            "VOICEOVER SCRIPT: \"[paste the full script here]\"\n\n"
            "VOICE: Female, European Spanish (Castilian accent). Warm, measured pace — not fast. "
            "Trusted professional tone.\n\n"
            "VISUALS: Professional stock footage of [relevant visuals for this topic — Spanish streets, "
            "documents, government buildings, people, legal offices]. Change scene every 3-4 seconds. "
            "No text-heavy slides.\n\n"
            "TEXT OVERLAYS: [list each overlay with timing and color:\n"
            "- \"OVERLAY TEXT\" (color: red for myths, green for facts, gold for numbers, white for general)]\n\n"
            "CAPTIONS: Word-by-word animated captions, bold white with black outline, bottom third of screen.\n\n"
            "MUSIC: Subtle documentary-style background music, 15% volume.\n\n"
            "FORMAT: 9:16 vertical, 1080x1920. Style: professional, warm, trustworthy. "
            "Fast-paced cuts every 3-5 seconds. Total duration: 15-30 seconds MAX.\n\n"
            "BRANDING: This is a promotional ad for tuspapeles2026.es. Include brand logo placement.\n\n"
            "The invideo_prompt should be a single string ready to paste directly into InVideo AI "
            "with zero editing needed.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"format": "face-to-camera|green-screen|pov|story-time|myth-vs-reality|quick-tips", '
            '"duration_seconds": number (15-30, never above 30), '
            '"hook": "string (first 2 seconds — must grab attention)", '
            '"script": "string (full spoken text — max 75 words)", '
            '"text_overlays": ["string", "string", "string"], '
            '"hashtags": "string", '
            '"production_tip": "string", '
            '"invideo_prompt": "string (full ready-to-paste InVideo AI prompt)"}'
        ),
        "carousel": (
            "\nCONTENT TYPE: INSTAGRAM CAROUSEL\n"
            "Write Instagram carousel content with 6-8 slides.\n\n"
            "SLIDE FORMAT RULES:\n"
            "- Each slide has: title (main heading), bullets (2-3 body lines), and tip_box (optional label line)\n"
            "- Slide 1 is always the cover (title + 1-2 subtitle lines, no tip_box)\n"
            "- Last slide is always the CTA (title + CTA body lines, no tip_box)\n"
            "- Content slides (2 through N-1) must have: 1 title + 2-3 bullets + 1 tip_box\n"
            "- tip_box starts with a label prefix: OJO:, IMPORTANTE:, TIP:, DATO:, CLAVE:, COSTO:, or CONSEJO:\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"topic": "string", '
            '"slides": [{"slide_number": 1, "title": "string", '
            '"bullets": ["string", "string"], "tip_box": "string or null"}], '
            '"caption": "string (Instagram caption with line breaks and emojis)", '
            '"hashtags": "string (30 hashtags)"}'
        ),
        "caption": (
            "\nCONTENT TYPE: SOCIAL MEDIA CAPTION\n"
            "Write a social media caption.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"platform": "instagram|facebook", "caption_text": "string", '
            '"hashtags": "string", "cta": "string"}'
        ),
        "whatsapp": (
            "\nCONTENT TYPE: WHATSAPP BROADCAST MESSAGE\n"
            "Write a WhatsApp broadcast message. Must be under 500 characters. "
            "Must feel personal — like a friend sharing useful info, not a company. "
            "Must be highly shareable/forwardable.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"type": "news|deadline|educational|referral|re-engagement", '
            '"message_text": "string (under 500 chars)", '
            '"suggested_send_time": "string"}'
        ),
        "fbpost": (
            "\nCONTENT TYPE: FACEBOOK GROUP POST\n"
            "Write an organic Facebook group post. VALUE-FIRST — educational, not promotional. "
            "Should feel like a real person sharing useful info. "
            "Soft CTA at end linking to a blog article, not directly to the bot.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"post_text": "string", '
            '"suggested_groups": ["colombianos en Madrid", "latinos en Barcelona"], '
            '"cta_link": "string"}'
        ),
        "story": (
            "\nCONTENT TYPE: INSTAGRAM STORY\n"
            "Write an Instagram Story concept with structured fields for visual generation.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"type": "tip|poll|quiz|countdown|quote|stat", '
            '"topic": "string (the topic of this story)", '
            '"background": "deep_blue|dark_teal|dark_warm", '
            '"label": "string (badge text, e.g. SABÍAS QUE..., ENCUESTA, TIP DEL DÍA, DATO)", '
            '"stat": "string (big number if applicable, e.g. 80-90%, or none)", '
            '"title": "string (main title text)", '
            '"body": "string (supporting body text)", '
            '"sticker": "string (poll question with options / quiz with answers / countdown target date / none)", '
            '"cta": "string (CTA text, e.g. Verifica tu elegibilidad GRATIS)"}'
        ),
        "topics": (
            "\nCONTENT TYPE: TOPIC SUGGESTIONS\n"
            "Generate 10 content topic suggestions for the current phase of the campaign. "
            "Each topic should work across multiple formats (blog, TikTok, carousel, etc.).\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"topics": [{"title": "string", "angle": "string", '
            '"best_formats": ["blog", "tiktok"]}]}'
        ),
        "news_analysis": (
            "\nCONTENT TYPE: NEWS ANALYSIS\n"
            "You are given recent news articles about regularización in Spain. "
            "For each article, suggest 1-2 content ideas we could create based on the news.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"analysis": [{"headline": "string", "summary": "string", '
            '"content_ideas": ["string"]}]}'
        ),
    }

    prompt = base
    prompt += phase_prompts.get(phase, phase_prompts["pre_boe"])
    prompt += type_prompts.get(content_type, "")

    return prompt


# ==============================================================================
# CLAUDE API HELPER
# ==============================================================================


async def generate_content(
    content_type: str, topic: str = "", phase: str = None,
    override_prompt: str = None,
) -> dict:
    """Call Claude API and return parsed JSON content.

    When override_prompt is set, uses a simple marketing system prompt and
    sends override_prompt as the user message. Returns raw text as a string
    instead of parsed JSON.
    """
    # Override mode: raw text generation for V4 prompt templates
    if override_prompt is not None:
        try:
            response = await asyncio.to_thread(
                claude.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system="Eres un experto en marketing digital para comunidades inmigrantes en España.",
                messages=[{"role": "user", "content": override_prompt}],
            )
            text = response.content[0].text.strip()
            track_generation(content_type)
            return text
        except Exception as e:
            logger.error(f"Claude API error (override): {e}")
            raise

    # Standard mode: JSON content generation (unchanged)
    if not phase:
        phase = get_current_phase()

    system = get_system_prompt(content_type, phase)

    user_msg = f"Generate a {content_type} "
    if topic:
        user_msg += f"about: {topic}"
    else:
        user_msg += "on a relevant topic for this phase of the campaign"

    for attempt in range(2):
        try:
            response = await asyncio.to_thread(
                claude.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )

            text = response.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:])
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                text = text[start:end]

            result = json.loads(text)

            # Track stats
            track_generation(content_type)

            return result

        except json.JSONDecodeError:
            if attempt == 0:
                logger.warning(
                    f"JSON parse failed for {content_type}, retrying..."
                )
                continue
            # Return raw text wrapped in a dict on second failure
            logger.error(f"JSON parse failed twice for {content_type}")
            return {"_raw": response.content[0].text, "_parse_error": True}

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


def track_generation(content_type: str):
    """Update generation stats."""
    gen_stats["total"] += 1
    gen_stats["by_type"][content_type] = (
        gen_stats["by_type"].get(content_type, 0) + 1
    )
    today = datetime.now().strftime("%Y-%m-%d")
    gen_stats["by_date"][today] = gen_stats["by_date"].get(today, 0) + 1


# ==============================================================================
# GITHUB PUBLISHING HELPER
# ==============================================================================


async def publish_to_github(
    repo: str, file_path: str, content: str, commit_msg: str
) -> bool:
    """Push a file to a GitHub repo. Returns True on success."""
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not set")
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    encoded = base64.b64encode(content.encode()).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        # Check if file exists (need sha for update)
        existing = await client.get(url, headers=headers)
        sha = None
        if existing.status_code == 200:
            sha = existing.json().get("sha")

        data = {
            "message": commit_msg,
            "content": encoded,
            "branch": "main",
        }
        if sha:
            data["sha"] = sha

        resp = await client.put(url, headers=headers, json=data)
        if resp.status_code in (200, 201):
            return True
        else:
            logger.error(
                f"GitHub publish failed: {resp.status_code} {resp.text}"
            )
            return False


async def post_to_channel(bot, text: str, parse_mode=ParseMode.MARKDOWN) -> tuple:
    """Post a message to the Telegram channel.

    Returns (True, "") on success or (False, error_detail) on failure.
    """
    if not TELEGRAM_CHANNEL:
        return False, "CHANNEL_ID not configured in environment variables"
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL,
            text=text[:TG_MAX_LEN],
            parse_mode=parse_mode,
            disable_web_page_preview=False,
        )
        return True, ""
    except Exception as e:
        logger.error(f"Channel post failed (parse_mode={parse_mode}): {e}")
        # Retry without parse_mode in case of markdown issues
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHANNEL,
                text=text[:TG_MAX_LEN],
            )
            return True, ""
        except Exception as e2:
            logger.error(f"Channel post retry failed: {e2}")
            return False, str(e2)


def detect_blog_category(title: str, topic: str = "") -> str:
    """Detect blog article category from title/topic text."""
    text = f"{title} {topic}".lower()
    if any(w in text for w in ["mito", "myth", "falso", "verdad o mentira"]):
        return "mitos"
    if any(w in text for w in [
        "real decreto", "boe", "consejo de estado", "audiencia",
        "ministerio", "actualización", "noticia", "borrador", "cronología",
        "update", "news",
    ]):
        return "noticias"
    if any(w in text for w in [
        "guía", "cómo", "paso a paso", "preparar", "documento",
        "certificado", "empadronamiento", "checklist",
    ]):
        return "guia"
    if any(w in text for w in [
        "vs", "comparación", "diferencia", "análisis", "impacto",
        "por qué", "tasa",
    ]):
        return "analisis"
    if any(w in text for w in [
        "historia", "testimonio", "vida", "cambió", "esperanza",
    ]):
        return "historias"
    return "guia"


async def update_blog_index(
    repo: str, slug: str, title: str, meta: str,
    html_content: str, category: str = "guia",
    date_override: str = None,
) -> bool:
    """Fetch blog/index.json, add new article entry, push updated JSON."""
    if not GITHUB_TOKEN:
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    index_url = f"https://api.github.com/repos/{repo}/contents/blog/index.json"

    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch current index.json
        resp = await client.get(index_url, headers=headers)
        if resp.status_code == 200:
            resp_data = resp.json()
            current_sha = resp_data.get("sha")
            current_content = json.loads(
                base64.b64decode(resp_data["content"]).decode("utf-8")
            )
        else:
            current_sha = None
            current_content = {"articles": []}

        # Build new entry
        word_count = len(html_content.split())
        new_entry = {
            "slug": slug,
            "title": title,
            "meta": meta,
            "date": date_override or datetime.now().strftime("%Y-%m-%d"),
            "published_at": date_override or datetime.now(timezone.utc).isoformat(),
            "reading_time": f"{max(1, word_count // 200)} min",
            "category": category,
            "image": None,
        }

        # Remove duplicate slugs
        current_content["articles"] = [
            a for a in current_content["articles"] if a.get("slug") != slug
        ]
        current_content["articles"].append(new_entry)
        # Sort by published_at descending (falls back to date for old articles)
        current_content["articles"].sort(
            key=lambda a: a.get("published_at", a.get("date", "")),
            reverse=True,
        )

        # Push updated index.json
        updated_json = json.dumps(current_content, ensure_ascii=False, indent=2)
        push_data = {
            "message": f"Update index: {title}",
            "content": base64.b64encode(updated_json.encode("utf-8")).decode("utf-8"),
            "branch": "main",
        }
        if current_sha:
            push_data["sha"] = current_sha

        push_resp = await client.put(index_url, headers=headers, json=push_data)
        if push_resp.status_code in (200, 201):
            return True
        else:
            logger.error(
                f"Index update failed: {push_resp.status_code} {push_resp.text}"
            )
            return False


async def update_estado_timeline(
    repo: str, title: str, summary: str, category: str,
    date_override: str = None,
) -> bool:
    """Inject a new timeline entry into the Estado section of index.html."""
    if not GITHUB_TOKEN:
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Fetch current index.html
    url = f"https://api.github.com/repos/{repo}/contents/index.html"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.error("Failed to fetch index.html for Estado update: %s", resp.status_code)
            return False

        resp_data = resp.json()
        current_sha = resp_data.get("sha")
        html_content = base64.b64decode(resp_data["content"]).decode("utf-8")

    # Map blog category to Estado tag
    tag_map = {
        "noticias": ("oficial", "Oficial"),
        "guia": ("tramitacion", "Tramitaci&oacute;n"),
        "mitos": ("tramitacion", "Tramitaci&oacute;n"),
        "analisis": ("tramitacion", "Tramitaci&oacute;n"),
        "historias": ("beneficio", "Beneficio"),
        "documentos": ("documento", "Documento"),
    }
    tag_class, tag_label = tag_map.get(category, ("tramitacion", "Tramitaci&oacute;n"))

    # Build date parts
    if date_override:
        try:
            dt = datetime.strptime(date_override[:10], "%Y-%m-%d")
        except ValueError:
            dt = datetime.now()
    else:
        dt = datetime.now()

    day = f"{dt.day:02d}"
    months_short = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                     "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    month_year = f"{months_short[dt.month]} {dt.year}"

    safe_title = html_mod.escape(title)
    safe_summary = html_mod.escape(summary[:200]) if summary else safe_title

    # Build the new timeline entry HTML
    new_entry = (
        f'\n                <!-- {day} {month_year} -->\n'
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
    marker_pos = html_content.find(marker)
    if marker_pos == -1:
        logger.error("Could not find updates-timeline marker in index.html")
        return False

    after = html_content[marker_pos:]
    first_comment = re.search(r'\n(\s*<!-- \d+ )', after)
    if first_comment:
        insert_pos = marker_pos + first_comment.start()
        updated_html = html_content[:insert_pos] + new_entry + html_content[insert_pos:]
    else:
        # Fallback: insert after the marker line
        end_of_marker_line = html_content.find('\n', marker_pos + len(marker))
        next_line_end = html_content.find('\n', end_of_marker_line + 1)
        insert_pos = next_line_end
        updated_html = html_content[:insert_pos] + new_entry + html_content[insert_pos:]

    # Update the timeline-entry date text
    months_full = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                   "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    today_str = f"{dt.day} de {months_full[dt.month]} de {dt.year}"
    updated_html = re.sub(
        r'(<span class="timeline-date">)[^<]+(</span>)',
        f'\\g<1>{today_str}\\g<2>',
        updated_html,
        count=1,
    )

    # Push updated index.html
    success = await publish_to_github(
        repo, "index.html", updated_html,
        f"Estado update: {title[:60]}"
    )
    return success


def wrap_blog_html(
    title: str, html_content: str, meta_description: str, date_str: str,
    slug: str = "article", category: str = "noticias",
) -> str:
    """Wrap article content in the full site template (nav, ticker, share, footer)."""
    safe_title = html_mod.escape(title)
    safe_meta = html_mod.escape(meta_description)

    cat_display_map = {
        "noticias": "Noticias", "guia": "Gu&iacute;a pr&aacute;ctica",
        "guias": "Gu&iacute;a pr&aacute;ctica", "mitos": "Mitos",
        "analisis": "An&aacute;lisis", "historias": "Historias",
        "documentos": "Documentos", "proceso": "Proceso",
    }
    cat_display = cat_display_map.get(category, category.title())

    word_count = len(html_content.split())
    reading_time = f"{max(1, word_count // 200)} min"

    return f"""<!-- Generated by Content Bot -->
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

        <!-- Prev/Next article navigation -->
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


# ==============================================================================
# NEWS FETCHING (multi-source: RSS + web scraping)
# ==============================================================================

NEWS_SOURCES = [
    {
        "name": "Google News - regularización",
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
        "name": "La Moncloa - Inclusión",
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
    # Fallback: try to decode base64 from the URL path
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


async def fetch_news() -> list:
    """Fetch latest regularización news from RSS feeds and web sources."""
    articles = []

    for source in NEWS_SOURCES:
        try:
            if source["type"] == "rss":
                feed = await asyncio.to_thread(feedparser.parse, source["url"])
                for entry in feed.entries[:5]:
                    source_title = source["name"]
                    if hasattr(entry, "source") and hasattr(entry.source, "title"):
                        source_title = entry.source.title
                    link = await asyncio.to_thread(resolve_google_news_url, entry.link)
                    articles.append({
                        "title": entry.title,
                        "link": link,
                        "source": source_title,
                        "published": getattr(entry, "published", ""),
                        "summary": getattr(entry, "summary", "")[:200],
                    })

            elif source["type"] == "web":
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        source["url"],
                        headers={"User-Agent": "Mozilla/5.0"},
                        follow_redirects=True,
                    )
                    if resp.status_code != 200:
                        continue
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for link in soup.find_all("a", href=True):
                            text = link.get_text().strip()
                            text_lower = text.lower()
                            if len(text) < 15:
                                continue
                            if any(kw in text_lower for kw in source["keywords"]):
                                href = link["href"]
                                if not href.startswith("http"):
                                    # Resolve relative URL
                                    from urllib.parse import urljoin
                                    href = urljoin(source["url"], href)
                                articles.append({
                                    "title": text[:150],
                                    "link": href,
                                    "source": source["name"],
                                    "published": "",
                                    "summary": "",
                                })
                    except ImportError:
                        logger.warning("beautifulsoup4 not installed, skipping web sources")
                        break

        except Exception as e:
            logger.error(f"News fetch error for {source['name']}: {e}")

    # Deduplicate by title similarity
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:15]


# ==============================================================================
# FORMATTING HELPERS
# ==============================================================================


def format_blog_for_telegram(data: dict) -> str:
    """Format blog article for Telegram message."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    word_count = data.get(
        "word_count", len(data.get("html_content", "").split())
    )
    reading_time = max(1, word_count // 200)

    # Strip HTML tags for Telegram preview
    html = data.get("html_content", "")
    plain = re.sub(r"<[^>]+>", "", html)

    return (
        f"📝 *BLOG ARTICLE READY*\n\n"
        f"*Title:* {escape_md(data.get('title', 'Sin título'))}\n"
        f"*Meta:* {escape_md(data.get('meta_description', ''))}\n"
        f"*Slug:* {data.get('slug', '')}\n"
        f"*Words:* {word_count} | *Reading time:* {reading_time} min\n\n"
        f"---ARTICLE START---\n"
        f"{escape_md(plain[:3000])}\n"
        f"---ARTICLE END---"
    )


def format_tiktok_for_telegram(data: dict) -> str:
    """Format TikTok script for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    overlays = data.get("text_overlays", [])
    overlays_text = "\n".join(
        f"  {i + 1}. {escape_md(o)}" for i, o in enumerate(overlays)
    )

    invideo = data.get("invideo_prompt", "")
    invideo_section = ""
    if invideo:
        invideo_section = (
            f"\n\n---INVIDEO PROMPT (paste into invideo.ai)---\n"
            f"{escape_md(invideo)}\n"
            f"---END---"
        )

    return (
        f"🎬 *TIKTOK SCRIPT*\n\n"
        f"*Format:* {escape_md(data.get('format', 'face-to-camera'))}\n"
        f"*Duration:* ~{data.get('duration_seconds', 25)}s\n\n"
        f"🎯 *HOOK (first 2 sec):*\n\"{escape_md(data.get('hook', ''))}\"\n\n"
        f"📝 *SCRIPT:*\n\"{escape_md(data.get('script', ''))}\"\n\n"
        f"📱 *TEXT OVERLAYS:*\n{overlays_text}\n\n"
        f"#️⃣ {escape_md(data.get('hashtags', ''))}"
        f"{invideo_section}\n\n"
        f"💡 *TIP:* {escape_md(data.get('production_tip', ''))}"
    )


def format_carousel_for_telegram(data: dict) -> str:
    """Format Instagram carousel for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    slides = data.get("slides", [])
    slides_text = ""
    for s in slides:
        # Title with 4-space indent
        title = s.get("title", s.get("headline", ""))
        slides_text += f"\n*Slide {s.get('slide_number', '?')}:*\n"
        slides_text += f"    {escape_md(title)}\n"
        # Bullets with 2-space indent
        bullets = s.get("bullets", [])
        if isinstance(bullets, list):
            for b in bullets:
                slides_text += f"  {escape_md(b)}\n"
        elif s.get("body"):
            slides_text += f"  {escape_md(s['body'])}\n"
        # Tip box
        tip_box = s.get("tip_box")
        if tip_box:
            slides_text += f"  {escape_md(tip_box)}\n"

    num_slides = len(slides)

    return (
        f"📸 *INSTAGRAM CAROUSEL*\n\n"
        f"*Topic:* {escape_md(data.get('topic', ''))}\n"
        f"*Slides:* {num_slides}\n"
        f"{slides_text}\n"
        f"*CAPTION:*\n{escape_md(data.get('caption', ''))}\n\n"
        f"#️⃣ {escape_md(data.get('hashtags', ''))}"
    )


def format_caption_for_telegram(data: dict) -> str:
    """Format social media caption for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    return (
        f"✏️ *SOCIAL MEDIA CAPTION*\n\n"
        f"*Platform:* {escape_md(data.get('platform', 'general'))}\n\n"
        f"📝 *Caption:*\n{escape_md(data.get('caption_text', ''))}\n\n"
        f"#️⃣ {escape_md(data.get('hashtags', ''))}\n\n"
        f"👉 *CTA:* {escape_md(data.get('cta', ''))}"
    )


def format_whatsapp_for_telegram(data: dict) -> str:
    """Format WhatsApp message for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    return (
        f"📱 *WHATSAPP MESSAGE*\n\n"
        f"*Type:* {escape_md(data.get('type', 'general'))}\n"
        f"*Send at:* {escape_md(data.get('suggested_send_time', 'any'))}\n\n"
        f"💬 *Message:*\n{escape_md(data.get('message_text', ''))}\n\n"
        f"_{len(data.get('message_text', ''))} characters_"
    )


def format_fbpost_for_telegram(data: dict) -> str:
    """Format Facebook post for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    groups = data.get("suggested_groups", [])
    groups_text = ", ".join(groups) if groups else "N/A"

    return (
        f"📘 *FACEBOOK POST*\n\n"
        f"📝 *Post:*\n{escape_md(data.get('post_text', ''))}\n\n"
        f"🎯 *Suggested groups:* {escape_md(groups_text)}\n"
        f"🔗 *CTA link:* {escape_md(data.get('cta_link', ''))}"
    )


def format_story_for_telegram(data: dict) -> str:
    """Format Instagram Story for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    stat = data.get("stat", "none")
    stat_line = f"*Stat:* {escape_md(stat)}\n" if stat and stat.lower() != "none" else ""

    return (
        f"📱 *INSTAGRAM STORY*\n\n"
        f"*Type:* {escape_md(data.get('type', 'tip'))}\n"
        f"*Topic:* {escape_md(data.get('topic', ''))}\n"
        f"*Background:* {escape_md(data.get('background', ''))}\n"
        f"*Label:* {escape_md(data.get('label', ''))}\n\n"
        f"{stat_line}"
        f"*Title:* {escape_md(data.get('title', ''))}\n\n"
        f"*Body:* {escape_md(data.get('body', ''))}\n\n"
        f"🎨 *Sticker:* {escape_md(data.get('sticker', ''))}\n"
        f"👉 *CTA:* {escape_md(data.get('cta', ''))}"
    )


def escape_md(text: str) -> str:
    """Escape special Markdown characters for Telegram Markdown mode.

    Only escapes characters that are problematic in Telegram's Markdown parser
    while preserving intentional formatting.
    """
    if not text:
        return ""
    # Replace characters that could break Telegram's markdown parsing
    # but preserve * for our own bold formatting
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("`", "\\`")
    return text


FORMATTERS = {
    "blog": format_blog_for_telegram,
    "tiktok": format_tiktok_for_telegram,
    "carousel": format_carousel_for_telegram,
    "caption": format_caption_for_telegram,
    "whatsapp": format_whatsapp_for_telegram,
    "fbpost": format_fbpost_for_telegram,
    "story": format_story_for_telegram,
}


# ==============================================================================
# CHANNEL FORMATTERS — for @tuspapeles2026 channel posts
# ==============================================================================


def channel_blog(data: dict) -> str:
    """Format blog article for channel post."""
    title = data.get("title", "Sin título")
    meta = data.get("meta_description", "")
    slug = data.get("slug", "article")
    url = f"https://tuspapeles2026.es/blog/{slug}.html"
    return (
        f"📝 *{title}*\n\n"
        f"{meta}\n\n"
        f"👉 Lee el artículo completo: {url}\n\n"
        f"@tuspapeles2026"
    )


def channel_tiktok(data: dict) -> str:
    """Format TikTok script for channel post."""
    hook = data.get("hook", "")
    script = data.get("script", "")
    hashtags = data.get("hashtags", "")
    return (
        f"🎬 *NUEVO TIKTOK*\n\n"
        f"🎯 *Hook:* {hook}\n\n"
        f"📝 {script}\n\n"
        f"{hashtags}\n\n"
        f"@tuspapeles2026"
    )


def channel_carousel(data: dict) -> str:
    """Format carousel for channel post."""
    topic = data.get("topic", "")
    slides = data.get("slides", [])
    slides_text = ""
    for s in slides:
        title = s.get("title", s.get("headline", ""))
        slides_text += f"📌 {title}\n"
    caption = data.get("caption", "")
    return (
        f"📸 *NUEVO CAROUSEL: {topic}*\n\n"
        f"{slides_text}\n"
        f"{caption}\n\n"
        f"@tuspapeles2026"
    )


def channel_caption(data: dict) -> str:
    """Format caption for channel post."""
    platform = data.get("platform", "general")
    caption_text = data.get("caption_text", "")
    hashtags = data.get("hashtags", "")
    return (
        f"✏️ *CAPTION ({platform})*\n\n"
        f"{caption_text}\n\n"
        f"{hashtags}\n\n"
        f"@tuspapeles2026"
    )


def channel_whatsapp(data: dict) -> str:
    """Format WhatsApp message for channel post."""
    msg_type = data.get("type", "general")
    message = data.get("message_text", "")
    return (
        f"📱 *MENSAJE WHATSAPP ({msg_type})*\n\n"
        f"{message}\n\n"
        f"@tuspapeles2026"
    )


def channel_fbpost(data: dict) -> str:
    """Format Facebook post for channel post."""
    post_text = data.get("post_text", "")
    return (
        f"📘 *FACEBOOK POST*\n\n"
        f"{post_text}\n\n"
        f"@tuspapeles2026"
    )


def channel_story(data: dict) -> str:
    """Format Instagram Story for channel post."""
    title = data.get("title", "")
    body = data.get("body", "")
    cta = data.get("cta", "")
    return (
        f"📱 *INSTAGRAM STORY*\n\n"
        f"*{title}*\n\n"
        f"{body}\n\n"
        f"👉 {cta}\n\n"
        f"@tuspapeles2026"
    )


CHANNEL_FORMATTERS = {
    "blog": channel_blog,
    "tiktok": channel_tiktok,
    "carousel": channel_carousel,
    "caption": channel_caption,
    "whatsapp": channel_whatsapp,
    "fbpost": channel_fbpost,
    "story": channel_story,
}


def format_content_for_channel(content_type: str, data: dict) -> str:
    """Route to the appropriate channel formatter."""
    formatter = CHANNEL_FORMATTERS.get(content_type)
    if formatter:
        return formatter(data)
    return f"📢 Nuevo contenido disponible\n\n@tuspapeles2026"


# ==============================================================================
# TELEGRAM MESSAGE HELPERS
# ==============================================================================


async def send_long_message(
    update_or_chat,
    text: str,
    context: ContextTypes.DEFAULT_TYPE,
    parse_mode=ParseMode.MARKDOWN,
    reply_markup=None,
    chat_id=None,
):
    """Send a message, splitting if it exceeds Telegram's limit."""
    if chat_id is None:
        chat_id = (
            update_or_chat.effective_chat.id
            if hasattr(update_or_chat, "effective_chat")
            else update_or_chat
        )

    if len(text) <= TG_MAX_LEN:
        return await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )

    # Split into chunks
    chunks = []
    while text:
        if len(text) <= TG_MAX_LEN:
            chunks.append(text)
            break
        # Find a good break point
        split_at = text.rfind("\n", 0, TG_MAX_LEN)
        if split_at == -1:
            split_at = TG_MAX_LEN
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    last_msg = None
    for i, chunk in enumerate(chunks):
        markup = reply_markup if i == len(chunks) - 1 else None
        try:
            last_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=parse_mode,
                reply_markup=markup,
            )
        except Exception:
            # Fallback: send without markdown if parsing fails
            last_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=chunk,
                reply_markup=markup,
            )
    return last_msg


async def send_as_file(
    chat_id: int,
    content: str,
    filename: str,
    caption: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Send content as a text file attachment."""
    file_bytes = content.encode("utf-8")
    bio = io.BytesIO(file_bytes)
    bio.name = filename
    await context.bot.send_document(
        chat_id=chat_id,
        document=bio,
        caption=caption[:1024],  # Telegram caption limit
    )


# ==============================================================================
# COMMAND HANDLERS — SINGLE GENERATION
# ==============================================================================


@team_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome = (
        "🤖 *Content Bot v3.0*\n\n"
        "AI Content Factory for tuspapeles2026.es\n"
        f"Phase: *{get_current_phase()}*\n\n"
        "Type /help to see all commands."
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)


@team_only
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 *Content Bot v4\\.1 — Commands*\n\n"
        "📐 *Ángulos:* fear|hope|urgency|proof|humor|curiosity|ad\n"
        "Usa /ideas para ver ejemplos de cada ángulo\\.\n\n"
        "*Predis auto\\-post \\(Claude → Predis\\.ai\\):*\n"
        "  /carousel \\[angle\\] \\[topic\\] — Carrusel branded\n"
        "  /image \\[angle\\] \\[topic\\] — Imagen única\n"
        "  /reel \\[angle\\] \\[topic\\] — Reel/vídeo corto\n"
        "  /meme \\[topic\\] — Meme \\(humor auto\\)\n"
        "  /quote \\[topic\\] — Frase motivacional\n\n"
        "*InVideo manual \\(Claude guión → copiar a InVideo\\):*\n"
        "  /video \\[angle\\] \\[topic\\] — Guión de vídeo\n"
        "  /video ad \\[topic\\] — Anuncio premium \\(5 estilos\\)\n"
        "  /video5 — 5 guiones variados\n\n"
        "*Texto \\(Claude directo\\):*\n"
        "  /blog \\[topic|noticias|guias|mitos\\] — Artículo SEO\n"
        "  /whatsapp \\[angle\\] \\[topic\\] — Mensaje WhatsApp\n"
        "  /fbtext \\[angle\\] \\[topic\\] — Post Facebook\n\n"
        "*Automatización:*\n"
        "  /daily — Generar contenido del día \\(videos \\+ textos\\)\n"
        "  /daily force — Regenerar todo aunque ya se ejecutó\n"
        "  ⏰ Predis se auto\\-genera a las 7:30am España\n\n"
        "*Planificación:*\n"
        "  /weekly — Pack semanal \\(25 piezas\\)\n"
        "  /ideas — Ejemplos de comandos por tipo\n"
        "  /news — Noticias regularización\n\n"
        "*Herramientas:*\n"
        "  /articles — Artículos publicados\n"
        "  /delete \\[slug|nº\\] — Eliminar artículo\n"
        "  /stats — Estadísticas de contenido\n"
        "  /predis — Test conexión Predis\\.ai\n"
        "  /help — Este mensaje"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)


@team_only
async def cmd_ideas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ideas — show example commands per media type with angles."""
    ideas_text = (
        "💡 <b>IDEAS — Ejemplos de comandos por tipo</b>\n\n"
        "<b>🎠 Carrusel (Predis):</b>\n"
        "<code>/carousel fear ¿Es seguro dar mis datos?</code>\n"
        "<code>/carousel hope Tu nueva vida con papeles</code>\n"
        "<code>/carousel urgency Solo quedan 8 semanas</code>\n\n"
        "<b>🖼 Imagen (Predis):</b>\n"
        "<code>/image proof 10.000 familias ya se preparan</code>\n"
        "<code>/image curiosity ¿Sabías que no necesitas contrato?</code>\n\n"
        "<b>🎬 Reel (Predis):</b>\n"
        "<code>/reel humor Cuando te piden el NIE por quinta vez</code>\n"
        "<code>/reel hope El día que todo cambia</code>\n\n"
        "<b>😂 Meme (Predis):</b>\n"
        "<code>/meme Cuando el abogado cobra €450 y tú pagas €199</code>\n\n"
        "<b>✨ Frase (Predis):</b>\n"
        "<code>/quote Ningún papel define tu valor</code>\n\n"
        "<b>🎥 Vídeo (InVideo manual):</b>\n"
        "<code>/video fear ¿Qué pasa si no presento a tiempo?</code>\n"
        "<code>/video ad Historia de María: de sin papeles a emprendedora</code>\n"
        "<code>/video5</code> — 5 guiones variados\n\n"
        "<b>📝 Texto (Claude):</b>\n"
        "<code>/blog regularización paso a paso</code>\n"
        "<code>/whatsapp urgency El plazo cierra en junio</code>\n"
        "<code>/fbtext proof Miles ya están preparados</code>\n\n"
        "<b>📦 Pack:</b>\n"
        "<code>/weekly</code> — 25 piezas con rotación de ángulos"
    )
    await update.message.reply_text(ideas_text, parse_mode=ParseMode.HTML)


@team_only
async def cmd_blog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /blog [topic|category] command.

    /blog             → suggest 3 topics from different categories
    /blog noticias    → suggest 3 news topics
    /blog <topic>     → generate article on that topic
    """
    args_text = " ".join(context.args) if context.args else ""

    # Check if arg is a category filter
    category_filter = None
    if args_text.lower() in BLOG_TOPICS:
        category_filter = args_text.lower()
        args_text = ""

    if not args_text:
        # Suggest 3 topics from local pool (instant, no API call)
        suggestions = suggest_blog_topics(category_filter, count=3)

        buttons = []
        for s in suggestions:
            icon = BLOG_CATEGORY_ICONS.get(s["category"], "📝")
            label = f"{icon} {s['topic']}"[:60]
            cb_data = f"blog_{s['topic'][:40]}"
            buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])

        cat_label = f" ({category_filter})" if category_filter else ""
        markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            f"📝 *Choose a blog topic{cat_label}:*",
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    topic = args_text

    wait_msg = await update.message.reply_text("⏳ Generating blog article...")
    try:
        data = await generate_content("blog", topic)

        # Store article for publish buttons
        article_id = hashlib.md5(
            json.dumps(data, default=str).encode()
        ).hexdigest()[:8]
        pending_articles[article_id] = data

        buttons = [
            [
                InlineKeyboardButton(
                    "🌐 Publicar en web", callback_data=f"pub_tp_{article_id}"
                ),
                InlineKeyboardButton(
                    "📢 Canal", callback_data=f"pub_ch_{article_id}"
                ),
            ]
        ]
        markup = InlineKeyboardMarkup(buttons)

        await wait_msg.delete()

        word_count = data.get("word_count", len(data.get("html_content", "").split()))
        reading_time = max(1, word_count // 200)
        category = detect_blog_category(data.get("title", ""), topic)

        # Always send short summary + publish buttons + file attachment
        meta_msg = (
            f"📝 *BLOG ARTICLE READY*\n\n"
            f"*Title:* {escape_md(data.get('title', 'Sin título'))}\n"
            f"*Meta:* {escape_md(data.get('meta_description', ''))}\n"
            f"*Slug:* {data.get('slug', '')}\n"
            f"*Category:* {category}\n"
            f"*Words:* {word_count} | *Reading time:* {reading_time} min\n\n"
            f"Full article attached as HTML file below."
        )
        await send_long_message(
            update, meta_msg, context, reply_markup=markup
        )
        html_content = data.get("html_content", "")
        await send_as_file(
            update.effective_chat.id,
            html_content,
            f"{data.get('slug', 'article')}.html",
            f"📝 {data.get('title', 'Blog article')}",
            context,
        )

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating blog: {e}")


async def _generate_premium_video(update, context, user_topic):
    """Generate a premium emotional ad video script (ad angle)."""
    topic_data = smart_pick_topic(content_type="tiktok", angle="ad", user_topic=user_topic if user_topic else None)
    topic = topic_data["text"]

    wait_msg = await update.message.reply_text(
        "\U0001f3ac\u2728 Generando ANUNCIO PREMIUM..."
    )

    premium_prompt = (
        "Genera un guión para un ANUNCIO EMOCIONAL de vídeo corto para redes sociales "
        "(TikTok/Instagram Reels) en español (España) sobre: " + topic + "\n\n"
        "ESTO NO ES UN EXPLAINER. Es un ANUNCIO EMOCIONAL tipo TV.\n\n"
        "ELIGE UNO de estos 5 estilos:\n"
        "1. TESTIMONIO: Historia en primera persona. 'Yo llegué a España hace 3 años...'\n"
        "2. CONTRASTE: Vida sin papeles vs vida con papeles. Dos realidades.\n"
        "3. CUENTA ATRÁS: Reloj, fechas, urgencia. 'Quedan X semanas...'\n"
        "4. CASCADA: Cascada de preguntas que el espectador se hace. '¿Y si...?'\n"
        "5. MINI PELÍCULA: Un día en la vida de alguien preparándose.\n\n"
        "REGLAS:\n"
        "- 20-30 segundos de duración\n"
        "- Máximo 75 palabras habladas\n"
        "- Abre con EMOCIÓN, no con información\n"
        "- Arco narrativo: emoción → tensión → resolución → acción\n"
        "- Línea de cierre memorable\n"
        "- Momentos de silencio/pausa para impacto\n"
        "- BRANDING: Esto es un anuncio para tuspapeles2026.es. Incluir logo.\n\n"
        "CONTEXTO: tuspapeles2026.es — regularización 2026, desde €199, "
        "IA + abogados reales, 5 meses residencia, abril-junio, 80-90% aprobación.\n\n"
        "Devuelve SOLO JSON válido con esta estructura:\n"
        '{"ad_style": "testimonio|contraste|cuenta_atras|cascada|mini_pelicula", '
        '"duration_seconds": number (20-30), '
        '"hook": "string (primeros 2 segundos — pura emoción)", '
        '"script": "string (guión hablado completo — máx 75 palabras)", '
        '"visual_direction": "string (descripción de escenas y transiciones)", '
        '"closing_line": "string (línea de cierre memorable)", '
        '"text_overlays": ["string", "string", "string"], '
        '"music_mood": "string (estado de ánimo de la música)", '
        '"invideo_prompt": "string (prompt completo para InVideo AI — '
        "debe empezar con 'Create a [DURATION]-second vertical ad video for social media' "
        "y terminar con 'BRANDING: This is a promotional ad for tuspapeles2026.es. "
        "Include brand logo placement.')\"}"
    )

    try:
        result = await generate_content(
            "tiktok", topic, override_prompt=premium_prompt,
        )

        # Try to parse as JSON
        data = None
        if isinstance(result, str):
            text = result.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:])
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

        await wait_msg.delete()

        if data and isinstance(data, dict):
            # Format nicely
            style = data.get("ad_style", "?")
            duration = data.get("duration_seconds", "?")
            hook = data.get("hook", "")
            script = data.get("script", "")
            visual = data.get("visual_direction", "")
            closing = data.get("closing_line", "")
            overlays = data.get("text_overlays", [])
            music = data.get("music_mood", "")
            invideo = data.get("invideo_prompt", "")

            overlays_text = "\n".join(
                f"  {i+1}. {escape_md(o)}" for i, o in enumerate(overlays)
            ) if overlays else "  (none)"

            formatted = (
                f"\U0001f3ac\u2728 *ANUNCIO PREMIUM*\n\n"
                f"*Estilo:* {escape_md(style)}\n"
                f"*Duración:* ~{duration}s\n\n"
                f"\U0001f3af *HOOK (2s):*\n\"{escape_md(hook)}\"\n\n"
                f"\U0001f4dd *GUIÓN:*\n\"{escape_md(script)}\"\n\n"
                f"\U0001f3ac *DIRECCIÓN VISUAL:*\n{escape_md(visual)}\n\n"
                f"\U0001f3ac *CIERRE:*\n\"{escape_md(closing)}\"\n\n"
                f"\U0001f4f1 *TEXT OVERLAYS:*\n{overlays_text}\n\n"
                f"\U0001f3b5 *MÚSICA:* {escape_md(music)}"
            )

            if invideo:
                formatted += (
                    f"\n\n---INVIDEO PROMPT (paste into invideo.ai)---\n"
                    f"{escape_md(invideo)}\n"
                    f"---END---"
                )

            post_id = hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]
            pending_channel_posts[post_id] = {"type": "tiktok", "data": data}
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "\U0001f4e2 Publicar en canal",
                    callback_data=f"chpost_{post_id}",
                )
            ]])
            await send_long_message(update, formatted, context, reply_markup=markup)
        else:
            # Fallback: raw text
            raw = result if isinstance(result, str) else str(result)
            formatted = (
                f"\U0001f3ac\u2728 *ANUNCIO PREMIUM*\n\n"
                f"{escape_md(raw[:3500])}"
            )
            await send_long_message(update, formatted, context)

        log_content("video_ad", "ad", topic, "invideo")

    except Exception as e:
        logger.error(f"Premium video error: {e}")
        await wait_msg.edit_text(f"\u274c Error generando anuncio premium: {e}")


@team_only
async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /video [angle] [topic] — generate video script with angle support."""
    args = context.args if context.args else []
    angle, user_topic = parse_angle_and_topic(args)

    # Ad angle → premium video pipeline
    if angle == "ad":
        await _generate_premium_video(update, context, user_topic)
        return

    topic_data = smart_pick_topic(content_type="tiktok", angle=angle, user_topic=user_topic if user_topic else None)
    topic = topic_data["text"]
    angle_label = f" [\U0001f3af {angle}]" if angle else ""
    wait_msg = await update.message.reply_text(f"\u23f3 Generating video script{angle_label}...")
    try:
        data = await generate_content("tiktok", topic)
        formatted = format_tiktok_for_telegram(data)
        post_id = hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]
        pending_channel_posts[post_id] = {"type": "tiktok", "data": data}
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001f4e2 Publicar en canal", callback_data=f"chpost_{post_id}")
        ]])
        await wait_msg.delete()
        await send_long_message(update, formatted, context, reply_markup=markup)
        log_content("video", angle, topic, "invideo")
    except Exception as e:
        await wait_msg.edit_text(f"\u274c Error generating video: {e}")


async def _send_carousel_media(chat_id: int, carousel_data: dict, context: ContextTypes.DEFAULT_TYPE):
    """Render and send carousel slides as images, video, and PDF."""
    from carousel_renderer import render_carousel

    logo_wide = os.path.join(LOGO_DIR, "tp2026.png")
    logo_sq = os.path.join(LOGO_DIR, "tp26sqlogo.png")

    slide_pngs, mp4_bytes, pdf_bytes = await asyncio.to_thread(
        render_carousel, carousel_data, logo_wide, logo_sq
    )

    topic_short = carousel_data.get("topic", "carousel")[:30]

    # Send slides as media group (Telegram max 10 per group)
    if slide_pngs:
        media = []
        for i, png in enumerate(slide_pngs[:10]):
            buf = io.BytesIO(png)
            buf.name = f"slide_{i + 1:02d}.png"
            media.append(InputMediaPhoto(media=buf))
        await context.bot.send_media_group(chat_id=chat_id, media=media)

    # Send MP4 video
    if mp4_bytes:
        mp4_buf = io.BytesIO(mp4_bytes)
        mp4_buf.name = f"carousel-{topic_short}.mp4"
        await context.bot.send_video(
            chat_id=chat_id, video=mp4_buf,
            caption="Video listo para Reels/TikTok/Stories",
            supports_streaming=True,
        )

    # Send PDF
    if pdf_bytes:
        pdf_buf = io.BytesIO(pdf_bytes)
        pdf_buf.name = f"carousel-{topic_short}.pdf"
        await context.bot.send_document(
            chat_id=chat_id, document=pdf_buf,
            caption="PDF para compartir por WhatsApp",
        )






@team_only
async def cmd_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /whatsapp [angle] [type/topic] command."""
    args = context.args if context.args else []
    angle, remaining = parse_angle_and_topic(args)

    valid_types = ["news", "deadline", "educational", "referral", "re-engagement"]
    msg_type = remaining.split()[0] if remaining else ""
    user_topic = None
    if msg_type in valid_types:
        user_topic = f"type: {msg_type}"
    elif remaining:
        user_topic = remaining
    topic_data = smart_pick_topic(content_type="whatsapp", angle=angle, user_topic=user_topic)
    topic = topic_data["text"]

    angle_label = f" [\U0001f3af {angle}]" if angle else ""
    wait_msg = await update.message.reply_text(f"\u23f3 Generating WhatsApp message{angle_label}...")
    try:
        data = await generate_content("whatsapp", topic)
        formatted = format_whatsapp_for_telegram(data)
        post_id = hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]
        pending_channel_posts[post_id] = {"type": "whatsapp", "data": data}
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001f4e2 Publicar en canal", callback_data=f"chpost_{post_id}")
        ]])
        await wait_msg.delete()
        await send_long_message(update, formatted, context, reply_markup=markup)
    except Exception as e:
        await wait_msg.edit_text(f"\u274c Error generating WhatsApp message: {e}")


@team_only
async def cmd_fbtext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fbtext [angle] [topic] — generate Facebook post with angle support."""
    args = context.args if context.args else []
    angle, user_topic = parse_angle_and_topic(args)
    topic_data = smart_pick_topic(content_type="fbpost", angle=angle, user_topic=user_topic if user_topic else None)
    topic = topic_data["text"]
    angle_label = f" [\U0001f3af {angle}]" if angle else ""
    wait_msg = await update.message.reply_text(f"\u23f3 Generating Facebook text{angle_label}...")
    try:
        data = await generate_content("fbpost", topic)
        formatted = format_fbpost_for_telegram(data)
        post_id = hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()[:8]
        pending_channel_posts[post_id] = {"type": "fbpost", "data": data}
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("\U0001f4e2 Publicar en canal", callback_data=f"chpost_{post_id}")
        ]])
        await wait_msg.delete()
        await send_long_message(update, formatted, context, reply_markup=markup)
    except Exception as e:
        await wait_msg.edit_text(f"\u274c Error generating FB text: {e}")



# ==============================================================================
# COMMAND HANDLERS — BATCH GENERATION
# ==============================================================================


async def _batch_generate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    content_type: str,
    count: int,
    topics: list = None,
):
    """Generate multiple pieces of content with progress updates."""
    chat_id = update.effective_chat.id
    formatter = FORMATTERS.get(content_type, lambda d: str(d))

    progress_msg = await update.message.reply_text(
        f"📦 Generating {content_type} 1/{count}..."
    )

    success_count = 0
    for i in range(count):
        topic = topics[i] if topics and i < len(topics) else ""

        try:
            await progress_msg.edit_text(
                f"📦 Generating {content_type} {i + 1}/{count}..."
            )
        except Exception:
            pass

        try:
            data = await generate_content(content_type, topic)
            formatted = formatter(data)

            # For blog articles, add publish buttons
            reply_markup = None
            if content_type == "blog":
                article_id = hashlib.md5(
                    json.dumps(data, default=str).encode()
                ).hexdigest()[:8]
                pending_articles[article_id] = data
                buttons = [
                    [
                        InlineKeyboardButton(
                            "🌐 Publicar en web",
                            callback_data=f"pub_tp_{article_id}",
                        ),
                        InlineKeyboardButton(
                            "📢 Canal",
                            callback_data=f"pub_ch_{article_id}",
                        ),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(buttons)

            await send_long_message(
                update,
                formatted,
                context,
                reply_markup=reply_markup,
            )

            # Render carousel images/video/PDF
            if content_type == "carousel":
                try:
                    await _send_carousel_media(chat_id, data, context)
                except Exception as render_err:
                    logger.error(f"Carousel render failed: {render_err}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Imágenes no generadas: {render_err}",
                    )

            success_count += 1

        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Error on {content_type} {i + 1}/{count}: {e}",
            )

        # Rate limit delay
        if i < count - 1:
            await asyncio.sleep(1.5)

    try:
        await progress_msg.edit_text(
            f"✅ *{content_type.upper()} BATCH DONE* — {success_count}/{count} generated",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    return success_count


@team_only
async def cmd_video5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /video5 — generate 5 video scripts."""
    topics = pick_multiple_topics("tiktok", 5)
    await _batch_generate(update, context, "tiktok", 5, topics)



# ==============================================================================
# COMMAND HANDLERS — WEEKLY MEGA-BATCH
# ==============================================================================


@team_only
async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weekly — generate full weekly content pack (25 pieces)."""
    chat_id = update.effective_chat.id

    # Check cooldown
    last = gen_stats.get("last_weekly")
    if last and (datetime.now() - last) < timedelta(hours=24):
        hours_ago = (datetime.now() - last).total_seconds() / 3600
        buttons = [
            [
                InlineKeyboardButton("Sí, generar", callback_data="weekly_confirm"),
                InlineKeyboardButton("Cancelar", callback_data="weekly_cancel"),
            ]
        ]
        await update.message.reply_text(
            f"⚠️ Último /weekly hace {hours_ago:.1f} horas. ¿Seguro?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    await _run_weekly(update, context)


async def _run_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the full weekly generation — 25 pieces with angle rotation.

    Phase 1 (Claude text, 11 pieces):
      4 video scripts (curiosity, fear, urgency, hope)
      1 premium ad video
      2 blog articles
      2 whatsapp (urgency, curiosity)
      2 fbtext (proof, curiosity)

    Phase 2 (Predis, 14 pieces, batches of 3):
      5 carousels (fear, hope, urgency, proof, curiosity)
      3 images (urgency, curiosity, proof)
      2 reels (humor, hope)
      2 memes (humor x2)
      2 quotes (hope x2)
    """
    chat_id = update.effective_chat.id
    gen_stats["last_weekly"] = datetime.now()

    await context.bot.send_message(
        chat_id=chat_id,
        text="🚀 <b>WEEKLY PACK — 25 piezas con rotación de ángulos</b>\n"
             "Fase 1: 11 piezas Claude | Fase 2: 14 piezas Predis",
        parse_mode=ParseMode.HTML,
    )

    piece = 0
    success = 0
    errors = 0

    # ── PHASE 1: CLAUDE TEXT (11 pieces) ──────────────────────────────
    await context.bot.send_message(
        chat_id=chat_id,
        text="📝 <b>FASE 1/2 — Texto (Claude)</b>",
        parse_mode=ParseMode.HTML,
    )

    # 4 video scripts with angles
    video_angles = ["curiosity", "fear", "urgency", "hope"]
    for angle in video_angles:
        piece += 1
        topic_data = smart_pick_topic(content_type="tiktok", angle=angle)
        topic = topic_data["text"]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ Generando pieza {piece}/25 — video [{angle}]...",
        )
        try:
            data = await generate_content("tiktok", topic)
            formatted = format_tiktok_for_telegram(data)
            await send_long_message(update, formatted, context)
            log_content("video", angle, topic, "invideo")
            success += 1
        except Exception as e:
            logger.error(f"weekly video [{angle}]: {e}")
            errors += 1

    # 1 premium ad video
    piece += 1
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏳ Generando pieza {piece}/25 — video premium [ad]...",
    )
    try:
        ad_data = smart_pick_topic(content_type="tiktok", angle="ad")
        await _generate_premium_video(update, context, ad_data["text"])
        success += 1
    except Exception as e:
        logger.error(f"weekly premium ad: {e}")
        errors += 1

    # 2 blog articles
    blog_topics = pick_multiple_topics("blog", 2)
    for i, topic in enumerate(blog_topics):
        piece += 1
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ Generando pieza {piece}/25 — blog...",
        )
        try:
            data = await generate_content("blog", topic)
            formatted = format_blog_for_telegram(data)
            article_id = hashlib.md5(
                json.dumps(data, default=str).encode()
            ).hexdigest()[:8]
            pending_articles[article_id] = data
            buttons = [
                [
                    InlineKeyboardButton(
                        "🌐 Publicar en web",
                        callback_data=f"pub_tp_{article_id}",
                    ),
                    InlineKeyboardButton(
                        "📢 Canal",
                        callback_data=f"pub_ch_{article_id}",
                    ),
                ]
            ]
            await send_long_message(
                update, formatted, context,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            log_content("blog", None, topic, "claude")
            success += 1
        except Exception as e:
            logger.error(f"weekly blog: {e}")
            errors += 1

    # 2 whatsapp (urgency, curiosity)
    wa_angles = ["urgency", "curiosity"]
    for angle in wa_angles:
        piece += 1
        topic_data = smart_pick_topic(content_type="whatsapp", angle=angle)
        topic = topic_data["text"]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ Generando pieza {piece}/25 — whatsapp [{angle}]...",
        )
        try:
            data = await generate_content("whatsapp", topic)
            formatted = format_whatsapp_for_telegram(data)
            await send_long_message(update, formatted, context)
            log_content("whatsapp", angle, topic, "claude")
            success += 1
        except Exception as e:
            logger.error(f"weekly whatsapp [{angle}]: {e}")
            errors += 1

    # 2 fbtext (proof, curiosity)
    fb_angles = ["proof", "curiosity"]
    for angle in fb_angles:
        piece += 1
        topic_data = smart_pick_topic(content_type="fbpost", angle=angle)
        topic = topic_data["text"]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏳ Generando pieza {piece}/25 — fbtext [{angle}]...",
        )
        try:
            data = await generate_content("fbpost", topic)
            formatted = format_fbpost_for_telegram(data)
            await send_long_message(update, formatted, context)
            log_content("fbtext", angle, topic, "claude")
            success += 1
        except Exception as e:
            logger.error(f"weekly fbtext [{angle}]: {e}")
            errors += 1

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Fase 1 completa — {success} textos generados",
    )

    # ── PHASE 2: PREDIS (14 pieces, batches of 3) ────────────────────
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎨 <b>FASE 2/2 — Predis.ai (branded)</b>",
        parse_mode=ParseMode.HTML,
    )

    # Define all Predis pieces: (content_type, prompt_template, media_type, angle)
    predis_pieces = [
        ("carousel", CAROUSEL_PROMPT_V4, "carousel", "fear"),
        ("carousel", CAROUSEL_PROMPT_V4, "carousel", "hope"),
        ("carousel", CAROUSEL_PROMPT_V4, "carousel", "urgency"),
        ("carousel", CAROUSEL_PROMPT_V4, "carousel", "proof"),
        ("carousel", CAROUSEL_PROMPT_V4, "carousel", "curiosity"),
        ("image", IMAGE_PROMPT_V4, "single_image", "urgency"),
        ("image", IMAGE_PROMPT_V4, "single_image", "curiosity"),
        ("image", IMAGE_PROMPT_V4, "single_image", "proof"),
        ("reel", REEL_PROMPT_V4, "video", "humor"),
        ("reel", REEL_PROMPT_V4, "video", "hope"),
        ("meme", MEME_PROMPT_V4, "single_image", "humor"),
        ("meme", MEME_PROMPT_V4, "single_image", "humor"),
        ("quote", QUOTE_PROMPT_V4, "single_image", "hope"),
        ("quote", QUOTE_PROMPT_V4, "single_image", "hope"),
    ]

    predis_success = 0
    predis_errors = 0

    # Process in batches of 3
    for batch_start in range(0, len(predis_pieces), 3):
        batch = predis_pieces[batch_start:batch_start + 3]

        for content_type, prompt_template, media_type, angle in batch:
            piece += 1
            topic_data = smart_pick_topic(content_type=content_type, angle=angle)
            topic = topic_data["text"]
            angle_instruction = get_angle_instruction(angle)
            seo_keywords = get_seo_keywords()
            formatted_prompt = prompt_template.format(
                angle_instruction=angle_instruction,
                seo_keywords=seo_keywords,
                topic=topic,
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏳ Generando pieza {piece}/25 — {content_type} [{angle}]...",
            )

            try:
                # Claude text generation
                generated_text = await generate_content(
                    content_type, topic, override_prompt=formatted_prompt,
                )
                if isinstance(generated_text, dict):
                    generated_text = generated_text.get("_raw", str(generated_text))
                if len(generated_text) > 950:
                    generated_text = generated_text[:950]

                if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"📝 {content_type.upper()} [{angle}]\n\n{generated_text[:500]}\n\n"
                             f"⚠️ Predis no configurado",
                    )
                    log_content(content_type, angle, topic, "claude_only")
                    predis_success += 1
                    continue

                # Create Predis content
                predis_kwargs = {
                    "text": generated_text,
                    "media_type": media_type,
                    "model_version": "4",
                }
                if media_type == "video":
                    predis_kwargs["video_duration"] = "15"

                create_result = await predis_create_content(**predis_kwargs)

                if not create_result.get("ok"):
                    error_msg = create_result.get("error", "Unknown")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ Predis error ({content_type} [{angle}]): {error_msg}",
                    )
                    log_content(content_type, angle, topic, "predis_error")
                    predis_errors += 1
                    continue

                post_id = create_result["post_ids"][0]

                # Poll until complete
                completed = await predis_poll_until_complete(post_id, max_wait=180, interval=5)

                if not completed.get("ok"):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Predis timeout ({content_type} [{angle}]). ID: {post_id}",
                    )
                    log_content(content_type, angle, topic, "predis", predis_post_id=post_id)
                    predis_errors += 1
                    continue

                # Send approval buttons
                post_data = {
                    "generated_text": generated_text,
                    "generated_media": completed.get("urls", []),
                }
                await send_predis_approval(
                    update, context, post_id, post_data, content_type, angle, topic,
                )
                log_content(content_type, angle, topic, "predis", predis_post_id=post_id)
                predis_success += 1

            except Exception as e:
                logger.error(f"weekly predis {content_type} [{angle}]: {e}")
                predis_errors += 1

        # Wait message between batches (except after last batch)
        if batch_start + 3 < len(predis_pieces):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏸ Batch completo. Siguiente batch...",
            )

    total_success = success + predis_success
    total_errors = errors + predis_errors

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ <b>WEEKLY PACK COMPLETO</b>\n\n"
            f"📊 {total_success}/25 piezas generadas\n"
            f"📝 Texto: {success} | 🎨 Predis: {predis_success}\n"
            f"{'❌ Errores: ' + str(total_errors) if total_errors else '🎉 Sin errores'}"
        ),
        parse_mode=ParseMode.HTML,
    )


# ==============================================================================
# COMMAND HANDLERS — /daily AUTO-GENERATION
# ==============================================================================

# Prompt template map for Predis pipeline
_DAILY_PROMPT_MAP = {
    "carousel": CAROUSEL_PROMPT_V4,
    "image": IMAGE_PROMPT_V4,
    "reel": REEL_PROMPT_V4,
    "meme": MEME_PROMPT_V4,
    "quote": QUOTE_PROMPT_V4,
}

# Predis media type mapping
_DAILY_PREDIS_MEDIA = {
    "carousel": "carousel",
    "image": "single_image",
    "reel": "video",
    "meme": "single_image",
    "quote": "single_image",
}


@team_only
async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate all content for today based on weekly calendar."""
    global topic_history

    today = datetime.now()
    day_of_week = today.weekday()
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    day_name = day_names[day_of_week]

    # Check if already run today
    today_str = today.strftime("%Y-%m-%d")
    last_daily = topic_history.get("last_daily")
    force = context.args and len(context.args) > 0 and context.args[0] == "force"

    if last_daily == today_str and not force:
        await update.message.reply_text(
            f"⚠️ Ya se generó contenido hoy ({day_name}).\n"
            "Usa: /daily force para regenerar"
        )
        return

    plan = DAILY_CONTENT_PLAN.get(day_of_week, [])
    active_plan = [(mt, ang, fun, tf) for mt, ang, fun, tf in plan if tf is not None]
    total = len(active_plan)

    await update.message.reply_text(
        f"📅 {day_name} — Generando {total} piezas...\n"
        "Te envío cada una cuando esté lista."
    )

    predis_types = {"carousel", "image", "reel", "meme", "quote"}
    auto_ran = topic_history.get("last_daily_auto") == today_str

    if auto_ran and not force:
        # Auto already created Predis content — only generate Claude items
        predis_items = []
        claude_items = [(mt, ang, fun, tf) for mt, ang, fun, tf in active_plan if mt not in predis_types]
        await update.message.reply_text(
            "ℹ️ Predis ya se generó automáticamente. Generando solo videos y textos..."
        )
    else:
        predis_items = [(mt, ang, fun, tf) for mt, ang, fun, tf in active_plan if mt in predis_types]
        claude_items = [(mt, ang, fun, tf) for mt, ang, fun, tf in active_plan if mt not in predis_types]

    chat_id = update.effective_chat.id
    generated = 0
    errors = 0

    # ── Claude items first (video scripts, blog, whatsapp, fbtext) ────
    for media_type, angle, funnel, theme_filter in claude_items:
        try:
            topic_data = smart_pick_topic(
                content_type=media_type, angle=angle, theme_filter=theme_filter,
            )
            topic = topic_data["text"]

            if media_type == "video":
                data = await generate_content("tiktok", topic)
                if data:
                    if isinstance(data, dict):
                        msg = format_tiktok_for_telegram(data)
                    else:
                        msg = f"🎬 VIDEO ({angle or 'auto'}) — {topic}\n\n{data}"
                    await send_long_message(chat_id, msg, context)
                    log_content("video", angle, topic, "invideo")
                    generated += 1

            elif media_type == "blog":
                data = await generate_content("blog", topic)
                if data:
                    if isinstance(data, dict):
                        msg = format_blog_for_telegram(data)
                        # Store for publish buttons
                        article_id = hashlib.md5(
                            json.dumps(data, default=str).encode()
                        ).hexdigest()[:8]
                        pending_articles[article_id] = data
                        buttons = [[
                            InlineKeyboardButton(
                                "🌐 Publicar en web",
                                callback_data=f"pub_tp_{article_id}",
                            ),
                            InlineKeyboardButton(
                                "📢 Canal",
                                callback_data=f"pub_ch_{article_id}",
                            ),
                        ]]
                        await send_long_message(
                            chat_id, msg, context,
                            reply_markup=InlineKeyboardMarkup(buttons),
                        )
                    else:
                        msg = f"📝 BLOG — {topic}\n\n{str(data)[:1500]}"
                        await send_long_message(chat_id, msg, context)
                    log_content("blog", None, topic, "claude")
                    generated += 1

            elif media_type == "whatsapp":
                data = await generate_content("whatsapp", topic)
                if data:
                    if isinstance(data, dict):
                        msg = format_whatsapp_for_telegram(data)
                    else:
                        msg = f"📱 WA ({angle or 'auto'}) — {topic}\n\n{data}"
                    await send_long_message(chat_id, msg, context)
                    log_content("whatsapp", angle, topic, "claude")
                    generated += 1

            elif media_type == "fbtext":
                data = await generate_content("fbpost", topic)
                if data:
                    if isinstance(data, dict):
                        msg = format_fbpost_for_telegram(data)
                    else:
                        msg = f"📘 FB ({angle or 'auto'}) — {topic}\n\n{data}"
                    await send_long_message(chat_id, msg, context)
                    log_content("fbtext", angle, topic, "claude")
                    generated += 1

            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Daily claude error ({media_type}): {e}")
            errors += 1

    # ── Predis items in batches of 3 ──────────────────────────────────
    for i in range(0, len(predis_items), 3):
        batch = predis_items[i:i + 3]
        for media_type, angle, funnel, theme_filter in batch:
            try:
                topic_data = smart_pick_topic(
                    content_type=media_type, angle=angle, theme_filter=theme_filter,
                )
                topic = topic_data["text"]
                actual_angle = "humor" if media_type == "meme" else ("hope" if media_type == "quote" else angle)

                prompt_template = _DAILY_PROMPT_MAP.get(media_type, CAROUSEL_PROMPT_V4)

                seo_str = get_seo_keywords()
                if topic_data.get("seo"):
                    seo_str += f" Incluye: {topic_data['seo']}\n"

                # Format prompt — meme/quote templates don't have angle_instruction
                if media_type in ("meme", "quote"):
                    prompt = prompt_template.format(seo_keywords=seo_str, topic=topic)
                else:
                    prompt = prompt_template.format(
                        angle_instruction=get_angle_instruction(actual_angle),
                        seo_keywords=seo_str,
                        topic=topic,
                    )

                text = await generate_content(media_type, topic, override_prompt=prompt)
                if not text:
                    errors += 1
                    continue
                if isinstance(text, dict):
                    text = text.get("_raw", str(text))
                if len(text) > 950:
                    text = text[:920] + "... tuspapeles2026.es #regularizacion2026"

                if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"📝 {media_type.upper()} (sin Predis):\n{text[:800]}",
                    )
                    log_content(media_type, actual_angle, topic, "claude_only")
                    generated += 1
                    continue

                # Predis params
                p_media = _DAILY_PREDIS_MEDIA[media_type]
                p_kwargs = {
                    "text": text,
                    "media_type": p_media,
                    "model_version": "4" if media_type in ("carousel", "image") else "2",
                }
                if media_type == "meme":
                    p_kwargs["post_type"] = "meme"
                elif media_type == "quote":
                    p_kwargs["post_type"] = "quotes"
                if media_type == "reel":
                    p_kwargs["video_duration"] = "short"

                create_result = await predis_create_content(**p_kwargs)
                if not create_result.get("ok"):
                    error_msg = create_result.get("error", "Unknown")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Predis error ({media_type}): {error_msg}\n📝 Texto:\n{text[:300]}",
                    )
                    errors += 1
                    continue

                post_id = create_result["post_ids"][0]

                post_data = await predis_poll_until_complete(post_id, max_wait=180, interval=5)

                if not post_data.get("ok"):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ Timeout: {media_type}. ID: {post_id}",
                    )
                    log_content(media_type, actual_angle, topic, "predis", predis_post_id=post_id)
                    generated += 1
                    continue

                approval_data = {
                    "generated_text": text,
                    "generated_media": post_data.get("urls", []),
                }
                await send_predis_approval(
                    update, context, post_id, approval_data,
                    media_type.upper(), actual_angle, topic,
                )
                log_content(media_type, actual_angle, topic, "predis", predis_post_id=post_id)
                generated += 1

            except Exception as e:
                logger.error(f"Daily predis error ({media_type}): {e}")
                errors += 1

        if i + 3 < len(predis_items):
            await asyncio.sleep(10)

    topic_history["last_daily"] = today_str
    save_topic_history(topic_history)

    await update.message.reply_text(
        f"✅ {day_name} completado\n\n"
        f"✅ {generated} generados | ❌ {errors} errores\n\n"
        f"Revisa y aprueba Predis ☝️\n"
        f"Copia y sube videos InVideo manualmente."
    )


async def scheduled_daily_generation(bot=None):
    """Auto-generate Predis content at 7:30am Madrid. Videos/text need manual /daily."""
    global topic_history

    today_str = datetime.now().strftime("%Y-%m-%d")
    if topic_history.get("last_daily") == today_str:
        logger.info(f"Daily already generated for {today_str}")
        return

    if not TEAM_CHAT_IDS or not bot:
        return

    day_of_week = datetime.now().weekday()
    plan = DAILY_CONTENT_PLAN.get(day_of_week, [])
    predis_types = {"carousel", "image", "reel", "meme", "quote"}
    predis_items = [
        (mt, ang, fun, tf)
        for mt, ang, fun, tf in plan
        if tf is not None and mt in predis_types
    ]

    if not predis_items:
        return

    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    day_name = day_names[day_of_week]

    # Notify team
    for tid in TEAM_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=tid,
                text=f"🤖 Auto-generando {len(predis_items)} piezas Predis ({day_name})...",
            )
        except Exception:
            pass

    generated = 0

    for i in range(0, len(predis_items), 3):
        batch = predis_items[i:i + 3]
        for media_type, angle, funnel, theme_filter in batch:
            try:
                topic_data = smart_pick_topic(
                    content_type=media_type, angle=angle, theme_filter=theme_filter,
                )
                topic = topic_data["text"]
                actual_angle = "humor" if media_type == "meme" else ("hope" if media_type == "quote" else angle)

                prompt_template = _DAILY_PROMPT_MAP.get(media_type, CAROUSEL_PROMPT_V4)

                seo_str = get_seo_keywords()
                if topic_data.get("seo"):
                    seo_str += f" Incluye: {topic_data['seo']}\n"

                if media_type in ("meme", "quote"):
                    prompt = prompt_template.format(seo_keywords=seo_str, topic=topic)
                else:
                    prompt = prompt_template.format(
                        angle_instruction=get_angle_instruction(actual_angle),
                        seo_keywords=seo_str,
                        topic=topic,
                    )

                text = await generate_content(media_type, topic, override_prompt=prompt)
                if not text or (isinstance(text, str) and len(text) < 20):
                    continue
                if isinstance(text, dict):
                    text = text.get("_raw", str(text))
                if len(text) > 950:
                    text = text[:920] + "... tuspapeles2026.es #regularizacion2026"

                if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
                    continue

                p_media = _DAILY_PREDIS_MEDIA[media_type]
                p_kwargs = {
                    "text": text,
                    "media_type": p_media,
                    "model_version": "4" if media_type in ("carousel", "image") else "2",
                }
                if media_type == "meme":
                    p_kwargs["post_type"] = "meme"
                elif media_type == "quote":
                    p_kwargs["post_type"] = "quotes"
                if media_type == "reel":
                    p_kwargs["video_duration"] = "short"

                create_result = await predis_create_content(**p_kwargs)
                if not create_result.get("ok"):
                    continue

                post_id = create_result["post_ids"][0]

                post_data = await predis_poll_until_complete(post_id, max_wait=180, interval=5)

                # Send approval to all team members
                for tid in TEAM_CHAT_IDS:
                    try:
                        caption = ""
                        if post_data.get("ok"):
                            caption = (
                                post_data.get("generated_text")
                                or post_data.get("caption")
                                or post_data.get("text", "")
                            )[:400]

                        buttons = [
                            [
                                InlineKeyboardButton(
                                    "✅ Aprobar", callback_data=f"pa_{post_id[:20]}",
                                ),
                                InlineKeyboardButton(
                                    "❌ Rechazar", callback_data=f"pr_{post_id[:20]}",
                                ),
                            ],
                            [
                                InlineKeyboardButton(
                                    "✏️ Editar",
                                    url="https://predis.ai/app/content_library",
                                ),
                            ],
                        ]

                        await bot.send_message(
                            chat_id=tid,
                            text=(
                                f"🤖 AUTO | {media_type.upper()} | {actual_angle}\n"
                                f"📝 {topic[:80]}\n\n{caption[:300]}"
                            ),
                            reply_markup=InlineKeyboardMarkup(buttons),
                        )

                        if post_data.get("ok"):
                            imgs = post_data.get("urls", [])
                            if imgs:
                                url = imgs[0] if isinstance(imgs[0], str) else imgs[0].get("url", "")
                                if url:
                                    try:
                                        await bot.send_photo(chat_id=tid, photo=url)
                                    except Exception:
                                        pass
                    except Exception as e:
                        logger.error(f"Scheduled approval send error: {e}")

                log_content(media_type, actual_angle, topic, "predis", predis_post_id=post_id)
                generated += 1
            except Exception as e:
                logger.error(f"Scheduled gen error ({media_type}): {e}")

        if i + 3 < len(predis_items):
            await asyncio.sleep(10)

    # Mark auto-generation as done
    topic_history["last_daily_auto"] = today_str
    save_topic_history(topic_history)

    for tid in TEAM_CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=tid,
                text=(
                    f"✅ Auto-generación: {generated} piezas Predis\n"
                    f"Revisa y aprueba ☝️\n\n"
                    f"Para videos y textos: /daily"
                ),
            )
        except Exception:
            pass


# ==============================================================================
# COMMAND HANDLERS — MONITORING & TOOLS
# ==============================================================================


@team_only
async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /news — fetch real news and suggest content with action buttons."""
    wait_msg = await update.message.reply_text("⏳ Scanning news sources...")

    try:
        articles = await fetch_news()

        if not articles:
            await wait_msg.edit_text("No recent news found. Try again later.")
            return

        await wait_msg.delete()

        # Show header
        today = datetime.now().strftime("%d %b %Y")
        header = f"📰 *NEWS SCAN — {today}*\n\nFound {len(articles)} relevant items:\n"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=header,
            parse_mode=ParseMode.MARKDOWN,
        )

        # Show each article with action buttons (top 8 max)
        for i, a in enumerate(articles[:8], 1):
            title = a["title"][:100]
            source = a.get("source", "")
            published = a.get("published", "")
            summary = a.get("summary", "")

            text = f"*{i}.* {escape_md(title)}\n"
            if source:
                text += f"   📍 {escape_md(source)}"
            if published:
                text += f" | {escape_md(published)}"
            text += "\n"
            if summary:
                text += f"   {escape_md(summary[:120])}\n"

            # Action buttons for this news item
            topic_short = title[:40]
            buttons = [
                [
                    InlineKeyboardButton(
                        "📝 Blog", callback_data=f"news_blog_{topic_short}"
                    ),
                    InlineKeyboardButton(
                        "🎬 TikTok", callback_data=f"news_tiktok_{topic_short}"
                    ),
                    InlineKeyboardButton(
                        "📱 WA", callback_data=f"news_wa_{topic_short}"
                    ),
                    InlineKeyboardButton(
                        "📢 Canal", callback_data=f"news_chan_{topic_short}"
                    ),
                ],
            ]
            markup = InlineKeyboardMarkup(buttons)

            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup,
                )
            except Exception:
                # Fallback without markdown
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=markup,
                )

        # Ask Claude to analyze top articles for content angles
        analysis_msg = await update.message.reply_text(
            "⏳ Analyzing for content angles..."
        )
        try:
            news_summary = "\n".join(
                f"- {a['title']} ({a.get('source', '')})" for a in articles[:8]
            )
            data = await generate_content(
                "news_analysis",
                topic=f"Analyze these REAL recent news articles:\n{news_summary}",
            )

            analysis_items = data.get("analysis", [])
            if analysis_items:
                analysis_text = "💡 *CONTENT IDEAS FROM NEWS*\n\n"
                for item in analysis_items:
                    analysis_text += f"📌 *{escape_md(item.get('headline', ''))}*\n"
                    analysis_text += f"{escape_md(item.get('summary', ''))}\n"
                    ideas = item.get("content_ideas", [])
                    for idea in ideas:
                        analysis_text += f"  → {escape_md(idea)}\n"
                    analysis_text += "\n"
                await analysis_msg.delete()
                await send_long_message(update, analysis_text, context)
            else:
                await analysis_msg.edit_text("No additional content ideas generated.")

        except Exception as e:
            await analysis_msg.edit_text(f"⚠️ Could not analyze: {e}")

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error fetching news: {e}")


@team_only
async def cmd_predis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /predis — test Predis API connection."""
    if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
        await update.message.reply_text(
            "❌ Predis no configurado. Faltan PREDIS_API_KEY o PREDIS_BRAND_ID."
        )
        return

    wait_msg = await update.message.reply_text("⏳ Probando conexión Predis.ai...")

    try:
        result = await predis_get_posts(page=1)

        if result.get("ok"):
            posts = result.get("posts", [])
            post_count = len(posts)
            text = (
                f"✅ <b>Predis conectado</b>\n\n"
                f"🔑 <b>Brand ID:</b> <code>{PREDIS_BRAND_ID}</code>\n"
                f"📦 <b>Posts en biblioteca:</b> {post_count}\n\n"
                f"<b>Comandos Predis disponibles:</b>\n"
                f"  /carousel — Carrusel branded\n"
                f"  /image — Imagen única\n"
                f"  /reel — Reel/vídeo corto\n"
                f"  /meme — Meme\n"
                f"  /quote — Frase motivacional"
            )
        else:
            error = result.get("error", "Unknown error")
            text = f"❌ <b>Error Predis:</b> {html_mod.escape(str(error))}"

        await wait_msg.edit_text(text, parse_mode=ParseMode.HTML)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error de conexión: {e}")


@team_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats — show content log statistics (last 7 days)."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Filter last 7 days
    recent = [
        entry for entry in content_log
        if entry.get("timestamp", "") >= week_ago.isoformat()
    ]

    total = len(recent)

    # Counts by media_type
    by_type = {}
    for entry in recent:
        mt = entry.get("media_type", "unknown")
        by_type[mt] = by_type.get(mt, 0) + 1

    type_lines = "\n".join(
        f"  {k}: {v}" for k, v in sorted(by_type.items())
    ) or "  Sin contenido aún"

    # Counts by angle
    by_angle = {}
    for entry in recent:
        a = entry.get("angle") or "sin ángulo"
        by_angle[a] = by_angle.get(a, 0) + 1

    angle_lines = "\n".join(
        f"  {k}: {v}" for k, v in sorted(by_angle.items())
    ) or "  Sin datos"

    # Least used angle (from VALID_ANGLES, excluding 'ad')
    countable_angles = {a for a in VALID_ANGLES if a != "ad"}
    least_used = min(countable_angles, key=lambda a: by_angle.get(a, 0))
    least_count = by_angle.get(least_used, 0)

    # Predis approval stats
    predis_entries = [e for e in recent if e.get("predis_post_id")]
    approved = sum(1 for e in predis_entries if e.get("approved") is True)
    rejected = sum(1 for e in predis_entries if e.get("approved") is False)
    pending = sum(1 for e in predis_entries if e.get("approved") is None)

    # All-time total
    all_time = len(content_log)

    text = (
        f"📊 <b>ESTADÍSTICAS — Últimos 7 días</b>\n\n"
        f"<b>Total piezas:</b> {total} (all-time: {all_time})\n\n"
        f"<b>Por tipo:</b>\n{type_lines}\n\n"
        f"<b>Por ángulo:</b>\n{angle_lines}\n\n"
        f"<b>Predis:</b> ✅ {approved} aprobados | ❌ {rejected} rechazados | ⏳ {pending} pendientes\n\n"
        f"<b>Ángulo menos usado:</b> {least_used} ({least_count})"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)



# ==============================================================================
# BACKFILL DATA (retained for reference, command removed)
# ==============================================================================

# 7 articles to backfill with their real historical dates
BACKFILL_ARTICLES = [
    {
        "slug": "gobierno-aprueba-regularizacion-extraordinaria",
        "title": "El Gobierno aprueba la tramitación de la regularización extraordinaria",
        "date": "2026-01-27",
        "date_str": "27 de enero de 2026",
        "category": "noticias",
        "meta": "El Consejo de Ministros autoriza la tramitación urgente de la regularización extraordinaria para 500.000 personas en España.",
        "prompt": (
            "Write a 500-word Spanish news blog article about: "
            "El Consejo de Ministros aprueba la tramitación urgente de la regularización extraordinaria. "
            "Include these facts: 500,000 estimated beneficiaries. April-June 2026 application window. "
            "5 months continuous residence requirement (NOT years). Vulnerability clause means NO job offer needed. "
            "Ministra de Inclusión Elma Saiz presented the decree. ILP (Iniciativa Legislativa Popular) "
            "with over 700,000 signatures was the origin. Digital submission confirmed. "
            "Include a summary of key requirements at the end. "
            "Return ONLY the HTML body content (no <html> or <head> tags). Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "borrador-decreto-que-sabemos",
        "title": "Se publica el borrador del Real Decreto: esto es lo que sabemos",
        "date": "2026-01-28",
        "date_str": "28 de enero de 2026",
        "category": "noticias",
        "meta": "Análisis del borrador del Real Decreto de regularización: dos vías, requisitos, plazos y novedades.",
        "prompt": (
            "Write a 600-word Spanish news analysis blog article about: "
            "The draft text (borrador) of the Real Decreto de regularización has been published. "
            "Include: Two pathways — irregular status pathway AND asylum seeker pathway. "
            "Key requirements: entry before Dec 31 2025, 5 months continuous residence, "
            "no serious criminal convictions (over 1 year sentence). "
            "1-year residence permit granted upon approval. Immediate provisional work authorization upon filing. "
            "Digital (telematic) submission confirmed. Minor children get 5-year permit. "
            "Process opens April 1 - June 30, 2026. Decision within 3 months max. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "ministerio-confirma-apertura-abril",
        "title": "El Ministerio confirma: las solicitudes se abrirán en abril",
        "date": "2026-02-04",
        "date_str": "4 de febrero de 2026",
        "category": "noticias",
        "meta": "El Ministerio de Inclusión confirma que las solicitudes de regularización se abrirán en abril de 2026.",
        "prompt": (
            "Write a 450-word Spanish news blog article about: "
            "Ministerio de Inclusión confirms April 2026 start for regularization applications. "
            "The Ministry calls for calm — the process is NOT open yet. "
            "Warns people against unofficial sources and scams. "
            "The text is still in audiencia pública (public comment period) until February 6. "
            "After that: Consejo de Estado review, then back to Consejo de Ministros, then BOE publication. "
            "Applications open the day after BOE publication. "
            "Emphasize: do NOT pay anyone yet, prepare documents now. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "audiencia-publica-cierra-1200-aportaciones",
        "title": "Cierra la audiencia pública con más de 1.200 aportaciones",
        "date": "2026-02-06",
        "date_str": "6 de febrero de 2026",
        "category": "noticias",
        "meta": "La audiencia pública del decreto de regularización cierra con más de 1.200 aportaciones ciudadanas.",
        "prompt": (
            "Write a 450-word Spanish news blog article about: "
            "The public comment period (audiencia pública) for the regularization decree has closed. "
            "Over 1,200 submissions received from citizens, organizations, and legal experts. "
            "The text now moves to the Consejo de Estado for mandatory review. "
            "Timeline remains on track for April opening. "
            "After Consejo de Estado: back to Consejo de Ministros for final approval, then BOE publication. "
            "Remind readers: use this waiting time to prepare documents. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "decreto-fase-informes-preceptivos",
        "title": "El Real Decreto entra en fase de informes preceptivos",
        "date": "2026-02-09",
        "date_str": "9 de febrero de 2026",
        "category": "noticias",
        "meta": "El Real Decreto de regularización pasa a la fase de informes preceptivos del Consejo de Estado.",
        "prompt": (
            "Write a 500-word Spanish news blog article about: "
            "The regularization Real Decreto enters the mandatory review phase (informes preceptivos). "
            "The Consejo de Estado is now reviewing the text. Expected ~15 business days for their report. "
            "After their report, the text goes back to Consejo de Ministros for final approval. "
            "Then: publication in the BOE. Then: process opens the next day. "
            "April timeline still achievable. "
            "Explain each step clearly for people who don't understand Spanish bureaucracy. "
            "Remind: prepare empadronamiento, pasaporte, antecedentes penales NOW. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "ces-respalda-regularizacion-informe",
        "title": "El Consejo Económico y Social respalda la regularización",
        "date": "2026-02-13",
        "date_str": "13 de febrero de 2026",
        "category": "noticias",
        "meta": "El CES presenta informe respaldando la regularización: la inmigración bien gestionada es una bendición.",
        "prompt": (
            "Write a 550-word Spanish news blog article about: "
            "The Consejo Económico y Social (CES) presents report 'Realidad Migratoria en España' in Pamplona. "
            "CES President Antón Costas says: 'immigration well managed is a blessing for the country.' "
            "Key data from the report: 3.1 million foreign workers affiliated to Social Security (14.1% of total). "
            "77% of new self-employment registrations (autónomos) in 2025 were foreign nationals. "
            "Ministra Elma Saiz confirms the plan operativo (operational plan) is being finalized. "
            "This institutional backing is important — it means broad support for the regularization. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs."
        ),
    },
    {
        "slug": "guia-completa-documentos-regularizacion-2026",
        "title": "Guía completa: todos los documentos que necesitas para la regularización 2026",
        "date": "2026-02-17",
        "date_str": "17 de febrero de 2026",
        "category": "guia",
        "meta": "Lista completa de documentos para la regularización 2026: empadronamiento, antecedentes, certificado médico y más.",
        "prompt": (
            "Write a 700-word Spanish guide blog article about all the documents needed for regularization 2026. "
            "Organize into sections:\n"
            "1. STRONGEST DOCUMENTS (most important): empadronamiento histórico, Social Security records (vida laboral), "
            "tax filings (declaración de la renta or modelo 303).\n"
            "2. REQUIRED DOCUMENTS: valid pasaporte, certificado de antecedentes penales "
            "(from home country, must be apostilled), certificado médico (costs 50-80€).\n"
            "3. SUPPORTING DOCUMENTS that prove 5 months residence: medical records, bank account statements, "
            "rental contract (contrato de alquiler), utility bills (luz, agua, gas), "
            "transport cards (abono transporte), delivery app records (Glovo, Uber Eats), "
            "money transfer records (Western Union, Ria), gym membership, library card, "
            "vet records (if you have pets), letters from community organizations.\n"
            "Emphasize: combinations matter — the more supporting documents, the stronger the case. "
            "Explain the 5-month proof requirement. "
            "End with CTA to eligibility check at tuspapeles2026.es. "
            "Return ONLY the HTML body content. Use <h2> for subheadings, <p> for paragraphs, <ul>/<li> for lists."
        ),
    },
]



# ==============================================================================
# DUPLICATE DETECTION
# ==============================================================================


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


async def fetch_blog_index(repo: str) -> tuple[list, str | None]:
    """Fetch blog/index.json from a GitHub repo. Returns (articles_list, sha)."""
    if not GITHUB_TOKEN:
        return [], None

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/contents/blog/index.json"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            resp_data = resp.json()
            content = json.loads(
                base64.b64decode(resp_data["content"]).decode("utf-8")
            )
            return content.get("articles", []), resp_data.get("sha")
    return [], None


async def delete_github_file(repo: str, path: str, commit_msg: str) -> bool:
    """Delete a file from a GitHub repo. Returns True on success."""
    if not GITHUB_TOKEN:
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/contents/{path}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Get current SHA
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.error("File not found for deletion: %s", path)
            return False
        sha = resp.json().get("sha")

        # Delete (use request() because delete() doesn't support json kwarg)
        resp = await client.request("DELETE", url, headers=headers, json={
            "message": commit_msg,
            "sha": sha,
            "branch": "main",
        })
        if resp.status_code == 200:
            return True
        logger.error("Delete failed for %s: %s %s", path, resp.status_code, resp.text[:200])
        return False


# ==============================================================================
# /ARTICLES COMMAND
# ==============================================================================


@team_only
async def cmd_articles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /articles — list all published articles."""
    repo = GITHUB_REPO_TP
    wait_msg = await update.message.reply_text("⏳ Fetching articles...")

    try:
        articles, _ = await fetch_blog_index(repo)

        if not articles:
            await wait_msg.edit_text("No articles found in blog/index.json.")
            return

        text = f"📚 *Artículos publicados ({len(articles)} total)*\n\n"
        for i, a in enumerate(articles, 1):
            icon = BLOG_CATEGORY_ICONS.get(a.get("category", ""), "📰")
            date_short = a.get("date", "")
            if date_short:
                try:
                    dt = datetime.strptime(date_short, "%Y-%m-%d")
                    date_short = f"{dt.day} {['', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'][dt.month]}"
                except ValueError:
                    pass
            category = a.get("category", "")
            text += f"{i}. {icon} {escape_md(a.get('title', 'Sin título'))} — {date_short} · {category}\n"

        text += f"\n/delete \\[número\\] para eliminar"

        await wait_msg.delete()
        await send_long_message(update, text, context)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {e}")


# ==============================================================================
# /DELETE COMMAND
# ==============================================================================

# In-memory state for delete flow
pending_deletes: dict = {}


@team_only
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete [slug|number] — delete an article from the site."""
    repo = GITHUB_REPO_TP
    args_text = " ".join(context.args) if context.args else ""

    # If slug provided directly, go to confirmation
    if args_text:
        wait_msg = await update.message.reply_text("⏳ Looking up article...")
        articles, index_sha = await fetch_blog_index(repo)

        # Check if it's a number (from /articles list)
        target_article = None
        try:
            num = int(args_text)
            if 1 <= num <= len(articles):
                target_article = articles[num - 1]
        except ValueError:
            # It's a slug
            slug = args_text.strip().lower()
            for a in articles:
                if a.get("slug", "") == slug:
                    target_article = a
                    break

        if not target_article:
            await wait_msg.edit_text(f"❌ Article not found: {args_text}")
            return

        # Store pending delete and ask for confirmation
        delete_id = hashlib.md5(target_article["slug"].encode()).hexdigest()[:8]
        pending_deletes[delete_id] = {
            "article": target_article,
            "index_sha": index_sha,
            "all_articles": articles,
        }

        buttons = [
            [
                InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"del_yes_{delete_id}"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"del_no_{delete_id}"),
            ]
        ]
        await wait_msg.edit_text(
            f"¿Eliminar '*{escape_md(target_article['title'])}*'?\n\n"
            f"Esta acción no se puede deshacer.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # No args — show numbered list
    wait_msg = await update.message.reply_text("⏳ Fetching articles...")
    try:
        articles, index_sha = await fetch_blog_index(repo)

        if not articles:
            await wait_msg.edit_text("No articles found.")
            return

        # Store for later lookup
        delete_session_id = hashlib.md5(
            datetime.now().isoformat().encode()
        ).hexdigest()[:8]
        pending_deletes[f"list_{delete_session_id}"] = {
            "articles": articles,
            "index_sha": index_sha,
        }

        text = "🗑️ *Selecciona el artículo a eliminar:*\n\n"
        buttons = []
        for i, a in enumerate(articles, 1):
            date_short = a.get("date", "")
            if date_short:
                try:
                    dt = datetime.strptime(date_short, "%Y-%m-%d")
                    date_short = f"{dt.day} {['', 'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'][dt.month]}"
                except ValueError:
                    pass
            text += f"\\[{i}\\] {escape_md(a.get('title', ''))} ({date_short})\n"

            # Add inline button per article (max 8 to avoid Telegram limits)
            if i <= 8:
                delete_id = hashlib.md5(a["slug"].encode()).hexdigest()[:8]
                pending_deletes[delete_id] = {
                    "article": a,
                    "index_sha": index_sha,
                    "all_articles": articles,
                }
                label = f"[{i}] {a.get('title', '')[:35]}"
                buttons.append([InlineKeyboardButton(label, callback_data=f"del_pick_{delete_id}")])

        markup = InlineKeyboardMarkup(buttons) if buttons else None

        await wait_msg.delete()
        await send_long_message(update, text, context, reply_markup=markup)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {e}")


# ==============================================================================
# NEWS AUTO-SCAN
# ==============================================================================


async def auto_scan_news(bot=None):
    """Scheduled scan for new regularización news. Alerts team on new items."""
    new_items = []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    for source_url in NEWS_SCAN_SOURCES:
        try:
            feed = await asyncio.to_thread(feedparser.parse, source_url)
            for entry in feed.entries[:8]:
                headline_key = entry.title.strip().lower()[:100]
                if headline_key in seen_headlines:
                    continue

                # 24-hour filter: skip items older than 24h
                published_str = getattr(entry, "published", "")
                pub_parsed = getattr(entry, "published_parsed", None)
                if pub_parsed:
                    try:
                        from time import mktime
                        pub_dt = datetime.fromtimestamp(mktime(pub_parsed), tz=timezone.utc)
                        if pub_dt < cutoff:
                            seen_headlines.add(headline_key)
                            continue
                    except Exception:
                        pass

                # Resolve Google News redirect URLs
                link = await asyncio.to_thread(resolve_google_news_url, entry.link)

                new_items.append({
                    "title": entry.title,
                    "link": link,
                    "date": published_str,
                    "summary": getattr(entry, "summary", "")[:200],
                })
                seen_headlines.add(headline_key)
        except Exception as e:
            logger.error(f"Auto-scan error for {source_url}: {e}")

    if not new_items:
        return

    # Deduplicate by title prefix
    seen_titles = set()
    unique = []
    for item in new_items:
        key = item["title"][:50].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(item)

    for item in unique[:5]:  # Max 5 alerts per scan
        topic_short = item["title"][:40]
        alert_text = (
            f"🚨 *NUEVA NOTICIA DETECTADA*\n\n"
            f"📰 {escape_md(item['title'])}\n"
            f"📅 {escape_md(item['date'])}\n\n"
            f"{escape_md(item['summary'])}\n\n"
            f"🔗 [Ver fuente]({item['link']})\n\n"
            f"¿Generar contenido sobre esto?"
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "📝 Blog", callback_data=f"news_blog_{topic_short}"
                ),
                InlineKeyboardButton(
                    "🎬 TikTok", callback_data=f"news_tiktok_{topic_short}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📱 WhatsApp", callback_data=f"news_wa_{topic_short}"
                ),
                InlineKeyboardButton(
                    "📢 Canal", callback_data=f"news_chan_{topic_short}"
                ),
                InlineKeyboardButton(
                    "❌ Ignorar", callback_data="news_ignore"
                ),
            ],
        ]
        markup = InlineKeyboardMarkup(buttons)

        for chat_id in TEAM_CHAT_IDS:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=alert_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup,
                )
            except Exception as e:
                logger.error(f"Failed to alert chat {chat_id}: {e}")



# ==============================================================================
# V4 PREDIS APPROVAL WORKFLOW
# ==============================================================================


async def send_predis_approval(update, context, post_id, post_data, media_label, angle, topic):
    """Send Predis content preview with approval buttons and review checklist."""
    chat_id = update.effective_chat.id

    # Extract caption from post_data (try multiple fields)
    caption = (
        post_data.get("generated_text")
        or post_data.get("caption")
        or post_data.get("text")
        or ""
    )
    if len(caption) > 1500:
        caption = caption[:1500] + "..."

    # Send image preview if available
    media_urls = post_data.get("generated_media") or post_data.get("urls") or []
    if media_urls:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media_urls[0] if isinstance(media_urls[0], str) else media_urls[0].get("url", ""),
            )
        except Exception as e:
            logger.warning(f"send_predis_approval: image preview failed: {e}")

    # Caption preview
    angle_tag = f" | \U0001f3af {angle}" if angle else ""
    preview_text = (
        f"\U0001f4cb <b>PREDIS REVIEW — {media_label.upper()}</b>{angle_tag}\n\n"
        f"\U0001f4dd <b>Texto generado:</b>\n{html_mod.escape(caption)}\n\n"
        f"\U0001f4cc <b>Tema:</b> {html_mod.escape(topic)}\n"
        f"\U0001f194 <b>Predis ID:</b> <code>{post_id}</code>"
    )

    # Review checklist
    checklist = (
        "\n\n\u2753 <b>CHECKLIST ANTES DE APROBAR:</b>\n"
        "\u2022 \u00bfInfo correcta?\n"
        "\u2022 \u00bfSin garant\u00edas de resultados?\n"
        "\u2022 \u00bfTono OK?\n"
        "\u2022 \u00bfLogo visible?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2705 Aprobar", callback_data=f"pa_{post_id[:20]}"),
            InlineKeyboardButton("\u274c Rechazar", callback_data=f"pr_{post_id[:20]}"),
        ],
        [
            InlineKeyboardButton(
                "\u270f\ufe0f Editar en Predis",
                url="https://predis.ai/app/content_library",
            ),
        ],
    ])

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=preview_text + checklist,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )

    # Store in review queue for callback handling
    predis_review_queue[msg.message_id] = {
        "post_id": post_id,
        "caption": caption,
        "media_urls": media_urls,
        "media_type": media_label,
        "source": f"v4_{media_label}",
        "chat_id": chat_id,
        "angle": angle,
        "topic": topic,
    }

    return msg


async def _predis_command_handler(
    update, context, content_type, prompt_template, media_type,
    model_version="4", post_type=None, video_duration=None, fixed_angle=None,
):
    """Shared pipeline: parse angle → generate prompt → Claude → Predis → review."""
    args = context.args if context.args else []

    # Determine angle and topic
    if fixed_angle:
        angle = fixed_angle
        user_topic = " ".join(args) if args else ""
    else:
        angle, user_topic = parse_angle_and_topic(args)

    topic_data = smart_pick_topic(content_type=content_type, angle=angle, user_topic=user_topic if user_topic else None)
    topic = topic_data["text"]

    # Build the formatted prompt
    angle_instruction = get_angle_instruction(angle)
    seo_keywords = get_seo_keywords()
    formatted_prompt = prompt_template.format(
        angle_instruction=angle_instruction,
        seo_keywords=seo_keywords,
        topic=topic,
    )

    angle_label = f" [\U0001f3af {angle}]" if angle else ""
    wait_msg = await update.message.reply_text(
        f"\u23f3 Generando {content_type}{angle_label}..."
    )

    try:
        # Generate text via Claude with override_prompt
        generated_text = await generate_content(
            content_type, topic, override_prompt=formatted_prompt,
        )

        # Ensure it's a string (override mode returns raw text)
        if isinstance(generated_text, dict):
            generated_text = generated_text.get("_raw", str(generated_text))

        # Truncate to 950 chars for Predis input
        if len(generated_text) > 950:
            generated_text = generated_text[:950]

        # If no Predis API key, just show the text
        if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
            await wait_msg.delete()
            result_text = (
                f"\U0001f4dd <b>{content_type.upper()}</b>{angle_label}\n\n"
                f"{html_mod.escape(generated_text)}\n\n"
                f"\u26a0\ufe0f <i>Predis no configurado — solo texto generado.</i>"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=result_text,
                parse_mode=ParseMode.HTML,
            )
            log_content(content_type, angle, topic, "claude_only")
            return

        # Create Predis content
        await wait_msg.edit_text(
            f"\u23f3 Texto listo. Enviando a Predis.ai ({media_type})..."
        )

        predis_kwargs = {
            "text": generated_text,
            "media_type": media_type,
            "model_version": model_version,
        }
        if post_type:
            predis_kwargs["post_type"] = post_type
        if video_duration:
            predis_kwargs["video_duration"] = video_duration

        create_result = await predis_create_content(**predis_kwargs)

        if not create_result.get("ok"):
            error_msg = create_result.get("error", "Unknown error")
            await wait_msg.edit_text(
                f"\u274c Predis error: {error_msg}\n\n"
                f"\U0001f4dd Texto generado:\n{generated_text[:500]}"
            )
            log_content(content_type, angle, topic, "predis_error")
            return

        post_id = create_result["post_ids"][0]

        await wait_msg.edit_text(
            f"\u23f3 Predis procesando ({media_type})... esperando resultado."
        )

        # Poll until complete
        completed = await predis_poll_until_complete(post_id, max_wait=180, interval=5)

        if not completed.get("ok"):
            await wait_msg.edit_text(
                f"\u26a0\ufe0f Predis timeout. ID: <code>{post_id}</code>\n"
                f"Revisa en predis.ai/app\n\n"
                f"\U0001f4dd Texto:\n{generated_text[:400]}",
                parse_mode=ParseMode.HTML,
            )
            log_content(content_type, angle, topic, "predis", predis_post_id=post_id)
            return

        await wait_msg.delete()

        # Build post_data for approval
        post_data = {
            "generated_text": generated_text,
            "generated_media": completed.get("urls", []),
        }

        await send_predis_approval(
            update, context, post_id, post_data, content_type, angle, topic,
        )

        log_content(content_type, angle, topic, "predis", predis_post_id=post_id)

    except Exception as e:
        logger.error(f"_predis_command_handler error ({content_type}): {e}")
        try:
            await wait_msg.edit_text(f"\u274c Error generando {content_type}: {e}")
        except Exception:
            pass


# ==============================================================================
# V4 COMMAND HANDLERS — /cr, /image, /reel, /meme, /quote
# ==============================================================================


@team_only
async def cmd_carousel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cr [angle] [topic] — generate branded carousel via V4 pipeline."""
    await _predis_command_handler(
        update, context,
        content_type="carousel",
        prompt_template=CAROUSEL_PROMPT_V4,
        media_type="carousel",
        model_version="4",
    )


@team_only
async def cmd_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /image [angle] [topic] — generate branded single image."""
    await _predis_command_handler(
        update, context,
        content_type="image",
        prompt_template=IMAGE_PROMPT_V4,
        media_type="single_image",
        model_version="4",
    )


@team_only
async def cmd_reel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reel [angle] [topic] — generate branded short video."""
    await _predis_command_handler(
        update, context,
        content_type="reel",
        prompt_template=REEL_PROMPT_V4,
        media_type="video",
        model_version="2",
        video_duration="short",
    )


@team_only
async def cmd_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /meme [topic] — generate branded meme (angle always humor)."""
    await _predis_command_handler(
        update, context,
        content_type="meme",
        prompt_template=MEME_PROMPT_V4,
        media_type="single_image",
        model_version="2",
        post_type="meme",
        fixed_angle="humor",
    )


@team_only
async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quote [topic] — generate motivational quote image (angle always hope)."""
    await _predis_command_handler(
        update, context,
        content_type="quote",
        prompt_template=QUOTE_PROMPT_V4,
        media_type="single_image",
        model_version="2",
        post_type="quotes",
        fixed_angle="hope",
    )


# ==============================================================================
# PREDIS REVIEW QUEUE + BRANDED COMMANDS
# ==============================================================================


async def send_predis_to_review(
    bot,
    chat_id: int,
    post_id: str,
    caption: str,
    media_urls: list,
    media_type: str,
    source: str = "manual",
):
    """Send Predis-generated content to review queue with preview + approve/reject buttons."""

    item_count = len(media_urls)
    type_label = {
        "carousel": f"\U0001f4ca {item_count}-slide carousel",
        "single_image": "\U0001f5bc Single image",
        "video": "\U0001f3ac Short video",
    }.get(media_type, f"\U0001f4e6 {media_type}")

    preview_text = (
        f"\U0001f4cb <b>PREDIS REVIEW</b> ({source})\n\n"
        f"\U0001f4dd <b>Caption:</b>\n{caption[:300]}{'...' if len(caption) > 300 else ''}\n\n"
        f"\U0001f3a8 <b>Content:</b> {type_label}\n"
        f"\U0001f194 <b>Predis ID:</b> <code>{post_id}</code>\n\n"
        f"Content is ready in your Predis.ai dashboard.\n"
        f"Tap \u2705 to confirm (schedule from Predis dashboard),\n"
        f"or \u274c to discard."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="\u2705 Approve", callback_data=f"{PREDIS_APPROVE}:{post_id[:20]}"),
            InlineKeyboardButton(text="\u274c Reject", callback_data=f"{PREDIS_REJECT}:{post_id[:20]}"),
        ],
        [
            InlineKeyboardButton(text="\U0001f517 Open in Predis", url="https://predis.ai/app"),
        ],
    ])

    # Send first image as preview if available
    msg = None
    if media_urls and media_type in ("carousel", "single_image"):
        try:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=media_urls[0],
                caption=preview_text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.warning(f"Failed to send preview image: {e}")

    if not msg:
        msg = await bot.send_message(
            chat_id=chat_id,
            text=preview_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    # Store in review queue
    predis_review_queue[msg.message_id] = {
        "post_id": post_id,
        "caption": caption,
        "media_urls": media_urls,
        "media_type": media_type,
        "source": source,
        "chat_id": chat_id,
    }

    # Review warning — Predis rewrites text, so human must verify
    review_msg = (
        "\u26a0\ufe0f ANTES DE APROBAR:\n"
        "\u2022 \u00bfDice algo legalmente incorrecto?\n"
        "\u2022 \u00bfPromete resultados garantizados?\n"
        "\u2022 \u00bfEl tono es apropiado?\n"
        "Si algo est\u00e1 mal \u2192 edita en predis.ai antes de publicar"
    )
    await bot.send_message(chat_id=chat_id, text=review_msg)

    return msg


async def handle_predis_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Predis review queue approve/reject callbacks."""
    query = update.callback_query
    await query.answer()

    msg_id = query.message.message_id
    data = query.data  # "predis_approve:postid" or "predis_reject:postid"

    action = data.split(":")[0]

    if msg_id not in predis_review_queue:
        await query.edit_message_text("\u26a0\ufe0f This review item has expired (bot restarted).")
        return

    item = predis_review_queue.pop(msg_id)

    if action == PREDIS_REJECT:
        await query.edit_message_text(
            f"\u274c <b>Rejected and discarded.</b>\n\n"
            f"Source: {item['source']}\n"
            f"Predis ID: <code>{item['post_id']}</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    if action == PREDIS_APPROVE:
        await query.edit_message_text(
            f"\u2705 <b>Approved!</b>\n\n"
            f"Content is in your Predis.ai dashboard ready to schedule.\n\n"
            f"\U0001f4cc <b>Next steps:</b>\n"
            f"1. Open predis.ai/app\n"
            f"2. Find this post in your content library\n"
            f"3. Schedule or publish to connected accounts\n\n"
            f"Predis ID: <code>{item['post_id']}</code>\n"
            f"Source: {item['source']}\n"
            f"Media: {len(item['media_urls'])} file(s)",
            parse_mode=ParseMode.HTML,
        )




async def handle_brand_it(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Brand It' button \u2014 sends existing carousel text to Predis for rendering."""
    query = update.callback_query
    await query.answer()

    key = query.data.replace("brand_it:", "")

    if key not in pending_branded:
        await query.edit_message_text(
            query.message.text + "\n\n\u26a0\ufe0f Carousel text expired (bot restarted)."
        )
        return

    if not PREDIS_API_KEY or not PREDIS_BRAND_ID:
        await query.edit_message_text(
            query.message.text + "\n\n\u274c Predis not configured. Run /predis_setup"
        )
        return

    item = pending_branded.pop(key)
    chat_id = item["chat_id"]
    text = item["text"]
    topic = item["topic"]

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="\U0001f3a8 Rendering branded carousel via Predis.ai...",
    )

    try:
        predis_result = await predis_create_content(
            text=text,
            media_type="carousel",
            model_version="4",
            n_posts=1,
        )

        if not predis_result.get("ok"):
            error = predis_result.get("error", predis_result.get("errors", "Unknown"))
            await status_msg.edit_text(f"\u274c Predis error: {str(error)[:300]}")
            return

        post_id = predis_result.get("post_ids", [""])[0]
        await status_msg.edit_text(f"\u23f3 Rendering... ({post_id[:12]})")

        completed = await predis_poll_until_complete(post_id, max_wait=180, interval=5)

        if not completed.get("ok"):
            await status_msg.edit_text("\u26a0\ufe0f Timed out. Check predis.ai/app")
            return

        media_urls = completed.get("urls", [])
        caption = (
            f"\U0001f4cb {topic}\n\n"
            f"La regularizaci\u00f3n 2026 abre en abril. "
            f"\u00bfCumples los requisitos? Verif\u00edcalo gratis.\n\n"
            f"\U0001f449 Link en bio \u2192 tuspapeles2026.es\n\n"
            f"#regularizacion2026 #papeles2026 #sinpapeles #tuspapeles"
        )

        await send_predis_to_review(
            bot=context.bot,
            chat_id=chat_id,
            post_id=post_id,
            caption=caption,
            media_urls=media_urls,
            media_type="carousel",
            source=f"brand_it: {topic[:40]}",
        )

    except Exception as e:
        logger.error(f"Brand It error: {e}", exc_info=True)
        await status_msg.edit_text(f"\u274c Error: {str(e)[:300]}")


# ==============================================================================
# CALLBACK HANDLERS
# ==============================================================================


async def handle_publish_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle publish button callbacks."""
    query = update.callback_query
    await query.answer()

    # Check team access
    if query.from_user.id not in TEAM_CHAT_IDS:
        await query.answer("Not authorized", show_alert=True)
        return

    data = query.data

    # Delete flow callbacks
    if data.startswith("del_pick_"):
        delete_id = data[9:]
        pending = pending_deletes.get(delete_id)
        if not pending:
            await query.answer("Session expired. Run /delete again.", show_alert=True)
            return
        article = pending["article"]
        buttons = [
            [
                InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"del_yes_{delete_id}"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"del_no_{delete_id}"),
            ]
        ]
        await query.edit_message_text(
            f"¿Eliminar '*{escape_md(article['title'])}*'?\n\n"
            f"Esta acción no se puede deshacer.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("del_no_"):
        await query.edit_message_text("Cancelado.")
        return

    if data.startswith("del_yes_"):
        delete_id = data[8:]
        pending = pending_deletes.get(delete_id)
        if not pending:
            await query.answer("Session expired. Run /delete again.", show_alert=True)
            return
        article = pending["article"]
        slug = article["slug"]
        repo = GITHUB_REPO_TP

        await query.edit_message_text(f"⏳ Eliminando '{article['title']}'...")

        try:
            # 1. Delete the HTML file
            html_deleted = await delete_github_file(
                repo, f"blog/{slug}.html", f"Delete: {article['title']}"
            )

            # 2. Remove from index.json
            all_articles = pending.get("all_articles", [])
            updated_articles = [a for a in all_articles if a.get("slug") != slug]
            index_data = json.dumps({"articles": updated_articles}, ensure_ascii=False, indent=2)

            index_ok = await publish_to_github(
                repo, "blog/index.json", index_data,
                f"Remove from index: {article['title']}",
            )

            if html_deleted and index_ok:
                await query.edit_message_text(f"✅ Eliminado: {article['title']}")
            elif html_deleted:
                await query.edit_message_text(f"⚠️ HTML eliminado, pero index.json falló.")
            else:
                await query.edit_message_text(f"❌ Error al eliminar. Inténtalo de nuevo.")

            # Clean up
            pending_deletes.pop(delete_id, None)

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {e}")
        return

    # Duplicate warning confirm
    if data.startswith("dup_yes_"):
        article_id = data[8:]
        article = pending_articles.get(article_id)
        if not article:
            await query.answer("Article expired. Generate again.", show_alert=True)
            return
        # Show publish buttons
        buttons = [
            [
                InlineKeyboardButton("🌐 Publicar en web", callback_data=f"pub_tp_{article_id}"),
                InlineKeyboardButton("📢 Canal", callback_data=f"pub_ch_{article_id}"),
            ]
        ]
        await query.edit_message_text(
            f"📝 *Publish anyway:* {escape_md(article.get('title', ''))}\n\nChoose destination:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    if data.startswith("dup_no_"):
        await query.edit_message_text("Publication cancelled.")
        return

    # Weekly confirm/cancel
    if data == "weekly_confirm":
        await query.edit_message_text("🚀 Starting weekly generation...")
        await _run_weekly(update, context)
        return
    elif data == "weekly_cancel":
        await query.edit_message_text("Cancelled.")
        return

    # News alert actions
    if data == "news_ignore":
        await query.edit_message_text("Ignored.")
        return
    if data.startswith("news_blog_"):
        topic = data[10:]
        wait_msg = await query.message.reply_text("⏳ Generating blog article from news...")
        try:
            article_data = await generate_content("blog", topic)
            article_id = hashlib.md5(
                json.dumps(article_data, default=str).encode()
            ).hexdigest()[:8]
            pending_articles[article_id] = article_data
            buttons = [
                [
                    InlineKeyboardButton("🌐 Publicar en web", callback_data=f"pub_tp_{article_id}"),
                    InlineKeyboardButton("📢 Canal", callback_data=f"pub_ch_{article_id}"),
                ]
            ]
            word_count = article_data.get("word_count", len(article_data.get("html_content", "").split()))
            meta_msg = (
                f"📝 *BLOG ARTICLE READY*\n\n"
                f"*Title:* {escape_md(article_data.get('title', ''))}\n"
                f"*Words:* {word_count}\n\n"
                f"Full article attached as HTML file below."
            )
            await wait_msg.delete()
            await send_long_message(update, meta_msg, context, reply_markup=InlineKeyboardMarkup(buttons), chat_id=query.message.chat_id)
            await send_as_file(
                query.message.chat_id,
                article_data.get("html_content", ""),
                f"{article_data.get('slug', 'article')}.html",
                f"📝 {article_data.get('title', 'Blog')}",
                context,
            )
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return
    if data.startswith("news_tiktok_"):
        topic = data[12:]
        wait_msg = await query.message.reply_text("⏳ Generating TikTok script from news...")
        try:
            tiktok_data = await generate_content("tiktok", topic)
            formatted = format_tiktok_for_telegram(tiktok_data)
            await wait_msg.delete()
            await send_long_message(update, formatted, context, chat_id=query.message.chat_id)
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return
    if data.startswith("news_wa_"):
        topic = data[8:]
        wait_msg = await query.message.reply_text("⏳ Generating WhatsApp message from news...")
        try:
            wa_data = await generate_content("whatsapp", f"type: news — {topic}")
            formatted = format_whatsapp_for_telegram(wa_data)
            await wait_msg.delete()
            await send_long_message(update, formatted, context, chat_id=query.message.chat_id)
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return
    if data.startswith("news_chan_"):
        topic = data[10:]
        await query.answer("Publicando noticia en canal...")
        try:
            channel_text = (
                f"🚨 *NOTICIA: Regularización 2026*\n\n"
                f"📰 {topic}\n\n"
                f"Más info en tuspapeles2026.es\n\n"
                f"@tuspapeles2026"
            )
            ok, err = await post_to_channel(context.bot, channel_text)
            original_text = query.message.text or ""
            if ok:
                new_text = original_text + "\n\n✅ Publicado en canal @tuspapeles2026"
            else:
                new_text = original_text + f"\n\n❌ Error al publicar en canal: {err}"
            try:
                await query.edit_message_text(new_text[:TG_MAX_LEN], parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await query.edit_message_text(new_text[:TG_MAX_LEN])
        except Exception as e:
            logger.error(f"News channel post error: {e}")
            await query.answer(f"Error: {e}", show_alert=True)
        return

    # Blog topic selection
    if data.startswith("blog_"):
        topic = data[5:]
        wait_msg = await query.message.reply_text("⏳ Generating blog article...")
        try:
            article_data = await generate_content("blog", topic)
            formatted = format_blog_for_telegram(article_data)

            article_id = hashlib.md5(
                json.dumps(article_data, default=str).encode()
            ).hexdigest()[:8]
            pending_articles[article_id] = article_data

            buttons = [
                [
                    InlineKeyboardButton(
                        "🌐 Publicar en web",
                        callback_data=f"pub_tp_{article_id}",
                    ),
                    InlineKeyboardButton(
                        "📢 Canal",
                        callback_data=f"pub_ch_{article_id}",
                    ),
                ]
            ]
            markup = InlineKeyboardMarkup(buttons)
            await wait_msg.delete()
            await send_long_message(update, formatted, context, reply_markup=markup, chat_id=query.message.chat_id)
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return

    # Channel post for non-blog content
    if data.startswith("chpost_"):
        post_id = data[7:]
        post_info = pending_channel_posts.get(post_id)
        if not post_info:
            await query.answer("Content expired. Generate again.", show_alert=True)
            return
        await query.answer("Publicando en canal...")
        try:
            content_type = post_info["type"]
            content_data = post_info["data"]
            channel_text = format_content_for_channel(content_type, content_data)
            ok, err = await post_to_channel(context.bot, channel_text)
            original_text = query.message.text or ""
            if ok:
                new_text = original_text + "\n\n✅ Publicado en canal @tuspapeles2026"
            else:
                new_text = original_text + f"\n\n❌ Error al publicar en canal: {err}"
            try:
                await query.edit_message_text(new_text[:TG_MAX_LEN], parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await query.edit_message_text(new_text[:TG_MAX_LEN])
        except Exception as e:
            logger.error(f"Channel post error: {e}")
            await query.answer(f"Error: {e}", show_alert=True)
        return

    # Publish to channel or GitHub
    if data.startswith("pub_"):
        parts = data.split("_", 2)  # pub, ch/tp, article_id
        if len(parts) < 3:
            await query.answer("Invalid callback data", show_alert=True)
            return

        target = parts[1]  # ch or tp
        article_id = parts[2]

        article = pending_articles.get(article_id)
        if not article:
            await query.answer(
                "Article expired from cache. Generate again.",
                show_alert=True,
            )
            return

        # Channel publish path
        if target == "ch":
            await query.answer("Publicando en canal...")
            try:
                channel_text = format_content_for_channel("blog", article)
                ok, err = await post_to_channel(context.bot, channel_text)
                original_text = query.message.text or ""
                if ok:
                    new_text = original_text + "\n\n✅ Publicado en canal @tuspapeles2026"
                else:
                    new_text = original_text + f"\n\n❌ Error al publicar en canal: {err}"
                try:
                    await query.edit_message_text(new_text[:TG_MAX_LEN], parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    await query.edit_message_text(new_text[:TG_MAX_LEN])
            except Exception as e:
                logger.error(f"Channel publish error: {e}")
                await query.answer(f"Error: {e}", show_alert=True)
            return

        # Web publish path (tp only now)
        repo = GITHUB_REPO_TP
        site_name = "tuspapeles2026"

        if not GITHUB_TOKEN:
            await query.answer(
                "GITHUB_TOKEN not configured. Cannot publish.",
                show_alert=True,
            )
            return

        # Check for duplicates before publishing
        try:
            existing_articles, _ = await fetch_blog_index(repo)
            dup_found, dup_title = is_duplicate(
                article.get("title", ""), existing_articles
            )
            if dup_found:
                buttons = [
                    [
                        InlineKeyboardButton("✅ Publish anyway", callback_data=f"dup_yes_{article_id}"),
                        InlineKeyboardButton("❌ Cancel", callback_data=f"dup_no_{article_id}"),
                    ]
                ]
                await query.edit_message_text(
                    f"⚠️ *Similar article exists:*\n{escape_md(dup_title)}\n\nPublish anyway?",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return
        except Exception as e:
            logger.warning("Duplicate check failed, proceeding: %s", e)

        await query.answer(f"Publishing to {site_name}...")

        try:
            title = article.get("title", "Untitled")
            slug = article.get("slug", "article")
            html_content = article.get("html_content", "")
            meta_desc = article.get("meta_description", "")
            date_str = datetime.now().strftime("%d de %B de %Y")

            category = detect_blog_category(title, slug)
            full_html = wrap_blog_html(
                title, html_content, meta_desc, date_str,
                slug=slug, category=category,
            )
            file_path = f"blog/{slug}.html"
            commit_msg = f"Publish blog: {title}"

            success = await publish_to_github(
                repo, file_path, full_html, commit_msg
            )

            if success:
                # Update blog/index.json
                index_ok = await update_blog_index(
                    repo, slug, title, meta_desc, html_content, category
                )
                index_status = " + index.json updated" if index_ok else " (index.json update failed)"

                # Update Estado timeline on homepage
                estado_ok = await update_estado_timeline(
                    repo, title, meta_desc, category
                )
                if estado_ok:
                    index_status += " + Estado updated"

                # Auto-generate branded carousel via Predis after publish
                if PREDIS_API_KEY and PREDIS_BRAND_ID:
                    try:
                        predis_text = (
                            f"{title}. "
                            f"Regularizaci\u00f3n extraordinaria 2026 en Espa\u00f1a. "
                            f"Requisitos: 5 meses de residencia continuada, sin necesidad de oferta de empleo. "
                            f"Ventana de solicitud: 1 abril \u2013 30 junio 2026. 100% online. "
                            f"tuspapeles2026.es"
                        )
                        predis_result = await predis_create_content(
                            text=predis_text,
                            media_type="carousel",
                            model_version="4",
                            n_posts=1,
                        )
                        if predis_result.get("ok"):
                            p_id = predis_result["post_ids"][0]
                            completed = await predis_poll_until_complete(p_id, max_wait=180, interval=5)
                            if completed.get("ok"):
                                p_urls = completed.get("urls", [])
                                p_caption = (
                                    f"\U0001f4f0 {title}\n\n"
                                    f"Lee el art\u00edculo completo en tuspapeles2026.es/informacion\n\n"
                                    f"#regularizacion2026 #papeles2026 #sinpapeles #tuspapeles"
                                )
                                for team_cid in TEAM_CHAT_IDS:
                                    try:
                                        await send_predis_to_review(
                                            bot=context.bot,
                                            chat_id=team_cid,
                                            post_id=p_id,
                                            caption=p_caption,
                                            media_urls=p_urls,
                                            media_type="carousel",
                                            source=f"auto: {title[:40]}",
                                        )
                                    except Exception as e:
                                        logger.warning(f"Failed to send review to {team_cid}: {e}")
                                index_status += " + Predis carousel queued"
                                logger.info(f"Auto branded carousel queued for review \u2014 {title}")
                            else:
                                logger.warning(f"Predis render timed out for {title}")
                        else:
                            logger.warning(f"Predis create failed: {predis_result}")
                    except Exception as e:
                        logger.error(f"Auto Predis error: {e}")

                # Update the message to show success
                original_text = query.message.text or ""
                new_text = original_text + f"\n\n\u2705 Published to {site_name}!{index_status}"
                try:
                    await query.edit_message_text(
                        new_text[:TG_MAX_LEN],
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    await query.edit_message_text(
                        new_text[:TG_MAX_LEN]
                    )
            else:
                original_text = query.message.text or ""
                new_text = (
                    original_text
                    + f"\n\n❌ Publish to {site_name} failed. "
                    "Copy the article text above and publish manually."
                )
                try:
                    await query.edit_message_text(
                        new_text[:TG_MAX_LEN],
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    await query.edit_message_text(
                        new_text[:TG_MAX_LEN]
                    )

        except Exception as e:
            logger.error(f"Publish error: {e}")
            await query.answer(
                f"Publish failed: {e}", show_alert=True
            )


# ==============================================================================
# UNIFIED CALLBACK ROUTER
# ==============================================================================


async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all callback queries to appropriate handlers."""
    query = update.callback_query
    data = query.data or ""

    # V4 approval: pa_ = approve, pr_ = reject
    if data.startswith("pa_"):
        await query.answer()
        post_id_fragment = data[3:]

        # Update content log
        for entry in reversed(content_log):
            pid = entry.get("predis_post_id") or ""
            if pid.startswith(post_id_fragment) or post_id_fragment in pid:
                entry["approved"] = True
                save_content_log()
                break

        # Also handle review queue if present
        msg_id = query.message.message_id
        if msg_id in predis_review_queue:
            predis_review_queue.pop(msg_id)

        await query.edit_message_text(
            "\u2705 Aprobado \u2014 se publica en pr\u00f3ximo horario",
        )
        return

    if data.startswith("pr_"):
        await query.answer()
        post_id_fragment = data[3:]

        # Update content log
        for entry in reversed(content_log):
            pid = entry.get("predis_post_id") or ""
            if pid.startswith(post_id_fragment) or post_id_fragment in pid:
                entry["approved"] = False
                save_content_log()
                break

        msg_id = query.message.message_id
        if msg_id in predis_review_queue:
            predis_review_queue.pop(msg_id)

        await query.edit_message_text(
            "\u274c Rechazado \u2014 \u26a0\ufe0f elimina manualmente en predis.ai/app",
        )
        return

    # Legacy Predis review (predis_approve:/predis_reject:)
    if data.startswith(f"{PREDIS_APPROVE}:") or data.startswith(f"{PREDIS_REJECT}:"):
        await handle_predis_review(update, context)
        return

    # Brand It callback
    if data.startswith("brand_it:"):
        await handle_brand_it(update, context)
        return

    # Everything else → legacy publish callback handler
    await handle_publish_callback(update, context)


# ==============================================================================
# MAIN
# ==============================================================================


def main():
    """Start the bot."""
    global topic_history
    load_content_log()
    topic_history = load_topic_history()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Core commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # Content generation commands (V4)
    app.add_handler(CommandHandler("blog", cmd_blog))
    app.add_handler(CommandHandler("video", cmd_video))
    app.add_handler(CommandHandler("carousel", cmd_carousel))
    app.add_handler(CommandHandler("image", cmd_image))
    app.add_handler(CommandHandler("reel", cmd_reel))
    app.add_handler(CommandHandler("meme", cmd_meme))
    app.add_handler(CommandHandler("quote", cmd_quote))
    app.add_handler(CommandHandler("whatsapp", cmd_whatsapp))
    app.add_handler(CommandHandler("fbtext", cmd_fbtext))

    # Batch generation commands
    app.add_handler(CommandHandler("video5", cmd_video5))

    # Weekly mega-batch
    app.add_handler(CommandHandler("weekly", cmd_weekly))

    # Daily auto-generation
    app.add_handler(CommandHandler("daily", cmd_daily))

    # Planning & discovery
    app.add_handler(CommandHandler("ideas", cmd_ideas))

    # Monitoring & tools
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("predis", cmd_predis))
    app.add_handler(CommandHandler("articles", cmd_articles))
    app.add_handler(CommandHandler("delete", cmd_delete))

    # Unified callback handler (routes pa_/pr_, predis review, brand_it, publish)
    app.add_handler(CallbackQueryHandler(handle_all_callbacks))

    # Catch-all for non-team members
    app.add_handler(MessageHandler(filters.ALL, handle_unauthorized))

    # Schedule news auto-scan every 6 hours (Madrid time)
    scheduler = AsyncIOScheduler(timezone="Europe/Madrid")

    async def post_init(application):
        """Start the scheduler and download logos after the application is initialized."""
        scheduler.add_job(
            auto_scan_news,
            "cron",
            hour="6,12,18,0",
            kwargs={"bot": application.bot},
        )
        scheduler.add_job(
            scheduled_daily_generation,
            "cron",
            hour=7,
            minute=30,
            kwargs={"bot": application.bot},
        )
        scheduler.start()
        logger.info("News auto-scan scheduler started (every 6h Madrid time)")
        logger.info("Daily auto-generation scheduled (7:30am Madrid)")
        await ensure_logos()
        logger.info("Logo download check complete")

    app.post_init = post_init

    logger.info("Content Bot v4.1 starting")
    logger.info(f"Team IDs: {TEAM_CHAT_IDS}")
    logger.info(f"Phase: {get_current_phase()}")
    app.run_polling()


if __name__ == "__main__":
    main()
