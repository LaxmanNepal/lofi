"""Prepare the legacy ACE-Step v1.0 pipeline for reliable Colab generation.

The project intentionally keeps the original ACE-Step 3.5B pipeline API. This
small runtime patch makes its configuration safer on free/consumer GPUs without
changing the rest of the studio API.
"""
from pathlib import Path
import os
import re


def prepare(server_path: str = "backend/server.py") -> dict:
    path = Path(server_path)
    text = path.read_text(encoding="utf-8")

    # T4 (SM 7.5) does not have native BF16 support. Never force BF16 there.
    bf16_env = os.getenv("ACE_BF16", "true").lower() == "true"
    try:
        import torch
        if torch.cuda.is_available():
            major, minor = torch.cuda.get_device_capability(0)
            if (major, minor) < (8, 0):
                bf16_env = False
                os.environ["ACE_BF16"] = "false"
    except Exception:
        pass

    # Use ACE-Step's supported memory-saving modes when requested.
    old = 'pipeline=ACEStepPipeline(checkpoint_dir=CHECKPOINT_DIR,dtype="bfloat16" if BF16 else "float32",torch_compile=False)'
    new = ('pipeline=ACEStepPipeline(checkpoint_dir=CHECKPOINT_DIR,'
           'dtype="bfloat16" if BF16 else "float32",torch_compile=False,'
           'cpu_offload=os.getenv("ACE_CPU_OFFLOAD","true").lower()=="true",'
           'overlapped_decode=os.getenv("ACE_OVERLAPPED_DECODE","true").lower()=="true")')
    if old in text:
        text = text.replace(old, new, 1)

    # Make the API identify the runtime configuration in /health.
    old_health = '"cuda":torch.cuda.is_available(),"audio_mastering"'
    new_health = ('"cuda":torch.cuda.is_available(),"gpu_name":(torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),'
                  '"gpu_capability":(list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None),'
                  '"bf16":BF16,"cpu_offload":os.getenv("ACE_CPU_OFFLOAD","true").lower()=="true",'
                  '"overlapped_decode":os.getenv("ACE_OVERLAPPED_DECODE","true").lower()=="true","audio_mastering"')
    if old_health in text and '"gpu_capability"' not in text:
        text = text.replace(old_health, new_health, 1)

    path.write_text(text, encoding="utf-8")
    return {
        "server": str(path),
        "bf16": bf16_env,
        "cpu_offload": os.getenv("ACE_CPU_OFFLOAD", "true").lower() == "true",
        "overlapped_decode": os.getenv("ACE_OVERLAPPED_DECODE", "true").lower() == "true",
    }


if __name__ == "__main__":
    print(prepare())
