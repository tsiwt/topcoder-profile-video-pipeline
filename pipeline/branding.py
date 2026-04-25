"""
Topcoder branding overlays:
  - Animated lower-third with handle + rating color
  - Track icons
  - Intro / outro clips
All rendering done with Pillow — NO ImageMagick dependency.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip
from config import TC_COLORS, TRACK_LABELS, ASSETS_DIR


def _get_font(size=36, bold=False):
    """Get a reliable font path."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def create_lower_third(handle, rating_color_hex, tracks, video_size, duration):
    """
    Render a Topcoder-style lower-third bar overlay.
    Appears after 0.5s, stays until end - 0.5s.
    """
    w, h = video_size
    bar_h = 80
    bar_w = min(500, w - 40)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x0 = 30
    y0 = h - bar_h - 40
    draw.rounded_rectangle(
        [x0, y0, x0 + bar_w, y0 + bar_h],
        radius=12,
        fill=(26, 26, 46, 200),
    )

    rc = _hex_to_rgb(rating_color_hex)
    draw.rectangle([x0, y0, x0 + 6, y0 + bar_h], fill=rc + (255,))

    font_handle = _get_font(32, bold=True)
    draw.text((x0 + 22, y0 + 8), handle, fill=(255, 255, 255, 255),
              font=font_handle)

    track_text = " · ".join([TRACK_LABELS.get(t, t) for t in tracks[:2]])
    font_track = _get_font(18)
    draw.text((x0 + 22, y0 + 48), track_text, fill=rc + (255,),
              font=font_track)

    draw.ellipse([x0 + bar_w - 36, y0 + 28, x0 + bar_w - 12, y0 + 52],
                 fill=rc + (255,))

    arr = np.array(img)
    clip = (ImageClip(arr, transparent=True)
            .set_start(0.5)
            .set_duration(max(0.5, duration - 1.0))
            .crossfadein(0.3))
    return clip


def create_track_icon_overlay(tracks, video_size, duration):
    """Render small track icon badges in the top-right corner."""
    w, h = video_size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    icons_map = {
        "development":  "{ }",
        "design":       "D",
        "data_science": "DS",
        "qa":           "QA",
        "competitive":  "CP",
    }

    font = _get_font(20, bold=True)
    x = w - 60
    y = 20
    for t in tracks[:3]:
        label = icons_map.get(t, "?")
        draw.rounded_rectangle([x - 10, y, x + 46, y + 36], radius=8,
                               fill=(26, 26, 46, 180))
        draw.text((x, y + 4), label, fill=(255, 255, 255, 255), font=font)
        y += 44

    arr = np.array(img)
    return (ImageClip(arr, transparent=True)
            .set_start(0.5)
            .set_duration(max(0.5, duration - 1.0))
            .crossfadein(0.3))


def create_intro_clip(handle, rating_color_hex, video_size, dur=2.0):
    """A Topcoder-branded intro card (2 seconds)."""
    w, h = video_size
    rc = _hex_to_rgb(rating_color_hex)

    img = Image.new("RGB", (w, h), _hex_to_rgb(TC_COLORS["dark"]))
    draw = ImageDraw.Draw(img)

    font_big = _get_font(64, bold=True)
    font_sub = _get_font(28)

    tc_text = "TOPCODER"
    try:
        bbox = draw.textbbox((0, 0), tc_text, font=font_big)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = 400
    draw.text(((w - tw) // 2, h // 2 - 70), tc_text,
              fill=_hex_to_rgb(TC_COLORS["primary"]), font=font_big)

    handle_text = f"★  {handle}  ★"
    try:
        bbox2 = draw.textbbox((0, 0), handle_text, font=font_sub)
        tw2 = bbox2[2] - bbox2[0]
    except Exception:
        tw2 = 200
    draw.text(((w - tw2) // 2, h // 2 + 20), handle_text,
              fill=rc, font=font_sub)

    draw.rectangle([w // 2 - 140, h // 2 + 60, w // 2 + 140, h // 2 + 64],
                   fill=rc)

    arr = np.array(img)
    return ImageClip(arr).set_duration(dur).crossfadeout(0.4)


def create_outro_clip(video_size, dur=2.0):
    """Outro card with CTA."""
    w, h = video_size
    img = Image.new("RGB", (w, h), _hex_to_rgb(TC_COLORS["dark"]))
    draw = ImageDraw.Draw(img)

    font_big = _get_font(48, bold=True)
    font_sm = _get_font(22)

    tc_text = "topcoder.com"
    try:
        bbox = draw.textbbox((0, 0), tc_text, font=font_big)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = 360
    draw.text(((w - tw) // 2, h // 2 - 50), tc_text,
              fill=_hex_to_rgb(TC_COLORS["primary"]), font=font_big)

    cta = "Join the world's premier digital talent network"
    try:
        bbox2 = draw.textbbox((0, 0), cta, font=font_sm)
        tw2 = bbox2[2] - bbox2[0]
    except Exception:
        tw2 = 400
    draw.text(((w - tw2) // 2, h // 2 + 20), cta,
              fill=(180, 180, 190), font=font_sm)

    arr = np.array(img)
    return ImageClip(arr).set_duration(dur).crossfadein(0.4)
