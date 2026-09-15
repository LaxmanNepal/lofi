# Laxman Lofi AI Studio — Google Colab runner
# Runtime: GPU (T4 recommended). This script installs ACE-Step v1 and starts the custom API.

import os, subprocess, sys, time

REPO = "/content/lofi"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
subprocess.run(["git", "clone", "https://github.com/LaxmanNepal/lofi.git", REPO], check=False)
os.chdir(REPO)

# ACE-Step v1 is the commercial-oriented prototype engine used by this project.
# Its current model card lists Apache 2.0. Verify current terms before publishing commercially.
subprocess.run(["git", "clone", "https://github.com/ace-step/ACE-Step.git", "/content/ACE-Step"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", "/content/ACE-Step"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastapi", "uvicorn[standard]", "soundfile", "numpy<2", "nest-asyncio"], check=True)

# Optional secret. Leave blank for a private/test tunnel. Set it before starting the server for basic protection.
# os.environ["LAXMAN_LOFI_API_KEY"] = "change-this-secret"
os.environ["ACE_CHECKPOINT_DIR"] = "/content/ace-checkpoints"
os.environ["ACE_BF16"] = "true"

# Start the API.
subprocess.Popen([
    sys.executable, "-m", "uvicorn", "backend.server:app",
    "--host", "0.0.0.0", "--port", "8000"
])

# Install Cloudflare's free quick-tunnel client.
subprocess.run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared", shell=True, check=True)

time.sleep(5)
subprocess.Popen(["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000"], stdout=open("/content/cloudflared.log", "w"), stderr=subprocess.STDOUT)

time.sleep(5)
print("\n--- Laxman Lofi API ---")
print("Open /content/cloudflared.log and copy the https://*.trycloudflare.com URL.")
print("Paste that URL into Laxman Lofi > Settings > ACE-Step API URL.")
print("\nHealth check: <YOUR_TUNNEL_URL>/health")
print("\nKeep this Colab tab/runtime alive while generating. A free Colab runtime can disconnect or expire.")
