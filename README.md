---
title: TC Profile Video
emoji: "🎬"
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Topcoder Profile Intro Video Pipeline

> **AI-powered pipeline that transforms a raw 15-30 s member intro clip + metadata into a polished, Topcoder-branded professional profile video -- fully automated, cloud-native, and scalable to 1.5 M+ members.**

| Live Demo | Before / After |
|---|---|
| <https://huggingface.co/spaces/larry5432112345/tc-profile-video> | See Demo Video section below |

---

## Feature Matrix

| Requirement | Implementation | Details |
|---|---|---|
| **Visual Enhancement** | OpenCV per-frame processing | Auto white-balance, brightness/contrast, saturation boost, Gaussian denoise |
| **Topcoder Branding** | Pillow RGBA compositing | Dynamic handle + rating-color lower-third, track icon badges, animated intro/outro cards |
| **Audio Post-Production** | noisereduce + pydub | Spectral-gating noise reduction, normalization, dynamic-range compression |
| **Smart Captions** | Local faster-whisper (base) | Real word-level timestamps, styled semi-transparent caption bars |
| **Background Music** | Programmatic BGM + auto-duck | Sine-wave ambient pad, volume ducks during detected speech |
| **Mobile-Ready Output** | FFmpeg H.264 Baseline | 1280x720, 2 Mbps, AAC 192 kbps -- plays natively on iOS/Android and social platforms |

---

## Architecture

```
 +----------------+   POST /api/process   +-----------------------------------+
 |  Browser /     | --------------------> |      FastAPI  (main.py)           |
 |  S3 Event /    |                       |  - Accepts upload + metadata      |
 |  API Client    |                       |  - Returns job_id                 |
 +-------+--------+                       +----------+------------------------+
         |                                           |  BackgroundTask
         |  GET /api/status/{id}                   v
         | <--------------------------  +--------------------------------------+
         |                              |     Pipeline Orchestrator            |
         |                              |                                      |
         |                              |  1. Load and validate source         |
         |                              |  2. Visual Enhancement  (OpenCV)     |
         |                              |  3. Audio Denoise  (noisereduce)     |
         |                              |  4. Caption Gen  (faster-whisper)    |
         |                              |  5. Branding Overlays  (Pillow)      |
         |                              |  6. Layer Compositing  (MoviePy)     |
         |                              |  7. Intro / Outro Cards              |
         |                              |  8. BGM Mix + Auto-Duck  (pydub)     |
         |                              |  9. Final Render  (FFmpeg H.264)     |
         |                              +----------+---------------------------+
         |  GET /api/download/{id}               |
         | <---------------------------------------+
         v
   Polished MP4  (web + mobile ready)
```

> **S3 Integration Note:** The pipeline is designed to be triggered by an S3 PUT event (or any object-store webhook). In the PoC the upload endpoint accepts multipart form-data directly; in production, replace the upload handler with an S3 presigned-URL flow -- the orchestrator is decoupled and accepts any local file path.

Full architecture document: [docs/architecture.md](docs/architecture.md)

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/process | Upload video + metadata, returns job_id |
| GET  | /api/status/{job_id} | Poll processing progress (0-100 percent) |
| GET  | /api/download/{job_id} | Download finished MP4 |
| GET  | /api/health | Health check (FFmpeg availability) |
| GET  | / | Web UI (single-page) |

---

## Modular / Template Design

The branding layer is **fully decoupled** from the processing pipeline:

```
assets/
  fonts/          <-- Drop custom fonts (e.g., TCO 2025 typeface)
  icons/          <-- Track icon PNGs; swap for event-specific badges
  music/          <-- Replace bgm.mp3 for themed events
  templates/      <-- Future: JSON template definitions
```

- **TCO Finals?** Swap assets/icons/ and assets/music/, update TC_COLORS in config.py -- zero code change in the pipeline.
- All brand constants live in **config.py** (TC_COLORS, RATING_COLORS, TRACK_LABELS) -- one-file update for any event.

---

## Cost Analysis -- $0.02 per video at scale

> **Direct answer to the challenge question:** This pipeline costs approximately **$0.00 on the free tier** and **at most $0.03 per video** at enterprise scale -- firmly at the $0.05 end, not the $5.00 end.

| Scale | Compute | Captions | Storage | Total / video |
|---|---|---|---|---|
| PoC (free tier) | $0 (HF Spaces / Render Free) | $0 (local whisper) | $0 | **$0.00** |
| Production (1500 /mo) | ~$0.005 (Render Starter $7) | $0 | ~$0.001 | **~$0.006** |
| Enterprise (50000 /mo) | ~$0.02 (GPU worker) | $0 | ~$0.002 | **~$0.02-0.03** |

Full breakdown: [docs/cost_analysis.md](docs/cost_analysis.md)

---

## Processing Latency

| Stage | Time (30 s input, CPU) |
|---|---|
| Video Enhancement | ~5-10 s |
| Audio Denoise | ~3-5 s |
| Caption Generation | ~5-8 s |
| Branding + Compositing | ~3-5 s |
| BGM Mixing | ~2-3 s |
| Final Render (ultrafast) | ~5-10 s |
| **End-to-end** | **~25-45 s** |

GPU acceleration (CUDA + medium preset) can bring this under **15 s**.

---

## Demo and Before / After

| Asset | Link |
|---|---|
| **Live Deployed App** | <https://huggingface.co/spaces/larry5432112345/tc-profile-video> |
| **Raw Input Sample** | included in submission |
| **Processed Output Sample** | included in submission |
| **Screen-Recording Demo** | demotopcoder.mp4 -- shows full upload, progress, download flow |

---

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/tsiwt/topcoder-profile-video-pipeline.git
cd topcoder-profile-video-pipeline

# 2. Install deps
pip install -r requirements.txt

# 3. Install FFmpeg
# Windows:  winget install Gyan.FFmpeg
# macOS:    brew install ffmpeg
# Linux:    apt-get install ffmpeg

# 4. Run
python main.py
# open http://localhost:8000
```

### CLI Mode (no browser)

```bash
python scripts/run_pipeline_cli.py input.mp4 --handle tourist --color red --tracks "competitive,development"
```

---

## Docker

```bash
docker build -t tc-profile-video .
docker run -p 7860:7860 tc-profile-video
```

---

## Deployment

| Platform | Method |
|---|---|
| **Hugging Face Spaces** | Auto-synced via GitHub Actions (.github/workflows/sync-to-hf.yml) |
| **Render.com** | render.yaml included -- connect repo and deploy |
| **Any Docker host** | Standard Dockerfile |

---

## Evaluation Criteria Mapping

| Criterion | How This Solution Addresses It |
|---|---|
| **The Wow Factor** | Intro/outro cards, animated lower-third with rating color, track badges, auto-ducking BGM, real AI captions -- looks professionally edited |
| **Metadata Integration** | Handle, rating color, track(s) all drive visual elements dynamically; config-driven, no hard-coding |
| **Production Speed** | 25-45 s on CPU for a 30 s clip; sub-15 s possible with GPU |
| **Cost Efficiency** | $0.00 on free tier; at most $0.03/video at scale; all processing is local (no per-call API fees) |

---

## Repository Structure

```
topcoder-profile-video-pipeline/
  main.py                  # FastAPI app + endpoints
  config.py                # All brand constants and env config
  Dockerfile               # Production container
  requirements.txt
  render.yaml              # Render.com deploy config
  pipeline/
    orchestrator.py        # 9-stage pipeline coordinator
    video_enhancer.py      # OpenCV per-frame enhancement
    audio_processor.py     # Noise reduction + normalization
    captions.py            # faster-whisper (local) + HF fallback
    branding.py            # Lower-third, icons, intro/outro
    music_mixer.py         # BGM generation + auto-ducking
    renderer.py            # Encoding presets (web/mobile/social)
  assets/                  # Swappable branding assets
  static/index.html        # Single-page Web UI
  scripts/                 # CLI tools and demo generator
  tests/                   # pytest suite
  docs/
    architecture.md        # Full architecture document
    cost_analysis.md       # Per-video cost and latency breakdown
    tooling_report.md      # Tool selection rationale and budget
```

---

## License

MIT
