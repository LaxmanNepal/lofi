"""Deterministic FFmpeg mix/master processing for Laxman Lofi V3.6.

This is an automatic DSP engine (not a generative AI model). It combines
Demucs stems, applies optional cleanup/EQ/compression/de-essing-style
processing, stereo width, and loudness normalization, then exports WAV/MP3.
"""

import re
import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def _run(args: list[str]) -> str:
    try:
        p = subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return p.stderr
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip().splitlines()[-1] if getattr(exc, "stderr", "") else "unknown FFmpeg error"
        raise RuntimeError(f"Mix/master processing failed: {detail}") from exc


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(value)))


def build_mix_master(
    vocals: Path,
    instrumental: Path,
    output_wav: Path,
    output_mp3: Path,
    vocal_gain: float = 1.0,
    instrumental_gain: float = 1.0,
    vocal_pan: float = 0.0,
    cleanup: float = 0.35,
    warmth: float = 0.25,
    presence: float = 0.20,
    compression: float = 0.35,
    deessing: float = 0.20,
    stereo_width: float = 1.0,
    target_lufs: float = -14.0,
    true_peak: float = -1.0,
) -> dict:
    """Build a stereo vocal/instrumental mix and normalized master."""
    for p in (vocals, instrumental):
        if not p.is_file():
            raise ValueError(f"Missing stem: {p.name}. Run stem separation first.")

    vocal_gain = _clamp(vocal_gain, 0, 2)
    instrumental_gain = _clamp(instrumental_gain, 0, 2)
    vocal_pan = _clamp(vocal_pan, -1, 1)
    cleanup = _clamp(cleanup, 0, 1)
    warmth = _clamp(warmth, -1, 1)
    presence = _clamp(presence, -1, 1)
    compression = _clamp(compression, 0, 1)
    deessing = _clamp(deessing, 0, 1)
    stereo_width = _clamp(stereo_width, 0, 1.5)
    target_lufs = _clamp(target_lufs, -18, -9)
    true_peak = _clamp(true_peak, -3, -0.1)

    # Cleanup: gentle gate + high-pass. De-essing uses a dynamic high-frequency
    # compressor where available; this avoids requiring another ML dependency.
    gate_db = -48 + cleanup * 18
    ratio = 1.5 + compression * 3.5
    threshold = -28 + compression * 12
    deess_ratio = 1.0 + deessing * 5.0
    deess_threshold = -34 + deessing * 12
    low_gain = warmth * 3.0
    high_gain = presence * 3.0

    pan_left = 1.0 - vocal_pan if vocal_pan >= 0 else 1.0
    pan_right = 1.0 + vocal_pan if vocal_pan <= 0 else 1.0

    vf = [
        "highpass=f=70",
        f"agate=threshold={gate_db:g}dB:ratio=2:attack=15:release=180",
        f"equalizer=f=180:t=q:w=0.8:g={low_gain:g}",
        f"equalizer=f=3200:t=q:w=0.9:g={high_gain:g}",
        f"acompressor=threshold={threshold:g}dB:ratio={ratio:g}:attack=8:release=100:makeup=1",
        f"acompressor=frequency=6500:threshold={deess_threshold:g}dB:ratio={deess_ratio:g}:attack=2:release=80",
        f"volume={vocal_gain:g}",
        f"pan=stereo|c0={pan_left:g}*c0|c1={pan_right:g}*c1",
    ]
    inst = ["highpass=f=30", f"volume={instrumental_gain:g}"]
    # Stereo width uses a mid/side transform. 1.0 is neutral.
    width = stereo_width
    inst.append(f"stereotools=mlev=1:slev={width:g}")

    filter_complex = (
        f"[0:a]{','.join(vf)}[v];"
        f"[1:a]{','.join(inst)}[i];"
        "[v][i]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[m];"
        f"[m]loudnorm=I={target_lufs:g}:TP={true_peak:g}:LRA=11,aresample=44100,pan=stereo[mout]"
    )

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    _run([
        FFMPEG, "-y", "-i", str(vocals), "-i", str(instrumental),
        "-filter_complex", filter_complex, "-map", "[mout]",
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s24le", str(output_wav),
    ])
    _run([
        FFMPEG, "-y", "-i", str(output_wav), "-codec:a", "libmp3lame",
        "-b:a", "320k", "-ar", "44100", "-ac", "2", str(output_mp3),
    ])

    return {
        "target_lufs": target_lufs,
        "true_peak_target": true_peak,
        "sample_rate": 44100,
        "wav_bit_depth": 24,
        "mp3_bitrate": "320 kbps",
        "processing": {
            "cleanup": cleanup,
            "warmth": warmth,
            "presence": presence,
            "compression": compression,
            "deessing": deessing,
            "stereo_width": stereo_width,
        },
    }
