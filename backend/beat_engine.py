"""V4.3 beat and tempo intelligence for Laxman Lofi.

Lightweight, dependency-free analysis of generated WAV audio. It estimates BPM
from a smoothed RMS/onset envelope, snaps reviewed section boundaries to the
estimated beat grid, and returns rhythm-aware transition metadata. It does not
claim symbolic beat/downbeat transcription.
"""
from __future__ import annotations
import math
import struct
import wave
from pathlib import Path


def _mono_samples(path: Path, target_rate: int = 8000):
    with wave.open(str(path), "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = w.readframes(w.getnframes())
    if width == 2:
        vals = struct.unpack("<" + "h" * (len(frames) // 2), frames); scale = 32768.0
    elif width == 4:
        vals = struct.unpack("<" + "i" * (len(frames) // 4), frames); scale = 2147483648.0
    else:
        vals = tuple(x - 128 for x in frames); scale = 128.0
    mono = [sum(vals[i:i + channels]) / max(1, channels) / scale for i in range(0, len(vals), channels)]
    step = max(1, round(rate / target_rate))
    return mono[::step], rate / step


def _energy_envelope(samples, rate, hop=0.02):
    size = max(1, int(rate * hop)); out=[]
    for i in range(0, len(samples), size):
        chunk=samples[i:i+size]
        if chunk: out.append(math.sqrt(sum(x*x for x in chunk)/len(chunk)))
    return out, hop


def estimate_bpm(path: Path) -> dict:
    if not path.is_file(): raise ValueError("Source audio not found.")
    samples, rate = _mono_samples(path)
    if len(samples) < int(rate * 8): raise ValueError("Audio is too short for beat analysis.")
    env, hop = _energy_envelope(samples, rate)
    sm=[sum(env[max(0,i-5):i+1])/len(env[max(0,i-5):i+1]) for i in range(len(env))]
    onset=[max(0.0, sm[i]-sm[i-3]) for i in range(3,len(sm))]
    best=(90,0.0)
    for bpm in range(55,151):
        lag=max(1,round(60.0/bpm/hop)); score=0.0; count=0
        for i in range(lag,len(onset),max(1,lag//2)):
            score += onset[i]*onset[i-lag]; count += 1
        score /= max(1,count)
        if 65 <= bpm <= 95: score *= 1.03
        if score > best[1]: best=(bpm,score)
    bpm=float(best[0]); beat=60.0/bpm; duration=len(samples)/rate
    first=max(0.0,min(2.0,duration-beat))
    return {"bpm":round(bpm,2),"beat_seconds":round(beat,4),"estimated_first_beat":round(first,3),"duration":round(duration,3),"method":"RMS onset-envelope tempo heuristic","confidence":round(min(1.0,max(0.0,best[1]*100)),3),"note":"BPM is an audio-derived estimate; downbeats and meter are not guaranteed."}


def snap_time(t: float, beat_seconds: float, origin: float = 0.0) -> float:
    return float(t) if beat_seconds <= 0 else origin + round((float(t)-origin)/beat_seconds)*beat_seconds


def beat_grid(path: Path, start: float = 0.0, count: int = 0) -> dict:
    info=estimate_bpm(path); beat=info["beat_seconds"]; duration=info["duration"]
    n=count or int(max(0,(duration-start)/beat))+1
    beats=[round(start+i*beat,3) for i in range(n) if start+i*beat <= duration]
    return {**info,"beats":beats,"bar_starts":[beats[i] for i in range(0,len(beats),4)],"beats_per_bar":4}


def snap_sections(sections: list[dict], beat_seconds: float, duration: float, origin: float = 0.0) -> list[dict]:
    out=[]
    for sec in sections or []:
        s=max(0,min(duration,snap_time(sec.get("start",0),beat_seconds,origin))); e=max(s,min(duration,snap_time(sec.get("end",duration),beat_seconds,origin)))
        if e-s < max(beat_seconds*0.5,0.1): e=min(duration,s+beat_seconds)
        out.append({**sec,"start":round(s,3),"end":round(e,3),"beat_aligned":True})
    return out


def analyze_beats(path: Path, sections: list[dict] | None = None) -> dict:
    info=estimate_bpm(path); grid=beat_grid(path,info["estimated_first_beat"])
    snapped=snap_sections(sections or [],info["beat_seconds"],info["duration"],info["estimated_first_beat"])
    return {**info,"beats":grid["beats"],"bar_starts":grid["bar_starts"],"beats_per_bar":4,"snapped_sections":snapped,"section_alignment":"beat/bar grid" if snapped else "not applied"}
