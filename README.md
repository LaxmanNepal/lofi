# Laxman Lofi AI Studio

Original-first Nepali music creation system for **Laxman Lofi**.

## V1 architecture

- **Frontend:** static, mobile-first web app in `web/`
- **Generation engine:** ACE-Step v1 3.5B (`ACE-Step/ACE-Step-v1-3.5B`), an Apache-2.0 checkpoint
- **Cloud runner:** Google Colab notebook in `backend/`
- **API contract:** frontend sends a generation request to a user-controlled ACE-Step API endpoint
- **No API key is hard-coded into the repository**

ACE-Step v1 supports text-to-music, structured lyrics, vocals, multiple languages, and audio durations suitable for original song production. The official v1 checkpoint is listed as Apache 2.0. Always verify the current model card and applicable law before commercial distribution.

## Important licensing note

This project deliberately targets **ACE-Step v1**, not ACE-Step 1.5, for the first commercial-oriented prototype. The current 1.5 ecosystem has additional restrictions around commercial hosted generation and commercial output verification, so it is not the default engine for this project.

The model license does not guarantee that every generated work is copyrightable or free from similarity claims. Use original prompts/lyrics, do not imitate living artists, and keep a generation record (prompt, lyrics, seed, model version, date).

## V1 workflow

1. Open the static frontend.
2. Enter a story or idea in Nepali/English.
3. Select mood, language, vocal/instrumental, duration and style.
4. Paste original lyrics or use your own lyric-writing workflow.
5. Generate through your own Colab/local ACE-Step server.
6. Review the result for originality before publishing.

## Suggested deployment

Host `web/` on your existing static site, for example:

`https://apps.laxmannepal.com.np/laxman-lofi/`

Run the Colab notebook, expose the API temporarily, then set the API URL in the app's Settings panel. For a permanent public service, move the model to a GPU host you control and keep the API protected.

## Roadmap

- V1: working generation dashboard + ACE-Step API connector
- V1.1: Nepali lyric helper + prompt builder
- V1.2: generation history + metadata/seed export
- V1.3: audio mastering and MP3/WAV packaging
- V1.4: cover-art generator + YouTube SEO pack
- V2: one-click "Story → Lyrics → Song → Cover → YouTube package"
