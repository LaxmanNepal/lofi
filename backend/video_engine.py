import base64
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg is required for video export but was not found on the server.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr[-3000:] or "FFmpeg video export failed.") from exc


def _escape_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")


def build_visualizer(audio_path: Path, cover_path: Path, output_path: Path, title: str,
                     artist: str = "Laxman Lofi", overlay_title: bool = True,
                     show_waveform: bool = True) -> None:
    if not audio_path.is_file():
        raise ValueError("Audio source was not found. Generate the song first.")
    if not cover_path.is_file():
        raise ValueError("Cover art was not found. Generate a cover first.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph = ["[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080[bg]"]
    current = "[bg]"
    if overlay_title:
        title = _escape_text(title)
        artist = _escape_text(artist)
        graph += [
            f"{current}drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{title}':fontcolor=white:fontsize=58:borderw=3:bordercolor=black@0.55:x=(w-text_w)/2:y=h-185:alpha='if(lt(t,1),t,1)'[t1]",
            f"[t1]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='{artist}':fontcolor=white@0.82:fontsize=30:borderw=2:bordercolor=black@0.4:x=(w-text_w)/2:y=h-110:alpha='if(lt(t,1),t,1)'[t2]",
        ]
        current = "[t2]"
    if show_waveform:
        graph += ["[1:a]showwaves=s=1600x170:mode=line:rate=30:colors=white@0.75:scale=sqrt[wave]",
                  f"{current}[wave]overlay=(W-w)/2:H-h-25:format=auto[vout]"]
    else:
        graph.append(f"{current}null[vout]")
    _run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(cover_path), "-i", str(audio_path),
        "-filter_complex", ";".join(graph), "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
        str(output_path)
    ])


def file_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")
