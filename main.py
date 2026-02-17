#!/usr/bin/env python3
"""
================================================================================
Content Bot v3.0 — AI Content Factory for tuspapeles2026
================================================================================
Repository: github.com/anacuero-bit/content-bot
Updated:    2026-02-16

Team-only Telegram bot that generates marketing content via Claude API.
Supports one-tap blog publishing to pombohorowitz.es and tuspapeles2026.es.

CHANGELOG:
----------
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
import random
import hashlib
import base64
import io
from datetime import datetime, timedelta

from typing import Optional
from functools import wraps

import anthropic
import httpx
import feedparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO_PH = os.environ.get("GITHUB_REPO_PH", "anacuero-bit/PH-Site")
GITHUB_REPO_TP = os.environ.get("GITHUB_REPO_TP", "anacuero-bit/tus-papeles-2026")

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
}

# Track recent topics to avoid repetition (in-memory, resets on restart)
RECENT_TOPICS = {
    "tiktok": [],
    "carousel": [],
    "story": [],
    "whatsapp": [],
    "fbpost": [],
}

MAX_RECENT = 10  # Remember last 10 topics per type

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


def pick_topic(content_type, user_topic=None):
    """Pick a topic, avoiding recent ones. If user provides topic, use it."""
    if user_topic:
        # User specified topic — use it but still track it
        RECENT_TOPICS.setdefault(content_type, []).append(user_topic)
        if len(RECENT_TOPICS[content_type]) > MAX_RECENT:
            RECENT_TOPICS[content_type].pop(0)
        return user_topic

    pool = TOPIC_POOLS.get(content_type, [])
    if not pool:
        return ""
    recent = RECENT_TOPICS.get(content_type, [])

    # Filter out recently used topics
    available = [t for t in pool if t not in recent]
    if not available:
        # All used — reset and start over
        RECENT_TOPICS[content_type] = []
        available = pool

    topic = random.choice(available)
    RECENT_TOPICS.setdefault(content_type, []).append(topic)
    if len(RECENT_TOPICS[content_type]) > MAX_RECENT:
        RECENT_TOPICS[content_type].pop(0)

    return topic


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
            "\nCONTENT TYPE: TIKTOK SCRIPT\n"
            "Write a TikTok script for 15-30 seconds.\n\n"
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
            "Create a [DURATION]-second vertical TikTok video in European Spanish (Spain). "
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
    content_type: str, topic: str = "", phase: str = None
) -> dict:
    """Call Claude API and return parsed JSON content."""
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
            "reading_time": f"{max(1, word_count // 200)} min",
            "category": category,
            "image": None,
        }

        # Remove duplicate slugs
        current_content["articles"] = [
            a for a in current_content["articles"] if a.get("slug") != slug
        ]
        current_content["articles"].append(new_entry)
        # Sort by date descending (newest first)
        current_content["articles"].sort(
            key=lambda a: a.get("date", ""), reverse=True
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


def wrap_blog_html(
    title: str, html_content: str, meta_description: str, date_str: str
) -> str:
    """Wrap article content in a full HTML page template for GitHub Pages."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | tuspapeles2026.es</title>
    <meta name="description" content="{meta_description}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://tuspapeles2026.es/blog/">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #333;
            max-width: 720px;
            margin: 0 auto;
            padding: 2rem 1rem;
            background: #fafafa;
        }}
        header {{
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #2563eb;
        }}
        header a {{
            color: #2563eb;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
        }}
        h1 {{
            font-size: 2rem;
            line-height: 1.3;
            margin: 1rem 0;
            color: #1a1a1a;
        }}
        .meta {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}
        h2 {{
            font-size: 1.4rem;
            margin: 1.5rem 0 0.8rem;
            color: #1a1a1a;
        }}
        p {{
            margin-bottom: 1rem;
        }}
        a {{
            color: #2563eb;
        }}
        .cta-box {{
            background: #2563eb;
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            margin: 2rem 0;
        }}
        .cta-box a {{
            color: white;
            font-weight: bold;
        }}
        footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            font-size: 0.85rem;
            color: #888;
            text-align: center;
        }}
    </style>
</head>
<body>
    <header>
        <a href="https://tuspapeles2026.es">← tuspapeles2026.es</a>
    </header>

    <article>
        <h1>{title}</h1>
        <div class="meta">Publicado el {date_str}</div>
        {html_content}
    </article>

    <div class="cta-box">
        <p>Verifica tu elegibilidad gratis</p>
        <p><a href="https://tuspapeles2026.es">tuspapeles2026.es</a> |
           <a href="https://t.me/tuspapeles2026bot">Telegram Bot</a></p>
    </div>

    <footer>
        &copy; 2026 tuspapeles2026.es — Respaldado por Pombo &amp; Horowitz Abogados
    </footer>
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
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
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
        "🤖 *Content Bot v3.0 — Commands*\n\n"
        "*Single Generation:*\n"
        "  /blog \\[topic|noticias|guias|mitos\\] — SEO blog article\n"
        "  /tiktok \\[topic\\] — TikTok script\n"
        "  /carousel \\[topic\\] — Instagram carousel\n"
        "  /caption \\[ig|fb\\] \\[topic\\] — Social caption\n"
        "  /whatsapp \\[type\\] — WhatsApp message\n"
        "  /fbpost \\[topic\\] — Facebook group post\n"
        "  /story \\[type\\] — Instagram Story\n\n"
        "*Batch Generation:*\n"
        "  /tiktok5 — 5 TikTok scripts\n"
        "  /carousel3 — 3 carousel sets\n"
        "  /captions10 — 10 social captions\n"
        "  /whatsapp5 — 5 WhatsApp messages\n"
        "  /fbpost5 — 5 Facebook posts\n"
        "  /stories7 — 7 Story concepts\n\n"
        "*Mega Batch:*\n"
        "  /weekly — Full weekly pack (~46 pieces)\n\n"
        "*Tools:*\n"
        "  /news — Latest regularización news\n"
        "  /scan — Force immediate news scan\n"
        "  /topics — 10 topic suggestions\n"
        "  /stats — Generation statistics\n"
        "  /phase \\[phase\\] — Set campaign phase\n"
        "  /backfill — Publish 7 launch articles\n"
        "  /articles — List all published articles\n"
        "  /delete \\[slug|number\\] — Remove a published article\n"
        "  /help — This message"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


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
                    "🚀 Publish to PH-Site", callback_data=f"pub_ph_{article_id}"
                ),
                InlineKeyboardButton(
                    "🌐 Publish to TP", callback_data=f"pub_tp_{article_id}"
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


@team_only
async def cmd_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tiktok [topic] command."""
    user_topic = " ".join(context.args) if context.args else None
    topic = pick_topic("tiktok", user_topic)
    wait_msg = await update.message.reply_text("⏳ Generating TikTok script...")
    try:
        data = await generate_content("tiktok", topic)
        formatted = format_tiktok_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating TikTok: {e}")


@team_only
async def cmd_carousel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /carousel [topic] command."""
    user_topic = " ".join(context.args) if context.args else None
    topic = pick_topic("carousel", user_topic)
    wait_msg = await update.message.reply_text("⏳ Generating carousel...")
    try:
        data = await generate_content("carousel", topic)
        formatted = format_carousel_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating carousel: {e}")


@team_only
async def cmd_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /caption [ig|fb] [topic] command."""
    args = context.args if context.args else []
    platform = ""
    topic_parts = []

    for arg in args:
        if arg.lower() in ("ig", "instagram", "fb", "facebook"):
            platform = "instagram" if arg.lower() in ("ig", "instagram") else "facebook"
        else:
            topic_parts.append(arg)

    user_topic = " ".join(topic_parts)
    if platform:
        user_topic = f"for {platform}. {user_topic}" if user_topic else f"for {platform}"
    topic = pick_topic("caption", user_topic if user_topic else None)

    wait_msg = await update.message.reply_text("⏳ Generating caption...")
    try:
        data = await generate_content("caption", topic)
        formatted = format_caption_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating caption: {e}")


@team_only
async def cmd_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /whatsapp [type] command."""
    msg_type = context.args[0] if context.args else ""
    valid_types = ["news", "deadline", "educational", "referral", "re-engagement"]
    user_topic = None
    if msg_type in valid_types:
        user_topic = f"type: {msg_type}"
    elif msg_type:
        user_topic = msg_type
    topic = pick_topic("whatsapp", user_topic)

    wait_msg = await update.message.reply_text("⏳ Generating WhatsApp message...")
    try:
        data = await generate_content("whatsapp", topic)
        formatted = format_whatsapp_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating WhatsApp message: {e}")


@team_only
async def cmd_fbpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fbpost [topic] command."""
    user_topic = " ".join(context.args) if context.args else None
    topic = pick_topic("fbpost", user_topic)
    wait_msg = await update.message.reply_text("⏳ Generating Facebook post...")
    try:
        data = await generate_content("fbpost", topic)
        formatted = format_fbpost_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating FB post: {e}")


@team_only
async def cmd_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /story [type] command."""
    story_type = context.args[0] if context.args else ""
    valid_types = ["poll", "question", "countdown", "quiz", "tip"]
    user_topic = None
    if story_type in valid_types:
        user_topic = f"type: {story_type}"
    elif story_type:
        user_topic = story_type
    topic = pick_topic("story", user_topic)

    wait_msg = await update.message.reply_text("⏳ Generating Story concept...")
    try:
        data = await generate_content("story", topic)
        formatted = format_story_for_telegram(data)
        await wait_msg.delete()
        await send_long_message(update, formatted, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating Story: {e}")


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
                            "🚀 PH-Site",
                            callback_data=f"pub_ph_{article_id}",
                        ),
                        InlineKeyboardButton(
                            "🌐 TP",
                            callback_data=f"pub_tp_{article_id}",
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
async def cmd_tiktok5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tiktok5 — generate 5 TikTok scripts."""
    topics = pick_multiple_topics("tiktok", 5)
    await _batch_generate(update, context, "tiktok", 5, topics)


@team_only
async def cmd_carousel3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /carousel3 — generate 3 carousel sets."""
    topics = pick_multiple_topics("carousel", 3)
    await _batch_generate(update, context, "carousel", 3, topics)


@team_only
async def cmd_captions10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /captions10 — generate 10 captions."""
    topics = pick_multiple_topics("caption", 10)
    await _batch_generate(update, context, "caption", 10, topics)


@team_only
async def cmd_whatsapp5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /whatsapp5 — generate 5 WhatsApp messages."""
    topics = pick_multiple_topics("whatsapp", 5)
    await _batch_generate(update, context, "whatsapp", 5, topics)


@team_only
async def cmd_fbpost5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fbpost5 — generate 5 Facebook posts."""
    topics = pick_multiple_topics("fbpost", 5)
    await _batch_generate(update, context, "fbpost", 5, topics)


@team_only
async def cmd_stories7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stories7 — generate 7 Story concepts."""
    topics = pick_multiple_topics("story", 7)
    await _batch_generate(update, context, "story", 7, topics)


# ==============================================================================
# COMMAND HANDLERS — WEEKLY MEGA-BATCH
# ==============================================================================


@team_only
async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /weekly — generate full weekly content pack."""
    chat_id = update.effective_chat.id

    # Check cooldown
    last = gen_stats.get("last_weekly")
    if last and (datetime.now() - last) < timedelta(hours=24):
        hours_ago = (datetime.now() - last).total_seconds() / 3600
        buttons = [
            [
                InlineKeyboardButton("Yes, generate", callback_data="weekly_confirm"),
                InlineKeyboardButton("Cancel", callback_data="weekly_cancel"),
            ]
        ]
        await update.message.reply_text(
            f"⚠️ Last weekly was {hours_ago:.1f} hours ago. Are you sure?",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    await _run_weekly(update, context)


async def _run_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the full weekly generation."""
    chat_id = update.effective_chat.id
    gen_stats["last_weekly"] = datetime.now()

    await context.bot.send_message(
        chat_id=chat_id,
        text="🚀 *Generating weekly content pack... this takes ~2 minutes*",
        parse_mode=ParseMode.MARKDOWN,
    )

    total = 0

    # 7 TikTok scripts (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 1/7: TikTok scripts*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "tiktok", 7, pick_multiple_topics("tiktok", 7))
    total += count

    # 5 Carousel sets (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 2/7: Carousels*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "carousel", 5, pick_multiple_topics("carousel", 5))
    total += count

    # 14 Stories (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 3/7: Stories*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "story", 14, pick_multiple_topics("story", 14))
    total += count

    # 3 WhatsApp messages (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 4/7: WhatsApp*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "whatsapp", 3, pick_multiple_topics("whatsapp", 3))
    total += count

    # 5 Facebook posts (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 5/7: Facebook posts*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "fbpost", 5, pick_multiple_topics("fbpost", 5))
    total += count

    # 2 Blog articles (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 6/7: Blog articles*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "blog", 2, pick_multiple_topics("blog", 2))
    total += count

    # 10 Captions (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 7/7: Captions*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "caption", 10, pick_multiple_topics("caption", 10))
    total += count

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *WEEKLY PACK COMPLETE* — {total} pieces generated!",
        parse_mode=ParseMode.MARKDOWN,
    )


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
async def cmd_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /topics — generate 10 topic suggestions."""
    wait_msg = await update.message.reply_text("⏳ Generating topic suggestions...")
    try:
        data = await generate_content("topics")
        topics_list = data.get("topics", [])

        text = f"💡 *10 TOPIC SUGGESTIONS* (Phase: {get_current_phase()})\n\n"
        for i, t in enumerate(topics_list, 1):
            formats = ", ".join(t.get("best_formats", []))
            text += (
                f"*{i}.* {escape_md(t.get('title', ''))}\n"
                f"   📐 {escape_md(t.get('angle', ''))}\n"
                f"   📱 Best for: {escape_md(formats)}\n\n"
            )

        await wait_msg.delete()
        await send_long_message(update, text, context)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Error: {e}")


@team_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats — show generation statistics."""
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = gen_stats["by_date"].get(today, 0)

    # Calculate this week's count
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_count = sum(
        v
        for k, v in gen_stats["by_date"].items()
        if k >= week_start.strftime("%Y-%m-%d")
    )

    # By type breakdown
    by_type = "\n".join(
        f"  {k}: {v}" for k, v in sorted(gen_stats["by_type"].items())
    )
    if not by_type:
        by_type = "  No content generated yet"

    last_weekly = gen_stats.get("last_weekly")
    weekly_info = (
        last_weekly.strftime("%Y-%m-%d %H:%M")
        if last_weekly
        else "Never"
    )

    text = (
        f"📊 *GENERATION STATS*\n\n"
        f"*Today:* {today_count}\n"
        f"*This week:* {week_count}\n"
        f"*Total:* {gen_stats['total']}\n\n"
        f"*By type:*\n{by_type}\n\n"
        f"*Last /weekly:* {weekly_info}\n"
        f"*Phase:* {get_current_phase()}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@team_only
async def cmd_phase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /phase [phase_name] — override campaign phase."""
    global phase_override

    valid_phases = ["pre_boe", "boe_week", "apps_open", "final_push"]

    if not context.args:
        phase_override = None
        await update.message.reply_text(
            f"Phase reset to auto-detect: *{get_current_phase()}*",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    new_phase = context.args[0].lower()
    if new_phase not in valid_phases:
        await update.message.reply_text(
            f"Invalid phase. Choose: {', '.join(valid_phases)}"
        )
        return

    phase_override = new_phase
    await update.message.reply_text(
        f"Phase set to: *{phase_override}*",
        parse_mode=ParseMode.MARKDOWN,
    )


# ==============================================================================
# BACKFILL — LAUNCH ARTICLES
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


@team_only
async def cmd_backfill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /backfill — generate and publish the 7 launch articles to TP repo."""
    chat_id = update.effective_chat.id
    repo = GITHUB_REPO_TP

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📚 *BACKFILL: Publishing {len(BACKFILL_ARTICLES)} launch articles to {repo}*\n"
             f"This will take a few minutes...",
        parse_mode=ParseMode.MARKDOWN,
    )

    success = 0
    for i, article in enumerate(BACKFILL_ARTICLES, 1):
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"📝 {i}/{len(BACKFILL_ARTICLES)}: {article['title'][:50]}...",
        )

        try:
            # Generate HTML body via Claude with legal facts in prompt
            phase = get_current_phase()
            system = get_system_prompt("blog", phase)
            user_msg = article["prompt"]

            response = await asyncio.to_thread(
                claude.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )

            html_body = response.content[0].text.strip()
            # Strip code blocks if present
            if html_body.startswith("```"):
                html_body = "\n".join(html_body.split("\n")[1:])
                if html_body.endswith("```"):
                    html_body = html_body[:-3]
                html_body = html_body.strip()

            # If Claude returned JSON instead of raw HTML, extract html_content
            if html_body.startswith("{"):
                try:
                    parsed = json.loads(html_body)
                    html_body = parsed.get("html_content", html_body)
                except json.JSONDecodeError:
                    pass

            # Wrap in full HTML template with historical date
            full_html = wrap_blog_html(
                article["title"],
                html_body,
                article["meta"],
                article["date_str"],
            )

            # Push article HTML
            file_path = f"blog/{article['slug']}.html"
            commit_msg = f"Publish: {article['title']}"
            pub_ok = await publish_to_github(repo, file_path, full_html, commit_msg)

            if pub_ok:
                # Update index.json with historical date
                idx_ok = await update_blog_index(
                    repo,
                    article["slug"],
                    article["title"],
                    article["meta"],
                    html_body,
                    article["category"],
                    date_override=article["date"],
                )
                status = "✅" if idx_ok else "⚠️ HTML ok, index failed"
                success += 1
            else:
                status = "❌ publish failed"

            await context.bot.send_message(chat_id=chat_id, text=f"  {status}")

        except Exception as e:
            logger.error(f"Backfill error for {article['slug']}: {e}")
            await context.bot.send_message(
                chat_id=chat_id, text=f"  ❌ Error: {e}"
            )

        # Rate limit
        await asyncio.sleep(2)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"📚 *BACKFILL COMPLETE* — {success}/{len(BACKFILL_ARTICLES)} articles published!",
        parse_mode=ParseMode.MARKDOWN,
    )


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

        # Delete
        resp = await client.delete(url, headers=headers, json={
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

    for source_url in NEWS_SCAN_SOURCES:
        try:
            feed = await asyncio.to_thread(feedparser.parse, source_url)
            for entry in feed.entries[:5]:
                headline_key = entry.title.strip().lower()[:100]
                if headline_key not in seen_headlines:
                    new_items.append({
                        "title": entry.title,
                        "link": entry.link,
                        "date": getattr(entry, "published", ""),
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


@team_only
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scan — force immediate news scan."""
    wait_msg = await update.message.reply_text("🔍 Scanning for new headlines...")
    await auto_scan_news(bot=context.bot)
    await wait_msg.edit_text("✅ News scan complete. Any new items were sent above.")


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
                InlineKeyboardButton("🚀 PH-Site", callback_data=f"pub_ph_{article_id}"),
                InlineKeyboardButton("🌐 TP", callback_data=f"pub_tp_{article_id}"),
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
                    InlineKeyboardButton("🚀 PH-Site", callback_data=f"pub_ph_{article_id}"),
                    InlineKeyboardButton("🌐 TP", callback_data=f"pub_tp_{article_id}"),
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
                        "🚀 Publish to PH-Site",
                        callback_data=f"pub_ph_{article_id}",
                    ),
                    InlineKeyboardButton(
                        "🌐 Publish to TP",
                        callback_data=f"pub_tp_{article_id}",
                    ),
                ]
            ]
            markup = InlineKeyboardMarkup(buttons)
            await wait_msg.delete()
            await send_long_message(update, formatted, context, reply_markup=markup, chat_id=query.message.chat_id)
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return

    # Publish to GitHub
    if data.startswith("pub_"):
        parts = data.split("_", 2)  # pub, ph/tp, article_id
        if len(parts) < 3:
            await query.answer("Invalid callback data", show_alert=True)
            return

        target = parts[1]  # ph or tp
        article_id = parts[2]
        repo = GITHUB_REPO_PH if target == "ph" else GITHUB_REPO_TP
        site_name = "PH-Site" if target == "ph" else "tuspapeles2026"

        article = pending_articles.get(article_id)
        if not article:
            await query.answer(
                "Article expired from cache. Generate again.",
                show_alert=True,
            )
            return

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

            full_html = wrap_blog_html(title, html_content, meta_desc, date_str)
            file_path = f"blog/{slug}.html"
            commit_msg = f"Publish blog: {title}"

            success = await publish_to_github(
                repo, file_path, full_html, commit_msg
            )

            if success:
                # Update blog/index.json
                category = detect_blog_category(title, slug)
                index_ok = await update_blog_index(
                    repo, slug, title, meta_desc, html_content, category
                )
                index_status = " + index.json updated" if index_ok else " (index.json update failed)"

                # Update the message to show success
                original_text = query.message.text or ""
                new_text = original_text + f"\n\n✅ Published to {site_name}!{index_status}"
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
# MAIN
# ==============================================================================


def main():
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Single generation commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("blog", cmd_blog))
    app.add_handler(CommandHandler("tiktok", cmd_tiktok))
    app.add_handler(CommandHandler("carousel", cmd_carousel))
    app.add_handler(CommandHandler("caption", cmd_caption))
    app.add_handler(CommandHandler("whatsapp", cmd_whatsapp))
    app.add_handler(CommandHandler("fbpost", cmd_fbpost))
    app.add_handler(CommandHandler("story", cmd_story))

    # Batch generation commands
    app.add_handler(CommandHandler("tiktok5", cmd_tiktok5))
    app.add_handler(CommandHandler("carousel3", cmd_carousel3))
    app.add_handler(CommandHandler("captions10", cmd_captions10))
    app.add_handler(CommandHandler("whatsapp5", cmd_whatsapp5))
    app.add_handler(CommandHandler("fbpost5", cmd_fbpost5))
    app.add_handler(CommandHandler("stories7", cmd_stories7))

    # Weekly mega-batch
    app.add_handler(CommandHandler("weekly", cmd_weekly))

    # Monitoring & tools
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("topics", cmd_topics))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("phase", cmd_phase))
    app.add_handler(CommandHandler("backfill", cmd_backfill))
    app.add_handler(CommandHandler("articles", cmd_articles))
    app.add_handler(CommandHandler("delete", cmd_delete))

    # Callback handlers (publish buttons, weekly confirm, blog topic selection)
    app.add_handler(CallbackQueryHandler(handle_publish_callback))

    # Catch-all for non-team members
    app.add_handler(MessageHandler(filters.ALL, handle_unauthorized))

    # Schedule news auto-scan every 6 hours (Madrid time)
    scheduler = AsyncIOScheduler(timezone="Europe/Madrid")

    async def post_init(application):
        """Start the scheduler after the application is initialized."""
        scheduler.add_job(
            auto_scan_news,
            "cron",
            hour="6,12,18,0",
            kwargs={"bot": application.bot},
        )
        scheduler.start()
        logger.info("News auto-scan scheduler started (every 6h Madrid time)")

    app.post_init = post_init

    logger.info("Content Bot v3.0 starting")
    logger.info(f"Team IDs: {TEAM_CHAT_IDS}")
    logger.info(f"Phase: {get_current_phase()}")
    app.run_polling()


if __name__ == "__main__":
    main()
