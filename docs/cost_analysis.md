# Cost and Performance Analysis

## Executive Summary

> **Does this cost $0.05 or $5.00 per video?**
>
> **Answer: approximately $0.00 on free tier, at most $0.03 at enterprise scale.**
> Every AI component runs locally -- there are **zero per-call API fees**. The only cost is compute time.

---

## 1. Per-Video Cost Breakdown (30-second input)

### Free Tier -- PoC / Low Volume

| Component | Provider | Per-Video Cost |
|---|---|---|
| AI Captions | Local faster-whisper (base, CPU) | $0.00 |
| Noise Reduction | Local noisereduce | $0.00 |
| Visual Enhancement | Local OpenCV | $0.00 |
| Video Rendering | Local FFmpeg | $0.00 |
| Hosting | HF Spaces (free) / Render Free | $0.00 |
| **TOTAL** | | **$0.00** |

### Production -- 1500 videos / month

| Component | Provider | Per-Video Cost |
|---|---|---|
| AI Captions | Local faster-whisper | $0.00 |
| Compute | Render Starter ($7/mo) | ~$0.005 |
| Storage | Ephemeral (cleaned after download) | ~$0.001 |
| **TOTAL** | | **~$0.006** |

### Enterprise -- 50000+ videos / month

| Component | Provider | Per-Video Cost |
|---|---|---|
| Compute | AWS EC2 GPU (g4dn.xlarge spot) | ~$0.02 |
| AI Captions | Local faster-whisper large-v3 (GPU) | $0.00 |
| S3 Storage | AWS S3 Standard | ~$0.001 |
| CDN Delivery | CloudFront | ~$0.002 |
| **TOTAL** | | **~$0.02 - $0.03** |

---

## 2. Why So Cheap?

1. **No paid AI APIs.** Captions use faster-whisper locally. Audio cleanup uses noisereduce. Video enhancement uses OpenCV. All open-source, all free.
2. **Processing is CPU-only.** A 30 s video processes in ~30-45 s on a 2-vCPU machine -- no GPU required for the base model.
3. **Stateless pipeline.** No database, no persistent storage (beyond temp files during processing). Output files can be moved to S3/CDN and the temp cleaned up.

---

## 3. Processing Latency (30-second input)

| Pipeline Stage | Duration (2-vCPU, CPU-only) | Duration (GPU, optimized) |
|---|---|---|
| Load and Validate | < 1 s | < 1 s |
| Visual Enhancement (OpenCV) | ~5-10 s | ~3-5 s |
| Audio Denoise + Normalize | ~3-5 s | ~2-3 s |
| Caption Generation (faster-whisper base) | ~5-8 s | ~1-2 s (large-v3 on CUDA) |
| Branding Overlays (Pillow) | ~3-5 s | ~2-3 s |
| BGM Mix + Auto-Duck | ~2-3 s | ~1-2 s |
| Final Render (FFmpeg ultrafast) | ~5-10 s | ~3-5 s (medium preset) |
| **Total End-to-End** | **~25-45 s** | **~12-20 s** |

---

## 4. Scalability for 1.5 Million Members

| Metric | Estimate |
|---|---|
| Year 1 adoption (5 percent of 1.5 M) | 75000 videos |
| At $0.02 / video | **$1500 total compute for Year 1** |
| Peak daily load (launch week) | ~5000 videos / day |
| Workers needed (40 s each, 8 h peak) | ~7 parallel containers |

The pipeline is **stateless and horizontally scalable**. Deploy N workers behind a queue (SQS, RabbitMQ, or Celery) -- each processes independently.

---

## 5. Comparison with Alternative Approaches

| Approach | Per-Video Cost | Latency | Offline? |
|---|---|---|---|
| **This pipeline (local whisper + OSS)** | **$0.00 - $0.03** | **25-45 s** | **Yes** |
| Cloud Whisper API + Runway ML | $0.10 - $0.50 | 30-60 s | No |
| AWS Transcribe + MediaConvert | $0.05 - $0.15 | 60-120 s | No |
| Human editor (Fiverr) | $5 - $25 | 24-48 h | N/A |
