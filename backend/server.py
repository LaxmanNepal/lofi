import base64
import os
import random
import time
from pathlib import Path

import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from acestep.pipeline_ace_step import ACEStepPipeline
from lyric_engine import LyricRequest, compose_lyrics, unload_model

API_KEY = os.getenv("LAXMAN_LOFI_API_KEY", "")
CHECKPOINT_DIR = os.getenv("ACE_CHECKPOINT_DIR", "/content/ace-checkpoints")
DEVICE_ID = int(os.getenv("ACE_DEVICE_ID", "0"))
BF16 = os.getenv("ACE_BF16", "true").lower() == "true"

app = FastAPI(title="Laxman Lofi AI Studio API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def check_key(authorization: str | None):
    if not API_KEY:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")


def load_pipeline():
    global pipeline
    if pipeline is None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(DEVICE_ID)
        Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
        pipeline = ACEStepPipeline(
            checkpoint_dir=CHECKPOINT_DIR,
            dtype="bfloat16" if BF16 else "float32",
            torch_compile=False,
        )
    return pipeline


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "ACE-Step v1 3.5B",
        "lyric_model": os.getenv("LYRIC_MODEL_ID", "ministral/Ministral-3b-instruct"),
        "cuda": torch.cuda.is_available(),
    }


@app.post("/compose")
def compose(req: ComposeRequest, authorization: str | None = Header(default=None)):
    check_key(authorization)
    try:
        return compose_lyrics(LyricRequest(
            idea=req.idea,
            mood=req.mood,
            language=req.language,
            voice=req.voice,
            duration=req.duration,
            style=req.style,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lyric AI failed: {exc}") from exc


@app.post("/generate")
def generate(req: GenerateRequest, authorization: str | None = Header(default=None)):
    check_key(authorization)
    if req.voice_mode == "instrumental":
        lyrics = "[inst]"
    else:
        lyrics = req.lyrics.strip()
        if not lyrics:
            raise HTTPException(status_code=400, detail="Original lyrics are required for vocal generation.")

    # ACE-Step and the lyric LLM are loaded sequentially so a Colab T4 can reuse VRAM.
    unload_model()
    seed = req.seed if req.seed is not None else random.randint(1, 2_147_483_647)
    out = Path("/content/laxman_lofi_output")
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / f"lofi_{int(time.time())}_{seed}.wav"

    p = load_pipeline()
    try:
        params = (
            float(req.audio_duration), req.prompt, lyrics, 27, 7.0,
            "euler", "cfg", 1.0, str(seed), 1.0, 0.0, 1.0,
            False, False, True, "", 0.0, 0.0,
        )
        p(*params, save_path=str(output_path))
    except Exception as exc:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise HTTPException(status_code=500, detail=f"ACE-Step generation failed: {exc}") from exc

    audio_bytes = output_path.read_bytes()
    return {
        "status": "success",
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
        "mime_type": "audio/wav",
        "seed": seed,
        "duration": req.audio_duration,
        "model": "ACE-Step v1 3.5B",
    }
