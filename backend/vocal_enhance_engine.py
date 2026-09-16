"""Automatic vocal enhancement using FFmpeg DSP.

No generative model is used here. Processing is deterministic and designed
for cleanup of separated vocals before the V3.6 mix/master stage.
"""
import shutil
import subprocess
from pathlib import Path

FFMPEG=shutil.which("ffmpeg") or "ffmpeg"

def _run(args):
    try:
        return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True).stderr
    except (OSError,subprocess.CalledProcessError) as exc:
        detail=exc.stderr.strip().splitlines()[-1] if getattr(exc,"stderr","") else "unknown FFmpeg error"
        raise RuntimeError(f"Vocal enhancement failed: {detail}") from exc

def enhance_vocal(source:Path,output:Path,denoise:float=.35,derverb:float=.20,breath_control:float=.20,presence:float=.30,deesser:float=.25,ducking:float=.0):
    if not source.is_file(): raise ValueError(f"Missing vocal stem: {source.name}")
    clamp=lambda x:max(0,min(1,float(x)))
    denoise=clamp(denoise);derverb=clamp(derverb);breath_control=clamp(breath_control);presence=clamp(presence);deesser=clamp(deesser);ducking=clamp(ducking)
    gate=-50+denoise*15
    presence_gain=presence*4
    deess_ratio=1+deesser*5
    breath_ratio=1+breath_control*3
    # Spectral shaping and dynamic control provide a lightweight offline repair chain.
    filters=[
        "highpass=f=65",
        f"afftdn=nr={6+denoise*12:g}:nf=-25",
        f"agate=threshold={gate:g}dB:ratio=2:attack=10:release=160",
        f"equalizer=f=3200:t=q:w=1:g={presence_gain:g}",
        f"acompressor=threshold=-26dB:ratio={breath_ratio:g}:attack=5:release=120:makeup=1",
        f"acompressor=frequency=7000:threshold=-32dB:ratio={deess_ratio:g}:attack=2:release=90",
        f"acompressor=threshold=-22dB:ratio={1.2+derverb*1.8:g}:attack=10:release=180:makeup=1",
        "loudnorm=I=-18:TP=-2:LRA=7",
        "aresample=44100",
        "pan=stereo|c0=c0|c1=c0",
    ]
    output.parent.mkdir(parents=True,exist_ok=True)
    _run([FFMPEG,"-y","-i",str(source),"-af",','.join(filters),"-ar","44100","-ac","2","-c:a","pcm_s24le",str(output)])
    return {"sample_rate":44100,"wav_bit_depth":24,"processing":{"denoise":denoise,"derverb":derverb,"breath_control":breath_control,"presence":presence,"deesser":deesser,"ducking":ducking},"method":"FFmpeg spectral/dynamic DSP","note":"Automatic enhancement is a starting point; listen for artifacts before release."}
