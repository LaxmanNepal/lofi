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


def build_visualizer(audio_path: Path, cover_path: Path, output_path: Path, title: str,
                     artist: str = "Laxman Lofi", duration: float = 0,
                     overlay_title: bool = True, show_waveform: bool = True,
                     fade_in: float = 1.0, fade_out: float = 2.0) -> None:
    if not audio_path.is_file():
        raise ValueError("Audio source was not found. Generate the song first.")
    if not cover_path.is_file():
        raise ValueError("Cover art was not found. Generate a cover first.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # The cover is looped to audio length. drawtext uses a common DejaVu font
    # available on most Debian/Colab images; if absent, FFmpeg will report it.
    filters = ["scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"]
    if overlay_title:
        safe_title = title.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        safe_artist = artist.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        filters.append(
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"text='{safe_title}':fontcolor=white:fontsize=58:borderw=3:bordercolor=black@0.55:"
            "x=(w-text_w)/2:y=h-185:alpha='if(lt(t,1),t,1)'"
        )
        filters.append(
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"text='{safe_artist}':fontcolor=white@0.82:fontsize=30:borderw=2:bordercolor=black@0.4:"
            "x=(w-text_w)/2:y=h-110:alpha='if(lt(t,1),t,1)'"
        )
    if show_waveform:
        filters.append(
            "showwaves=s=1600x170:mode=line:colors=white@0.75:rate=30:scale=sqrt,format=rgba[wave]"
        )
        filters.append("[0:v][wave]overlay=(W-w)/2:H-h-25:format=auto")
    vf = ",".join(filters)
    # Keep audio untouched; encode video as broadly compatible H.264/AAC.
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(cover_path), "-i", str(audio_path),
        "-filter_complex", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
        "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
        str(output_path)
    ]
    # A simpler video path is used when waveform overlay is disabled because
    # the filter graph otherwise needs a second audio-derived video stream.
    if not show_waveform:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(cover_path), "-i", str(audio_path),
            "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
            "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-shortest", "-movflags", "+faststart", str(output_path)
        ]
    _run(cmd)


def file_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")
