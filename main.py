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
from collections import deque
from typing import Optional
from functools import wraps

import anthropic
import httpx
import feedparser
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


# ==============================================================================
# TOPIC ROTATION POOL
# ==============================================================================

# Each topic has: key (unique ID), topic (prompt text), pillar (content category)
TOPIC_POOL = {
    "tiktok": [
        # Educational — myths
        {"key": "myth_job", "topic": "Mito: necesitas contrato de trabajo", "pillar": "educational"},
        {"key": "myth_money", "topic": "Mito: la regularización cuesta miles de euros", "pillar": "educational"},
        {"key": "myth_time", "topic": "Mito: ya es demasiado tarde para prepararse", "pillar": "educational"},
        {"key": "myth_lawyer", "topic": "Mito: necesitas un abogado carísimo", "pillar": "educational"},
        {"key": "myth_deport", "topic": "Mito: si pides papeles te deportan", "pillar": "educational"},
        # Educational — documents
        {"key": "docs_empadronamiento", "topic": "Cómo conseguir tu empadronamiento", "pillar": "educational"},
        {"key": "docs_antecedentes", "topic": "Certificado de antecedentes paso a paso", "pillar": "educational"},
        {"key": "docs_medical", "topic": "El certificado médico: qué es y dónde sacarlo", "pillar": "educational"},
        {"key": "docs_passport", "topic": "Pasaporte vencido: qué hacer si el tuyo expiró", "pillar": "educational"},
        {"key": "docs_proof", "topic": "Qué documentos prueban tu residencia en España", "pillar": "educational"},
        # Educational — process
        {"key": "vulnerability", "topic": "La cláusula de vulnerabilidad explicada", "pillar": "educational"},
        {"key": "compare_2005", "topic": "2005 vs 2026: qué cambió", "pillar": "educational"},
        {"key": "timeline", "topic": "Calendario de la regularización 2026", "pillar": "educational"},
        {"key": "cost", "topic": "Cuánto cuesta regularizarse realmente", "pillar": "educational"},
        {"key": "digital", "topic": "Todo se hace digital en 2026", "pillar": "educational"},
        {"key": "first_steps", "topic": "Los 3 primeros pasos para prepararte hoy", "pillar": "educational"},
        {"key": "scams", "topic": "Cómo detectar estafas de regularización", "pillar": "educational"},
        {"key": "pricing", "topic": "Todo por menos de 250 euros", "pillar": "educational"},
        {"key": "rights", "topic": "Tus derechos durante el proceso", "pillar": "educational"},
        # Educational — FAQs
        {"key": "fear_deportation", "topic": "¿Me pueden deportar si inicio el trámite?", "pillar": "educational"},
        {"key": "family", "topic": "Regularización y reunificación familiar", "pillar": "educational"},
        {"key": "work_permit", "topic": "Permiso de trabajo: qué cambia con los papeles", "pillar": "educational"},
        {"key": "faq_children", "topic": "¿Mis hijos también se regularizan?", "pillar": "educational"},
        {"key": "faq_criminal", "topic": "¿Antecedentes penales me descalifican?", "pillar": "educational"},
        {"key": "faq_years", "topic": "¿Cuántos años necesito en España?", "pillar": "educational"},
        # Emotional
        {"key": "emotional_fear", "topic": "Sabemos que tienes miedo. Es normal.", "pillar": "emotional"},
        {"key": "emotional_hope", "topic": "Imagina tu vida con papeles", "pillar": "emotional"},
        {"key": "emotional_family", "topic": "Volver a ver a tu familia sin miedo", "pillar": "emotional"},
        {"key": "emotional_work", "topic": "Trabajar sin miedo: lo que cambia con papeles", "pillar": "emotional"},
        {"key": "emotional_dignity", "topic": "Vivir con dignidad: tu vida después de regularizarte", "pillar": "emotional"},
        # News / Urgency
        {"key": "urgency_slots", "topic": "1.000 plazas: por qué importa ser rápido", "pillar": "news"},
        {"key": "urgency_prepare", "topic": "No esperes al BOE para prepararte", "pillar": "news"},
        {"key": "urgency_deadline", "topic": "La fecha límite se acerca: qué debes hacer ya", "pillar": "news"},
        {"key": "news_boe_update", "topic": "Lo último sobre el BOE y la regularización", "pillar": "news"},
        # Social proof
        {"key": "social_proof", "topic": "Miles de personas ya se están preparando", "pillar": "social_proof"},
        {"key": "social_testimonial", "topic": "Historia de alguien que se preparó a tiempo", "pillar": "social_proof"},
        {"key": "referral", "topic": "Invita a un amigo: programa de referidos", "pillar": "social_proof"},
        # Behind the scenes
        {"key": "behind_ai", "topic": "Cómo nuestra IA revisa tus documentos", "pillar": "behind_scenes"},
        {"key": "behind_team", "topic": "El equipo de abogados detrás de tuspapeles2026", "pillar": "behind_scenes"},
    ],
    "carousel": [
        {"key": "car_5myths", "topic": "5 mitos sobre la regularización desmentidos", "pillar": "educational"},
        {"key": "car_docs_checklist", "topic": "Checklist: los documentos que necesitas", "pillar": "educational"},
        {"key": "car_step_by_step", "topic": "Paso a paso: cómo iniciar tu trámite", "pillar": "educational"},
        {"key": "car_2005_vs_2026", "topic": "Diferencias entre la regularización de 2005 y 2026", "pillar": "educational"},
        {"key": "car_vulnerability", "topic": "La cláusula de vulnerabilidad en 6 slides", "pillar": "educational"},
        {"key": "car_cost_compare", "topic": "Compara precios: nosotros vs la competencia", "pillar": "educational"},
        {"key": "car_faq_top5", "topic": "Las 5 preguntas más frecuentes respondidas", "pillar": "educational"},
        {"key": "car_digital_process", "topic": "Todo el proceso es digital: así funciona", "pillar": "educational"},
        {"key": "car_scam_signs", "topic": "5 señales de que te están estafando", "pillar": "educational"},
        {"key": "car_empadronamiento", "topic": "Guía visual: cómo sacar tu empadronamiento", "pillar": "educational"},
        {"key": "car_timeline", "topic": "Calendario visual de la regularización 2026", "pillar": "news"},
        {"key": "car_deadline", "topic": "Cuenta atrás: lo que debes hacer antes de junio", "pillar": "news"},
        {"key": "car_imagine_life", "topic": "Imagina tu vida con papeles en 6 imágenes", "pillar": "emotional"},
        {"key": "car_fear_to_hope", "topic": "Del miedo a la esperanza: tu camino a los papeles", "pillar": "emotional"},
        {"key": "car_family_reunion", "topic": "Reunificación familiar: lo que significa regularizarte", "pillar": "emotional"},
        {"key": "car_success_stories", "topic": "Historias de éxito de la regularización de 2005", "pillar": "social_proof"},
        {"key": "car_numbers", "topic": "Los números: cuántas personas ya se preparan", "pillar": "social_proof"},
        {"key": "car_referral", "topic": "Programa Cónsul/Embajador: invita y ahorra", "pillar": "social_proof"},
        {"key": "car_ai_works", "topic": "Así funciona nuestra IA de validación de documentos", "pillar": "behind_scenes"},
        {"key": "car_rights", "topic": "Tus derechos durante el proceso de regularización", "pillar": "educational"},
    ],
    "whatsapp": [
        {"key": "wa_news_boe", "topic": "type: news — últimas novedades sobre el BOE", "pillar": "news"},
        {"key": "wa_news_update", "topic": "type: news — actualización del proceso de regularización", "pillar": "news"},
        {"key": "wa_deadline_reminder", "topic": "type: deadline — recordatorio de fecha límite", "pillar": "news"},
        {"key": "wa_deadline_countdown", "topic": "type: deadline — cuenta atrás para junio 2026", "pillar": "news"},
        {"key": "wa_edu_docs", "topic": "type: educational — prepara tus documentos ahora", "pillar": "educational"},
        {"key": "wa_edu_vulnerability", "topic": "type: educational — no necesitas contrato de trabajo", "pillar": "educational"},
        {"key": "wa_edu_process", "topic": "type: educational — el proceso paso a paso", "pillar": "educational"},
        {"key": "wa_edu_cost", "topic": "type: educational — cuánto cuesta realmente", "pillar": "educational"},
        {"key": "wa_edu_scams", "topic": "type: educational — cómo evitar estafas", "pillar": "educational"},
        {"key": "wa_referral_invite", "topic": "type: referral — invita a un amigo y ahorra €25", "pillar": "social_proof"},
        {"key": "wa_referral_consul", "topic": "type: referral — conviértete en Cónsul y gana más", "pillar": "social_proof"},
        {"key": "wa_reengage_quiet", "topic": "type: re-engagement — hace tiempo que no sabemos de ti", "pillar": "emotional"},
        {"key": "wa_reengage_ready", "topic": "type: re-engagement — ¿ya tienes tus documentos listos?", "pillar": "emotional"},
        {"key": "wa_emotional_hope", "topic": "type: educational — imagina poder viajar a ver a tu familia", "pillar": "emotional"},
        {"key": "wa_social_proof", "topic": "type: news — miles de personas ya se están preparando", "pillar": "social_proof"},
    ],
    "fbpost": [
        {"key": "fb_myth_job", "topic": "Desmintiendo el mito del contrato de trabajo", "pillar": "educational"},
        {"key": "fb_docs_guide", "topic": "Guía: qué documentos necesitas para la regularización", "pillar": "educational"},
        {"key": "fb_vulnerability", "topic": "La cláusula de vulnerabilidad explicada para todos", "pillar": "educational"},
        {"key": "fb_empadronamiento", "topic": "Cómo conseguir tu empadronamiento paso a paso", "pillar": "educational"},
        {"key": "fb_antecedentes", "topic": "Certificado de antecedentes: guía completa", "pillar": "educational"},
        {"key": "fb_cost_truth", "topic": "La verdad sobre los costes de regularización", "pillar": "educational"},
        {"key": "fb_scams_warning", "topic": "Cuidado con las estafas de regularización", "pillar": "educational"},
        {"key": "fb_faq_children", "topic": "Pregunta frecuente: ¿mis hijos se regularizan también?", "pillar": "educational"},
        {"key": "fb_faq_years", "topic": "¿Cuántos años necesitas llevar en España?", "pillar": "educational"},
        {"key": "fb_digital_2026", "topic": "En 2026 todo es digital: lo que necesitas saber", "pillar": "educational"},
        {"key": "fb_2005_vs_2026", "topic": "Lo que aprendimos de la regularización de 2005", "pillar": "educational"},
        {"key": "fb_rights", "topic": "Tus derechos como inmigrante durante el trámite", "pillar": "educational"},
        {"key": "fb_timeline", "topic": "Calendario de la regularización: fechas clave", "pillar": "news"},
        {"key": "fb_urgency", "topic": "Por qué prepararte ahora y no esperar al BOE", "pillar": "news"},
        {"key": "fb_hope", "topic": "Un mensaje de esperanza para quien tiene miedo", "pillar": "emotional"},
        {"key": "fb_family", "topic": "Regularización y familia: lo que significa tener papeles", "pillar": "emotional"},
        {"key": "fb_fear_normal", "topic": "Es normal tener miedo. Así te ayudamos.", "pillar": "emotional"},
        {"key": "fb_social_thousands", "topic": "Miles de personas ya se preparan: únete", "pillar": "social_proof"},
        {"key": "fb_referral", "topic": "Ayuda a tu comunidad: programa de referidos", "pillar": "social_proof"},
        {"key": "fb_behind_team", "topic": "Conoce al equipo de abogados de Pombo & Horowitz", "pillar": "behind_scenes"},
    ],
    "caption": [
        {"key": "cap_myth_job", "topic": "for instagram — mito del contrato de trabajo", "pillar": "educational"},
        {"key": "cap_vulnerability", "topic": "for instagram — cláusula de vulnerabilidad", "pillar": "educational"},
        {"key": "cap_docs_ready", "topic": "for instagram — prepara tus documentos", "pillar": "educational"},
        {"key": "cap_cost", "topic": "for facebook — precio real de regularizarse", "pillar": "educational"},
        {"key": "cap_digital", "topic": "for instagram — todo es digital en 2026", "pillar": "educational"},
        {"key": "cap_scams", "topic": "for facebook — cómo detectar estafas", "pillar": "educational"},
        {"key": "cap_first_steps", "topic": "for instagram — 3 pasos para empezar hoy", "pillar": "educational"},
        {"key": "cap_faq_children", "topic": "for facebook — ¿mis hijos se regularizan?", "pillar": "educational"},
        {"key": "cap_faq_years", "topic": "for instagram — años necesarios en España", "pillar": "educational"},
        {"key": "cap_2005_lesson", "topic": "for facebook — lecciones de 2005", "pillar": "educational"},
        {"key": "cap_hope", "topic": "for instagram — imagina tu vida con papeles", "pillar": "emotional"},
        {"key": "cap_fear", "topic": "for instagram — sabemos que tienes miedo", "pillar": "emotional"},
        {"key": "cap_family", "topic": "for facebook — volver a ver a tu familia", "pillar": "emotional"},
        {"key": "cap_dignity", "topic": "for instagram — vivir con dignidad", "pillar": "emotional"},
        {"key": "cap_timeline", "topic": "for facebook — fechas clave de la regularización", "pillar": "news"},
        {"key": "cap_deadline", "topic": "for instagram — la cuenta atrás ha empezado", "pillar": "news"},
        {"key": "cap_boe_update", "topic": "for facebook — novedades sobre el BOE", "pillar": "news"},
        {"key": "cap_social_proof", "topic": "for instagram — miles ya se preparan", "pillar": "social_proof"},
        {"key": "cap_referral", "topic": "for facebook — programa de referidos", "pillar": "social_proof"},
        {"key": "cap_behind_ai", "topic": "for instagram — nuestra IA de validación", "pillar": "behind_scenes"},
    ],
    "story": [
        {"key": "st_poll_myth", "topic": "type: poll — ¿verdad o mito? sobre la regularización", "pillar": "educational"},
        {"key": "st_poll_ready", "topic": "type: poll — ¿ya tienes tu empadronamiento?", "pillar": "educational"},
        {"key": "st_poll_docs", "topic": "type: poll — ¿qué documento te falta?", "pillar": "educational"},
        {"key": "st_quiz_cost", "topic": "type: quiz — ¿cuánto cuesta regularizarse?", "pillar": "educational"},
        {"key": "st_quiz_req", "topic": "type: quiz — ¿conoces los requisitos?", "pillar": "educational"},
        {"key": "st_quiz_2005", "topic": "type: quiz — ¿qué sabes de la regularización de 2005?", "pillar": "educational"},
        {"key": "st_tip_docs", "topic": "type: tip — consejo rápido sobre documentos", "pillar": "educational"},
        {"key": "st_tip_scams", "topic": "type: tip — cómo detectar una estafa", "pillar": "educational"},
        {"key": "st_tip_empad", "topic": "type: tip — consejo sobre empadronamiento", "pillar": "educational"},
        {"key": "st_question_fear", "topic": "type: question — ¿cuál es tu mayor miedo?", "pillar": "emotional"},
        {"key": "st_question_dream", "topic": "type: question — ¿qué harías primero con papeles?", "pillar": "emotional"},
        {"key": "st_question_family", "topic": "type: question — ¿a quién verías primero?", "pillar": "emotional"},
        {"key": "st_countdown_boe", "topic": "type: countdown — cuenta atrás para el BOE", "pillar": "news"},
        {"key": "st_countdown_deadline", "topic": "type: countdown — días hasta la fecha límite", "pillar": "news"},
        {"key": "st_tip_referral", "topic": "type: tip — invita a un amigo y ahorra", "pillar": "social_proof"},
        {"key": "st_poll_ai", "topic": "type: poll — ¿usarías IA para revisar tus documentos?", "pillar": "behind_scenes"},
    ],
    "blog": [
        {"key": "blog_vulnerability", "topic": "Cláusula de vulnerabilidad: qué es y por qué es importante", "pillar": "educational"},
        {"key": "blog_docs_complete", "topic": "Guía completa de documentos para la regularización 2026", "pillar": "educational"},
        {"key": "blog_empadronamiento", "topic": "Cómo conseguir tu empadronamiento paso a paso", "pillar": "educational"},
        {"key": "blog_antecedentes", "topic": "Certificado de antecedentes penales: guía completa", "pillar": "educational"},
        {"key": "blog_myths_5", "topic": "5 mitos peligrosos sobre la regularización 2026", "pillar": "educational"},
        {"key": "blog_2005_vs_2026", "topic": "Regularización 2005 vs 2026: todas las diferencias", "pillar": "educational"},
        {"key": "blog_cost_guide", "topic": "Cuánto cuesta regularizarse en España en 2026", "pillar": "educational"},
        {"key": "blog_scams", "topic": "Cómo detectar y evitar estafas de regularización", "pillar": "educational"},
        {"key": "blog_faq", "topic": "Las 10 preguntas más frecuentes sobre la regularización", "pillar": "educational"},
        {"key": "blog_digital", "topic": "Regularización digital: cómo funciona el trámite online", "pillar": "educational"},
        {"key": "blog_children", "topic": "Regularización y menores: qué pasa con tus hijos", "pillar": "educational"},
        {"key": "blog_work_permit", "topic": "Del permiso de trabajo a la vida laboral: todo lo que cambia", "pillar": "educational"},
        {"key": "blog_rights", "topic": "Tus derechos como inmigrante durante el proceso", "pillar": "educational"},
        {"key": "blog_first_steps", "topic": "Los primeros pasos para preparar tu regularización", "pillar": "educational"},
        {"key": "blog_timeline", "topic": "Calendario de la regularización 2026: todas las fechas", "pillar": "news"},
        {"key": "blog_boe_explained", "topic": "Qué es el BOE y por qué importa para tu regularización", "pillar": "news"},
        {"key": "blog_hope", "topic": "Un futuro con papeles: historias de esperanza", "pillar": "emotional"},
        {"key": "blog_family", "topic": "Regularización y familia: reunificación familiar explicada", "pillar": "emotional"},
        {"key": "blog_2005_stories", "topic": "Historias de la regularización de 2005: lecciones para hoy", "pillar": "social_proof"},
        {"key": "blog_ai_validation", "topic": "Cómo la inteligencia artificial valida tus documentos", "pillar": "behind_scenes"},
    ],
}

# Track recently used topics per content type (max 10, prevents repeats)
RECENT_TOPICS: dict[str, deque] = {
    ctype: deque(maxlen=10) for ctype in TOPIC_POOL
}

# Pillar distribution for /weekly (40% edu, 25% emotional, 20% news, 10% proof, 5% behind)
WEEKLY_PILLAR_WEIGHTS = {
    "educational": 0.40,
    "emotional": 0.25,
    "news": 0.20,
    "social_proof": 0.10,
    "behind_scenes": 0.05,
}


def pick_topic(content_type: str) -> str:
    """Pick a single non-recent topic from the pool for this content type."""
    pool = TOPIC_POOL.get(content_type, [])
    if not pool:
        return ""

    recent = RECENT_TOPICS.get(content_type, deque(maxlen=10))
    available = [t for t in pool if t["key"] not in recent]
    if not available:
        recent.clear()
        available = pool

    chosen = random.choice(available)
    recent.append(chosen["key"])
    return chosen["topic"]


def pick_topics_batch(content_type: str, count: int) -> list[str]:
    """Pick multiple unique non-recent topics from the pool."""
    pool = TOPIC_POOL.get(content_type, [])
    if not pool:
        return [""] * count

    recent = RECENT_TOPICS.get(content_type, deque(maxlen=10))
    available = [t for t in pool if t["key"] not in recent]
    if len(available) < count:
        recent.clear()
        available = list(pool)

    selected = random.sample(available, min(count, len(available)))
    topics = []
    for t in selected:
        topics.append(t["topic"])
        recent.append(t["key"])

    while len(topics) < count:
        topics.append("")
    return topics


def pick_topics_weekly(content_type: str, count: int) -> list[str]:
    """Pick topics for /weekly with pillar distribution."""
    pool = TOPIC_POOL.get(content_type, [])
    if not pool:
        return [""] * count

    recent = RECENT_TOPICS.get(content_type, deque(maxlen=10))
    recent.clear()  # Reset for weekly to maximize variety

    # Calculate how many from each pillar
    pillar_counts = {}
    assigned = 0
    pillars = list(WEEKLY_PILLAR_WEIGHTS.items())
    for pillar, weight in pillars:
        n = round(count * weight)
        pillar_counts[pillar] = n
        assigned += n
    # Distribute rounding remainder to educational
    if assigned < count:
        pillar_counts["educational"] += count - assigned
    elif assigned > count:
        pillar_counts["educational"] -= assigned - count

    topics = []
    for pillar, n in pillar_counts.items():
        if n <= 0:
            continue
        pillar_pool = [t for t in pool if t["pillar"] == pillar]
        if not pillar_pool:
            pillar_pool = pool
        chosen = random.sample(pillar_pool, min(n, len(pillar_pool)))
        for t in chosen:
            topics.append(t["topic"])
            recent.append(t["key"])
        # Fill shortfall from any pillar
        while len(topics) < sum(
            v for k, v in pillar_counts.items() if list(pillar_counts.keys()).index(k) <= list(pillar_counts.keys()).index(pillar)
        ):
            fallback = [t for t in pool if t["key"] not in recent]
            if not fallback:
                break
            extra = random.choice(fallback)
            topics.append(extra["topic"])
            recent.append(extra["key"])

    random.shuffle(topics)
    while len(topics) < count:
        topics.append("")
    return topics[:count]


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
            "Write a TikTok script for 15-60 seconds.\n\n"
            "After the main JSON fields, also include a field called 'invideo_prompt' — "
            "this is a ready-to-paste prompt for InVideo AI's Script-to-Video tool. The prompt must:\n"
            "- Start with 'Create a [duration]-second vertical TikTok video in Spanish'\n"
            "- Include the full script as the voiceover text\n"
            "- Specify 'warm Latin American Spanish female voice'\n"
            "- Describe the text overlays with colors (red for myths/problems, green for solutions/reality)\n"
            "- Describe the visual style: 'professional stock footage of Spanish streets, documents on desks, "
            "government buildings, people looking hopeful, immigrant communities'\n"
            "- Request 'word-by-word animated captions in bold white with black outline'\n"
            "- Request 'subtle dramatic background music, low volume'\n"
            "- End with 'Format: 9:16 vertical for TikTok. Style: professional, warm, trustworthy.'\n"
            "The invideo_prompt should be a single string ready to paste directly into InVideo AI "
            "with zero editing needed.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"format": "face-to-camera|green-screen|pov|story-time|myth-vs-reality|quick-tips", '
            '"duration_seconds": number, '
            '"hook": "string (first 2 seconds — must grab attention)", '
            '"script": "string (full spoken text)", '
            '"text_overlays": ["string", "string", "string"], '
            '"hashtags": "string", '
            '"production_tip": "string", '
            '"invideo_prompt": "string (full ready-to-paste InVideo AI prompt)"}'
        ),
        "carousel": (
            "\nCONTENT TYPE: INSTAGRAM CAROUSEL\n"
            "Write Instagram carousel content with 6-8 slides.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"topic": "string", '
            '"slides": [{"slide_number": 1, "headline": "string", "body": "string"}], '
            '"caption": "string (Instagram caption with line breaks)", '
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
            "Write an Instagram Story concept.\n\n"
            "IMPORTANT: Return ONLY valid JSON with this exact structure:\n"
            '{"type": "poll|question|countdown|quiz|tip", '
            '"main_text": "string", '
            '"sticker_suggestion": "string", '
            '"background_suggestion": "string"}'
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
# NEWS FETCHING
# ==============================================================================


async def fetch_news() -> list:
    """Fetch latest regularización news from Google News RSS."""
    queries = [
        "regularización+extraordinaria+España+2026",
        "regularización+masiva+inmigrantes+España",
        "papeles+España+2026",
    ]
    articles = []

    for q in queries:
        url = f"https://news.google.com/rss/search?q={q}&hl=es&gl=ES&ceid=ES:es"
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries[:3]:
                source_title = "Desconocido"
                if hasattr(entry, "source") and hasattr(entry.source, "title"):
                    source_title = entry.source.title

                articles.append(
                    {
                        "title": entry.title,
                        "link": entry.link,
                        "source": source_title,
                        "published": getattr(entry, "published", ""),
                    }
                )
        except Exception as e:
            logger.error(f"News fetch error for query '{q}': {e}")

    # Deduplicate by title similarity
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    return unique[:10]


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
            f"\n\n🎬 *INVIDEO PROMPT (paste into invideo.io):*\n"
            f"───────────────────\n"
            f"{escape_md(invideo)}\n"
            f"───────────────────"
        )

    return (
        f"🎬 *TIKTOK SCRIPT*\n\n"
        f"*Format:* {escape_md(data.get('format', 'face-to-camera'))}\n"
        f"*Duration:* ~{data.get('duration_seconds', 30)}s\n\n"
        f"🎯 *HOOK (first 2 sec):*\n\"{escape_md(data.get('hook', ''))}\"\n\n"
        f"📝 *SCRIPT:*\n\"{escape_md(data.get('script', ''))}\"\n\n"
        f"📱 *TEXT OVERLAYS:*\n{overlays_text}\n\n"
        f"#️⃣ {escape_md(data.get('hashtags', ''))}\n\n"
        f"💡 *TIP:* {escape_md(data.get('production_tip', ''))}"
        f"{invideo_section}"
    )


def format_carousel_for_telegram(data: dict) -> str:
    """Format Instagram carousel for Telegram."""
    if data.get("_parse_error"):
        return f"⚠️ *Couldn't parse — raw output below:*\n\n{data['_raw'][:3500]}"

    slides = data.get("slides", [])
    slides_text = ""
    for s in slides:
        slides_text += (
            f"\n*Slide {s.get('slide_number', '?')}:*\n"
            f"  📌 {escape_md(s.get('headline', ''))}\n"
            f"  {escape_md(s.get('body', ''))}\n"
        )

    return (
        f"📸 *INSTAGRAM CAROUSEL*\n\n"
        f"*Topic:* {escape_md(data.get('topic', ''))}\n"
        f"{slides_text}\n"
        f"✏️ *CAPTION:*\n{escape_md(data.get('caption', ''))}\n\n"
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

    return (
        f"📖 *INSTAGRAM STORY*\n\n"
        f"*Type:* {escape_md(data.get('type', 'tip'))}\n\n"
        f"📝 *Text:*\n{escape_md(data.get('main_text', ''))}\n\n"
        f"🎨 *Sticker:* {escape_md(data.get('sticker_suggestion', ''))}\n"
        f"🖼 *Background:* {escape_md(data.get('background_suggestion', ''))}"
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
        "  /blog \\[topic\\] — SEO blog article\n"
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
        "  /topics — 10 topic suggestions\n"
        "  /stats — Generation statistics\n"
        "  /phase \\[phase\\] — Set campaign phase\n"
        "  /help — This message"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


@team_only
async def cmd_blog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /blog [topic] command."""
    topic = " ".join(context.args) if context.args else ""

    if not topic:
        # Suggest 3 topics via Claude
        wait_msg = await update.message.reply_text("⏳ Generating topic suggestions...")
        try:
            data = await generate_content("topics", phase=get_current_phase())
            topics_list = data.get("topics", [])[:3]

            if not topics_list:
                await wait_msg.edit_text("❌ Could not generate topics. Try /blog <topic> instead.")
                return

            buttons = []
            for t in topics_list:
                title = t.get("title", "Topic")[:60]
                buttons.append(
                    [InlineKeyboardButton(title, callback_data=f"blog_{title[:40]}")]
                )
            markup = InlineKeyboardMarkup(buttons)
            await wait_msg.edit_text(
                "📝 *Choose a blog topic:*",
                reply_markup=markup,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await wait_msg.edit_text(f"❌ Error: {e}")
        return

    wait_msg = await update.message.reply_text("⏳ Generating blog article...")
    try:
        data = await generate_content("blog", topic)
        formatted = format_blog_for_telegram(data)

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

        # If article is too long, send as file
        html_content = data.get("html_content", "")
        if len(formatted) > TG_MAX_LEN:
            # Send metadata + buttons as message
            meta_msg = (
                f"📝 *BLOG ARTICLE READY*\n\n"
                f"*Title:* {escape_md(data.get('title', ''))}\n"
                f"*Meta:* {escape_md(data.get('meta_description', ''))}\n"
                f"*Words:* {data.get('word_count', '?')}\n\n"
                f"Full article sent as file below."
            )
            await send_long_message(
                update, meta_msg, context, reply_markup=markup
            )
            await send_as_file(
                update.effective_chat.id,
                html_content,
                f"{data.get('slug', 'article')}.html",
                "Blog article HTML",
                context,
            )
        else:
            await send_long_message(
                update, formatted, context, reply_markup=markup
            )

    except Exception as e:
        await wait_msg.edit_text(f"❌ Error generating blog: {e}")


@team_only
async def cmd_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tiktok [topic] command."""
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        topic = pick_topic("tiktok")
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
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        topic = pick_topic("carousel")
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

    topic = " ".join(topic_parts)
    if platform:
        topic = f"for {platform}. {topic}" if topic else f"for {platform}"
    if not topic:
        topic = pick_topic("caption")

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
    topic = ""
    if msg_type in valid_types:
        topic = f"type: {msg_type}"
    elif msg_type:
        topic = msg_type
    if not topic:
        topic = pick_topic("whatsapp")

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
    topic = " ".join(context.args) if context.args else ""
    if not topic:
        topic = pick_topic("fbpost")
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
    topic = ""
    if story_type in valid_types:
        topic = f"type: {story_type}"
    elif story_type:
        topic = story_type
    if not topic:
        topic = pick_topic("story")

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
    topics = pick_topics_batch("tiktok", 5)
    await _batch_generate(update, context, "tiktok", 5, topics)


@team_only
async def cmd_carousel3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /carousel3 — generate 3 carousel sets."""
    topics = pick_topics_batch("carousel", 3)
    await _batch_generate(update, context, "carousel", 3, topics)


@team_only
async def cmd_captions10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /captions10 — generate 10 captions."""
    topics = pick_topics_batch("caption", 10)
    await _batch_generate(update, context, "caption", 10, topics)


@team_only
async def cmd_whatsapp5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /whatsapp5 — generate 5 WhatsApp messages."""
    topics = pick_topics_batch("whatsapp", 5)
    await _batch_generate(update, context, "whatsapp", 5, topics)


@team_only
async def cmd_fbpost5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /fbpost5 — generate 5 Facebook posts."""
    topics = pick_topics_batch("fbpost", 5)
    await _batch_generate(update, context, "fbpost", 5, topics)


@team_only
async def cmd_stories7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stories7 — generate 7 Story concepts."""
    topics = pick_topics_batch("story", 7)
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
    count = await _batch_generate(update, context, "tiktok", 7, pick_topics_weekly("tiktok", 7))
    total += count

    # 5 Carousel sets (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 2/7: Carousels*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "carousel", 5, pick_topics_weekly("carousel", 5))
    total += count

    # 14 Stories (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 3/7: Stories*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "story", 14, pick_topics_weekly("story", 14))
    total += count

    # 3 WhatsApp messages (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 4/7: WhatsApp*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "whatsapp", 3, pick_topics_weekly("whatsapp", 3))
    total += count

    # 5 Facebook posts (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 5/7: Facebook posts*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "fbpost", 5, pick_topics_weekly("fbpost", 5))
    total += count

    # 2 Blog articles (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 6/7: Blog articles*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "blog", 2, pick_topics_weekly("blog", 2))
    total += count

    # 10 Captions (pillar-distributed)
    await context.bot.send_message(chat_id=chat_id, text="📦 *Phase 7/7: Captions*", parse_mode=ParseMode.MARKDOWN)
    count = await _batch_generate(update, context, "caption", 10, pick_topics_weekly("caption", 10))
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
    """Handle /news — fetch and analyze regularización news."""
    wait_msg = await update.message.reply_text("⏳ Fetching latest news...")

    try:
        articles = await fetch_news()

        if not articles:
            await wait_msg.edit_text("No recent news found. Try again later.")
            return

        # Format news list
        news_text = "📰 *LATEST REGULARIZACIÓN NEWS*\n\n"
        for i, a in enumerate(articles, 1):
            news_text += (
                f"*{i}.* {escape_md(a['title'])}\n"
                f"   Source: {escape_md(a['source'])} | {escape_md(a.get('published', ''))}\n\n"
            )

        await wait_msg.delete()
        await send_long_message(update, news_text, context)

        # Ask Claude to analyze for content ideas
        news_summary = "\n".join(
            f"- {a['title']} ({a['source']})" for a in articles
        )
        analysis_msg = await update.message.reply_text(
            "⏳ Analyzing for content ideas..."
        )

        try:
            data = await generate_content(
                "news_analysis",
                topic=f"Analyze these recent news articles:\n{news_summary}",
            )

            analysis_items = data.get("analysis", [])
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

        except Exception as e:
            await analysis_msg.edit_text(f"⚠️ Could not analyze news: {e}")

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

    # Weekly confirm/cancel
    if data == "weekly_confirm":
        await query.edit_message_text("🚀 Starting weekly generation...")
        await _run_weekly(update, context)
        return
    elif data == "weekly_cancel":
        await query.edit_message_text("Cancelled.")
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
                # Update the message to show success
                original_text = query.message.text or ""
                new_text = original_text + f"\n\n✅ Published to {site_name}!"
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
    app.add_handler(CommandHandler("topics", cmd_topics))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("phase", cmd_phase))

    # Callback handlers (publish buttons, weekly confirm, blog topic selection)
    app.add_handler(CallbackQueryHandler(handle_publish_callback))

    # Catch-all for non-team members
    app.add_handler(MessageHandler(filters.ALL, handle_unauthorized))

    logger.info("Content Bot v3.0 starting")
    logger.info(f"Team IDs: {TEAM_CHAT_IDS}")
    logger.info(f"Phase: {get_current_phase()}")
    app.run_polling()


if __name__ == "__main__":
    main()
