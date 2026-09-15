import base64
import os
import random
import re
import time
import subprocess
from pathlib import Path
import torch
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from acestep.pipeline_ace_step import ACEStepPipeline
from audio_engine import export_mp3, master_audio
from lyric_engine import LyricRequest, compose_lyrics, unload_model
from seo_engine import build_seo
from package_engine import build_package
from stem_engine import separate_stems
from video_engine import build_visualizer, file_base64

API_KEY=os.getenv("LAXMAN_LOFI_API_KEY","")
CHECKPOINT_DIR=os.getenv("ACE_CHECKPOINT_DIR","/content/ace-checkpoints")
DEVICE_ID=int(os.getenv("ACE_DEVICE_ID","0")); BF16=os.getenv("ACE_BF16","true").lower()=="true"
OUTPUT_DIR=Path(os.getenv("LAXMAN_LOFI_OUTPUT_DIR","/content/laxman_lofi_output"))
app=FastAPI(title="Laxman Lofi AI Studio API",version="3.1.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
pipeline=None
class ComposeRequest(BaseModel):
 idea:str=Field(min_length=3,max_length=1000); mood:str=Field(default="emotional",max_length=50); language:str=Field(default="Nepali",max_length=30); voice:str=Field(default="male",max_length=20); duration:int=Field(default=180,ge=30,le=300); style:str=Field(default="warm piano, mellow guitar, dusty vinyl texture",max_length=500)
class GenerateRequest(BaseModel):
 prompt:str=Field(min_length=3,max_length=3000); lyrics:str=""; audio_duration:float=Field(default=180,ge=10,le=300); duration:float=Field(default=180,ge=10,le=300); voice_mode:str="male"; language:str="nepali"; seed:int|None=None
class MasterRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$"); duration:float=Field(default=180,ge=10,le=300); fade_in:float=Field(default=2,ge=0,le=10); fade_out:float=Field(default=3,ge=0,le=10)
class SEORequest(BaseModel):
 title:str=Field(min_length=1,max_length=200); story:str=Field(default="",max_length=2000); lyrics:str=Field(default="",max_length=8000); mood:str=Field(default="emotional",max_length=50); language:str=Field(default="Nepali",max_length=30)
class CoverRequest(BaseModel):
 prompt:str=Field(min_length=3,max_length=1500); seed:int|None=None
class StemRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$"); model:str=Field(default="htdemucs",max_length=50)
class StemMixRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$"); vocal_gain:float=Field(default=1.0,ge=0,le=2); instrumental_gain:float=Field(default=1.0,ge=0,le=2); vocal_pan:float=Field(default=0,ge=-1,le=1)
class PackageRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$"); title:str=Field(min_length=1,max_length=200); metadata:dict={}; seo:dict|None=None; cover_base64:str|None=None
class VideoRequest(BaseModel):
 output_id:str=Field(min_length=8,max_length=100,pattern=r"^[A-Za-z0-9_-]+$"); title:str=Field(min_length=1,max_length=200); cover_base64:str|None=None; overlay_title:bool=True; show_waveform:bool=True
def check_key(authorization:str|None):
 if API_KEY and authorization!=f"Bearer {API_KEY}": raise HTTPException(status_code=401,detail="Invalid API key")
def load_pipeline():
 global pipeline
 if pipeline is None:
  os.environ["CUDA_VISIBLE_DEVICES"]=str(DEVICE_ID); Path(CHECKPOINT_DIR).mkdir(parents=True,exist_ok=True); pipeline=ACEStepPipeline(checkpoint_dir=CHECKPOINT_DIR,dtype="bfloat16" if BF16 else "float32",torch_compile=False)
 return pipeline
def source_path(output_id:str)->Path:return OUTPUT_DIR/f"{output_id}.wav"
def master_paths(output_id:str)->tuple[Path,Path]:return OUTPUT_DIR/f"{output_id}_master.wav",OUTPUT_DIR/f"{output_id}_master.mp3"
def stem_dir(output_id:str)->Path:return OUTPUT_DIR/"stems"/output_id
def stem_paths(output_id:str)->tuple[Path,Path]:return stem_dir(output_id)/"vocals.wav",stem_dir(output_id)/"instrumental.wav"
def video_path(output_id:str)->Path:return OUTPUT_DIR/"videos"/f"{output_id}.mp4"
def audio_b64(path:Path)->str:return base64.b64encode(path.read_bytes()).decode("ascii")
@app.get("/health")
def health():return {"status":"healthy","version":"3.1.0","model":"ACE-Step v1 3.5B","lyric_model":os.getenv("LYRIC_MODEL_ID","ministral/Ministral-3b-instruct"),"cuda":torch.cuda.is_available(),"audio_mastering":"ffmpeg","cover_art":"sdxl","stem_separation":"demucs","video_export":"ffmpeg","package_export":"zip"}
@app.post("/compose")
def compose(req:ComposeRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:return compose_lyrics(LyricRequest(idea=req.idea,mood=req.mood,language=req.language,voice=req.voice,duration=req.duration,style=req.style))
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Lyric AI failed: {exc}") from exc
@app.post("/generate")
def generate(req:GenerateRequest,authorization:str|None=Header(default=None)):
 check_key(authorization); lyrics="[inst]" if req.voice_mode=="instrumental" else req.lyrics.strip()
 if req.voice_mode!="instrumental" and not lyrics:raise HTTPException(status_code=400,detail="Original lyrics are required for vocal generation.")
 unload_model(); seed=req.seed if req.seed is not None else random.randint(1,2147483647); OUTPUT_DIR.mkdir(parents=True,exist_ok=True); output_id=f"lofi_{int(time.time())}_{seed}_{random.randint(1000,9999)}"; output_path=source_path(output_id); p=load_pipeline()
 try:p(*(float(req.audio_duration),req.prompt,lyrics,27,7.0,"euler","cfg",1.0,str(seed),1.0,0.0,1.0,False,False,True,"",0.0,0.0),save_path=str(output_path))
 except Exception as exc:
  if torch.cuda.is_available():torch.cuda.empty_cache()
  raise HTTPException(status_code=500,detail=f"ACE-Step generation failed: {exc}") from exc
 return {"status":"success","audio_base64":audio_b64(output_path),"mime_type":"audio/wav","seed":seed,"duration":req.audio_duration,"model":"ACE-Step v1 3.5B","output_id":output_id}
@app.get("/audio/{file_name}")
def audio(file_name:str,authorization:str|None=Header(default=None)):
 check_key(authorization)
 if not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:wav|mp3)",file_name):raise HTTPException(status_code=400,detail="Invalid audio filename")
 path=OUTPUT_DIR/file_name
 if not path.is_file():raise HTTPException(status_code=404,detail="Audio file not found. The Colab runtime may have expired.")
 return FileResponse(path,media_type="audio/mpeg" if path.suffix.lower()==".mp3" else "audio/wav",filename=path.name)
@app.post("/master")
def master(req:MasterRequest,authorization:str|None=Header(default=None)):
 check_key(authorization); source=source_path(req.output_id)
 if not source.is_file():raise HTTPException(status_code=404,detail="Source audio not found. Generate the song again if the runtime expired.")
 master_wav,master_mp3=master_paths(req.output_id)
 try:master_audio(source,master_wav,req.duration,req.fade_in,req.fade_out); export_mp3(master_wav,master_mp3)
 except RuntimeError as exc:raise HTTPException(status_code=500,detail=str(exc)) from exc
 return {"status":"success","output_id":req.output_id,"wav_base64":audio_b64(master_wav),"mp3_base64":audio_b64(master_mp3),"wav_mime_type":"audio/wav","mp3_mime_type":"audio/mpeg","target":"approximately -14 LUFS / -1 dBTP","sample_rate":44100,"wav_bit_depth":24,"mp3_bitrate":"320 kbps","fade_in":req.fade_in,"fade_out":req.fade_out}
@app.post("/stems")
def stems(req:StemRequest,authorization:str|None=Header(default=None)):
 check_key(authorization); source=source_path(req.output_id)
 if not source.is_file():raise HTTPException(status_code=404,detail="Source audio not found. Generate the song again if the runtime expired.")
 try:
  paths=separate_stems(source,OUTPUT_DIR/"stems"/req.output_id,req.model)
  return {"status":"success","output_id":req.output_id,"model":req.model,"stems":{name:{"file_name":path.name,"mime_type":"audio/wav","audio_base64":audio_b64(path)} for name,path in paths.items()}}
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 except RuntimeError as exc:raise HTTPException(status_code=500,detail=str(exc)) from exc
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Stem separation failed: {exc}") from exc
@app.post("/stem-mix")
def stem_mix(req:StemMixRequest,authorization:str|None=Header(default=None)):
 check_key(authorization); vocals,instrumental=stem_paths(req.output_id)
 if not vocals.is_file() or not instrumental.is_file():raise HTTPException(status_code=404,detail="Separate vocals and instrumental stems first.")
 out=stem_dir(req.output_id)/"custom_mix.wav"
 try:
  vpan=max(-1.0,min(1.0,req.vocal_pan)); left=1.0-vpan if vpan>=0 else 1.0; right=1.0+vpan if vpan<=0 else 1.0
  filter_complex=f"[0:a]volume={req.vocal_gain:g},pan=stereo|c0={left:g}*c0|c1={right:g}*c1[v];[1:a]volume={req.instrumental_gain:g}[i];[v][i]amix=inputs=2:duration=longest:normalize=0[a]"
  subprocess.run(["ffmpeg","-y","-i",str(vocals),"-i",str(instrumental),"-filter_complex",filter_complex,"-map","[a]","-ar","44100","-ac","2","-c:a","pcm_s24le",str(out)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  return {"status":"success","file_name":out.name,"mime_type":"audio/wav","audio_base64":audio_b64(out),"vocal_gain":req.vocal_gain,"instrumental_gain":req.instrumental_gain,"vocal_pan":req.vocal_pan}
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Custom stem mix failed: {exc}") from exc
@app.post("/seo")
def seo(req:SEORequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:return build_seo(req.title,req.story,req.lyrics,req.mood,req.language)
 except Exception as exc:raise HTTPException(status_code=500,detail=f"SEO generation failed: {exc}") from exc
@app.post("/cover")
def cover(req:CoverRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:
  from cover_engine import generate_cover
  image_base64,seed=generate_cover(req.prompt,req.seed)
  return {"status":"success","image_base64":image_base64,"mime_type":"image/png","width":1024,"height":576,"seed":seed,"model":os.getenv("COVER_MODEL_ID","stabilityai/stable-diffusion-xl-base-1.0"),"originality_note":"AI-generated cover draft. Review before publishing."}
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Cover generation failed: {exc}") from exc
@app.post("/video")
def video(req:VideoRequest,authorization:str|None=Header(default=None)):
 check_key(authorization); source=source_path(req.output_id)
 if not source.is_file():raise HTTPException(status_code=404,detail="Source audio not found.")
 cover_path=OUTPUT_DIR/"videos"/f"{req.output_id}-cover.png"
 if req.cover_base64:
  try:cover_path.parent.mkdir(parents=True,exist_ok=True);cover_path.write_bytes(base64.b64decode(req.cover_base64))
  except Exception as exc:raise HTTPException(status_code=400,detail="Invalid cover image data.") from exc
 if not cover_path.is_file():raise HTTPException(status_code=400,detail="Generate or provide cover art first.")
 out=video_path(req.output_id)
 try:
  build_visualizer(source,cover_path,out,req.title,overlay_title=req.overlay_title,show_waveform=req.show_waveform)
  return {"status":"success","output_id":req.output_id,"file_name":out.name,"mime_type":"video/mp4","width":1920,"height":1080,"video_base64":file_base64(out),"codec":"H.264 + AAC","youtube_ready":True}
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 except RuntimeError as exc:raise HTTPException(status_code=500,detail=str(exc)) from exc
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Video export failed: {exc}") from exc
@app.post("/package")
def package(req:PackageRequest,authorization:str|None=Header(default=None)):
 check_key(authorization)
 try:
  package_base64,filename=build_package(OUTPUT_DIR,req.output_id,req.title,req.metadata,req.seo,req.cover_base64)
  return {"status":"success","filename":filename,"mime_type":"application/zip","package_base64":package_base64}
 except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc)) from exc
 except Exception as exc:raise HTTPException(status_code=500,detail=f"Package export failed: {exc}") from exc
