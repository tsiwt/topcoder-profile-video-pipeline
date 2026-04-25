# Tooling and Budget Report

## 1. Tool Selection Rationale

### FastAPI (Web Framework)
- **Why chosen:** Native async support, automatic OpenAPI documentation, built-in BackgroundTasks for long-running pipeline jobs, first-class Python typing.
- **Alternatives considered:** Flask (no native async), Django (too heavy for a single-purpose API).
- **License:** MIT | **Cost:** Free

### MoviePy + FFmpeg (Video Processing and Rendering)
- **Why chosen:** MoviePy provides Pythonic clip compositing (layering, concatenation, transitions). FFmpeg handles the actual H.264/AAC encoding -- the industry standard.
- **Alternatives considered:** OpenCV-only (poor audio support), cloud video APIs (per-call cost).
- **License:** MIT / LGPL | **Cost:** Free

### OpenCV Headless (Visual Enhancement)
- **Why chosen:** Extremely fast per-frame operations (white balance, contrast, saturation). Headless variant avoids GUI dependencies in Docker.
- **Alternatives considered:** Pillow (slower for pixel-level ops), cloud enhancement APIs (cost per call).
- **License:** Apache 2.0 | **Cost:** Free

### Pillow (Branding Overlays and Caption Rendering)
- **Why chosen:** Reliable RGBA image generation for lower-thirds, track badges, caption bars. Eliminates the ImageMagick dependency that MoviePy TextClip requires.
- **Alternatives considered:** MoviePy TextClip + ImageMagick (hard to install in Docker, version conflicts).
- **License:** HPND (MIT-like) | **Cost:** Free

### faster-whisper (AI Captions)
- **Why chosen:** Runs locally -- no network latency, no API rate limits, no per-call cost. 4x faster than openai-whisper on CPU via CTranslate2 INT8 quantization. Provides real word-level timestamps for synchronized captions.
- **Alternatives considered:**
  - OpenAI Whisper API: $0.006/min -- adds cost at scale.
  - HF Inference API: Free tier has cold-start 503s and occasional 404s (experienced in v1).
  - AWS Transcribe: $0.024/min -- adds cost and vendor lock-in.
- **Model size:** base (~150 MB) for PoC; large-v3 recommended for production accuracy.
- **License:** MIT | **Cost:** Free

### noisereduce + pydub (Audio Post-Production)
- **Why chosen:** noisereduce provides spectral-gating noise reduction (removes AC hum, keyboard clicks). pydub handles normalization, dynamic-range compression, and BGM mixing with auto-ducking.
- **Alternatives considered:** Adobe Podcast API (not publicly available), cloud audio APIs (per-call cost).
- **License:** MIT | **Cost:** Free

### Docker (Containerization)
- **Why chosen:** Ensures FFmpeg, system fonts, and all Python deps are reproducibly installed. Compatible with Hugging Face Spaces, Render.com, AWS ECS, and any container platform.
- **License:** Apache 2.0 | **Cost:** Free

### GitHub Actions (CI/CD)
- **Why chosen:** Auto-syncs the repository to Hugging Face Spaces on every push to main. Zero manual deployment.
- **Cost:** Free for public repos.

---

## 2. Budget Summary

### PoC (Current)

| Item | Monthly Cost |
|---|---|
| All OSS libraries (MoviePy, OpenCV, Pillow, faster-whisper, etc.) | $0 |
| Hosting: Hugging Face Spaces (free Docker) | $0 |
| CI/CD: GitHub Actions (public repo) | $0 |
| **Total** | **$0 / month** |

### Production (Low Volume)

| Item | Monthly Cost |
|---|---|
| All OSS libraries | $0 |
| Hosting: Render Starter (2 vCPU, 2 GB) | $7 |
| **Total** | **$7 / month** |

### Enterprise (High Volume)

| Item | Monthly Cost (est. 50000 videos) |
|---|---|
| All OSS libraries | $0 |
| Compute: 4x g4dn.xlarge spot instances | ~$800 |
| S3 Storage (50000 x 8 MB, 30-day retention) | ~$12 |
| CloudFront CDN | ~$50 |
| **Total** | **~$862 / month (~$0.017 / video)** |

---

## 3. Projected Cost per 30-Second Video

| Tier | Cost per Video |
|---|---|
| Free tier (PoC) | **$0.00** |
| Starter (Render $7/mo) | **~$0.006** |
| Enterprise (AWS GPU) | **~$0.02** |

> **Bottom line:** The entire stack is open-source. The only variable cost is compute time, which is minimal because all AI inference runs locally.
