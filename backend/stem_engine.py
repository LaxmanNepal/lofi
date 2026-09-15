"""GPU stem separation for Laxman Lofi using Demucs.

The separator produces vocals, drums, bass and other stems. Instrumental is
then rendered from drums+bass+other. The implementation intentionally runs as
an on-demand subprocess so a Colab T4 does not keep another large model in VRAM.
"""
import shutil
import subprocess
from pathlib import Path


def _demucs_bin() -> str:
    return shutil.which("demucs") or "demucs"


def separate_stems(input_path: Path, output_dir: Path, model: str = "htdemucs") -> dict[str, Path]:
    if not input_path.is_file():
        raise ValueError("Source audio not found. Generate the song again if the runtime expired.")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / input_path.stem
    cmd = [_demucs_bin(), "-n", model, "--two-stems", "vocals", "-o", str(output_dir), str(input_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("Demucs is not installed. Re-run the Colab setup cell to install stem separation.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip().splitlines()[-1] if exc.stderr else "unknown Demucs error"
        raise RuntimeError(f"Stem separation failed: {detail}") from exc

    two_stem = target / "vocals.wav"
    no_vocals = target / "no_vocals.wav"
    if not two_stem.is_file() or not no_vocals.is_file():
        raise RuntimeError("Demucs completed but the expected vocal/instrumental stems were not found.")
    return {"vocals": two_stem, "instrumental": no_vocals}
