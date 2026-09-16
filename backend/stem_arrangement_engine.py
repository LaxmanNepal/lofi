"""Stem-aware section arrangement for Laxman Lofi.

Uses the existing Demucs vocal/instrumental WAV stems and deterministic
Python/FFmpeg processing. No new model is loaded and no instruments are
invented. Energy analysis is calculated from PCM samples; rendering applies
section gain, stereo-width shaping and optional vocal sidechain ducking.
"""
from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path


def _duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _energy_windows(path: Path, window: float = 4.0) -> list[dict]:
    with wave.open(str(path), "rb") as w:
        channels = w.getnchannels()
        rate = w.getframerate()
        width = w.getsampwidth()
        frames_per = max(1, int(rate * window))
        out = []
        index = 0
        while True:
            raw = w.readframes(frames_per)
            if not raw:
                break
            if width == 2:
                import array
                vals = array.array("h")
                vals.frombytes(raw)
                if vals and __import__("sys").byteorder != "little":
                    vals.byteswap()
                rms = math.sqrt(sum(float(x) * x for x in vals) / len(vals)) / 32768.0
            elif width == 4:
                import array
                vals = array.array("i")
                vals.frombytes(raw)
                if vals and __import__("sys").byteorder != "little":
                    vals.byteswap()
                rms = math.sqrt(sum(float(x) * x for x in vals) / len(vals)) / 2147483648.0
            else:
                vals = list(raw)
                rms = math.sqrt(sum(((x - 128) / 128.0) ** 2 for x in vals) / max(1, len(vals)))
            db = 20.0 * math.log10(max(rms, 1e-7))
            start = index * window
            out.append({"start": round(start, 3), "end": round(min(_duration(path), start + window), 3), "energy_db": round(db, 2)})
            index += 1
    return out


def _default_sections(duration: float, windows: list[dict]) -> list[dict]:
    if not windows:
        return [{"label": "full", "start": 0.0, "end": round(duration, 3), "energy_db": -30.0}]
    groups = max(4, min(8, round(duration / 30)))
    step = duration / groups
    sections = []
    for i in range(groups):
        s, e = i * step, duration if i == groups - 1 else (i + 1) * step
        vals = [x["energy_db"] for x in windows if x["start"] < e and x["end"] > s]
        avg = sum(vals) / len(vals) if vals else -30.0
        if i == 0:
            label = "intro"
        elif i == groups - 1:
            label = "outro"
        elif i == groups // 2 and groups >= 6:
            label = "bridge"
        elif avg >= sorted([x["energy_db"] for x in windows])[-max(1, len(windows)//3)]:
            label = "chorus"
        elif i == 1:
            label = "verse"
        else:
            label = "pre-chorus"
        sections.append({"label": label, "start": round(s, 3), "end": round(e, 3), "energy_db": round(avg, 2)})
    return sections


def analyze_stems(vocals: Path, instrumental: Path, window: float = 4.0, structure: list[dict] | None = None) -> dict:
    if not vocals.is_file() or not instrumental.is_file():
        raise ValueError("Separate vocals and instrumental stems first.")
    vd, idur = _duration(vocals), _duration(instrumental)
    duration = min(vd, idur)
    vwin = _energy_windows(vocals, window)
    iwin = _energy_windows(instrumental, window)
    sections = structure or _default_sections(duration, iwin)
    return {
        "duration": round(duration, 3),
        "vocal_windows": vwin,
        "instrumental_windows": iwin,
        "sections": sections,
        "method": "PCM RMS energy + reviewed section timeline",
        "note": "Energy is measured from the existing Demucs stems. Section labels are editable heuristics unless supplied by the reviewed V3.9 timeline.",
    }


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _gain_expr(sections: list[dict], key: str, duration: float) -> str:
    expr = "1"
    for sec in reversed(sections):
        s = _clamp(sec.get("start", 0), 0, duration)
        e = _clamp(sec.get("end", duration), s, duration)
        g = _clamp(sec.get(key, 1), 0, 2)
        expr = f"if(between(t,{s:.3f},{e:.3f}),{g:.6f},{expr})"
    return expr


def _width_filter(width: float) -> str:
    # width=1 is unchanged; >1 expands L/R, <1 narrows toward mono.
    w = _clamp(width, 0, 1.5)
    a = (1 + w) / 2
    b = (1 - w) / 2
    return f"pan=stereo|c0={a:.6f}*c0+{b:.6f}*c1|c1={b:.6f}*c0+{a:.6f}*c1"


def build_stem_arrangement(
    vocals: Path,
    instrumental: Path,
    wav_out: Path,
    mp3_out: Path,
    structure: list[dict],
    vocal_level: float = 1.0,
    instrumental_level: float = 1.0,
    chorus_vocal_lift: float = 0.08,
    chorus_instrumental_lift: float = 0.10,
    bridge_reduction: float = 0.12,
    ducking: float = 0.18,
    stereo_width: float = 1.05,
    target_lufs: float = -14.0,
    true_peak: float = -1.0,
) -> dict:
    if not vocals.is_file() or not instrumental.is_file():
        raise ValueError("Separate vocals and instrumental stems first.")
    duration = min(_duration(vocals), _duration(instrumental))
    if duration < 1:
        raise ValueError("Stem duration is too short for arrangement.")
    sections = []
    for raw in structure or _default_sections(duration, _energy_windows(instrumental)):
        s = _clamp(raw.get("start", 0), 0, duration)
        e = _clamp(raw.get("end", duration), s, duration)
        if e <= s:
            continue
        label = str(raw.get("label", "verse")).lower().strip()
        vg = vocal_level
        ig = instrumental_level
        if label in {"chorus", "final chorus"}:
            vg *= 1 + _clamp(chorus_vocal_lift, 0, .30)
            ig *= 1 + _clamp(chorus_instrumental_lift, 0, .30)
        if label == "final chorus":
            vg *= 1.03
            ig *= 1.03
        if label == "bridge":
            vg *= 1 - _clamp(bridge_reduction, 0, .60)
            ig *= 1 - _clamp(bridge_reduction, 0, .60)
        if label == "intro":
            vg *= .88
            ig *= .78
        if label == "outro":
            vg *= .84
            ig *= .72
        sections.append({"label": label, "start": s, "end": e, "vocal_gain": vg, "instrumental_gain": ig})
    if not sections:
        sections = [{"label": "full", "start": 0.0, "end": duration, "vocal_gain": vocal_level, "instrumental_gain": instrumental_level}]

    vexpr = _gain_expr(sections, "vocal_gain", duration)
    iexpr = _gain_expr(sections, "instrumental_gain", duration)
    duck = _clamp(ducking, 0, .80)
    ratio = 1.0 + duck * 5.0
    threshold = -24.0 + duck * 10.0
    width_filter = _width_filter(stereo_width)
    fc = (
        f"[0:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{vexpr}',aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[v];"
        f"[1:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume='{iexpr}',{width_filter},aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[i];"
        f"[i][v]sidechaincompress=threshold={threshold:.2f}dB:ratio={ratio:.2f}:attack=20:release=180:makeup=1:mix=1[ducked];"
        f"[v][ducked]amix=inputs=2:duration=longest:normalize=0,loudnorm=I={target_lufs:.2f}:TP={true_peak:.2f}:LRA=11[a]"
    )
    wav_out.parent.mkdir(parents=True, exist_ok=True)
    mp3_out.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["ffmpeg", "-y", "-i", str(vocals), "-i", str(instrumental), "-filter_complex", fc, "-map", "[a]", "-ar", "44100", "-ac", "2", "-c:a", "pcm_s24le", str(wav_out)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_out), "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "320k", str(mp3_out)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg is not installed in the runtime.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown FFmpeg error"
        raise RuntimeError(f"Stem arrangement render failed: {detail}") from exc
    return {
        "duration": round(duration, 3),
        "sections": sections,
        "controls": {"vocal_level": vocal_level, "instrumental_level": instrumental_level, "chorus_vocal_lift": chorus_vocal_lift, "chorus_instrumental_lift": chorus_instrumental_lift, "bridge_reduction": bridge_reduction, "ducking": ducking, "stereo_width": stereo_width, "target_lufs": target_lufs, "true_peak": true_peak},
        "method": "Demucs stems + FFmpeg section automation + sidechain compression",
        "note": "V4.1 processes the existing vocal and instrumental stems independently. It does not synthesize new instruments or voices.",
    }
