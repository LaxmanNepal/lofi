# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V3.8 — Story → Lyrics → Music → Stems → Vocal Enhance → Mix → Smart Arrange → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** deterministic FFmpeg DSP
- **Stems:** Demucs `htdemucs` on demand
- **Vocal enhancement:** noise reduction, dynamics, presence and de-essing-style processing
- **Mix + master:** stem balance, EQ, compression, stereo width and loudness normalization
- **Smart Arrangement V3.8:** FFmpeg/FFprobe energy analysis, heuristic verse/build/chorus labels, optional leading/trailing silence trimming, intro/outro fades and conservative chorus-energy lift
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

### V3.8 controls

- Trim silence
- Intro fade
- Outro fade
- Chorus lift (0–30%)
- Energy sensitivity

Section detection is **heuristic**, based on audio energy; it is not claimed to be perfect musical transcription. Review the arrangement before publishing.

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key.
