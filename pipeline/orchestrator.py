"""
Main pipeline orchestrator – coordinates all processing stages.

v2: Pillow captions (no ImageMagick), removed face detection, ultrafast render
v3: Local faster-whisper for real captions
"""
import os, tempfile, shutil
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, ImageClip, ColorClip,
    concatenate_videoclips
)
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import ASSETS_DIR, TC_COLORS, RATING_COLORS
from pipeline.video_enhancer import enhance_frame
from pipeline.audio_processor import process_audio
from pipeline.captions import generate_captions
from pipeline.branding import (
    create_lower_third,
    create_intro_clip,
    create_outro_clip,
    create_track_icon_overlay,
)
from pipeline.music_mixer import mix_with_bgm


def _get_font(size=32, bold=False):
    """Get a reliable font."""
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


def _make_caption_clip(text, start, duration, video_w, video_h):
    """
    Render a single caption as a Pillow RGBA image -> MoviePy ImageClip.
    NO TextClip, NO ImageMagick required.
    """
    font = _get_font(30, bold=True)

    # Measure text with word wrap
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    max_width = video_w - 120
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        try:
            bbox = dummy_draw.textbbox((0, 0), test, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(test) * 16
        if tw > max_width and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    if not lines:
        return None

    line_height = 40
    padding = 16
    img_h = len(lines) * line_height + padding * 2 + 20
    img_w = video_w

    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Semi-transparent background bar
    draw.rounded_rectangle(
        [40, 0, img_w - 40, img_h],
        radius=8,
        fill=(0, 0, 0, 160),
    )

    # Draw text centered
    y = padding
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except Exception:
            tw = len(line) * 16
        x = (img_w - tw) // 2
        # Shadow
        draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 200), font=font)
        # White text
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
        y += line_height

    arr = np.array(img)

    clip = (ImageClip(arr, transparent=True)
            .set_position(("center", video_h - img_h - 50))
            .set_start(start)
            .set_duration(duration))
    return clip


def run_pipeline(
    video_path: str,
    metadata: dict,
    output_path: str,
    progress_callback=None,
):
    """Full pipeline: raw video -> polished branded output."""
    cb = progress_callback or (lambda p: None)
    tmp = tempfile.mkdtemp(prefix="tc_pipeline_")

    try:
        # -- Stage 1: Load source --
        cb(5)
        clip = VideoFileClip(video_path)
        fps = clip.fps or 24
        w, h = clip.size
        duration = clip.duration
        print(f"[pipeline] Input: {w}x{h}, {duration:.1f}s, {fps}fps")

        target_w = 1280
        if w < target_w:
            clip = clip.resize(width=target_w)
            w, h = clip.size

        # -- Stage 2: Enhance video --
        cb(15)
        print("[pipeline] Stage 2: Enhancing video (fast mode)...")
        enhanced_clip = clip.fl_image(enhance_frame)

        # -- Stage 3: Process audio --
        cb(25)
        print("[pipeline] Stage 3: Processing audio...")
        raw_audio_path = os.path.join(tmp, "raw_audio.wav")
        clean_audio_path = os.path.join(tmp, "clean_audio.wav")
        has_audio = False

        if clip.audio is not None:
            clip.audio.write_audiofile(raw_audio_path, fps=44100, logger=None)
            process_audio(raw_audio_path, clean_audio_path)
            clean_audio = AudioFileClip(clean_audio_path)
            enhanced_clip = enhanced_clip.set_audio(clean_audio)
            has_audio = True
        else:
            print("[pipeline] WARNING: No audio track in source video!")

        # -- Stage 4: Generate captions (local whisper) --
        cb(40)
        print("[pipeline] Stage 4: Generating captions...")
        caption_segments = []
        if has_audio:
            caption_segments = generate_captions(raw_audio_path)
        print(f"[pipeline] Got {len(caption_segments)} caption segments")

        # -- Stage 5: Build branded overlays --
        cb(55)
        print("[pipeline] Stage 5: Building branding overlays...")
        handle = metadata.get("handle", "Member")
        rating_color = metadata.get("rating_color", "blue")
        tracks = metadata.get("tracks", ["development"])
        color_hex = RATING_COLORS.get(rating_color, RATING_COLORS["blue"])

        lower_third = create_lower_third(
            handle=handle,
            rating_color_hex=color_hex,
            tracks=tracks,
            video_size=(w, h),
            duration=duration,
        )

        track_overlay = create_track_icon_overlay(
            tracks=tracks,
            video_size=(w, h),
            duration=duration,
        )

        # Caption clips (Pillow-based, no TextClip!)
        caption_clips = []
        for seg in caption_segments:
            try:
                txt = seg.get("text", "").strip()
                if not txt:
                    continue
                start = seg.get("start", 0)
                end = seg.get("end", start + 2)
                dur = min(end - start, duration - start)
                if dur <= 0:
                    continue
                cap = _make_caption_clip(txt, start, dur, w, h)
                if cap:
                    caption_clips.append(cap)
            except Exception as e:
                print(f"[pipeline] Skip caption: {e}")

        print(f"[pipeline] Built {len(caption_clips)} caption clips")

        # -- Stage 6: Composite main body --
        cb(65)
        print("[pipeline] Stage 6: Compositing layers...")
        layers = [enhanced_clip, lower_third, track_overlay] + caption_clips
        body = CompositeVideoClip(layers, size=(w, h))
        body = body.set_duration(duration)

        # -- Stage 7: Intro / Outro --
        cb(72)
        print("[pipeline] Stage 7: Building intro/outro...")
        intro = create_intro_clip(handle, color_hex, (w, h))
        outro = create_outro_clip((w, h))

        final_video = concatenate_videoclips(
            [intro, body, outro], method="compose"
        )

        # -- Stage 8: Mix background music --
        cb(82)
        print("[pipeline] Stage 8: Mixing BGM...")
        if has_audio and final_video.audio is not None:
            body_audio_path = os.path.join(tmp, "body_audio.wav")
            final_audio_path = os.path.join(tmp, "final_audio.wav")

            final_video.audio.write_audiofile(
                body_audio_path, fps=44100, logger=None
            )
            mix_with_bgm(
                body_audio_path, final_audio_path, final_video.duration
            )

            final_audio = AudioFileClip(final_audio_path)
            final_video = final_video.set_audio(final_audio)
        else:
            print("[pipeline] Skipping BGM (no audio)")

        # -- Stage 9: Render --
        cb(90)
        print(f"[pipeline] Stage 9: Rendering -> {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=min(fps, 24),
            preset="ultrafast",      # fast for dev; "medium" for production
            bitrate="2000k",
            audio_bitrate="192k",
            threads=4,
            logger="bar",            # shows FFmpeg progress in terminal
        )
        cb(100)
        print("[pipeline] ✅ Pipeline complete!")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        try:
            clip.close()
        except Exception:
            pass
