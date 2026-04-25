# Architecture Document

## System Overview

The Topcoder Profile Video Pipeline is a cloud-native, API-driven system
that ingests a raw member intro video plus metadata and outputs a polished,
branded profile video.

## High-Level Flow

```
┌─────────────┐      POST /api/process       ┌──────────────────┐
│  Browser /   │  ──────────────────────────▶  │   FastAPI App    │
│  API Client  │                               │   (main.py)      │
└──────┬──────┘                               └────────┬─────────┘
       │                                               │
       │  GET /api/status/{id}                         │ BackgroundTask
       │◀──────────────────────────────────────────────│
       │                                               ▼
       │                                    ┌─────────────────────┐
       │                                    │  Pipeline           │
       │                                    │  Orchestrator       │
       │                                    │                     │
       │                                    │  Stage 1: Load      │
       │                                    │  Stage 2: Enhance   │
       │                                    │  Stage 3: Audio     │
       │                                    │  Stage 4: Captions  │
       │                                    │   (local whisper)   │
       │                                    │  Stage 5: Branding  │
       │                                    │  Stage 6: Composite │
       │                                    │  Stage 7: Intro/Out │
       │                                    │  Stage 8: BGM Mix   │
       │                                    │  Stage 9: Render    │
       │                                    └─────────────────────┘
       │                                               │
       │  GET /api/download/{id}                       │
       │◀──────────────────────────────────────────────│
       ▼                                               ▼
 Polished MP4                                    Stored Output
```

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Web Framework** | FastAPI (Python) | Async, fast, auto-docs, background tasks |
| **Video Processing** | MoviePy + FFmpeg | Industry-standard, compositing, encoding |
| **Visual Enhancement** | OpenCV | White balance, contrast, saturation |
| **Audio Cleanup** | noisereduce + pydub | Spectral gating + normalization |
| **AI Captions** | faster-whisper (local) | No network needed, real timestamps |
| **Branding** | Pillow + MoviePy | RGBA overlays, no ImageMagick |
| **BGM Mixing** | pydub | Auto-ducking, gain control |
| **Deployment** | Render.com (Docker) | Free tier, auto-deploy |

## v3 Changes

- v1: HF API for captions (404 errors)
- v2: Removed face detection, Pillow captions, ultrafast render
- v3: Local faster-whisper for real captions, HF API as fallback only
