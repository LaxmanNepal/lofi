# Laxman Lofi AI Studio — Google Colab runner
# Runtime: GPU (T4 recommended). Starts the custom FastAPI API for music generation.

import os, subprocess, sys, time

REPO = "/content/lofi"
ACE_REPO = "/content/ACE-Step"

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)

if os.path.isdir(os.path.join(REPO, ".git")):
    subprocess.run(["git", "-C", REPO, "pull", "--ff-only"], check=False)
else:
    subprocess.run(["git", "clone", "https://github.com/LaxmanNepal/lofi.git", REPO], check=True)
os.chdir(REPO)

if os.path.isdir(os.path.join(ACE_REPO, ".git")):
    subprocess.run(["git", "-C", ACE_REPO, "pull", "--ff-only"], check=False)
else:
    subprocess.run(["git", "clone", "https://github.com/ace-step/ACE-Step.git", ACE_REPO], check=True)

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", ACE_REPO], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "backend/requirements.txt"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "nest-asyncio"], check=True)

# Optional secret. Set it before starting the server for basic protection.
# os.environ["LAXMAN_LOFI_API_KEY"] = "change-this-secret"
os.environ["ACE_CHECKPOINT_DIR"] = "/content/ace-checkpoints"
os.environ["ACE_CPU_OFFLOAD"] = "true"
os.environ["ACE_OVERLAPPED_DECODE"] = "true"

# NVIDIA T4 is compute capability 7.5 and does not have native BF16 support.
# Use BF16 only on GPUs with compute capability >= 8.0.
try:
    import torch
    if torch.cuda.is_available():
        major, minor = torch.cuda.get_device_capability(0)
        os.environ["ACE_BF16"] = "true" if major >= 8 else "false"
        print(f"GPU: {torch.cuda.get_device_name(0)} | compute {major}.{minor} | ACE_BF16={os.environ['ACE_BF16']}")
    else:
        os.environ["ACE_BF16"] = "false"
        print("WARNING: CUDA GPU not detected. ACE-Step generation will be very slow on CPU.")
except Exception as exc:
    os.environ["ACE_BF16"] = "false"
    print(f"GPU capability check failed; using ACE_BF16=false: {exc}")

# Apply the runtime-safe ACE-Step configuration to the checked-out API.
subprocess.run([sys.executable, "backend/prepare_generation.py"], check=True)

try:
    from acestep.pipeline_ace_step import ACEStepPipeline
    print("ACE-Step import: OK")
except Exception as exc:
    raise RuntimeError(f"ACE-Step import failed before API startup: {exc}") from exc

api_log = open("/content/laxman-lofi-api.log", "w")
api = subprocess.Popen([
    sys.executable, "-m", "uvicorn", "backend.server:app",
    "--host", "0.0.0.0", "--port", "8000"
], stdout=api_log, stderr=subprocess.STDOUT)

subprocess.run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared", shell=True, check=True)

time.sleep(3)
if api.poll() is not None:
    api_log.flush()
    print("\nERROR: Laxman Lofi API exited during startup.")
    print("Read /content/laxman-lofi-api.log for the exact traceback.")
    raise RuntimeError("Laxman Lofi API failed to start")

cf_log = open("/content/cloudflared.log", "w")
subprocess.Popen(["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000"], stdout=cf_log, stderr=subprocess.STDOUT)
time.sleep(5)

print("\n--- Laxman Lofi API ---")
print("Open /content/cloudflared.log and copy the https://*.trycloudflare.com URL.")
print("Paste that URL into Laxman Lofi > Settings > ACE-Step API URL.")
print("\nHealth check: <YOUR_TUNNEL_URL>/health")
print("API log: /content/laxman-lofi-api.log")
print("\nKeep this Colab tab/runtime alive while generating. A free Colab runtime can disconnect or expire.")
