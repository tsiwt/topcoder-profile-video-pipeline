"""
Audio post-production:
  - Noise reduction (noisereduce)
  - Normalisation & compression
"""
import os
import numpy as np
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range


def process_audio(input_path: str, output_path: str):
    """Full audio cleanup pipeline."""

    # 1. Load
    data, sr = sf.read(input_path)

    # Mono conversion if stereo
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # 2. Noise reduction
    reduced = nr.reduce_noise(
        y=data,
        sr=sr,
        prop_decrease=0.75,
        stationary=True,
    )

    # 3. Write intermediate
    temp_path = output_path + ".tmp.wav"
    sf.write(temp_path, reduced, sr)

    # 4. Normalise & light compression via pydub
    audio = AudioSegment.from_wav(temp_path)
    audio = normalize(audio)
    audio = compress_dynamic_range(
        audio,
        threshold=-20.0,
        ratio=3.0,
        attack=5.0,
        release=50.0,
    )
    audio = normalize(audio, headroom=1.0)
    audio.export(output_path, format="wav")

    # cleanup
    os.remove(temp_path)
