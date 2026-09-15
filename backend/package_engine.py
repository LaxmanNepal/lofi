"""Create a portable ZIP release package for a generated Laxman Lofi song."""
import base64
import io
import json
import zipfile
from pathlib import Path


def build_package(output_dir: Path, output_id: str, title: str, metadata: dict, seo: dict | None, cover_base64: str | None):
    safe = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:80] or "laxman-lofi"
    source = output_dir / f"{output_id}.wav"
    master_wav = output_dir / f"{output_id}_master.wav"
    master_mp3 = output_dir / f"{output_id}_master.mp3"
    stem_root = output_dir / "stems" / output_id
    if not source.is_file():
        raise ValueError("Source audio not found. Generate the song again if the runtime expired.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(source, f"audio/{safe}-ORIGINAL.wav")
        if master_wav.is_file(): z.write(master_wav, f"audio/{safe}-MASTER.wav")
        if master_mp3.is_file(): z.write(master_mp3, f"audio/{safe}-320kbps.mp3")
        for stem_name, archive_name in (("vocals.wav", "stems/VOCALS.wav"), ("instrumental.wav", "stems/INSTRUMENTAL.wav"), ("custom_mix.wav", "stems/CUSTOM-MIX.wav")):
            stem = stem_root / stem_name
            if stem.is_file(): z.write(stem, archive_name)
        if cover_base64:
            try: z.writestr(f"artwork/{safe}-COVER.png", base64.b64decode(cover_base64))
            except Exception as exc: raise ValueError("Invalid cover image data.") from exc
        z.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        if seo:
            z.writestr("youtube-seo.json", json.dumps(seo, ensure_ascii=False, indent=2))
            lines = [f"TITLE: {seo.get('youtube_title', title)}", "", "DESCRIPTION:", seo.get("description", ""), "", "TAGS:", ", ".join(seo.get("tags", [])), "", "HASHTAGS:", " ".join(seo.get("hashtags", []))]
            z.writestr("youtube-description.txt", "\n".join(lines))
        z.writestr("README.txt", "Laxman Lofi creation package\n\nReview AI-generated lyrics, audio, artwork and metadata before publishing.\n\nStem files are separated with Demucs when requested. Review all AI-generated material before release.\n")
    return base64.b64encode(buf.getvalue()).decode("ascii"), f"{safe}-Laxman-Lofi-Package.zip"
