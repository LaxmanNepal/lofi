# GPU backend

## Free Colab V1

Use a Google Colab GPU runtime. T4/16GB is the practical target for this first prototype.

1. Open the repository's `backend/colab_laxman_lofi.py` in Colab.
2. Select **Runtime → Change runtime type → T4 GPU** when available.
3. Run the script.
4. The script installs the official ACE-Step v1 repository, starts `backend/server.py`, and creates a free Cloudflare quick tunnel.
5. Read `/content/cloudflared.log` and copy the generated `https://...trycloudflare.com` URL.
6. Open the Laxman Lofi web app → ⚙ Settings → paste the URL.
7. The green **API online** indicator should appear.

### Why this engine?

The first prototype uses ACE-Step v1 rather than ACE-Step 1.5. The official v1 3.5B checkpoint is currently listed as Apache 2.0 and the project documents lyrics, vocals, multiple languages, and up to 4-minute generation. The newer 1.5 release has extra restrictions concerning commercial hosted generation and commercial output verification, so it is intentionally not the default here.

### Security

For testing, the quick tunnel is public. Before leaving it running for a long time, set `LAXMAN_LOFI_API_KEY` in the Colab script and paste the same key into the web app Settings. Never commit the key to GitHub.

### Limitations of free Colab

- Runtime availability is not guaranteed.
- Sessions can disconnect or expire.
- Generated WAV files are held in the temporary Colab runtime.
- This is a creator tool, not a production public SaaS backend.

For a permanent generator, move the same backend to a GPU machine you control.
