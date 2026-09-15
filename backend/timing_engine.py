import re
from pathlib import Path
_model = None

def _norm(s): return re.sub(r"[^\w\u0900-\u097F]+", "", s.lower(), flags=re.UNICODE)
def _lines(lyrics): return [x.strip() for x in lyrics.splitlines() if x.strip() and not re.fullmatch(r"\s*\[[^\]]+\]\s*", x)]
def estimate_timing(lyrics, duration, intro=0.0, outro=0.0):
    lines=_lines(lyrics); usable=max(1.0,duration-intro-outro); weights=[max(1,len(re.findall(r"\S+",x))) for x in lines]; total=sum(weights) or 1; cur=intro; out=[]
    for i,(text,w) in enumerate(zip(lines,weights)):
        end=duration-outro if i==len(lines)-1 else cur+usable*w/total; out.append({"text":text,"start":round(cur,3),"end":round(end,3),"source":"estimated"}); cur=end
    return out

def _load_model(model_size="small"):
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        import torch
        device="cuda" if torch.cuda.is_available() else "cpu"; compute="float16" if device=="cuda" else "int8"
        _model=WhisperModel(model_size,device=device,compute_type=compute)
    return _model

def transcribe(audio_path: Path, model_size="small", language=None):
    if not audio_path.is_file(): raise ValueError("Vocal audio not found.")
    model=_load_model(model_size); segments,info=model.transcribe(str(audio_path),language=language or None,word_timestamps=True,vad_filter=True); rows=[]
    for seg in segments:
        words=[{"text":w.word.strip(),"start":round(w.start,3),"end":round(w.end,3)} for w in (seg.words or [])]
        if seg.text.strip(): rows.append({"text":seg.text.strip(),"start":round(seg.start,3),"end":round(seg.end,3),"words":words})
    return rows,getattr(info,"language",language or "auto")

def match_lyrics(lyrics, transcript, duration, intro=0.0, outro=0.0):
    lines=_lines(lyrics); used=set(); matched=[]
    for line in lines:
        target=_norm(line); best=None; score=0
        for i,seg in enumerate(transcript):
            if i in used: continue
            src=_norm(seg["text"]); common=len(set(target)&set(src)); ratio=common/max(1,len(set(target)))
            if target and (target in src or src in target): ratio+=0.8
            if ratio>score: score=ratio; best=i
        if best is not None and score>=0.25:
            seg=transcript[best]; used.add(best); matched.append({"text":line,"start":seg["start"],"end":seg["end"],"source":"asr","confidence":round(min(1,score),3),"words":seg.get("words",[])})
        else: matched.append({"text":line,"start":None,"end":None,"source":"unmatched"})
    est=estimate_timing(lyrics,duration,intro,outro)
    for i,row in enumerate(matched):
        if row["start"] is None: row.update(start=est[i]["start"],end=est[i]["end"],source="estimated")
    return matched

def time_lyrics(audio_path: Path, lyrics, duration, model_size="small", language=None, intro=0.0, outro=0.0):
    transcript,detected=transcribe(audio_path,model_size,language); rows=match_lyrics(lyrics,transcript,duration,intro,outro)
    return {"segments":rows,"transcript":transcript,"language":detected,"method":"faster-whisper ASR + lyric matching","asr_lines":sum(x["source"]=="asr" for x in rows),"estimated_count":sum(x["source"]=="estimated" for x in rows)}
