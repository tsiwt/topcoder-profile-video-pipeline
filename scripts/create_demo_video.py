"""
Generate a simple demo/test video for pipeline testing.
Creates a 15-second synthetic video with audio.
Usage: python scripts/create_demo_video.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoClip, AudioClip

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                      "uploads", "demo_raw.mp4")


def create_demo():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    duration = 15
    W, H = 1280, 720
    fps = 24

    def make_frame(t):
        img = Image.new("RGB", (W, H), (
            int(30 + 20 * np.sin(t * 0.5)),
            int(40 + 30 * np.sin(t * 0.3)),
            int(80 + 50 * np.sin(t * 0.7)),
        ))
        draw = ImageDraw.Draw(img)

        # Fake person circle
        cx, cy = W // 2, H // 2 - 30
        r = 100
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(180, 150, 130))
        draw.ellipse([cx-30, cy-60, cx+30, cy-10], fill=(200, 170, 150))

        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
        except Exception:
            font = ImageFont.load_default()

        text = "Hi, I'm TechStar!"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, H // 2 + 100), text,
                  fill=(255, 255, 255), font=font)

        text2 = "Development Track"
        bbox2 = draw.textbbox((0, 0), text2, font=font)
        tw2 = bbox2[2] - bbox2[0]
        draw.text(((W - tw2) // 2, H // 2 + 150), text2,
                  fill=(44, 149, 215), font=font)

        return np.array(img)

    def make_audio(t):
        freq = 220
        return np.sin(2 * np.pi * freq * t) * 0.1

    video = VideoClip(make_frame, duration=duration)
    audio = AudioClip(make_audio, duration=duration, fps=44100).set_duration(duration)
    video = video.set_audio(audio)
    video.write_videofile(OUTPUT, fps=fps, codec="libx264",
                          audio_codec="aac", logger=None)
    print(f"\n✅ Demo video created: {OUTPUT}")
    print(f"   Duration: {duration}s, Size: {W}x{H}")


if __name__ == "__main__":
    create_demo()
