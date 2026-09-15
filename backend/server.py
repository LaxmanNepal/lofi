import base64
import os
import random
import re
import time
from pathlib import Path

import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from acestep.pipeline_ace_step import ACEStepPipeline
from audio_engine import export_mp3, master_audio
from lyric_engine import LyricRequest, compose_lyrics, unload_model

API_KEY = os.getenv("LAXMAN_LOFI_API_KEY", "")
CHECKPOINT_DIR = os.getenv("ACE_CHECKPOINT_DIR", "/content/ace-checkpoints")
DEVICE_ID = int(os.getenv("ACE_DEVICE_ID", "0"))
BF16 = os.getenv("ACE_BF16", "true").lower() == "true"
OUTPUT_DIR = Path(os.getenv("LAXMAN_LOFI_OUTPUT_DIR", "/content/laxman_lofi_output"))

app = FastAPI(title="Laxman Lofi AI Studio API", version="1.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
pipeline = None

class ComposeRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=1000)
    mood: str = Field(default="emotional", max_length=50)
    language: str = Field(default="Nepali", max_length=30)
    voice: str = Field(default="male", max_length=20)
    duration: int = Field(default=180, ge=30, le=300)
    style: str = Field(default="warm piano, mellow guitar, dusty vinyl texture", max_length=500)

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=3000)
    lyrics: str = ""
    audio_duration: float = Field(default=180, ge=10, le=300)
    duration: float = Field(default=180, ge=10, le=300)
    voice_mode: str = "male"
    language: str = "nepali"
    seed: int | None = None

class MasterRequest(BaseModel):
    output_id: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    duration: float = Field(default=180, ge=10, le=300)
    fade_in: float = Field(default=2, ge=0, le=10)
    fade_out: float = Field(default=3, ge=0, le=10)

def check_key(authorization: str | None):
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")

def load_pipeline():
    global pipeline
    if pipeline is None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(DEVICE_ID)
        Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
        pipeline = ACEStepPipeline(checkpoint_dir=CHECKPOINT_DIR, dtype="bfloat16" if BF16 else "float32", torch_compile=False)
    return pipeline

def source_path(output_id: str) -> Path:
    return OUTPUT_DIR / f"{output_id}.wav"

def master_paths(output_id: str) -> tuple[Path, Path]:
    return OUTPUT_DIR / f"{output_id}_master.wav", OUTPUT_DIR / f"{output_id}_master.mp3"

@app.get("/health")
def health():
    return {"status": "healthy", "model": "ACE-Step v1 3.5B", "lyric_model": os.getenv("LYRIC_MODEL_ID", "ministral/Ministral-3b-instruct"), "cuda": torch.cuda.is_available(), "audio_mastering": "ffmpeg"}

@app.post("/compose")
def compose(req: ComposeRequest, authorization: str | None = Header(default=None)):
    check_key(authorization)
    try:
        return compose_lyrics(LyricRequest(idea=req.idea, mood=req.mood, language=req.language, voice=req.voice, duration=req.duration, style=req.style))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lyric AI failed: {exc}") from exc

@app.post("/generate")
def generate(req: GenerateRequest, authorization: str | None = Header(default=None)):
    check_key(authorization)
    lyrics = "[inst]" if req.voice_mode == "instrumental" else req.lyrics.strip()
    if req.voice_mode != "instrumental" and not lyrics:
        raise HTTPException(status_code=400, detail="Original lyrics are required for vocal generation.")
    unload_model()
    seed = req.seed if req.seed is not None else random.randint(1, 2_147_483_647)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_id = f"lofi_{int(time.time())}_{seed}_{random.randint(1000, 9999)}"
    output_path = source_path(output_id)
    p = load_pipeline()
    try:
        params = (float(req.audio_duration), req.prompt, lyrics, 27, 7.0, "euler", "cfg", 1.0, str(seed), 1.0, 0.0, 1.0, False, False, True, "", 0.0, 0.0)
        p(*params, save_path=str(output_path))
    except Exception as exc:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=f"ACE-Step generation failed: {exc}") from exc
    audio_bytes = output_path.read_bytes()
    return {"status": "success", "audio_base64": base64.b64encode(audio_bytes).decode("ascii"), "mime_type": "audio/wav", "seed": seed, "duration": req.audio_duration, "model": "ACE-Step v1 3.5B", "output_id": output_id}

@app.get("/audio/{file_name}")
def audio(file_name: str, authorization: str | None = Header(default=None)):
    check_key(authorization)
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:wav|mp3)", file_name):
        raise HTTPException(status_code=400, detail="Invalid audio filename")
    path = OUTPUT_DIR / file_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found. The Colab runtime may have expired.")
    media = "audio/mpeg" if path.suffix.lower() == ".mp3" else "audio/wav"
    return FileResponse(path, media_type=media, filename=path.name)

@app.post("/master")
def master(req: MasterRequest, authorization: str | None = Header(default=None)):
    check_key(authorization)
    source = source_path(req.output_id)
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Source audio not found. Generate the song again if the runtime expired.")
    master_wav, master_mp3 = master_paths(req.output_id)
    try:
        master_audio(source, master_wav, req.duration, req.fade_in, req.fade_out)
        export_mp3(master_wav, master_mp3)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    wav_bytes = master_wav.read_bytes()
    mp3_bytes = master_mp3.read_bytes()
    return {
        "status": "success",
        "output_id": req.output_id,
        "wav_base64": base64.b64encode(wav_bytes).decode("ascii"),
        "mp3_base64": base64.b64encode(mp3_bytes).decode("ascii"),
        "wav_mime_type": "audio/wav",
        "mp3_mime_type": "audio/mpeg",
        "target": "approximately -14 LUFS / -1 dBTP",
        "sample_rate": 44100,
        "wav_bit_depth": 24,
        "mp3_bitrate": "320 kbps",
        "fade_in": req.fade_in,
        "fade_out": req.fade_out,
    }
