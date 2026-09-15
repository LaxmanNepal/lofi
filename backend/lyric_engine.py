"""AI lyric composer for Laxman Lofi.

Uses a user-controlled Hugging Face Transformers model. No paid API is required.
The default model is Apache-2.0 licensed; generated lyrics are still drafts and
must be reviewed for originality before publication.
"""

import gc
import json
import os
import re
from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = os.getenv("LYRIC_MODEL_ID", "ministral/Ministral-3b-instruct")
USE_4BIT = os.getenv("LYRIC_4BIT", "true").lower() == "true"

_tokenizer = None
_model = None


@dataclass
class LyricRequest:
    idea: str
    mood: str = "emotional"
    language: str = "Nepali"
    voice: str = "male"
    duration: int = 180
    style: str = "warm piano, mellow guitar, dusty vinyl texture"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _load_model():
    global _tokenizer, _model
    if _model is not None:
        return _tokenizer, _model

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    kwargs = {"device_map": "auto"}
    if USE_4BIT and torch.cuda.is_available():
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    else:
        kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32
    _model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
    return _tokenizer, _model


def unload_model():
    global _tokenizer, _model
    _model = None
    _tokenizer = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _prompt(req: LyricRequest) -> str:
    lang_rule = {
        "Nepali": "Write natural modern Nepali in Devanagari. Do not translate English line-by-line.",
        "English": "Write natural contemporary English.",
        "Hinglish": "Write a natural Nepali-English mix using Roman script.",
    }.get(req.language, "Write naturally in the requested language.")
    return f"""You are the original songwriting writer for Laxman Lofi.
Create a completely original emotional lo-fi song from the user's story.
Never imitate or mention a specific artist, existing song, or copyrighted lyric.
Avoid clichés and repeated generic lines. Use concrete scenes, sensory details,
and a memorable but original chorus. Do not explain your process.

Language: {req.language}. {lang_rule}
Mood: {req.mood}
Vocal: {req.voice}
Approximate song duration: {req.duration} seconds
Production: {req.style}
Story: {req.idea}

Return ONLY valid JSON with exactly these keys:
{{
  "title": "short searchable song title",
  "lyrics": "[verse]\n...\n\n[pre-chorus]\n...\n\n[chorus]\n...\n\n[verse]\n...\n\n[bridge]\n...\n\n[chorus]\n...",
  "music_prompt": "a concise production prompt for ACE-Step"
}}
"""


def compose_lyrics(req: LyricRequest) -> dict:
    idea = _clean(req.idea)
    if not idea:
        raise ValueError("A song idea is required.")
    if len(idea) > 1000:
        raise ValueError("Song idea must be 1000 characters or fewer.")

    tokenizer, model = _load_model()
    messages = [
        {"role": "system", "content": "You write original songs. Output only the requested JSON."},
        {"role": "user", "content": _prompt(req)},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True,
        return_tensors="pt", return_dict=True,
    ).to(model.device)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1200,
            temperature=0.9,
            top_p=0.92,
            do_sample=True,
            repetition_penalty=1.12,
        )
    raw = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        raise RuntimeError("Lyric model returned invalid JSON. Try generating again.")
    data = json.loads(match.group(0))
    lyrics = str(data.get("lyrics", "")).strip()
    if not lyrics:
        raise RuntimeError("Lyric model returned empty lyrics.")
    return {
        "status": "success",
        "title": str(data.get("title", "Untitled Lofi")).strip(),
        "lyrics": lyrics,
        "music_prompt": str(data.get("music_prompt", req.style)).strip(),
        "model": MODEL_ID,
        "originality_note": "AI-generated draft. Review the lyrics and audio for originality before publishing.",
    }
