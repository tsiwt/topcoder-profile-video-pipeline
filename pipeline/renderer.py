"""
Additional rendering utilities.
"""

def get_encoding_params(target: str = "web") -> dict:
    """Return FFmpeg encoding params for different targets."""
    presets = {
        "web": {
            "codec": "libx264",
            "audio_codec": "aac",
            "preset": "medium",
            "bitrate": "3000k",
            "audio_bitrate": "192k",
        },
        "mobile": {
            "codec": "libx264",
            "audio_codec": "aac",
            "preset": "fast",
            "bitrate": "1500k",
            "audio_bitrate": "128k",
        },
        "social": {
            "codec": "libx264",
            "audio_codec": "aac",
            "preset": "fast",
            "bitrate": "4000k",
            "audio_bitrate": "192k",
        },
    }
    return presets.get(target, presets["web"])
