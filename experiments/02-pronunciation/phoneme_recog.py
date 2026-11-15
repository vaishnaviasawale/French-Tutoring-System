"""Audio -> phonemes actually spoken, using a wav2vec2 CTC model that outputs espeak phonemes.

    uv run python 02-pronunciation/phoneme_recog.py recordings/s01_good.wav

The model (Xu et al. 2021) was fine-tuned on multilingual CommonVoice with espeak phoneme labels,
so its symbols mostly match what g2p.py produces. First run downloads ~1.2 GB.
"""

import sys
from functools import lru_cache

import numpy as np
import torch
from audio import SAMPLE_RATE, load_audio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL_ID = "facebook/wav2vec2-xlsr-53-espeak-cv-ft"


@lru_cache(maxsize=1)
def _load():
    return Wav2Vec2Processor.from_pretrained(MODEL_ID), Wav2Vec2ForCTC.from_pretrained(MODEL_ID).eval()


def recognize(audio: np.ndarray) -> list[str]:
    processor, model = _load()
    inputs = processor(audio, sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.inference_mode():
        logits = model(inputs.input_values).logits
    return processor.batch_decode(logits.argmax(dim=-1))[0].split()


if __name__ == "__main__":
    print(" ".join(recognize(load_audio(sys.argv[1]))))
