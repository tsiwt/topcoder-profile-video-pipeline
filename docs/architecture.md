# Architecture Document

## 1. System Overview

The **Topcoder Profile Video Pipeline** is a cloud-native, API-driven, modular system that ingests a raw member intro video (15-60 s) plus member-specific metadata and outputs a polished, Topcoder-branded professional profile video.

**Design principles:**

- **API-Driven:** Every interaction is through RESTful endpoints -- easy to integrate with Topcoder's existing platform or trigger from an S3 event.
- **Modular:** Each processing stage is an independent Python module; the branding template (colors, fonts, icons, music) is asset-driven and can be swapped for special events (e.g., TCO Finals) without code changes.
- **Cloud-Native and Stateless:** The pipeline stores no session state; any instance can process any job -- enabling horizontal scaling behind a load balancer.

---

## 2. High-Level Flow

```
+----------------------------------------------------------------------+
|                        EXTERNAL TRIGGERS                              |
|                                                                       |
|   Browser Upload    S3 PUT Event     Platform API Call                |
|        |                |                   |                         |
+--------+----------------+-------------------+-------------------------+
         |                |                   |
         v                v                   v
+----------------------------------------------------------------------+
|                     FastAPI Application  (main.py)                    |
|                                                                       |
|   POST /api/process                                                   |
|     +- Validate upload (size <= 50 MB, video MIME)                    |
|     +- Parse metadata  { handle, rating_color, tracks[], tagline }  |
|     +- Persist raw file to  uploads/{job_id}.mp4                    |
|     +- Create job record in  jobs/{job_id}.json                     |
|     +- Enqueue BackgroundTask -> orchestrator.run_pipeline()          |
|                                                                       |
|   GET /api/status/{job_id}   -> { status, progress 0-100 }       |
|   GET /api/download/{job_id} -> FileResponse (polished MP4)        |
|   GET /api/health              -> { status, ffmpeg: bool }         |
+----------------------------------------------------------------------+
         |
         v
+----------------------------------------------------------------------+
|              Pipeline Orchestrator  (pipeline/orchestrator.py)         |
|                                                                       |
|   Stage 1 -- Load and Validate                                        |
|     - Open source clip via MoviePy/FFmpeg                             |
|     - Upscale to 1280 px width if smaller                             |
|                                                                       |
|   Stage 2 -- Visual Enhancement  (pipeline/video_enhancer.py)         |
|     - Per-frame: auto white-balance, brightness/contrast,             |
|       saturation boost, light Gaussian denoise                        |
|     - Uses OpenCV (headless) -- no GPU required                       |
|                                                                       |
|   Stage 3 -- Audio Post-Production  (pipeline/audio_processor.py)     |
|     - Extract WAV from source                                         |
|     - Spectral-gating noise reduction  (noisereduce)                  |
|     - Normalize + dynamic-range compression  (pydub)                  |
|                                                                       |
|   Stage 4 -- Smart Caption Generation  (pipeline/captions.py)         |
|     - PRIMARY: Local faster-whisper (base model, INT8, CPU)           |
|       -- no network call, real word-level timestamps                  |
|     - FALLBACK 1: HF Inference API (multiple Whisper models)          |
|     - FALLBACK 2: Silence-based segmentation (placeholder text)       |
|                                                                       |
|   Stage 5 -- Branding Overlays  (pipeline/branding.py)                |
|     - Lower-third bar: handle + rating-color accent + track label     |
|     - Top-right track icon badges (e.g., { } for Dev)               |
|     - All rendered via Pillow RGBA -> MoviePy ImageClip               |
|     - NO ImageMagick dependency                                       |
|                                                                       |
|   Stage 6 -- Layer Compositing                                        |
|     - CompositeVideoClip: enhanced video + lower-third + icons        |
|       + caption clips (Pillow-rendered, positioned at bottom)         |
|                                                                       |
|   Stage 7 -- Intro / Outro Animation                                  |
|     - Intro (2 s): TOPCODER + handle + rating-color bar               |
|     - Outro (2 s): topcoder.com + community CTA                      |
|     - Cross-fade transitions                                          |
|                                                                       |
|   Stage 8 -- BGM Mixing  (pipeline/music_mixer.py)                    |
|     - Load custom BGM from assets/music/ or generate ambient pad      |
|     - Detect speech regions via silence detection                     |
|     - Auto-duck BGM by -10 dB during speech, with 100 ms fades       |
|     - Fade-in (500 ms) / fade-out (1000 ms) on final mix             |
|                                                                       |
|   Stage 9 -- Final Render                                             |
|     - FFmpeg H.264 encode, AAC audio                                  |
|     - Optimized for web + mobile: Baseline profile compatible         |
|     - Output: outputs/{job_id}_final.mp4                            |
+----------------------------------------------------------------------+
```

---

## 3. Technology Stack

| Layer | Technology | License | Rationale |
|---|---|---|---|
| Web Framework | FastAPI | MIT | Native async, auto OpenAPI docs, BackgroundTasks, zero boilerplate |
| Video Processing | MoviePy + FFmpeg | MIT / LGPL | Industry-standard compositing, concat, encode |
| Visual Enhancement | OpenCV (headless) | Apache 2.0 | Fast per-frame white-balance, contrast, saturation |
| Audio Cleanup | noisereduce + pydub | MIT | Spectral gating + normalization -- no cloud API needed |
| AI Captions | faster-whisper (local) | MIT | 4x faster than original-whisper, real timestamps, offline |
| Branding Render | Pillow | HPND | RGBA image generation -- no ImageMagick required |
| BGM Mixing | pydub | MIT | Auto-ducking, gain control, export |
| Containerization | Docker | Apache 2.0 | Reproducible builds, HF Spaces and Render compatible |
| CI/CD | GitHub Actions | -- | Auto-sync to Hugging Face Spaces on push |

---

## 4. Modular Template System

All branding assets are **external to the pipeline code**:

```
assets/
  fonts/       <-- Custom typefaces (fallback: system DejaVu / Arial)
  icons/       <-- Track badge images (swap for TCO-themed versions)
  music/       <-- bgm.mp3 -- replace for event-specific soundtrack
  templates/   <-- Reserved for future JSON-driven template definitions
```

**Brand constants** (config.py):

```python
TC_COLORS      # Primary palette -- one dict to update for themed events
RATING_COLORS  # Maps "red"/"yellow"/etc to hex -- drives lower-third accent
TRACK_LABELS   # Human-readable track names
```

**Event customization workflow** (e.g., TCO 2025 Finals):
1. Drop new icon PNGs into assets/icons/
2. Replace assets/music/bgm.mp3 with event soundtrack
3. Update TC_COLORS["primary"] in config.py
4. Redeploy -- zero pipeline code changes.

---

## 5. S3 / Object Storage Integration Strategy

The PoC uses direct multipart upload via the /api/process endpoint. For production at scale:

```
Member -> Presigned S3 PUT URL -> S3 Bucket
                                      |
                                      v  (S3 Event Notification)
                                Lambda / SQS -> POST /api/process
                                                    |
                                                    v
                                Pipeline processes -> output to S3
                                                    |
                                                    v
                                CDN (CloudFront) serves final MP4
```

The orchestrator is already decoupled -- it accepts any local file path. Plugging in S3 download/upload is a thin wrapper.

---

## 6. Mobile-Friendly Output

| Parameter | Value | Rationale |
|---|---|---|
| Resolution | 1280 x 720 | Fits all mobile screens; social-platform optimized |
| Codec | H.264 Baseline | Maximum device compatibility (iOS, Android, web) |
| Bitrate | 2000 kbps video / 192 kbps audio | Good quality at small file size (~7 MB for 30 s) |
| Container | MP4 (moov atom front) | Instant web playback, no progressive download needed |
| Aspect | 16:9 | Standard for profile embeds and social sharing |

pipeline/renderer.py provides presets for **web**, **mobile**, and **social** targets.

---

## 7. Scalability Path

| Scale | Architecture |
|---|---|
| **PoC** (1-50 /day) | Single container on HF Spaces / Render Free |
| **Growth** (500 /day) | Render Starter ($7/mo) or single EC2 |
| **Enterprise** (5000+ /day) | Stateless workers behind SQS queue + ALB; S3 for I/O; GPU instances for faster-whisper large-v3 |

The pipeline is **stateless** -- any number of workers can process jobs in parallel with no shared state beyond the filesystem (replaceable with S3).

---

## 8. Version History

| Version | Changes |
|---|---|
| v1 | HF API for captions (unreliable 404 errors) |
| v2 | Removed face detection, Pillow-only captions, ultrafast render |
| v3 (current) | Local faster-whisper for real captions, HF API as optional fallback, improved docs |
