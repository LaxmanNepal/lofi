"""V4.4 beat/bar-aware automation for existing Demucs stems."""
from __future__ import annotations
import subprocess,wave
from pathlib import Path
from beat_engine import analyze_beats

def duration(p):
    with wave.open(str(p),'rb') as w:return w.getnframes()/w.getframerate()
def clamp(v,a,b):return max(a,min(b,float(v)))
def grid(d,beat,first):
    beat=max(.1,float(beat));t=clamp(first,0,d);beats=[]
    while t<=d+1e-6:beats.append(round(t,4));t+=beat
    return beats,[beats[i] for i in range(0,len(beats),4)]
def section(sections,t):
    for s in sections:
        if float(s.get('start',0))<=t<=float(s.get('end',0)):return str(s.get('label','verse')).lower()
    return 'verse'
def gain_expr(bars,beat,d,sections,kind,pulse,chorus,transition):
    expr='1'
    for s in reversed(bars):
        e=min(d,s+beat*4);lab=section(sections,s+beat*2);g=1
        if lab in ('chorus','final chorus'):g+=chorus
        if lab=='bridge':g*=.92
        if lab in ('intro','outro'):g*=.85
        if kind=='drums':
            a=s+beat*3.55;b=min(e,s+beat*4);gexpr=f"{g:.5f}*(1+{clamp(pulse,0,1)*.30:.5f}*if(between(t,{a:.4f},{b:.4f}),1,0))"
        else:gexpr=f'{g:.5f}'
        if transition:
            f=min(transition*beat,beat*1.5);r=f"if(between(t,{s:.4f},{s+f:.4f}),(t-{s:.4f})/{f:.5f},if(between(t,{e-f:.4f},{e:.4f}),({e:.4f}-t)/{f:.5f},1))";gexpr=f'({gexpr})*({r})'
        expr=f'if(between(t,{s:.4f},{e:.4f}),{gexpr},{expr})'
    return expr

def analyze_rhythm(path,sections=None,bpm_override=None,beat_override=None,first_override=None):
    info=analyze_beats(path,sections or []);bpm=float(bpm_override or info['bpm']);beat=float(beat_override or 60/bpm);first=float(info['estimated_first_beat'] if first_override is None else first_override);beats,bars=grid(info['duration'],beat,first);snapped=[]
    for s in sections or []:
        a=first+round((float(s.get('start',0))-first)/beat)*beat;b=first+round((float(s.get('end',info['duration']))-first)/beat)*beat;a=clamp(a,0,info['duration']);b=clamp(max(a,b),0,info['duration']);snapped.append({**s,'start':round(a,3),'end':round(b,3),'beat_aligned':True})
    return {**info,'bpm':round(bpm,2),'beat_seconds':round(beat,4),'estimated_first_beat':round(first,3),'beats':beats,'bar_starts':bars,'bar_count':len(bars),'snapped_sections':snapped,'method':'V4.4 beat/bar automation heuristic'}

def build_rhythm_arrangement(stems,wav_out,mp3_out,structure,bpm,beat_seconds,first_beat,drum_pulse=.35,chorus_lift=.10,bass_transition=.10,melody_transition=.10,bar_transition=1,ducking=.15,intro_outro_fade_bars=1,target_lufs=-14,true_peak=-1):
    req=('vocals','drums','bass','other');stems={k:Path(stems[k]) for k in req}
    if any(not p.is_file() for p in stems.values()):raise ValueError('Prepare all four Demucs stems first.')
    d=min(duration(p) for p in stems.values());beat=float(beat_seconds or 60/max(1,float(bpm)));beats,bars=grid(d,beat,float(first_beat or 0));secs=structure or [{'label':'full','start':0,'end':d}];tr=max(0,int(bar_transition));de=gain_expr(bars,beat,d,secs,'drums',drum_pulse,chorus_lift,tr);be=gain_expr(bars,beat,d,secs,'bass',0,bass_transition,tr);oe=gain_expr(bars,beat,d,secs,'other',0,melody_transition,tr);fade=max(0,int(intro_outro_fade_bars))*beat;vf=f'fade=t=in:d={fade:.3f},afade=t=out:st={max(0,d-fade):.3f}:d={fade:.3f}' if fade else 'anull';duck=clamp(ducking,0,.8);fc=(f'[0:a]atrim=duration={d:.3f},asetpts=PTS-STARTPTS,{vf}[v];[1:a]atrim=duration={d:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume="{de}"[dr];[2:a]atrim=duration={d:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume="{be}"[ba];[3:a]atrim=duration={d:.3f},asetpts=PTS-STARTPTS,volume=eval=frame:volume="{oe}"[ot];[dr][ba][ot]amix=inputs=3:normalize=0[inst];[inst][v]sidechaincompress=threshold={-24+duck*10:.2f}dB:ratio={1+duck*5:.2f}:attack=20:release=180:makeup=1:mix=1[di];[v][di]amix=inputs=2:normalize=0,loudnorm=I={float(target_lufs):.2f}:TP={float(true_peak):.2f}:LRA=11,aresample=44100[a]');wav_out=Path(wav_out);mp3_out=Path(mp3_out);wav_out.parent.mkdir(parents=True,exist_ok=True);mp3_out.parent.mkdir(parents=True,exist_ok=True)
    try:
        subprocess.run(['ffmpeg','-y','-i',str(stems['vocals']),'-i',str(stems['drums']),'-i',str(stems['bass']),'-i',str(stems['other']),'-filter_complex',fc,'-map','[a]','-ar','44100','-ac','2','-c:a','pcm_s24le',str(wav_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);subprocess.run(['ffmpeg','-y','-i',str(wav_out),'-ar','44100','-ac','2','-c:a','libmp3lame','-b:a','320k',str(mp3_out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    except FileNotFoundError as e:raise RuntimeError('FFmpeg is not installed in the runtime.') from e
    except subprocess.CalledProcessError as e:raise RuntimeError('V4.4 rhythm arrangement failed: '+(e.stderr.strip().splitlines()[-1] if e.stderr else 'unknown FFmpeg error')) from e
    return {'duration':round(d,3),'bpm':round(float(bpm),2),'beat_seconds':round(beat,4),'first_beat':round(float(first_beat),3),'beats':beats,'bar_starts':bars,'bar_count':len(bars),'sections':secs,'controls':{'drum_pulse':drum_pulse,'chorus_lift':chorus_lift,'bass_transition':bass_transition,'melody_transition':melody_transition,'bar_transition':bar_transition,'ducking':ducking,'intro_outro_fade_bars':intro_outro_fade_bars,'target_lufs':target_lufs,'true_peak':true_peak},'method':'Demucs four stems + beat/bar-synced FFmpeg automation','note':'Drum fills are gain accents on existing drums; no new instruments or voices are synthesized.'}
