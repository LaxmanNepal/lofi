"""Local AI YouTube SEO pack generator for Laxman Lofi."""
import json
import re
from lyric_engine import _load_model, MODEL_ID


def build_seo(title: str, story: str, lyrics: str, mood: str, language: str) -> dict:
    tokenizer, model = _load_model()
    prompt = f'''You are a YouTube SEO editor for Laxman Lofi, an original Nepali lo-fi music channel.
Create metadata for ONE original song. Do not claim awards, facts, collaborations, artist names, or events that are not provided.
Do not imitate any artist or existing song. Keep titles natural and searchable, not keyword spam.
Language: {language}
Mood: {mood}
Title: {title}
Story: {story[:1800]}
Lyrics: {lyrics[:5000]}

Return ONLY JSON with exactly these keys:
{{
 "youtube_title":"one compelling title under 90 characters",
 "description":"YouTube description with a short hook, song context, original-music note, and relevant hashtags",
 "tags":["15 to 25 relevant search tags"],
 "hashtags":["5 to 8 hashtags"],
 "short_description":"one sentence for social sharing"
}}'''
    messages=[
        {"role":"system","content":"You create factual, clean YouTube metadata. Output only valid JSON."},
        {"role":"user","content":prompt},
    ]
    inputs=tokenizer.apply_chat_template(messages,add_generation_prompt=True,tokenize=True,return_tensors="pt",return_dict=True).to(model.device)
    import torch
    with torch.inference_mode():
        outputs=model.generate(**inputs,max_new_tokens=900,temperature=0.7,top_p=0.9,do_sample=True,repetition_penalty=1.08)
    raw=tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:],skip_special_tokens=True).strip()
    match=re.search(r"\{.*\}",raw,re.S)
    if not match: raise RuntimeError("SEO model returned invalid JSON. Try again.")
    data=json.loads(match.group(0))
    return {
      "status":"success","model":MODEL_ID,
      "youtube_title":str(data.get("youtube_title",title)).strip()[:100],
      "description":str(data.get("description","")).strip(),
      "tags":[str(x).strip() for x in data.get("tags",[]) if str(x).strip()][:25],
      "hashtags":[str(x).strip() for x in data.get("hashtags",[]) if str(x).strip()][:10],
      "short_description":str(data.get("short_description","")).strip(),
      "note":"AI-generated SEO draft. Verify claims, links, and keywords before publishing."
    }
