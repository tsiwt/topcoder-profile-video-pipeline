---
title: TC Profile Video
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---
# 🎬 Topcoder Profile Intro Video Pipeline

An AI-powered pipeline that transforms raw member intro clips into polished,
Topcoder-branded professional profile videos.

## ✨ Features

| Feature | Implementation |
|---|---|
| **Visual Enhancement** | OpenCV auto-leveling, color correction |
| **Topcoder Branding** | Dynamic handle/rating overlays, track icons, intro/outro |
| **Audio Post-Production** | Noise reduction, voice leveling via `noisereduce` + `pydub` |
| **Smart Captions** | Local faster-whisper → real timestamped subtitles |
| **Background Music** | Auto-ducking BGM that dips during speech |
| **Mobile-Ready** | H.264 MP4 optimised for web & social sharing |

## 🏗️ Architecture

```
Raw Video + Metadata (JSON)
    │
    ▼
┌──────────────────────────┐
│  FastAPI  /api/process   │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│   Pipeline Orchestrator  │
│  ┌────────┐ ┌──────────┐ │
│  │ Video  │ │  Audio   │ │
│  │Enhance │ │ Denoise  │ │
│  └───┬────┘ └────┬─────┘ │
│      │            │       │
│  ┌───▼────────────▼─────┐ │
│  │  Caption Generation  │ │   ← Local faster-whisper
│  └──────────┬───────────┘ │
│  ┌──────────▼───────────┐ │
│  │   Branding Overlay   │ │   ← Handle, Rating, Icons
│  └──────────┬───────────┘ │
│  ┌──────────▼───────────┐ │
│  │   Music Mixer        │ │   ← Auto-duck BGM
│  └──────────┬───────────┘ │
│  ┌──────────▼───────────┐ │
│  │   Final Renderer     │ │   ← FFmpeg H.264
│  └──────────────────────┘ │
└──────────────────────────┘
             │
             ▼
     Polished MP4 Output
```

## 🚀 Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/<you>/topcoder-profile-video-pipeline.git
cd topcoder-profile-video-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install FFmpeg (Windows)
winget install Gyan.FFmpeg

# 4. (Optional) Set Hugging Face token for cloud captions fallback
set HF_API_TOKEN=hf_xxxxxxxxx

# 5. Run
python main.py
```

Open **http://localhost:8000** in your browser.

## 🌐 Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New **Web Service**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Add env variable `HF_API_TOKEN` in the dashboard (optional)
6. Deploy!

## 💰 Cost Analysis (per 30-second video)

| Component | Cost |
|---|---|
| Local faster-whisper (CPU) | $0.00 |
| Render Free Tier compute | $0.00 |
| FFmpeg / OpenCV (OSS) | $0.00 |
| **Total (free tier)** | **$0.00** |

See [docs/cost_analysis.md](docs/cost_analysis.md) for full breakdown.

## 📄 License

MIT
