import base64,os,random,re,time,subprocess
from pathlib import Path
import torch
from fastapi import FastAPI,Header,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from acestep.pipeline_ace_step import ACEStepPipeline
from audio_engine import export_mp3,master_audio
from lyric_engine import LyricRequest,compose_lyrics,unload_model
from seo_engine import build_seo
from package_engine import build_package
from stem_engine import separate_stems
from video_engine import build_visualizer,file_base64
from lyric_video_engine import build_lyric_video
from timing_engine import time_lyrics
from mix_engine import build_mix_master
from vocal_enhance_engine import enhance_vocal
from arrangement_engine import build_arrangement,analyze_arrangement
API_KEY=os.getenv("LAXMAN_LOFI_API_KEY","");CHECKPOINT_DIR=os.getenv("ACE_CHECKPOINT_DIR","/content/ace-checkpoints");DEVICE_ID=int(os.getenv("ACE_DEVICE_ID","0"));BF16=os.getenv("ACE_BF16","true").lower()=="true";OUTPUT_DIR=Path(os.getenv("LAXMAN_LOFI_OUTPUT_DIR","/content/laxman_lofi_output"))
app=FastAPI(title="Laxman Lofi AI Studio API",version="3.8.0");app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"]);pipeline=None
class ComposeRequest(BaseModel):
 idea:str=Field(min_length=3,max_length=1000);mood:str=Field(default="emotional",max_length=50);language:str=Field(default="Nepali",max_length=30);voice:str=Field(default="male",max_length=20);duration:int=Field(default=180,ge=30,le=300);style:str=Field(default="warm piano, mellow guitar, dusty vinyl texture",max_length=500)
class GenerateRequest(BaseModel):
 prompt:str=Field(min_length=3,max_length=3000);lyrics:str="";audio_duration:float=Field(default=180,ge=10,le=300);duration:float=Field(default=180,ge=10,le=300);voice_mode:str="male";language:str="nepali";seed:int|None=None
class MasterRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");duration:float=Field(default=180,ge=10,le=300);fade_in:float=Field(default=2,ge=0,le=10);fade_out:float=Field(default=3,ge=0,le=10)
class SEORequest(BaseModel):
 title:str=Field(min_length=1,max_length=200);story:str=Field(default="",max_length=2000);lyrics:str=Field(default="",max_length=8000);mood:str=Field(default="emotional",max_length=50);language:str=Field(default="Nepali",max_length=30)
class CoverRequest(BaseModel):
 prompt:str=Field(min_length=3,max_length=1500);seed:int|None=None
class StemRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");model:str=Field(default="htdemucs",max_length=50)
class StemMixRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");vocal_gain:float=Field(default=1,ge=0,le=2);instrumental_gain:float=Field(default=1,ge=0,le=2);vocal_pan:float=Field(default=0,ge=-1,le=1)
class MixMasterRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");vocal_gain:float=Field(default=1,ge=0,le=2);instrumental_gain:float=Field(default=1,ge=0,le=2);vocal_pan:float=Field(default=0,ge=-1,le=1);cleanup:float=Field(default=.35,ge=0,le=1);warmth:float=Field(default=.25,ge=-1,le=1);presence:float=Field(default=.2,ge=-1,le=1);compression:float=Field(default=.35,ge=0,le=1);deessing:float=Field(default=.2,ge=0,le=1);stereo_width:float=Field(default=1,ge=0,le=1.5);target_lufs:float=Field(default=-14,ge=-18,le=-9);true_peak:float=Field(default=-1,ge=-3,le=-.1)
class VocalEnhanceRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");denoise:float=Field(default=.35,ge=0,le=1);derverb:float=Field(default=.2,ge=0,le=1);breath_control:float=Field(default=.2,ge=0,le=1);presence:float=Field(default=.3,ge=0,le=1);deesser:float=Field(default=.25,ge=0,le=1);ducking:float=Field(default=0,ge=0,le=1)
class ArrangementRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");trim_silence:bool=True;intro_fade:float=Field(default=2,ge=0,le=10);outro_fade:float=Field(default=3,ge=0,le=10);chorus_lift:float=Field(default=.08,ge=0,le=.30);energy_sensitivity:float=Field(default=.55,ge=.05,le=1)
class PackageRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");title:str=Field(min_length=1,max_length=200);metadata:dict={};seo:dict|None=None;cover_base64:str|None=None
class VideoRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");title:str=Field(min_length=1,max_length=200);cover_base64:str|None=None;overlay_title:bool=True;show_waveform:bool=True
class TimingRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");lyrics:str=Field(min_length=1,max_length=12000);model_size:str=Field(default="small",max_length=30);language:str|None=None
class LyricVideoRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$");title:str=Field(min_length=1,max_length=200);lyrics:str=Field(min_length=1,max_length=12000);cover_base64:str|None=None;timing:list[dict]|None=None;theme:str=Field(default="night",pattern=r"^(night|warm|minimal|nepal)$");karaoke:bool=True;intro_seconds:float=Field(default=2,ge=0,le=10);outro_seconds:float=Field(default=2,ge=0,le=10);waveform:bool=True
def check_key(authorization:str|None):
 if API_KEY and authorization!=f"Bearer {API_KEY}":raise HTTPException(status_code=401,detail="Invalid API key")
def load_pipeline():
 global pipeline
 if pipeline is None:
  os.environ["CUDA_VISIBLE_DEVICES"]=str(DEVICE_ID);Path(CHECKPOINT_DIR).mkdir(parents=True,exist_ok=True);pipeline=ACEStepPipeline(checkpoint_dir=CHECKPOINT_DIR,dtype="bfloat16" if BF16 else "float32",torch_compile=False)
 return pipeline
def source_path(i:str)->Path:return OUTPUT_DIR/f"{i}.wav"
def master_paths(i:str):return OUTPUT_DIR/f"{i}_master.wav",OUTPUT_DIR/f"{i}_master.mp3"
def stem_dir(i:str)->Path:return OUTPUT_DIR/"stems"/i
def stem_paths(i:str):return stem_dir(i)/"vocals.wav",stem_dir(i)/"instrumental.wav"
def video_path(i:str)->Path:return OUTPUT_DIR/"videos"/f"{i}.mp4"
def lyric_video_path(i:str)->Path:return OUTPUT_DIR/"videos"/f"{i}-lyrics.mp4"
def arrangement_paths(i:str):return OUTPUT_DIR/"arranged"/i/"SMART-ARRANGEMENT.wav",OUTPUT_DIR/"arranged"/i/"SMART-ARRANGEMENT-320kbps.mp3"
def audio_b64(p:Path):return base64.b64encode(p.read_bytes()).decode("ascii")
@app.get("/health")
def health():return {"status":"healthy","version":"3.8.0","model":"ACE-Step v1 3.5B","lyric_model":os.getenv("LYRIC_MODEL_ID","ministral/Ministral-3b-instruct"),"cuda":torch.cuda.is_available(),"audio_mastering":"ffmpeg","cover_art":"sdxl","stem_separation":"demucs","video_export":"ffmpeg","lyric_video":"ffmpeg+ass","lyric_timing":"faster-whisper","vocal_enhancement":"ffmpeg-dsp","mix_master":"ffmpeg-dsp","smart_arrangement":"ffmpeg-rms-heuristic","package_export":"zip"}
@app.post("/arrangement/analyze")
def arrangement_analyze(req:ArrangementRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 try:return {"status":"success","output_id":req.output_id,**analyze_arrangement(s,req.energy_sensitivity)}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
@app.post("/arrangement")
def arrangement(req:ArrangementRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 w,m=arrangement_paths(req.output_id)
 try:
  info=build_arrangement(s,w,m,req.trim_silence,req.intro_fade,req.outro_fade,req.chorus_lift,req.energy_sensitivity)
  return {"status":"success","output_id":req.output_id,"wav_file_name":w.name,"mp3_file_name":m.name,"wav_base64":audio_b64(w),"mp3_base64":audio_b64(m),"wav_mime_type":"audio/wav","mp3_mime_type":"audio/mpeg",**info}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
@app.post("/vocal-enhance")
def vocal_enhance(req:VocalEnhanceRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);v,_=stem_paths(req.output_id)
 if not v.is_file():raise HTTPException(status_code=404,detail="Separate vocals and instrumental stems first.")
 out=OUTPUT_DIR/"enhanced"/req.output_id/"ENHANCED-VOCAL.wav"
 try:
  info=enhance_vocal(v,out,req.denoise,req.derverb,req.breath_control,req.presence,req.deesser,req.ducking);return {"status":"success","output_id":req.output_id,"file_name":out.name,"mime_type":"audio/wav","audio_base64":audio_b64(out),**info}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
@app.post("/mix-master")
def mix_master(req:MixMasterRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);v,i=stem_paths(req.output_id)
 if not v.is_file() or not i.is_file():raise HTTPException(status_code=404,detail="Separate vocals and instrumental stems first.")
 d=OUTPUT_DIR/"mixes"/req.output_id;w=d/"FINAL-MASTER.wav";m=d/"FINAL-MASTER-320kbps.mp3"
 try:
  info=build_mix_master(v,i,w,m,req.vocal_gain,req.instrumental_gain,req.vocal_pan,req.cleanup,req.warmth,req.presence,req.compression,req.deessing,req.stereo_width,req.target_lufs,req.true_peak);return {"status":"success","output_id":req.output_id,"wav_file_name":w.name,"mp3_file_name":m.name,"wav_base64":audio_b64(w),"mp3_base64":audio_b64(m),"wav_mime_type":"audio/wav","mp3_mime_type":"audio/mpeg",**info}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
@app.post("/compose")
def compose(req:ComposeRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:return compose_lyrics(LyricRequest(idea=req.idea,mood=req.mood,language=req.language,voice=req.voice,duration=req.duration,style=req.style))
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Lyric AI failed: {e}") from e
@app.post("/generate")
def generate(req:GenerateRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);lyrics="[inst]" if req.voice_mode=="instrumental" else req.lyrics.strip()
 if req.voice_mode!="instrumental" and not lyrics:raise HTTPException(status_code=400,detail="Original lyrics are required for vocal generation.")
 unload_model();seed=req.seed if req.seed is not None else random.randint(1,2147483647);OUTPUT_DIR.mkdir(parents=True,exist_ok=True);output_id=f"lofi_{int(time.time())}_{seed}_{random.randint(1000,9999)}";out=source_path(output_id);p=load_pipeline()
 try:p(*(float(req.audio_duration),req.prompt,lyrics,27,7.0,"euler","cfg",1.0,str(seed),1.0,0.0,1.0,False,False,True,"",0.0,0.0),save_path=str(out))
 except Exception as e:
  if torch.cuda.is_available():torch.cuda.empty_cache()
  raise HTTPException(status_code=500,detail=f"ACE-Step generation failed: {e}") from e
 return {"status":"success","audio_base64":audio_b64(out),"mime_type":"audio/wav","seed":seed,"duration":req.audio_duration,"model":"ACE-Step v1 3.5B","output_id":output_id}
@app.get("/audio/{file_name}")
def audio(file_name:str,authorization:str|None=Header(default=None)):
 check_key(authorization)
 if not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:wav|mp3)",file_name):raise HTTPException(status_code=400,detail="Invalid audio filename")
 p=OUTPUT_DIR/file_name
 if not p.is_file():raise HTTPException(status_code=404,detail="Audio file not found. The Colab runtime may have expired.")
 return FileResponse(p,media_type="audio/mpeg" if p.suffix.lower()==".mp3" else "audio/wav",filename=p.name)
@app.post("/master")
def master(req:MasterRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found. Generate the song again if the runtime expired.")
 w,m=master_paths(req.output_id)
 try:master_audio(s,w,req.duration,req.fade_in,req.fade_out);export_mp3(w,m)
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
 return {"status":"success","output_id":req.output_id,"wav_base64":audio_b64(w),"mp3_base64":audio_b64(m),"wav_mime_type":"audio/wav","mp3_mime_type":"audio/mpeg","target":"approximately -14 LUFS / -1 dBTP","sample_rate":44100,"wav_bit_depth":24,"mp3_bitrate":"320 kbps","fade_in":req.fade_in,"fade_out":req.fade_out}
@app.post("/stems")
def stems(req:StemRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found. Generate the song again if the runtime expired.")
 try:
  paths=separate_stems(s,OUTPUT_DIR/"stems"/req.output_id,req.model);return {"status":"success","output_id":req.output_id,"model":req.model,"stems":{n:{"file_name":p.name,"mime_type":"audio/wav","audio_base64":audio_b64(p)} for n,p in paths.items()}}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Stem separation failed: {e}") from e
@app.post("/stem-mix")
def stem_mix(req:StemMixRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);v,i=stem_paths(req.output_id)
 if not v.is_file() or not i.is_file():raise HTTPException(status_code=404,detail="Separate vocals and instrumental stems first.")
 out=stem_dir(req.output_id)/"custom_mix.wav"
 try:
  pan=max(-1,min(1,req.vocal_pan));l=1-pan if pan>=0 else 1;r=1+pan if pan<=0 else 1;fc=f"[0:a]volume={req.vocal_gain:g},pan=stereo|c0={l:g}*c0|c1={r:g}*c1[v];[1:a]volume={req.instrumental_gain:g}[i];[v][i]amix=inputs=2:duration=longest:normalize=0[a]";subprocess.run(["ffmpeg","-y","-i",str(v),"-i",str(i),"-filter_complex",fc,"-map","[a]","-ar","44100","-ac","2","-c:a","pcm_s24le",str(out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);return {"status":"success","file_name":out.name,"mime_type":"audio/wav","audio_base64":audio_b64(out),"vocal_gain":req.vocal_gain,"instrumental_gain":req.instrumental_gain,"vocal_pan":req.vocal_pan}
 except Exception as e:raise HTTPException(status_code=500,detail=f"Custom stem mix failed: {e}") from e
@app.post("/seo")
def seo(req:SEORequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:return build_seo(req.title,req.story,req.lyrics,req.mood,req.language)
 except Exception as e:raise HTTPException(status_code=500,detail=f"SEO generation failed: {e}") from e
@app.post("/cover")
def cover(req:CoverRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:
  from cover_engine import generate_cover
  b,s=generate_cover(req.prompt,req.seed);return {"status":"success","image_base64":b,"mime_type":"image/png","width":1024,"height":576,"seed":s,"model":os.getenv("COVER_MODEL_ID","stabilityai/stable-diffusion-xl-base-1.0"),"originality_note":"AI-generated cover draft. Review before publishing."}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Cover generation failed: {e}") from e
@app.post("/video")
def video(req:VideoRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 c=OUTPUT_DIR/"videos"/f"{req.output_id}-cover.png"
 if req.cover_base64:
  try:c.parent.mkdir(parents=True,exist_ok=True);c.write_bytes(base64.b64decode(req.cover_base64))
  except Exception as e:raise HTTPException(status_code=400,detail="Invalid cover image data.") from e
 if not c.is_file():raise HTTPException(status_code=400,detail="Generate or provide cover art first.")
 o=video_path(req.output_id)
 try:build_visualizer(s,c,o,req.title,overlay_title=req.overlay_title,show_waveform=req.show_waveform);return {"status":"success","output_id":req.output_id,"file_name":o.name,"mime_type":"video/mp4","width":1920,"height":1080,"video_base64":file_base64(o),"codec":"H.264 + AAC","youtube_ready":True}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Video export failed: {e}") from e
@app.post("/lyric-timing")
def lyric_timing(req:TimingRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 try:return time_lyrics(s,req.lyrics,300,req.model_size,req.language)
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"ASR timing failed: {e}") from e
@app.post("/lyric-video")
def lyric_video(req:LyricVideoRequest,authorization:str|None=Header(default=None)):
 check_key(authorization);s=source_path(req.output_id)
 if not s.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 c=OUTPUT_DIR/"videos"/f"{req.output_id}-cover.png"
 if req.cover_base64:
  try:c.parent.mkdir(parents=True,exist_ok=True);c.write_bytes(base64.b64decode(req.cover_base64))
  except Exception as e:raise HTTPException(status_code=400,detail="Invalid cover image data.") from e
 if not c.is_file():raise HTTPException(status_code=400,detail="Generate or provide cover art first.")
 o=lyric_video_path(req.output_id)
 try:
  info=build_lyric_video(s,c,o,req.lyrics,req.title,theme=req.theme,karaoke=req.karaoke,intro=req.intro_seconds,outro=req.outro_seconds,waveform=req.waveform,timing=req.timing);return {"status":"success","output_id":req.output_id,"file_name":o.name,"mime_type":"video/mp4","width":1920,"height":1080,"video_base64":file_base64(o),"codec":"H.264 + AAC + ASS lyrics","youtube_ready":True,**info}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except RuntimeError as e:raise HTTPException(status_code=500,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Lyric video export failed: {e}") from e
@app.post("/package")
def package(req:PackageRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:
  b,f=build_package(OUTPUT_DIR,req.output_id,req.title,req.metadata,req.seo,req.cover_base64);return {"status":"success","filename":f,"mime_type":"application/zip","package_base64":b}
 except ValueError as e:raise HTTPException(status_code=400,detail=str(e)) from e
 except Exception as e:raise HTTPException(status_code=500,detail=f"Package export failed: {e}") from e
