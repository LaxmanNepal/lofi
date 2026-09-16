"""V4.6 lightweight harmonic intelligence for existing audio.

This module estimates pitch-class/chroma energy, key, chord candidates and
section harmonic activity. It is intentionally heuristic: lo-fi mixes,
reverb, noise and layered instruments make exact symbolic transcription
unreliable without a dedicated music-transcription model.
"""
from __future__ import annotations
import math, wave
from pathlib import Path

NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
MAJOR = [6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]
MINOR = [6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17]
CHORDS = {
    "maj": [0,4,7], "min": [0,3,7], "sus2": [0,2,7], "sus4": [0,5,7],
    "7": [0,4,7,10], "min7": [0,3,7,10]
}

def _read_mono(path: Path, max_seconds: float = 900.0):
    with wave.open(str(path), "rb") as w:
        ch, rate, width, frames = w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getnframes()
        if width != 2:
            raise ValueError("V4.6 currently expects 16-bit PCM WAV input.")
        frames = min(frames, int(rate * max_seconds))
        raw = w.readframes(frames)
    vals = []
    step = ch * 2
    for i in range(0, len(raw) - step + 1, step):
        total = 0
        for c in range(ch):
            total += int.from_bytes(raw[i+c*2:i+c*2+2], "little", signed=True)
        vals.append((total / ch) / 32768.0)
    return vals, rate

def _chroma(samples, rate, start, seconds=8.0):
    a, b = int(start*rate), min(len(samples), int((start+seconds)*rate))
    x = samples[a:b]
    if len(x) < 256: return [0.0]*12, 0.0
    # Downsample for predictable CPU cost while retaining musical fundamentals.
    target = 8000
    stride = max(1, rate // target)
    x = x[::stride]
    sr = rate / stride
    n = min(len(x), 8192)
    if n < 512: return [0.0]*12, 0.0
    x = x[:n]
    # Hann window + direct frequency-bin sampling across fundamentals/harmonics.
    out = [0.0]*12
    total = 0.0
    for pc in range(12):
        for octave in range(2, 6):
            f = 16.3516 * (2**octave) * (2**(pc/12))
            if f >= sr/2: continue
            for h, weight in ((1,1.0),(2,.55),(3,.30),(4,.16)):
                ff = f*h
                if ff >= sr/2: continue
                k = int(round(ff*n/sr))
                if k < 1 or k >= n//2: continue
                re = im = 0.0
                for j, v in enumerate(x):
                    q = v * (0.5 - 0.5*math.cos(2*math.pi*j/(n-1)))
                    ang = 2*math.pi*k*j/n
                    re += q*math.cos(ang); im -= q*math.sin(ang)
                mag = math.sqrt(re*re+im*im) / n
                out[pc] += mag*weight
                total += mag*weight
    if total <= 1e-9: return out, 0.0
    out = [v/total for v in out]
    return out, total

def _corr(a,b):
    am=sum(a)/12; bm=sum(b)/12
    num=sum((x-am)*(y-bm) for x,y in zip(a,b))
    da=math.sqrt(sum((x-am)**2 for x in a)); db=math.sqrt(sum((y-bm)**2 for y in b))
    return num/(da*db+1e-9)

def estimate_key(chroma):
    best=[]
    for root in range(12):
        for mode, prof in (("major",MAJOR),("minor",MINOR)):
            rotated=chroma[root:]+chroma[:root]
            score=_corr(rotated,prof)
            best.append((score,root,mode))
    best.sort(reverse=True)
    top=best[0]; gap=top[0]-best[1][0] if len(best)>1 else 0
    return {"key":NAMES[top[1]],"mode":top[2],"confidence":round(max(0,min(1,(top[0]+1)/2*.65+gap*2.2)),3),"score":round(top[0],4)}

def estimate_chord(chroma, key=None):
    if sum(chroma) <= 0: return {"chord":"N/A","root":None,"type":None,"confidence":0.0}
    best=[]
    for root in range(12):
        for typ, ints in CHORDS.items():
            mask=set((root+i)%12 for i in ints)
            inside=sum(chroma[i] for i in mask)/len(mask)
            outside=sum(chroma[i] for i in range(12) if i not in mask)/max(1,12-len(mask))
            score=inside-outside*.65
            best.append((score,root,typ))
    best.sort(reverse=True)
    top=best[0]; second=best[1]
    conf=max(0,min(1,(top[0]-second[0])*4+top[0]*1.5))
    return {"chord":f"{NAMES[top[1]]}{'' if top[2]=='maj' else top[2]}","root":NAMES[top[1]],"type":top[2],"confidence":round(conf,3)}

def analyze_harmony(path: Path, window: float = 8.0):
    if not path.is_file(): raise ValueError("Audio file not found.")
    samples, rate = _read_mono(path)
    duration=len(samples)/rate
    windows=[]; t=0.0
    while t < duration:
        c, energy=_chroma(samples,rate,t,window)
        if energy>0: windows.append({"start":round(t,3),"end":round(min(duration,t+window),3),"chroma":c,"energy":round(energy,6)})
        t += window
    if not windows: raise ValueError("Could not extract harmonic information from the WAV.")
    avg=[sum(w["chroma"][i] for w in windows)/len(windows) for i in range(12)]
    key=estimate_key(avg)
    timeline=[]
    last=None
    for w in windows:
        ch=estimate_chord(w["chroma"],key)
        tension=max(0,min(1,1-ch["confidence"] + sum(w["chroma"][i] for i in range(12) if i not in {(NAMES.index(key['key'])+x)%12 for x in (0,4,7)})*.55))
        item={"start":w["start"],"end":w["end"],**ch,"tension":round(tension,3),"energy":w["energy"]}
        if last and item["chord"]==last["chord"]:
            last["end"]=item["end"]; last["confidence"]=round((last["confidence"]+item["confidence"])/2,3); last["tension"]=round((last["tension"]+item["tension"])/2,3)
        else:
            timeline.append(item); last=item
    changes=max(0,len(timeline)-1)
    density=changes/max(1,duration/60)
    return {"duration":round(duration,3),"window_seconds":window,"key":key["key"],"mode":key["mode"],"key_confidence":key["confidence"],"chord_changes":changes,"harmonic_density_per_minute":round(density,3),"timeline":timeline,"method":"lightweight chroma + Krumhansl-style key profile + chord-template heuristic","note":"Estimated harmonic map only. Lo-fi noise, reverb, layered instruments and bass ambiguity can produce incorrect keys or chords; this is not exact MIDI/chord transcription."}
