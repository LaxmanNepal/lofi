"""FFmpeg-based audio quality and pre-publish checks for Laxman Lofi."""
import re
import shutil
import subprocess
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def _run(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        raise RuntimeError("FFmpeg/FFprobe is required for quality analysis.") from exc
    return p.stdout, p.stderr, p.returncode


def _duration(path):
    out, err, code = _run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)])
    if code:
        raise RuntimeError(err[-1000:] or "Unable to inspect audio.")
    return float(out.strip())


def _loudness(path):
    _, err, _ = _run([FFMPEG, "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    text = err
    m = re.search(r"I:\s*([+-]?\d+(?:\.\d+)?)\s*LUFS", text)
    tp = re.findall(r"(?:True peak|Peak):\s*([+-]?\d+(?:\.\d+)?)\s*dBFS", text, re.I)
    return (float(m.group(1)) if m else None), (float(tp[-1]) if tp else None)


def _silence(path):
    _, err, _ = _run([FFMPEG, "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-50dB:d=1", "-f", "null", "-"])
    starts = re.findall(r"silence_start:\s*([0-9.]+)", err)
    ends = re.findall(r"silence_end:\s*([0-9.]+)", err)
    return len(starts), len(ends)


def analyze_audio(path: Path):
    if not path.is_file():
        raise ValueError("Audio file not found.")
    duration = _duration(path)
    loudness, true_peak = _loudness(path)
    silence_starts, silence_ends = _silence(path)
    checks = []
    if loudness is None:
        checks.append({"id": "loudness", "status": "warning", "message": "Integrated loudness could not be measured."})
    else:
        status = "pass" if -16.0 <= loudness <= -12.0 else "warning"
        checks.append({"id": "loudness", "status": status, "message": f"Integrated loudness: {loudness:.1f} LUFS (production target ≈ -14 LUFS)."})
    if true_peak is None:
        checks.append({"id": "true_peak", "status": "warning", "message": "True peak could not be measured."})
    else:
        status = "pass" if true_peak <= -1.0 else "warning"
        checks.append({"id": "true_peak", "status": status, "message": f"True peak: {true_peak:.1f} dBFS (target ≤ -1 dBTP)."})
    status = "pass" if duration >= 10 else "warning"
    checks.append({"id": "duration", "status": status, "message": f"Duration: {duration:.1f} seconds."})
    checks.append({"id": "silence", "status": "pass" if silence_starts <= 3 else "warning", "message": f"Detected {silence_starts} long silence region(s). Review unusually long gaps before publishing."})
    warnings = sum(x["status"] == "warning" for x in checks)
    return {"status": "ready" if warnings == 0 else "review", "duration": round(duration, 3), "integrated_lufs": loudness, "true_peak_dbfs": true_peak, "long_silence_regions": silence_starts, "checks": checks, "summary": "All automated checks passed." if warnings == 0 else f"{warnings} check(s) need review before publishing.", "method": "FFmpeg ebur128 + silencedetect + ffprobe", "note": "Automated checks are production aids, not a substitute for listening on headphones and speakers."}
