import re
import subprocess
from pathlib import Path


def _run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-3000:] or "FFmpeg command failed")
    return p.stdout.strip()


def audio_duration(path: Path) -> float:
    return float(_run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]))


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    cs = int(round((s - int(s)) * 100))
    if cs >= 100:
        s = int(s) + 1
        cs = 0
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def _escape_ass(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def _lyric_lines(lyrics: str):
    out = []
    for raw in lyrics.splitlines():
        line = re.sub(r"^\s*(?:\[[^\]]+\]|[-*•]+)\s*", "", raw).strip()
        if line and not re.fullmatch(r"(?:verse|chorus|bridge|intro|outro|hook|verse\s*\d+).*", line, re.I):
            out.append(line)
    return out


def build_timing(lyrics: str, duration: float, intro: float = 2.0, outro: float = 2.0):
    lines = _lyric_lines(lyrics)
    if not lines:
        raise ValueError("At least one lyric line is required.")
    usable = max(1.0, duration - intro - outro)
    weights = [max(1, len(re.findall(r"\S+", x))) + max(0, len(x) // 18) * 0.35 for x in lines]
    total = sum(weights)
    cursor = intro
    events = []
    for i, (line, weight) in enumerate(zip(lines, weights)):
        span = usable * weight / total
        end = duration - outro if i == len(lines) - 1 else cursor + span
        events.append((cursor, end, line))
        cursor = end
    return events


def _karaoke_text(line: str, span: float) -> str:
    words = re.findall(r"\S+", line)
    if not words:
        return _escape_ass(line)
    units = max(1, int(round(span * 100 / len(words))))
    return " ".join("{\\k" + str(units) + "}" + _escape_ass(word) for word in words)


def write_ass(events, path: Path, theme: str = "night"):
    themes = {
        "night": ("Noto Sans Devanagari", 64, "&H00FFFFFF", "&H00BFE8FF", "&H99000000"),
        "warm": ("Noto Sans Devanagari", 64, "&H00FFF4DF", "&H00FFD08A", "&H990B0703"),
        "minimal": ("Noto Sans Devanagari", 60, "&H00FFFFFF", "&H00FFFFFF", "&H99000000"),
        "nepal": ("Noto Sans Devanagari", 66, "&H00FFFFFF", "&H00FF6B6B", "&H99050008"),
    }
    font, size, primary, secondary, back = themes.get(theme, themes["night"])
    lines = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
        "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Lyric,{font},{size},{primary},{secondary},&H00101010,{back},1,0,0,0,100,100,0,0,1,3,1,2,120,120,100,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    for start, end, text in events:
        lines.append(f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Lyric,,0,0,0,karaoke,{_karaoke_text(text, end-start)}")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_lyric_video(audio_path: Path, cover_path: Path, output_path: Path, lyrics: str, title: str, theme: str = "night", karaoke: bool = True, intro: float = 2.0, outro: float = 2.0, waveform: bool = True):
    if not audio_path.is_file():
        raise ValueError("Source audio not found.")
    if not cover_path.is_file():
        raise ValueError("Cover image not found.")
    if not lyrics.strip():
        raise ValueError("Lyrics are required for lyric video generation.")
    duration = audio_duration(audio_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path = output_path.with_suffix(".ass")
    events = build_timing(lyrics, duration, intro, outro)
    write_ass(events, ass_path, theme)

    safe_title = title.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    vf = "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.00035,1.08)':d=1:s=1920x1080:fps=30,format=yuv420p"
    if waveform:
        vf += ",drawbox=x=0:y=1010:w=iw:h=4:color=white@0.20:t=fill"
    vf += f",subtitles='{str(ass_path).replace(chr(39), chr(92)+chr(39))}'"
    fade_end = max(0.0, duration - outro)
    vf += f",fade=t=in:st=0:d={min(1.2, intro):g},fade=t=out:st={fade_end:g}:d={min(1.5, outro):g}"

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(cover_path), "-i", str(audio_path), "-vf", vf, "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duration:g}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", "-metadata", f"title={safe_title}", str(output_path)]
    _run(cmd)
    try:
        ass_path.unlink(missing_ok=True)
    except Exception:
        pass
    return {"duration": duration, "lines": len(events), "theme": theme, "estimated_timing": True}
