"""V4.2 instrument-stem intelligence for Laxman Lofi.

Uses full Demucs separation to expose vocals, drums, bass and other. Energy is
measured from the real separated stems; arrangement is deterministic FFmpeg
DSP. No symbolic transcription or new instrument synthesis is claimed.
"""
from __future__ import annotations
import math
import shutil
import subprocess
import wave
from pathlib import Path


def _demucs_bin() -> str:
    return shutil.which("demucs") or "demucs"


def _duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def separate_instrument_stems(input_path: Path, output_dir: Path, model: str = "htdemucs") -> dict[str, Path]:
    if not input_path.is_file():
        raise ValueError("Source audio not found. Generate the song again if the runtime expired.")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [_demucs_bin(), "-n", model, "-o", str(output_dir), str(input_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Demucs is not installed. Re-run the Colab setup cell to install stem separation.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown Demucs error"
        raise RuntimeError(f"4-stem separation failed: {detail}") from exc
    found = {}
    for name in ("vocals", "drums", "bass", "other"):
        matches = list(output_dir.rglob(f"{name}.wav"))
        if matches:
            found[name] = matches[-1]
    missing = [x for x in ("vocals", "drums", "bass", "other") if x not in found]
    if missing:
        raise RuntimeError(f"Demucs completed but missing stems: {', '.join(missing)}")
    return found


def _rms_windows(path: Path, window: float = 4.0) -> list[dict]:
    with wave.open(str(path), "rb") as w:
        channels, rate, width = w.getnchannels(), w.getframerate(), w.getsampwidth()
        frames_per = max(1, int(rate * window)); out=[]; index=0; max_amp=32768.0 if width==2 else 2147483648.0
        while True:
            raw=w.readframes(frames_per)
            if not raw: break
            if width==2:
                import array,sys
                vals=array.array("h"); vals.frombytes(raw)
                if sys.byteorder!="little": vals.byteswap()
            elif width==4:
                import array,sys
                vals=array.array("i"); vals.frombytes(raw)
                if sys.byteorder!="little": vals.byteswap()
            else:
                vals=[x-128 for x in raw]; max_amp=128.0
            rms=math.sqrt(sum(float(x)*float(x) for x in vals)/max(1,len(vals)))/max_amp
            start=index*window; out.append({"start":round(start,3),"end":round(min(_duration(path),start+window),3),"energy_db":round(20*math.log10(max(rms,1e-7)),2)})
            index+=1
    return out


def _section_windows(windows: list[dict], sections: list[dict]) -> list[dict]:
    out=[]
    for sec in sections:
        vals=[x["energy_db"] for x in windows if x["start"] < sec["end"] and x["end"] > sec["start"]]
        avg=sum(vals)/len(vals) if vals else -60.0
        peak=max(vals) if vals else -60.0
        out.append({"label":sec.get("label","section"),"start":round(float(sec.get("start",0)),3),"end":round(float(sec.get("end",0)),3),"energy_db":round(avg,2),"peak_db":round(peak,2)})
    return out


def analyze_instrument_stems(stems: dict[str, Path], structure: list[dict] | None = None, window: float = 4.0) -> dict:
    required=("vocals","drums","bass","other")
    if any(not stems.get(k) or not stems[k].is_file() for k in required):
        raise ValueError("Prepare all four Demucs stems first.")
    duration=min(_duration(stems[k]) for k in required)
    raw={k:_rms_windows(stems[k],window) for k in required}
    sections=structure or [{"label":"full","start":0,"end":duration}]
    section_data={k:_section_windows(raw[k],sections) for k in ("drums","bass","other")}
    return {"duration":round(duration,3),"drums_windows":raw["drums"],"bass_windows":raw["bass"],"other_windows":raw["other"],"sections":sections,"section_energy":section_data,"method":"full Demucs 4-stem separation + PCM RMS analysis","note":"Drums, bass and other/melodic energy come from real Demucs stems. Melodic density is represented by other-stem energy; this is not symbolic music transcription."}


def _clamp(v,lo,hi): return max(lo,min(hi,float(v)))

def _gain_expr(sections,key,duration):
    expr="1"
    for sec in reversed(sections):
        s=_clamp(sec.get("start",0),0,duration); e=_clamp(sec.get("end",duration),s,duration); g=_clamp(sec.get(key,1),0,2)
        expr=f"if(between(t,{s:.3f},{e:.3f}),{g:.6f},{expr})"
    return expr

def _width_filter(width):
    w=_clamp(width,0,1.5); a=(1+w)/2; b=(1-w)/2
    return f"pan=stereo|c0={a:.6f}*c0+{b:.6f}*c1|c1={b:.6f}*c0+{a:.6f}*c1"

def build_instrument_arrangement(stems,wav_out,mp3_out,structure,drum_level=1.0,bass_level=1.0,other_level=1.0,chorus_drum_lift=.10,chorus_bass_lift=.08,chorus_other_lift=.10,bridge_reduction=.12,intro_reduction=.22,outro_reduction=.25,stereo_width=1.05,ducking=.18,target_lufs=-14.0,true_peak=-1.0):
    required=("vocals","drums","bass","other")
    if any(not stems.get(k) or not stems[k].is_file() for k in required): raise ValueError("Prepare all four Demucs stems first.")
    duration=min(_duration(stems[k]) for k in required); sections=[]
    for raw in structure or [{"label":"full","start":0,"end":duration}]:
        s=_clamp(raw.get("start",0),0,duration); e=_clamp(raw.get("end",duration),s,duration)
        if e<=s: continue
        label=str(raw.get("label","verse")).lower().strip(); dg=drum_level; bg=bass_level; og=other_level
        if label in {"chorus","final chorus"}: dg*=1+_clamp(chorus_drum_lift,0,.30); bg*=1+_clamp(chorus_bass_lift,0,.30); og*=1+_clamp(chorus_other_lift,0,.30)
        if label=="bridge": dg*=1-_clamp(bridge_reduction,0,.60); bg*=1-_clamp(bridge_reduction,0,.60); og*=1-_clamp(bridge_reduction,0,.60)
        if label=="intro": dg*=1-_clamp(intro_reduction,0,.80); bg*=1-_clamp(intro_reduction,0,.80); og*=1-_clamp(intro_reduction,0,.80)
        if label=="outro": dg*=1-_clamp(outro_reduction,0,.80); bg*=1-_clamp(outro_reduction,0,.80); og*=1-_clamp(outro_reduction,0,.80)
        sections.append({"label":label,"start":s,"end":e,"drum_gain":dg,"bass_gain":bg,"other_gain":og})
    if not sections: sections=[{"label":"full","start":0,"end":duration,"drum_gain":drum_level,"bass_gain":bass_level,"other_gain":other_level}]
    de=_gain_expr(sections,"drum_gain",duration); be=_gain_expr(sections,"bass_gain",duration); oe=_gain_expr(sections,"other_gain",duration)
    duck=_clamp(ducking,0,.80); ratio=1+duck*5; threshold=-24+duck*10
    fc=(f"[0:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=stereo[v];" f"[1:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{de}',aformat=sample_rates=44100:channel_layouts=stereo[d];" f"[2:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{be}',aformat=sample_rates=44100:channel_layouts=stereo[b];" f"[3:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{oe}',{_width_filter(stereo_width)},aformat=sample_rates=44100:channel_layouts=stereo[o];" f"[d][b][o]amix=inputs=3:duration=longest:normalize=0[inst];[inst][v]sidechaincompress=threshold={threshold:.2f}dB:ratio={ratio:.2f}:attack=20:release=180:makeup=1:mix=1[ducked];[v][ducked]amix=inputs=2:duration=longest:normalize=0,loudnorm=I={target_lufs:.2f}:TP={true_peak:.2f}:LRA=11,aresample=44100[a]")
    wav_out.parent.mkdir(parents=True,exist_ok=True); mp3_out.parent.mkdir(parents=True,exist_ok=True)
    try:
        subprocess.run(["ffmpeg","-y","-i",str(stems["vocals"]),"-i",str(stems["drums"]),"-i",str(stems["bass"]),"-i",str(stems["other"]),"-filter_complex",fc,"-map","[a]","-ar","44100","-ac","2","-c:a","pcm_s24le",str(wav_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        subprocess.run(["ffmpeg","-y","-i",str(wav_out),"-ar","44100","-ac","2","-c:a","libmp3lame","-b:a","320k",str(mp3_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    except FileNotFoundError as exc: raise RuntimeError("FFmpeg is not installed in the runtime.") from exc
    except subprocess.CalledProcessError as exc:
        detail=exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown FFmpeg error"; raise RuntimeError(f"V4.2 instrument arrangement render failed: {detail}") from exc
    return {"duration":round(duration,3),"sections":sections,"controls":{"drum_level":drum_level,"bass_level":bass_level,"other_level":other_level,"chorus_drum_lift":chorus_drum_lift,"chorus_bass_lift":chorus_bass_lift,"chorus_other_lift":chorus_other_lift,"bridge_reduction":bridge_reduction,"intro_reduction":intro_reduction,"outro_reduction":outro_reduction,"stereo_width":stereo_width,"ducking":ducking,"target_lufs":target_lufs,"true_peak":true_peak},"method":"Demucs vocals/drums/bass/other + FFmpeg section automation + sidechain compression","note":"V4.2 uses actual four-stem separation. Other-stem energy is a practical melodic-density proxy; no new instruments or voices are synthesized."}
