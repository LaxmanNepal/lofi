"""V4.5 groove and humanization analysis for Laxman Lofi.

Deterministic DSP only: analyzes the existing beat grid and applies subtle,
beat-synchronous gain timing to existing stems. It does not synthesize drums,
instruments, voices, or new musical notes.
"""
from __future__ import annotations
import math
import subprocess
import wave
from pathlib import Path


def _duration(p: Path) -> float:
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))


def _grid(duration, bpm, first=0.0):
    beat = 60.0 / max(1.0, float(bpm))
    first = _clamp(first, 0, duration)
    beats=[]; t=first
    while t <= duration + 1e-6:
        beats.append(round(t,4)); t += beat
    return beat, beats


def groove_profile(name: str):
    profiles={
        "lofi":{"swing":0.10,"human":0.10,"drum":0.06,"bass":0.035,"melody":0.025},
        "chill":{"swing":0.06,"human":0.07,"drum":0.045,"bass":0.025,"melody":0.02},
        "boom-bap":{"swing":0.18,"human":0.14,"drum":0.09,"bass":0.05,"melody":0.03},
        "cinematic":{"swing":0.025,"human":0.04,"drum":0.035,"bass":0.03,"melody":0.04},
    }
    return profiles.get(str(name).lower(), profiles["lofi"])


def build_groove_map(duration, bpm, first=0.0, profile="lofi", amount=1.0, seed=42):
    beat, beats = _grid(duration,bpm,first); p=groove_profile(profile); amount=_clamp(amount,0,1.5)
    bars=[]
    for i,t in enumerate(beats):
        pos=i%4
        # deterministic pseudo-random humanization, bounded and repeatable.
        x=math.sin((i+1)*(seed%997+17))*43758.5453
        rnd=(x-math.floor(x))*2-1
        swing=(p["swing"]*amount) if pos in (1,3) else 0
        timing=rnd*p["human"]*amount*0.08
        velocity=rnd*0.035*amount
        bars.append({"beat":i+1,"bar":i//4+1,"position":pos+1,"time":round(max(0,t+timing+swing*beat*0.22),4),"timing_offset":round(timing+swing*beat*0.22,4),"velocity":round(velocity,4)})
    return {"bpm":round(float(bpm),2),"beat_seconds":round(beat,4),"first_beat":round(float(first),4),"beats":bars,"bar_count":math.ceil(len(beats)/4),"profile":profile,"amount":amount}


def analyze_groove(duration,bpm,first=0.0,profile="lofi",amount=1.0,seed=42):
    g=build_groove_map(duration,bpm,first,profile,amount,seed)
    return {**g,"method":"deterministic beat-grid groove heuristic","note":"Timing and gain offsets are subtle, repeatable DSP automation applied to existing audio; they are not true MIDI velocity or note-level transcription."}


def _expr(beats, beat, duration, stem, amount, profile):
    p=groove_profile(profile); expr="1"
    # Short gain accents around each beat. This creates humanized pulse without adding notes.
    strength=p[stem]*_clamp(amount,0,1.5)
    for i in range(len(beats)-1,-1,-1):
        t=float(beats[i]); pos=i%4; width=min(beat*.22,0.14)
        sign=1 if pos in (0,2) else -0.45
        g=1+strength*sign
        expr=f"if(between(t,{t:.4f},{min(duration,t+width):.4f}),{g:.5f},{expr})"
    return expr


def build_groove_arrangement(stems,wav_out,mp3_out,bpm,first_beat,profile="lofi",amount=1.0,ducking=.12,target_lufs=-14,true_peak=-1):
    required=("vocals","drums","bass","other")
    stems={k:Path(v) for k,v in stems.items()}
    if any(not stems.get(k) or not stems[k].is_file() for k in required): raise ValueError("Prepare all four Demucs stems first.")
    duration=min(_duration(stems[k]) for k in required); beat,beats=_grid(duration,bpm,first_beat)
    de=_expr(beats,beat,duration,"drum",amount,profile); be=_expr(beats,beat,duration,"bass",amount,profile); oe=_expr(beats,beat,duration,"melody",amount,profile)
    duck=_clamp(ducking,0,.8); ratio=1+duck*5; threshold=-24+duck*10
    fc=(f"[0:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=stereo[v];"
        f"[1:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{de}',aformat=sample_rates=44100:channel_layouts=stereo[d];"
        f"[2:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{be}',aformat=sample_rates=44100:channel_layouts=stereo[b];"
        f"[3:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{oe}',aformat=sample_rates=44100:channel_layouts=stereo[o];"
        f"[d][b][o]amix=inputs=3:duration=longest:normalize=0[inst];[inst][v]sidechaincompress=threshold={threshold:.2f}dB:ratio={ratio:.2f}:attack=18:release=160:makeup=1:mix=1[ducked];[v][ducked]amix=inputs=2:duration=longest:normalize=0,loudnorm=I={float(target_lufs):.2f}:TP={float(true_peak):.2f}:LRA=11,aresample=44100[a]")
    wav_out.parent.mkdir(parents=True,exist_ok=True); mp3_out.parent.mkdir(parents=True,exist_ok=True)
    try:
        subprocess.run(["ffmpeg","-y","-i",str(stems["vocals"]),"-i",str(stems["drums"]),"-i",str(stems["bass"]),"-i",str(stems["other"]),"-filter_complex",fc,"-map","[a]","-ar","44100","-ac","2","-c:a","pcm_s24le",str(wav_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        subprocess.run(["ffmpeg","-y","-i",str(wav_out),"-ar","44100","-ac","2","-c:a","libmp3lame","-b:a","320k",str(mp3_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    except FileNotFoundError as exc: raise RuntimeError("FFmpeg is not installed in the runtime.") from exc
    except subprocess.CalledProcessError as exc:
        detail=exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown FFmpeg error"; raise RuntimeError(f"V4.5 groove render failed: {detail}") from exc
    return {"duration":round(duration,3),"bpm":round(float(bpm),2),"beat_seconds":round(beat,4),"first_beat":round(float(first_beat),4),"profile":profile,"amount":amount,"beats":len(beats),"bar_count":math.ceil(len(beats)/4),"method":"existing Demucs four stems + deterministic groove/humanization gain automation","note":"V4.5 humanization changes timing-adjacent gain accents on existing audio only; it does not synthesize new notes or instruments."}
