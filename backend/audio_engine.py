"""Server-side mastering and export helpers for Laxman Lofi.

FFmpeg is used deliberately: it keeps the Python dependency surface small and
provides reliable WAV/MP3 encoding plus EBU-style loudness normalization.
"""

import shutil
import subprocess
from pathlib import Path


FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def ensure_ffmpeg() -> None:
    if shutil.which(FFMPEG) is None and FFMPEG != "ffmpeg":
        raise RuntimeError("FFmpeg is not installed on the generation server.")
    try:
        subprocess.run([FFMPEG, "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("FFmpeg is required for mastering and MP3 export.") from exc


def _run(args: list[str]) -> None:
    ensure_ffmpeg()
    try:
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown FFmpeg error"
        raise RuntimeError(f"Audio processing failed: {detail}") from exc


def master_audio(input_path: Path, output_wav: Path, duration: float, fade_in: float = 2.0, fade_out: float = 3.0) -> None:
    """Create a normalized 44.1 kHz 24-bit WAV master.

    Target is approximately -14 LUFS integrated with -1 dBTP ceiling. Actual
    platform playback normalization can vary, so this is a production target,
    not a guarantee of final loudness on YouTube or another platform.
    """
    fade_in = max(0.0, min(float(fade_in), 10.0))
    fade_out = max(0.0, min(float(fade_out), 10.0))
    out_duration = max(0.0, float(duration))
    filters = ["loudnorm=I=-14:TP=-1.0:LRA=11"]
    if fade_in > 0:
        filters.append(f"afade=t=in:st=0:d={fade_in:g}")
    if fade_out > 0 and out_duration > fade_out:
        filters.append(f"afade=t=out:st={out_duration - fade_out:g}:d={fade_out:g}")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    _run([
        FFMPEG, "-y", "-i", str(input_path),
        "-af", ",".join(filters),
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s24le", str(output_wav),
    ])


def export_mp3(master_wav: Path, output_mp3: Path) -> None:
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    _run([
        FFMPEG, "-y", "-i", str(master_wav),
        "-codec:a", "libmp3lame", "-b:a", "320k", "-ar", "44100", "-ac", "2",
        str(output_mp3),
    ])
