"""Deterministic FFmpeg smart arrangement helpers for Laxman Lofi V3.8."""
import math, shutil, subprocess
from pathlib import Path
FFMPEG=shutil.which("ffmpeg") or "ffmpeg"
FFPROBE=shutil.which("ffprobe") or "ffprobe"

def _run(args):
    try:
        p=subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        return p.stdout.strip()
    except (OSError,subprocess.CalledProcessError) as e:
        detail=(e.stderr or "").strip().splitlines()[-1] if getattr(e,"stderr","") else "unknown FFmpeg error"
        raise RuntimeError(f"Arrangement processing failed: {detail}") from e

def _duration(path):
    return float(_run([FFPROBE,"-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)]))

def analyze_arrangement(audio, energy_sensitivity=0.55):
    audio=Path(audio)
    if not audio.is_file(): raise ValueError(f"Missing audio: {audio.name}")
    dur=_duration(audio)
    raw=_run([FFMPEG,"-hide_banner","-i",str(audio),"-af","silencedetect=noise=-48dB:d=0.7,astats=metadata=1:reset=1","-f","null","-"])
    rms=[]
    for line in raw.splitlines():
        if "RMS level dB:" in line:
            try:rms.append(float(line.split(":",1)[1].strip()))
            except ValueError:pass
    clean=[x for x in rms if math.isfinite(x)]
    if not clean:
        return {"duration":round(dur,2),"sections":[],"method":"ffmpeg-heuristic","note":"No RMS windows available; section labels unavailable."}
    lo,hi=min(clean),max(clean); span=max(hi-lo,1.0); sens=max(.05,min(1,float(energy_sensitivity)))
    threshold=lo+span*(.45+.25*sens); step=max(1,dur/len(clean)); sections=[];active=None
    for idx,v in enumerate(clean):
        start=idx*step; end=min(dur,start+step); label="chorus" if v>=threshold else ("build" if v>=lo+span*.28 else "verse")
        if active and active["label"]==label:
            active["end"]=round(end,2); active["energy_db"]=round((active["energy_db"]+v)/2,2)
        else:
            if active: sections.append(active)
            active={"label":label,"start":round(start,2),"end":round(end,2),"energy_db":round(v,2)}
    if active: sections.append(active)
    return {"duration":round(dur,2),"sections":sections,"threshold_db":round(threshold,2),"method":"ffmpeg-rms-heuristic","note":"Section labels are heuristic energy estimates, not musical transcription."}

def build_arrangement(source, output_wav, output_mp3, trim_silence=True, intro_fade=2.0, outro_fade=3.0, chorus_lift=0.08, energy_sensitivity=0.55):
    source=Path(source); output_wav=Path(output_wav); output_mp3=Path(output_mp3)
    report=analyze_arrangement(source,energy_sensitivity); dur=report["duration"]
    start,end=0.0,dur
    if trim_silence:
        raw=_run([FFMPEG,"-hide_banner","-i",str(source),"-af","silencedetect=noise=-48dB:d=0.7","-f","null","-"])
        starts=[];ends=[]
        for line in raw.splitlines():
            if "silence_start:" in line:
                try: starts.append(float(line.rsplit(":",1)[1]))
                except ValueError: pass
            if "silence_end:" in line:
                try: ends.append(float(line.rsplit(":",1)[1].split(" |")[0]))
                except ValueError: pass
        if starts and starts[0] <= min(8,dur*.15): start=min(starts[0]+.05,dur)
        if ends and ends[-1] >= dur-min(8,dur*.15): end=max(ends[-1]-.05,start+1)
    length=max(.1,end-start); fi=min(max(0,float(intro_fade)),length/3); fo=min(max(0,float(outro_fade)),length/3); lift=max(0,min(.30,float(chorus_lift)))
    filters=[f"atrim=start={start:g}:end={end:g}","asetpts=PTS-STARTPTS"]
    if fi: filters.append(f"afade=t=in:st=0:d={fi:g}")
    if fo: filters.append(f"afade=t=out:st={max(0,length-fo):g}:d={fo:g}")
    if lift and any(s["label"]=="chorus" for s in report["sections"]): filters.append(f"volume={1+lift:g}")
    filters += ["loudnorm=I=-14:TP=-1:LRA=11","aresample=44100","pan=stereo"]
    output_wav.parent.mkdir(parents=True,exist_ok=True); output_mp3.parent.mkdir(parents=True,exist_ok=True)
    _run([FFMPEG,"-y","-i",str(source),"-af",",".join(filters),"-ar","44100","-ac","2","-c:a","pcm_s24le",str(output_wav)])
    _run([FFMPEG,"-y","-i",str(output_wav),"-codec:a","libmp3lame","-b:a","320k","-ar","44100","-ac","2",str(output_mp3)])
    report.update({"trim_silence":bool(trim_silence),"trim_start":round(start,2),"trim_end":round(end,2),"intro_fade":round(fi,2),"outro_fade":round(fo,2),"chorus_lift":lift,"output_duration":round(length,2)})
    return report
