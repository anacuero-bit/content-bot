#!/usr/bin/env python3
"""
carousel_renderer.py — Branded slide renderer for tuspapeles2026 carousels.

Renders carousel JSON data into:
  - Individual 1080x1350 PNG slide images
  - MP4 video (4 sec/slide, 30fps)
  - PDF document with all slides
"""

import io
import os
import math
import shutil
import subprocess
import tempfile
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# ── Brand colours ──
DEEP_BLUE = (27, 58, 92)
GOLD = (212, 168, 67)
WHITE = (255, 255, 255)
LIGHT_BG = (240, 244, 250)
MID_BLUE = (45, 80, 120)
GREEN = (45, 139, 78)
SOFT_GRAY = (180, 190, 205)
DARK_GRAY = (80, 90, 100)
PROGRESS_GRAY = (100, 110, 130)

# ── Dimensions ──
W, H = 1080, 1350
FOOTER_H = 80
PILL_RADIUS = 20

# ── Font paths (Ubuntu/Debian with fonts-dejavu-core) ──
_FONT_BOLD = None
_FONT_REGULAR = None

FONT_SEARCH_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def _find_font(bold: bool = False) -> str:
    """Find a DejaVu Sans font file on the system."""
    target = "Bold" if bold else "Sans.ttf"
    for p in FONT_SEARCH_PATHS:
        if os.path.exists(p) and target.split(".")[0] in p:
            return p
    # Fallback: return first existing
    for p in FONT_SEARCH_PATHS:
        if os.path.exists(p):
            return p
    return ""


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load a font at the given size."""
    global _FONT_BOLD, _FONT_REGULAR
    if bold:
        if _FONT_BOLD is None:
            _FONT_BOLD = _find_font(bold=True)
        path = _FONT_BOLD
    else:
        if _FONT_REGULAR is None:
            _FONT_REGULAR = _find_font(bold=False)
        path = _FONT_REGULAR
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _strip_emoji(text: str) -> str:
    """Remove emoji/non-BMP characters that DejaVu can't render."""
    return "".join(c for c in text if ord(c) < 0x10000 and ord(c) not in range(0x2600, 0x27C0) and ord(c) not in range(0xFE00, 0xFE0F + 1) and ord(c) not in range(0x1F000, 0x1FFFF + 1))


def _load_logo(path: str, remove_black_bg: bool = True) -> Optional[Image.Image]:
    """Load a logo PNG, optionally removing black background."""
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path).convert("RGBA")
        if remove_black_bg:
            pixels = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b, a = pixels[x, y]
                    brightness = (r + g + b) / 3
                    if brightness < 60:
                        pixels[x, y] = (r, g, b, 0)
        return img
    except Exception:
        return None


def _draw_rounded_rect(draw: ImageDraw.Draw, xy, fill, radius=20):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _draw_pill(draw: ImageDraw.Draw, xy, fill, radius=None):
    """Draw a pill (fully rounded rectangle)."""
    x0, y0, x1, y1 = xy
    h = y1 - y0
    r = radius if radius else h // 2
    draw.rounded_rectangle(xy, radius=r, fill=fill)


def _draw_logo_in_pill(img: Image.Image, logo: Optional[Image.Image], center_x: int, center_y: int,
                        max_logo_h: int = 28, pill_pad: int = 16):
    """Draw a logo inside a white pill container at the given center position."""
    if logo is None:
        return
    # Scale logo
    ratio = max_logo_h / logo.height
    lw = int(logo.width * ratio)
    lh = max_logo_h
    logo_resized = logo.resize((lw, lh), Image.LANCZOS)

    # Pill dimensions
    pw = lw + pill_pad * 2
    ph = lh + pill_pad
    px0 = center_x - pw // 2
    py0 = center_y - ph // 2

    draw = ImageDraw.Draw(img)
    _draw_pill(draw, (px0, py0, px0 + pw, py0 + ph), fill=WHITE, radius=ph // 2)
    # Paste logo centered in pill
    lx = px0 + (pw - lw) // 2
    ly = py0 + (ph - lh) // 2
    img.paste(logo_resized, (lx, ly), logo_resized)


def _draw_progress_dots(draw: ImageDraw.Draw, total: int, current: int, y: int):
    """Draw progress dots at the top of the slide."""
    dot_r = 6
    gap = 18
    total_w = total * (dot_r * 2) + (total - 1) * gap
    start_x = (W - total_w) // 2
    for i in range(total):
        cx = start_x + i * (dot_r * 2 + gap) + dot_r
        fill = GOLD if i == current else PROGRESS_GRAY
        draw.ellipse((cx - dot_r, y - dot_r, cx + dot_r, y + dot_r), fill=fill)


def _draw_footer(img: Image.Image, logo_wide: Optional[Image.Image]):
    """Draw the branded footer bar at the bottom of the slide."""
    draw = ImageDraw.Draw(img)
    fy = H - FOOTER_H
    # Deep blue bar
    draw.rectangle((0, fy, W, H), fill=DEEP_BLUE)
    # Gold accent line
    draw.rectangle((0, fy, W, fy + 3), fill=GOLD)
    # Logo pill
    _draw_logo_in_pill(img, logo_wide, W // 2 - 100, fy + FOOTER_H // 2, max_logo_h=22, pill_pad=10)
    # URL text
    font_sm = _get_font(20, bold=False)
    draw.text((W // 2 + 20, fy + FOOTER_H // 2 - 10), "tuspapeles2026.es", fill=GOLD, font=font_sm)


def _draw_icon(draw: ImageDraw.Draw, icon_type: str, cx: int, cy: int, size: int = 40):
    """Draw a simple geometric icon (no emoji needed)."""
    s = size
    hs = s // 2
    icons = {
        "calendar": lambda: [
            draw.rectangle((cx - hs, cy - hs, cx + hs, cy + hs), outline=GOLD, width=3),
            draw.rectangle((cx - hs, cy - hs, cx + hs, cy - hs + s // 3), fill=GOLD),
            draw.line((cx - hs // 2, cy - hs - 6, cx - hs // 2, cy - hs + 4), fill=GOLD, width=3),
            draw.line((cx + hs // 2, cy - hs - 6, cx + hs // 2, cy - hs + 4), fill=GOLD, width=3),
        ],
        "rocket": lambda: [
            draw.polygon([(cx, cy - hs), (cx + hs // 2, cy + hs), (cx - hs // 2, cy + hs)], fill=GOLD),
            draw.rectangle((cx - hs // 3, cy + hs, cx + hs // 3, cy + hs + s // 4), fill=GOLD),
        ],
        "clock": lambda: [
            draw.ellipse((cx - hs, cy - hs, cx + hs, cy + hs), outline=GOLD, width=3),
            draw.line((cx, cy, cx, cy - hs + 8), fill=GOLD, width=3),
            draw.line((cx, cy, cx + hs - 10, cy), fill=GOLD, width=3),
        ],
        "lock": lambda: [
            draw.rectangle((cx - hs + 5, cy, cx + hs - 5, cy + hs), fill=GOLD),
            draw.arc((cx - hs // 2, cy - hs, cx + hs // 2, cy + 4), 0, 360, fill=GOLD, width=3),
        ],
        "hourglass": lambda: [
            draw.polygon([(cx - hs, cy - hs), (cx + hs, cy - hs), (cx, cy)], fill=GOLD),
            draw.polygon([(cx - hs, cy + hs), (cx + hs, cy + hs), (cx, cy)], fill=GOLD),
        ],
        "checkmark": lambda: [
            draw.line((cx - hs, cy, cx - hs // 3, cy + hs // 2), fill=GOLD, width=4),
            draw.line((cx - hs // 3, cy + hs // 2, cx + hs, cy - hs // 2), fill=GOLD, width=4),
        ],
    }
    icon_keys = list(icons.keys())
    fn = icons.get(icon_type, icons[icon_keys[hash(icon_type) % len(icon_keys)]])
    fn()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        tw = bbox[2] - bbox[0]
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


# ── Slide Renderers ──

def _render_cover(slide_data: dict, topic: str, total_slides: int,
                  logo_wide: Optional[Image.Image], logo_sq: Optional[Image.Image]) -> Image.Image:
    """Render the cover slide (slide 1)."""
    img = Image.new("RGB", (W, H), DEEP_BLUE)
    draw = ImageDraw.Draw(img)

    # Progress dots
    _draw_progress_dots(draw, total_slides, 0, 50)

    # Gold accent line
    draw.rectangle((W // 2 - 120, 80, W // 2 + 120, 83), fill=GOLD)

    # Wide logo in pill
    _draw_logo_in_pill(img, logo_wide, W // 2, 140, max_logo_h=40, pill_pad=20)

    # Title
    title = _strip_emoji(slide_data.get("title", slide_data.get("headline", topic)))
    font_title = _get_font(72, bold=True)
    title_lines = _wrap_text(title, font_title, W - 140)
    ty = 220
    for line in title_lines[:3]:
        bbox = font_title.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, ty), line, fill=GOLD, font=font_title)
        ty += 85

    # Subtitle — topic
    font_sub = _get_font(40, bold=True)
    sub = _strip_emoji(topic)
    sub_lines = _wrap_text(sub, font_sub, W - 160)
    for line in sub_lines[:2]:
        bbox = font_sub.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, ty), line, fill=WHITE, font=font_sub)
        ty += 50

    # Gold divider
    ty += 20
    draw.rectangle((W // 2 - 80, ty, W // 2 + 80, ty + 3), fill=GOLD)
    ty += 30

    # Body text (bullets from the first slide)
    font_body = _get_font(28, bold=False)
    bullets = slide_data.get("bullets", [])
    if isinstance(bullets, list):
        for b in bullets[:4]:
            b_clean = _strip_emoji(b)
            b_lines = _wrap_text(b_clean, font_body, W - 200)
            for line in b_lines[:2]:
                bbox = font_body.getbbox(line)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) // 2, ty), line, fill=SOFT_GRAY, font=font_body)
                ty += 36
            ty += 8

    # "Desliza para ver..." card
    card_y = H - FOOTER_H - 130
    _draw_rounded_rect(draw, (W // 2 - 200, card_y, W // 2 + 200, card_y + 60), fill=MID_BLUE, radius=30)
    font_card = _get_font(26, bold=True)
    card_text = "Desliza para ver..."
    bbox = font_card.getbbox(card_text)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, card_y + 16), card_text, fill=WHITE, font=font_card)

    # Footer
    _draw_footer(img, logo_wide)

    return img


def _render_content_slide(slide_data: dict, slide_idx: int, total_slides: int,
                           logo_wide: Optional[Image.Image], logo_sq: Optional[Image.Image]) -> Image.Image:
    """Render a content slide (slides 2 through N-1)."""
    img = Image.new("RGB", (W, H), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    # Square logo watermark (faint, top-left)
    if logo_sq:
        wm = logo_sq.resize((60, 60), Image.LANCZOS)
        # Make it semi-transparent
        wm_faint = wm.copy()
        wm_faint.putalpha(40)
        img.paste(wm_faint, (30, 25), wm_faint)

    # Progress dots
    _draw_progress_dots(draw, total_slides, slide_idx, 50)

    # Blue top bar with gold underline
    draw.rectangle((0, 70, W, 120), fill=DEEP_BLUE)
    draw.rectangle((0, 120, W, 124), fill=GOLD)

    # Slide number label badge
    font_badge = _get_font(22, bold=True)
    badge_text = f"PASO {slide_idx + 1}"
    _draw_pill(draw, (60, 85, 200, 115), fill=MID_BLUE, radius=15)
    draw.text((80, 89), badge_text, fill=GOLD, font=font_badge)

    # Gold number circle
    cx_num = W - 80
    cy_num = 97
    draw.ellipse((cx_num - 22, cy_num - 22, cx_num + 22, cy_num + 22), fill=GOLD)
    font_num = _get_font(24, bold=True)
    num_text = str(slide_idx + 1)
    bbox = font_num.getbbox(num_text)
    nw = bbox[2] - bbox[0]
    draw.text((cx_num - nw // 2, cy_num - 14), num_text, fill=DEEP_BLUE, font=font_num)

    # Geometric icon
    icon_types = ["calendar", "rocket", "clock", "lock", "hourglass", "checkmark"]
    _draw_icon(draw, icon_types[slide_idx % len(icon_types)], W // 2, 190, size=50)

    # Title
    title = _strip_emoji(slide_data.get("title", slide_data.get("headline", "")))
    font_title = _get_font(42, bold=True)
    title_lines = _wrap_text(title, font_title, W - 140)
    ty = 240
    for line in title_lines[:3]:
        bbox = font_title.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, ty), line, fill=DEEP_BLUE, font=font_title)
        ty += 52

    # Gold divider
    ty += 10
    draw.rectangle((70, ty, W - 70, ty + 2), fill=GOLD)
    ty += 24

    # Bullet points
    font_bullet = _get_font(30, bold=False)
    bullets = slide_data.get("bullets", [])
    if isinstance(bullets, list):
        for b in bullets[:6]:
            b_clean = _strip_emoji(b)
            b_lines = _wrap_text(b_clean, font_bullet, W - 200)
            # Gold dot
            draw.ellipse((80, ty + 8, 92, ty + 20), fill=GOLD)
            for j, line in enumerate(b_lines[:3]):
                x = 110 if j == 0 else 110
                draw.text((x, ty), line, fill=DARK_GRAY, font=font_bullet)
                ty += 38
            ty += 10
    elif slide_data.get("body"):
        body = _strip_emoji(slide_data["body"])
        body_lines = _wrap_text(body, font_bullet, W - 160)
        for line in body_lines[:8]:
            draw.text((80, ty), line, fill=DARK_GRAY, font=font_bullet)
            ty += 38

    # Tip box at bottom (if present)
    tip = slide_data.get("tip_box", "")
    if tip:
        tip = _strip_emoji(tip)
        font_tip = _get_font(24, bold=False)
        font_tip_label = _get_font(20, bold=True)
        tip_lines = _wrap_text(tip, font_tip, W - 200)
        tip_h = max(80, 50 + len(tip_lines) * 30)
        tip_y = H - FOOTER_H - tip_h - 30
        _draw_rounded_rect(draw, (50, tip_y, W - 50, tip_y + tip_h), fill=DEEP_BLUE, radius=16)
        # Label badge
        _draw_pill(draw, (70, tip_y + 10, 170, tip_y + 36), fill=GOLD, radius=13)
        draw.text((82, tip_y + 12), "CONSEJO", fill=DEEP_BLUE, font=font_tip_label)
        # Tip text
        tip_ty = tip_y + 44
        for line in tip_lines[:3]:
            draw.text((80, tip_ty), line, fill=GOLD, font=font_tip)
            tip_ty += 30

    # Footer
    _draw_footer(img, logo_wide)

    return img


def _render_cta_slide(slide_data: dict, total_slides: int,
                       logo_wide: Optional[Image.Image], logo_sq: Optional[Image.Image]) -> Image.Image:
    """Render the CTA slide (last slide)."""
    img = Image.new("RGB", (W, H), DEEP_BLUE)
    draw = ImageDraw.Draw(img)

    # Square logo watermark
    if logo_sq:
        wm = logo_sq.resize((60, 60), Image.LANCZOS)
        wm_faint = wm.copy()
        wm_faint.putalpha(40)
        img.paste(wm_faint, (30, 25), wm_faint)

    # Progress dots
    _draw_progress_dots(draw, total_slides, total_slides - 1, 50)

    # Large green checkmark circle
    cx, cy = W // 2, 220
    r = 70
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GREEN)
    # Checkmark inside
    draw.line((cx - 30, cy, cx - 8, cy + 25), fill=WHITE, width=6)
    draw.line((cx - 8, cy + 25, cx + 35, cy - 25), fill=WHITE, width=6)

    # Title
    title = _strip_emoji(slide_data.get("title", slide_data.get("headline", "Empieza hoy")))
    font_title = _get_font(52, bold=True)
    title_lines = _wrap_text(title, font_title, W - 120)
    ty = 330
    for line in title_lines[:3]:
        bbox = font_title.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, ty), line, fill=WHITE, font=font_title)
        ty += 64

    # Gold divider
    ty += 10
    draw.rectangle((W // 2 - 60, ty, W // 2 + 60, ty + 3), fill=GOLD)
    ty += 30

    # Bullets
    font_body = _get_font(30, bold=False)
    bullets = slide_data.get("bullets", [])
    if isinstance(bullets, list):
        for b in bullets[:5]:
            b_clean = _strip_emoji(b)
            b_lines = _wrap_text(b_clean, font_body, W - 200)
            draw.ellipse((80, ty + 8, 92, ty + 20), fill=GOLD)
            for j, line in enumerate(b_lines[:2]):
                draw.text((110 if j == 0 else 110, ty), line, fill=SOFT_GRAY, font=font_body)
                ty += 38
            ty += 6
    elif slide_data.get("body"):
        body = _strip_emoji(slide_data["body"])
        for line in _wrap_text(body, font_body, W - 160)[:5]:
            draw.text((80, ty), line, fill=SOFT_GRAY, font=font_body)
            ty += 38

    # CTA button
    ty += 30
    btn_w, btn_h = 600, 70
    bx = (W - btn_w) // 2
    _draw_rounded_rect(draw, (bx, ty, bx + btn_w, ty + btn_h), fill=GOLD, radius=35)
    font_cta = _get_font(24, bold=True)
    cta_text = "VERIFICAR ELEGIBILIDAD GRATIS"
    bbox = font_cta.getbbox(cta_text)
    cta_tw = bbox[2] - bbox[0]
    draw.text(((W - cta_tw) // 2, ty + 20), cta_text, fill=DEEP_BLUE, font=font_cta)
    ty += btn_h + 16

    # "Link en bio"
    font_sm = _get_font(22, bold=False)
    link_text = "Link en bio"
    bbox = font_sm.getbbox(link_text)
    ltw = bbox[2] - bbox[0]
    draw.text(((W - ltw) // 2, ty), link_text, fill=SOFT_GRAY, font=font_sm)
    ty += 40

    # Credibility card
    cred_text = "Pombo, Horowitz y Espinosa  -  Abogados"
    card_w, card_h = 520, 50
    cx_card = (W - card_w) // 2
    _draw_rounded_rect(draw, (cx_card, ty, cx_card + card_w, ty + card_h), fill=MID_BLUE, radius=25)
    font_cred = _get_font(20, bold=False)
    bbox = font_cred.getbbox(cred_text)
    ctw = bbox[2] - bbox[0]
    draw.text(((W - ctw) // 2, ty + 13), cred_text, fill=SOFT_GRAY, font=font_cred)

    # Footer
    _draw_footer(img, logo_wide)

    return img


# ── Main Entry Point ──

def render_carousel(carousel_data: dict, logo_wide_path: str, logo_sq_path: str) -> tuple:
    """
    Render a carousel into slide PNGs, an MP4 video, and a PDF.

    Args:
        carousel_data: JSON from generate_content("carousel", topic).
            Keys: topic, slides [{slide_number, title, bullets, tip_box}], caption, hashtags
        logo_wide_path: Path to tp2026.png (wide logo)
        logo_sq_path: Path to tp26sqlogo.png (square logo)

    Returns:
        (slide_pngs, mp4_bytes, pdf_bytes)
        - slide_pngs: list of PNG bytes per slide
        - mp4_bytes: MP4 video bytes (4s/slide) or None if ffmpeg unavailable
        - pdf_bytes: PDF bytes with all slides
    """
    logo_wide = _load_logo(logo_wide_path)
    logo_sq = _load_logo(logo_sq_path)

    slides_data = carousel_data.get("slides", [])
    topic = carousel_data.get("topic", "Carousel")
    total = len(slides_data)
    if total == 0:
        raise ValueError("No slides in carousel data")

    # Render each slide
    rendered: list[Image.Image] = []
    for i, sd in enumerate(slides_data):
        if i == 0:
            rendered.append(_render_cover(sd, topic, total, logo_wide, logo_sq))
        elif i == total - 1 and total > 2:
            rendered.append(_render_cta_slide(sd, total, logo_wide, logo_sq))
        else:
            rendered.append(_render_content_slide(sd, i, total, logo_wide, logo_sq))

    # Convert to PNG bytes
    slide_pngs: list[bytes] = []
    for img in rendered:
        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        slide_pngs.append(buf.getvalue())

    # Generate PDF
    pdf_bytes = b""
    try:
        pdf_buf = io.BytesIO()
        rgb_slides = [img.convert("RGB") for img in rendered]
        rgb_slides[0].save(pdf_buf, "PDF", save_all=True, append_images=rgb_slides[1:])
        pdf_bytes = pdf_buf.getvalue()
    except Exception:
        pass

    # Generate MP4 via ffmpeg
    mp4_bytes = None
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                for i, img in enumerate(rendered):
                    img.save(os.path.join(tmpdir, f"slide_{i:02d}.png"))
                out_path = os.path.join(tmpdir, "output.mp4")
                cmd = [
                    ffmpeg_path, "-y",
                    "-framerate", "1/4",
                    "-i", os.path.join(tmpdir, "slide_%02d.png"),
                    "-vf", "scale=1080:1350,format=yuv420p",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "20",
                    "-r", "30",
                    "-movflags", "+faststart",
                    out_path,
                ]
                subprocess.run(cmd, capture_output=True, timeout=60, check=True)
                with open(out_path, "rb") as f:
                    mp4_bytes = f.read()
        except Exception:
            pass

    return slide_pngs, mp4_bytes, pdf_bytes
