"""
Background music mixing with auto-ducking:
  - Generate or load a BGM track
  - Detect speech and lower BGM during voice
  - Export mixed audio
"""
import os, math
import numpy as np
from pydub import AudioSegment
from pydub.generators import Sine
from pydub.silence import detect_nonsilent
from config import ASSETS_DIR


def _generate_bgm(duration_ms: int) -> AudioSegment:
    """
    Generate a simple ambient BGM programmatically.
    Uses layered sine waves for a pleasant pad-like sound.
    """
    base_freq = 220  # A3
    freqs = [base_freq, base_freq * 1.25, base_freq * 1.5, base_freq * 2]

    combined = AudioSegment.silent(duration=duration_ms)

    for i, freq in enumerate(freqs):
        tone = Sine(freq).to_audio_segment(duration=duration_ms)
        tone = tone - (20 + i * 3)

        chunk_ms = 500
        modulated = AudioSegment.silent(duration=0)
        for j in range(0, duration_ms, chunk_ms):
            chunk = tone[j:j + chunk_ms]
            mod = math.sin(j / 2000.0 * math.pi) * 3
            chunk = chunk + mod
            modulated += chunk

        combined = combined.overlay(modulated)

    shimmer = Sine(880).to_audio_segment(duration=duration_ms) - 30
    combined = combined.overlay(shimmer)

    return combined


def _load_or_generate_bgm(duration_sec: float) -> AudioSegment:
    """Try to load a BGM file from assets, else generate one."""
    bgm_path = os.path.join(str(ASSETS_DIR), "music", "bgm.mp3")
    duration_ms = int(duration_sec * 1000)

    if os.path.exists(bgm_path):
        bgm = AudioSegment.from_file(bgm_path)
        while len(bgm) < duration_ms:
            bgm += bgm
        return bgm[:duration_ms]

    return _generate_bgm(duration_ms)


def mix_with_bgm(voice_path: str, output_path: str, total_duration: float):
    """Mix voice audio with BGM, auto-ducking BGM during speech."""
    voice = AudioSegment.from_wav(voice_path)
    bgm = _load_or_generate_bgm(total_duration)

    target_ms = int(total_duration * 1000)
    if len(voice) < target_ms:
        voice += AudioSegment.silent(duration=target_ms - len(voice))
    else:
        voice = voice[:target_ms]
    bgm = bgm[:target_ms]

    # Base BGM volume: low
    bgm = bgm - 22

    # Detect speech regions for ducking
    try:
        speech_regions = detect_nonsilent(
            voice, min_silence_len=300, silence_thresh=-35
        )
    except Exception:
        speech_regions = []

    # Apply ducking
    DUCK_DB = -10
    FADE_MS = 100

    for start_ms, end_ms in speech_regions:
        duck_start = max(0, start_ms - FADE_MS)
        duck_end = min(target_ms, end_ms + FADE_MS)

        before = bgm[:duck_start]
        ducked = bgm[duck_start:duck_end] + DUCK_DB
        after = bgm[duck_end:]

        if len(ducked) > FADE_MS * 2:
            ducked = ducked.fade_in(FADE_MS).fade_out(FADE_MS)

        bgm = before + ducked + after

        if len(bgm) < target_ms:
            bgm += AudioSegment.silent(duration=target_ms - len(bgm))
        bgm = bgm[:target_ms]

    bgm = bgm.fade_in(500).fade_out(1000)

    mixed = voice.overlay(bgm)
    mixed.export(output_path, format="wav")
