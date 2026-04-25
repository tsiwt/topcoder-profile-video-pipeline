"""
Caption generation — Local faster-whisper (primary) + HF API (fallback).

v3 FIXED:
  - Uses faster-whisper locally (no network needed, no 404)
  - HF API as optional fallback
  - Real word-level timestamps
  - Silence-based fallback as last resort
"""
import os, time, requests
from config import HF_API_TOKEN, HF_WHISPER_MODEL, LOCAL_WHISPER_MODEL


def generate_captions(audio_path: str) -> list:
    """
    Returns list of dicts: [{"text": "...", "start": 0.0, "end": 2.5}, ...]
    Priority: local whisper → HF API → silence detection fallback.
    """
    # Priority 1: Local faster-whisper (best reliability)
    try:
        return _local_whisper(audio_path)
    except ImportError:
        print("[captions] faster-whisper not installed, trying HF API...")
    except Exception as e:
        print(f"[captions] Local whisper failed ({e}), trying HF API...")

    # Priority 2: HF API
    if HF_API_TOKEN:
        try:
            return _hf_whisper(audio_path)
        except Exception as e:
            print(f"[captions] HF API failed ({e}), using fallback")

    # Priority 3: Silence-based fallback
    return _fallback_captions(audio_path)


def _local_whisper(audio_path: str) -> list:
    """
    Use faster-whisper locally — no network needed.
    First run will download the model (~150MB for 'base'), then cached.
    """
    from faster_whisper import WhisperModel

    model_size = LOCAL_WHISPER_MODEL

    print(f"[captions] Loading local Whisper model: {model_size}")
    print(f"[captions] (First run downloads ~150MB, then cached in ~/.cache/huggingface/)")

    model = WhisperModel(
        model_size,
        device="cpu",          # use "cuda" if you have NVIDIA GPU
        compute_type="int8",   # fast on CPU
    )

    print(f"[captions] Transcribing: {audio_path}")
    segments_gen, info = model.transcribe(
        audio_path,
        language="en",
        beam_size=5,
        word_timestamps=True,
    )

    print(f"[captions] Detected language: {info.language} "
          f"(prob={info.language_probability:.2f})")

    # Convert generator to list
    segments = []
    for seg in segments_gen:
        text = seg.text.strip()
        if not text:
            continue
        segments.append({
            "text": text,
            "start": seg.start,
            "end": seg.end,
        })
        print(f"[captions]   [{seg.start:.1f}s -> {seg.end:.1f}s] {text}")

    print(f"[captions] Total segments: {len(segments)}")
    return segments


def _hf_whisper(audio_path: str) -> list:
    """Call Hugging Face Inference API with retry + multiple model fallback."""
    model_ids = [
        HF_WHISPER_MODEL,
        "openai/whisper-large-v3",  # nosemgrep: ai.generic.detect-generic-ai-oai.detect-generic-ai-oai
        "openai/whisper-small",  # nosemgrep: ai.generic.detect-generic-ai-oai.detect-generic-ai-oai
        "openai/whisper-base",  # nosemgrep: ai.generic.detect-generic-ai-oai.detect-generic-ai-oai
    ]

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
    }

    with open(audio_path, "rb") as f:
        data = f.read()

    for model_id in model_ids:
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        print(f"[captions] Trying HF model: {model_id}")

        try:
            for attempt in range(2):
                resp = requests.post(url, headers=headers, data=data, timeout=120)

                if resp.status_code == 503:
                    try:
                        wait_time = resp.json().get("estimated_time", 20)
                    except Exception:
                        wait_time = 20
                    print(f"[captions] Model loading, waiting {wait_time:.0f}s...")
                    time.sleep(min(wait_time, 30))
                    continue

                if resp.status_code == 404:
                    print(f"[captions] Model {model_id} not found, trying next...")
                    break

                resp.raise_for_status()

                result = resp.json()
                print(f"[captions] HF response: {str(result)[:200]}")
                return _parse_hf_response(result)

        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                continue
            raise

    raise RuntimeError("All HF Whisper models returned errors")


def _parse_hf_response(result) -> list:
    """Parse HF API response into segments."""
    if isinstance(result, dict):
        if "chunks" in result:
            segments = []
            for chunk in result["chunks"]:
                ts = chunk.get("timestamp", [0, 2])
                segments.append({
                    "text": chunk.get("text", ""),
                    "start": ts[0] if ts[0] is not None else 0,
                    "end": ts[1] if ts[1] is not None else (ts[0] or 0) + 3,
                })
            return segments
        elif "text" in result:
            return _split_text(result["text"])
    elif isinstance(result, list) and len(result) > 0:
        text = (result[0].get("text", "")
                if isinstance(result[0], dict) else str(result[0]))
        return _split_text(text)
    return []


def _split_text(text: str, chunk_sec: float = 3.0) -> list:
    """Split a long text into ~3-second caption chunks."""
    words = text.split()
    if not words:
        return []
    wps = 2.5
    chunk_words = max(3, int(chunk_sec * wps))
    segments = []
    t = 0.0
    for i in range(0, len(words), chunk_words):
        seg_words = words[i:i + chunk_words]
        seg_text = " ".join(seg_words)
        dur = len(seg_words) / wps
        segments.append({"text": seg_text, "start": t, "end": t + dur})
        t += dur
    return segments


def _fallback_captions(audio_path: str) -> list:
    """Silence-based fallback (placeholder text only)."""
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent

        audio = AudioSegment.from_wav(audio_path)
        intervals = detect_nonsilent(
            audio, min_silence_len=400, silence_thresh=-40
        )
        segments = []
        for i, (start_ms, end_ms) in enumerate(intervals):
            segments.append({
                "text": f"[speech segment {i + 1}]",
                "start": start_ms / 1000.0,
                "end": end_ms / 1000.0,
            })
        return segments
    except Exception:
        return []