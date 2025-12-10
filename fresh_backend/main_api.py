# main_api.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os, uuid, asyncio

from summarize import summarize_text
from utils import generate_docx_from_minutes
from transcribe_fw import transcribe_file  # <-- faster-whisper

app = FastAPI(title="MoM-fresh-backend")

# ------------------- CORS -------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- Paths -------------------
BASE_UPLOAD = "uploads"
BASE_OUTPUT = "outputs"
os.makedirs(BASE_UPLOAD, exist_ok=True)
os.makedirs(BASE_OUTPUT, exist_ok=True)

# ------------------- Health Check -------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "fresh backend running"}

# ------------------- TRANSCRIBE (faster-whisper) -------------------
@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...), language: str = "en"):
    """
    Accepts audio file -> returns transcript using faster-whisper.
    """
    uid = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".wav"
    in_path = os.path.join(BASE_UPLOAD, uid + ext)

    # Save uploaded audio
    with open(in_path, "wb") as f:
        f.write(await file.read())

    # Run faster-whisper in thread (avoids blocking)
    loop = asyncio.get_event_loop()
    try:
        transcript = await loop.run_in_executor(
            None, transcribe_file, in_path, language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"transcription error: {e}")

    return {"transcript": transcript, "filename": file.filename}

# ------------------- SUMMARIZE -------------------
@app.post("/summarize")
async def summarize_endpoint(payload: dict):
    text = payload.get("text", "")
    num_sentences = int(payload.get("num_sentences", 6))

    if not text.strip():
        raise HTTPException(status_code=400, detail="text required")

    summary, minutes_struct = summarize_text(text, num_sentences=num_sentences)
    return {"summary": summary, "minutes": minutes_struct}

# ------------------- EXPORT DOCX -------------------
@app.post("/docx")
async def docx_endpoint(payload: dict):
    title = payload.get("title", "Meeting Minutes")
    summary = payload.get("summary", "")
    minutes = payload.get("minutes", {})

    uid = str(uuid.uuid4())
    out_path = os.path.join(BASE_OUTPUT, f"{uid}.docx")

    try:
        generate_docx_from_minutes(out_path, title, summary, minutes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"docx error: {e}")

    return {"download": f"/download/{uid}.docx"}

# ------------------- DOWNLOAD FILE -------------------
@app.get("/download/{fname}")
def download_file(fname: str):
    path = os.path.join(BASE_OUTPUT, fname)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=fname
    )

