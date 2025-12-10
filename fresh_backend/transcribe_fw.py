# transcribe_fw.py
from faster_whisper import WhisperModel
from pathlib import Path

# Load model once at import time (small is a good balance)
# compute_type="int8" improves speed and reduces RAM on CPU
MODEL_SIZE = "small"  # options: tiny, base, small, medium, large
MODEL_DEVICE = "cpu"
MODEL_COMPUTE_TYPE = "int8"

# Model will be cached in the HF cache directory automatically
# Loading may take a few seconds the first time.
model = WhisperModel(MODEL_SIZE, device=MODEL_DEVICE, compute_type=MODEL_COMPUTE_TYPE)

def transcribe_file(path: str, language: str = None, task: str = "transcribe"):
    """
    Transcribe audio at `path`. Returns full text (string).
    language: None (auto) or "en", "hi", etc.
    task: "transcribe" or "translate"
    """
    segments, info = model.transcribe(path, language=language, task=task)
    # segments is an iterator/generator of segments; join them
    text_parts = []
    for seg in segments:
        # seg has attributes: start, end, text
        text_parts.append(seg.text)
    return " ".join(text_parts)
