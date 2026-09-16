# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V3.9 — Story → Lyrics → Music → Stems → Vocal Enhance → Mix → Smart Arrange → Song Structure → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** deterministic FFmpeg DSP
- **Stems:** Demucs `htdemucs` on demand
- **Vocal enhancement:** noise reduction, dynamics, presence and de-essing-style processing
- **Mix + master:** stem balance, EQ, compression, stereo width and loudness normalization
- **Smart Arrangement V3.8:** FFmpeg/FFprobe energy analysis, heuristic verse/build/chorus labels, optional leading/trailing silence trimming, intro/outro fades and conservative chorus-energy lift
- **Song Structure V3.9:** editable Intro / Verse / Pre-Chorus / Chorus / Bridge / Final Chorus / Outro timeline inferred from energy, position and repetition heuristics
- **Structure indicators:** section energy plus heuristic vocal/instrumental density labels
- **Structure rendering:** applies the current FFmpeg arrangement engine while retaining the editable structure timeline as release metadata
- **Arrangement report:** detected sections, energy threshold, trim boundaries and output duration
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support and karaoke highlighting
- **Lyric synchronization:** faster-whisper ASR with editable timing
- **Audio quality:** loudness, peak, duration and silence inspection
- **Export:** WAV 24-bit / 44.1 kHz and MP3 320 kbps where applicable

### V3.8 API

- `POST /arrangement/analyze` — inspect energy and heuristic sections
- `POST /arrangement` — build the smart-arranged WAV + MP3

### V3.9 Studio

- Structure modes: Balanced, Lofi / relaxed, Cinematic
- Editable section labels
- Section timeline with start/end and energy
- Heuristic vocal/instrumental density indicators
- Chorus lift
- Bridge reduction control
- Final chorus lift control
- Structured WAV + 320 kbps MP3 export

V3.9 structure inference is **heuristic**, not semantic AI music transcription. The current renderer uses the existing deterministic FFmpeg arrangement engine; it does not invent new instruments or regenerate the song. Review the structure before publishing.

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key.
