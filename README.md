# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V4.3 — Story → Lyrics → Music → 4 Stems → Vocal Enhance → Mix → Smart Arrange → Structure → Section-Aware Arrangement → Stem-Aware Arrangement → Instrument Stem Intelligence → Beat & Tempo Intelligence → Master → Cover → Video → Lyric Video → ASR Sync → Quality Check → SEO → ZIP

- **Frontend:** static, mobile-first web app in `web/`
- **Lyric AI:** local Hugging Face Transformers model
- **Music engine:** ACE-Step v1 3.5B
- **Audio production:** deterministic FFmpeg DSP
- **Stems:** Demucs `htdemucs` on demand
- **Vocal enhancement:** noise reduction, dynamics, presence and de-essing-style processing
- **Mix + master:** stem balance, EQ, compression, stereo width and loudness normalization
- **Smart Arrangement V3.8:** FFmpeg/FFprobe energy analysis and heuristic section shaping
- **Song Structure V3.9:** editable Intro/Verse/Pre-Chorus/Chorus/Bridge/Final Chorus/Outro timeline
- **Section-Aware Arrangement V4.0:** browser OfflineAudioContext section-specific gain/EQ/transitions
- **Stem-Aware Arrangement V4.1:** independent vocal/instrumental section gains, chorus lifts, bridge reduction and ducking
- **Instrument Stem Intelligence V4.2:** full Demucs vocals/drums/bass/other separation with independent energy timelines and section-aware stem automation
- **Beat & Tempo Intelligence V4.3:** estimated BPM, beat grid, 4/4 bar map and reviewed section snapping; server engine plus browser fallback
- **Cover art:** optional local SDXL generation on the Colab GPU
- **YouTube video:** 1920×1080 H.264 + AAC visualizer
- **Lyric video:** FFmpeg + ASS subtitles with Nepali Devanagari support and karaoke highlighting
- **Lyric synchronization:** faster-whisper ASR with editable timing
- **Audio quality:** loudness, peak, duration and silence inspection
- **Export:** WAV 24-bit / 44.1 kHz and MP3 320 kbps where applicable

### V4.3 beat & tempo controls

- Audio-derived BPM estimate
- Beat duration and estimated first beat
- Beat grid and bar starts
- 4 beats per bar display for practical lofi arrangement work
- Confidence indicator
- Snap reviewed song sections to the nearest beat boundary
- Beat map JSON copy/export through the browser workflow
- Uses the backend `/beat/analyze` route when available, with a browser Web Audio RMS/onset fallback

V4.3 beat detection is intentionally transparent: it uses an RMS/onset-envelope tempo heuristic rather than claiming perfect beat tracking, downbeat detection or symbolic transcription. Review the grid against the waveform before using it for a final release.

### V4.2 instrument controls

- Drum level
- Bass level
- Melody / other level
- Chorus drum/bass/melody lifts
- Bridge, intro and outro reductions
- Other-stem stereo width
- Vocal ducking
- Target loudness
- Per-section drum, bass and other energy meters

### API

- `POST /instrument-arrangement/analyze` — prepare four Demucs stems and inspect drums/bass/other energy
- `POST /instrument-arrangement` — render vocals + drums + bass + other
- `POST /beat/analyze` — optional server-side V4.3 BPM/beat analysis when the Colab server includes the latest API
- `POST /stem-arrangement/analyze` — inspect vocal/instrumental energy
- `POST /stem-arrangement` — render the V4.1 stem-aware arrangement
- `POST /arrangement/analyze` — inspect energy and heuristic sections
- `POST /arrangement` — build the smart-arranged WAV + MP3

The project is designed for user-controlled Colab/cloud execution and does not hardcode an API key. Section and beat detection are analytical heuristics and should be reviewed before publishing.
