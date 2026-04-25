"""
Basic pipeline tests.
Run: python -m pytest tests/ -v
"""
import os, sys
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.video_enhancer import (
    auto_white_balance,
    adjust_brightness_contrast,
    boost_saturation,
    enhance_frame,
)


def test_auto_white_balance():
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    result = auto_white_balance(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


def test_brightness_contrast():
    img = np.full((50, 50, 3), 100, dtype=np.uint8)
    result = adjust_brightness_contrast(img, brightness=20, contrast=1.0)
    assert result.mean() > img.mean()


def test_boost_saturation():
    img = np.random.randint(50, 200, (50, 50, 3), dtype=np.uint8)
    result = boost_saturation(img, factor=1.5)
    assert result.shape == img.shape


def test_enhance_frame_rgb():
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = enhance_frame(frame)
    assert result.shape == frame.shape
    assert result.dtype == np.uint8


def test_caption_split():
    from pipeline.captions import _split_text
    segments = _split_text("Hello my name is Tourist and I love competitive programming")
    assert len(segments) > 0
    assert all("text" in s and "start" in s and "end" in s for s in segments)


def test_bgm_generation():
    from pipeline.music_mixer import _generate_bgm
    bgm = _generate_bgm(3000)
    assert len(bgm) >= 2900


def test_hex_to_rgb():
    from pipeline.branding import _hex_to_rgb
    assert _hex_to_rgb("#EF3A3A") == (239, 58, 58)
    assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)


def test_local_whisper_import():
    """Check that faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel
        assert True
    except ImportError:
        pytest.skip("faster-whisper not installed")
