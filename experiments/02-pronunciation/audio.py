"""Load any audio file (wav, m4a, webm, ...) as 16 kHz mono float32 via ffmpeg."""

import subprocess
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000


def load_audio(path: str | Path, sr: int = SAMPLE_RATE) -> np.ndarray:
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32)
