# Tooling & Budget Report

## Tool Selection Rationale

### 1. FastAPI (Python Web Framework)
- **Why**: Native async, auto OpenAPI docs, BackgroundTasks
- **Cost**: Free (MIT)

### 2. MoviePy (Video Compositing)
- **Why**: Pythonic clip layering, uses FFmpeg
- **Cost**: Free (MIT)

### 3. OpenCV (Visual Enhancement)
- **Why**: White balance, contrast, saturation — fast per-frame
- **Cost**: Free (Apache 2.0)

### 4. Pillow (Branding + Captions)
- **Why**: RGBA image generation, no ImageMagick dependency
- **Cost**: Free (MIT-like)

### 5. faster-whisper (AI Captions) ← NEW in v3
- **Why**: Local STT, no network needed, 4x faster than openai-whisper
- **Replaces**: HF Whisper API (was getting 404 errors)
- **Cost**: Free (MIT)

### 6. noisereduce + pydub (Audio)
- **Why**: Spectral noise reduction + normalization/compression
- **Cost**: Free (MIT)

### 7. Render.com (Deployment)
- **Why**: Free Docker hosting, GitHub auto-deploy
- **Cost**: Free for PoC; $7/mo Starter

## Budget Summary

| Item | Monthly Cost |
|---|---|
| All OSS libraries | $0 |
| Local whisper (no API) | $0 |
| Render.com (free tier) | $0 |
| **PoC Total** | **$0/month** |
| **Production (Starter)** | **~$7/month** |
