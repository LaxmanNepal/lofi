"""Optional local SDXL cover-art generator for Colab GPU runtimes."""
import base64
import io
import os
import gc
import torch

MODEL_ID=os.getenv("COVER_MODEL_ID","stabilityai/stable-diffusion-xl-base-1.0")
_pipe=None

def _load():
    global _pipe
    if _pipe is not None: return _pipe
    from diffusers import StableDiffusionXLPipeline
    if not torch.cuda.is_available(): raise RuntimeError("Cover generation requires a CUDA GPU. Use the included Colab runtime.")
    _pipe=StableDiffusionXLPipeline.from_pretrained(MODEL_ID,torch_dtype=torch.float16,use_safetensors=True)
    _pipe.enable_model_cpu_offload()
    return _pipe

def generate_cover(prompt: str, seed: int|None=None):
    if not prompt.strip(): raise ValueError("A cover prompt is required.")
    p=_load()
    generator=torch.Generator(device="cpu").manual_seed(seed if seed is not None else int.from_bytes(os.urandom(4),"big"))
    full=("Original Nepali lo-fi music cover art, cinematic photographic illustration, " + prompt + ", premium music artwork, atmospheric lighting, emotionally restrained, "
          "clean composition, strong focal subject, subtle Nepal setting, no logos, no watermarks, no text, no famous person, no artist imitation")
    image=p(prompt=full,negative_prompt="text, watermark, logo, distorted face, extra fingers, celebrity, artist imitation, low quality",width=1024,height=576,num_inference_steps=30,guidance_scale=6.5,generator=generator).images[0]
    buf=io.BytesIO(); image.save(buf,format="PNG",optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii"), generator.initial_seed()

def unload_cover_model():
    global _pipe
    _pipe=None; gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache()
