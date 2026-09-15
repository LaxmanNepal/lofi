const $ = (id) => document.getElementById(id);
const API_KEY = 'laxman-lofi-api-url';
const KEY_KEY = 'laxman-lofi-api-key';
const HISTORY_KEY = 'laxman-lofi-history-v1';
let selectedMood = 'emotional';
let lastGeneration = null;

function getApi(){ return (localStorage.getItem(API_KEY) || '').replace(/\/$/,''); }
function setState(online){ $('apiState').textContent = online ? 'API online' : 'API offline'; $('apiState').className = `status ${online?'online':'offline'}`; }
function authHeaders(){ const k=localStorage.getItem(KEY_KEY)||''; return k?{'Authorization':`Bearer ${k}`}:{ }; }
function readHistory(){ try{return JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');}catch{return[];} }
function writeHistory(items){ localStorage.setItem(HISTORY_KEY,JSON.stringify(items.slice(0,30))); }
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}

$('settingsBtn').onclick=()=>{ $('apiUrl').value=getApi(); $('apiKey').value=localStorage.getItem(KEY_KEY)||''; $('settingsDialog').showModal(); };
$('saveSettings').onclick=()=>{ localStorage.setItem(API_KEY,$('apiUrl').value.trim()); localStorage.setItem(KEY_KEY,$('apiKey').value.trim()); setState(!!getApi()); health(); };
$('historyBtn').onclick=()=>{ $('historyPanel').classList.toggle('hidden'); renderHistory(); if(!$('historyPanel').classList.contains('hidden')) $('historyPanel').scrollIntoView({behavior:'smooth'}); };
$('clearHistory').onclick=()=>{ if(confirm('Clear all saved generation records from this browser?')){writeHistory([]);renderHistory();} };
for(const chip of document.querySelectorAll('.chip')) chip.onclick=()=>{ document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); selectedMood=chip.dataset.value; };
$('newBtn').onclick=()=>{ $('result').classList.add('hidden'); $('audio').removeAttribute('src'); $('songTitle').value=''; $('lyrics').value=''; lastGeneration=null; resetMasterUI(); $('idea').focus(); window.scrollTo({top:0,behavior:'smooth'}); };
$('formatBtn').onclick=()=>{ let v=$('lyrics').value.trim(); if(!v)return; if(!/^\[verse\]/im.test(v))v='[verse]\n'+v; $('lyrics').value=v; };

async function health(){ const url=getApi(); if(!url){setState(false);return;} try{const r=await fetch(`${url}/health`,{headers:authHeaders()});setState(r.ok);}catch{setState(false);} }
function stylePrompt(){ const bpm={slow:'65–75 BPM',mid:'75–85 BPM',upbeat:'85–100 BPM'}[$('tempo').value]; const vocal=$('voice').value==='instrumental'?'instrumental only':`${$('voice').value} vocal`; const idea=$('idea').value.trim(); return `${idea ? `Song story: ${idea}. ` : ''}${$('style').value}, ${selectedMood} mood, ${bpm}, ${vocal}, ${$('language').value} music, original composition, intimate late-night lofi production`; }

$('composeBtn').onclick=async()=>{
  const api=getApi(); if(!api){$('settingsDialog').showModal();return;}
  const idea=$('idea').value.trim(); if(!idea){alert('Write the song story/idea first.');$('idea').focus();return;}
  const btn=$('composeBtn');btn.disabled=true;$('progress').classList.remove('hidden');$('progressText').textContent='Writing original lyrics with the AI model…';
  try{
    const payload={idea,mood:selectedMood,language:$('language').value,voice:$('voice').value,duration:Number($('duration').value),style:$('style').value};
    const res=await fetch(`${api}/compose`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
    if(!res.ok){let d='Lyric AI error';try{const e=await res.json();d=e.detail||d;}catch{}throw new Error(d);}
    const body=await res.json(); $('songTitle').value=body.title||''; $('lyrics').value=body.lyrics||''; $('style').value=body.music_prompt||$('style').value; $('regenerateBtn').classList.remove('hidden'); $('lyrics').focus();
  }catch(err){alert(err.message||String(err));}
  finally{btn.disabled=false;$('progress').classList.add('hidden');}
};
$('regenerateBtn').onclick=()=>$('composeBtn').click();

$('generateBtn').onclick=async()=>{
  const api=getApi(); if(!api){$('settingsDialog').showModal();return;}
  const lyrics=$('lyrics').value.trim(); if($('voice').value!=='instrumental'&&!lyrics){alert('Create AI lyrics or write your own lyrics first.');return;}
  const btn=$('generateBtn');btn.disabled=true;$('progress').classList.remove('hidden');$('progressText').textContent='Generating music on your GPU server…';
  try{
    const prompt=stylePrompt();
    const payload={prompt,lyrics,audio_duration:Number($('duration').value),duration:Number($('duration').value),voice_mode:$('voice').value,language:$('language').value};
    const res=await fetch(`${api}/generate`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
    if(!res.ok){let d='Generation server error';try{const e=await res.json();d=e.detail||d;}catch{}throw new Error(d);}
    const body=await res.json(); if(body.status!=='success'||!body.audio_base64||!body.output_id)throw new Error('Server returned no audio record.');
    const audioUrl=`data:${body.mime_type||'audio/wav'};base64,${body.audio_base64}`;
    const record={id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),title:$('songTitle').value.trim()||'Untitled Lofi',idea:$('idea').value.trim(),mood:selectedMood,language:$('language').value,voice:$('voice').value,duration:Number($('duration').value),style:$('style').value,prompt,lyrics,seed:body.seed??null,model:body.model||'ACE-Step v1',outputId:body.output_id,createdAt:new Date().toISOString()};
    lastGeneration={...record,audioUrl};
    const history=readHistory().filter(x=>x.id!==record.id);history.unshift(record);writeHistory(history);renderHistory(); resetMasterUI();
    $('audio').src=audioUrl; $('download').href=audioUrl; $('download').download=`${safeFilename(record.title)}.wav`; $('resultTitle').textContent=record.title; $('result').classList.remove('hidden'); $('seed').textContent=record.seed??'—'; $('metaDuration').textContent=(body.duration||record.duration)+' sec'; $('result').scrollIntoView({behavior:'smooth'});
  }catch(err){alert(err.message||String(err));}
  finally{btn.disabled=false;$('progress').classList.add('hidden');}
};

$('masterBtn').onclick=async()=>{
  const api=getApi(); if(!api){$('settingsDialog').showModal();return;}
  if(!lastGeneration?.outputId){alert('Generate a song first.');return;}
  const btn=$('masterBtn');btn.disabled=true;$('masterState').textContent='Mastering…';$('masterState').className='status';
  try{
    const payload={output_id:lastGeneration.outputId,duration:lastGeneration.duration,fade_in:Number($('fadeIn').value),fade_out:Number($('fadeOut').value)};
    const res=await fetch(`${api}/master`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
    if(!res.ok){let d='Mastering failed';try{const e=await res.json();d=e.detail||d;}catch{}throw new Error(d);}
    const body=await res.json();
    const wavUrl=`${api}${body.wav_url}`; const mp3Url=`${api}${body.mp3_url}`;
    $('masterWav').href=wavUrl;$('masterWav').download=`${safeFilename(lastGeneration.title)}-MASTER.wav`;
    $('masterMp3').href=mp3Url;$('masterMp3').download=`${safeFilename(lastGeneration.title)}-320kbps.mp3`;
    $('masterLinks').classList.remove('hidden');$('masterState').textContent='Master ready ✓';$('masterState').className='status online';
    lastGeneration.master={target:body.target,sampleRate:body.sample_rate,wavBitDepth:body.wav_bit_depth,mp3Bitrate:body.mp3_bitrate,fadeIn:body.fade_in,fadeOut:body.fade_out,createdAt:new Date().toISOString()};
    const history=readHistory();const idx=history.findIndex(x=>x.id===lastGeneration.id);if(idx>=0){history[idx]={...history[idx],master:lastGeneration.master};writeHistory(history);}
  }catch(err){$('masterState').textContent='Mastering failed';$('masterState').className='status offline';alert(err.message||String(err));}
  finally{btn.disabled=false;}
};

function resetMasterUI(){ $('masterState').textContent='Not mastered';$('masterState').className='status offline';$('masterLinks').classList.add('hidden');$('masterWav').removeAttribute('href');$('masterMp3').removeAttribute('href'); }
function safeFilename(s){return String(s||'laxman-lofi').replace(/[^a-z0-9\u0900-\u097F\- _]/gi,'').trim().replace(/\s+/g,'-').slice(0,80)||'laxman-lofi';}
function exportMetadata(){
  if(!lastGeneration)return alert('Generate a song first.');
  const {audioUrl,...meta}=lastGeneration;
  const blob=new Blob([JSON.stringify(meta,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`${safeFilename(meta.title)}-metadata.json`;a.click();URL.revokeObjectURL(url);
}
async function copyPrompt(){
  if(!lastGeneration)return alert('Generate a song first.');
  try{await navigator.clipboard.writeText(lastGeneration.prompt);$('copyPrompt').textContent='Copied ✓';setTimeout(()=>$('copyPrompt').textContent='Copy prompt',1500);}catch{alert(lastGeneration.prompt);}
}
$('saveMetadata').onclick=exportMetadata;
$('copyPrompt').onclick=copyPrompt;

function renderHistory(){
  const list=readHistory();$('historyEmpty').classList.toggle('hidden',list.length>0);
  $('historyList').innerHTML=list.map((r,i)=>`<button class="history-item" data-index="${i}"><div><strong>${escapeHtml(r.title)}</strong><span>${escapeHtml(r.mood)} · ${escapeHtml(r.language)} · ${r.duration}s${r.master?' · mastered':''}</span></div><small>${new Date(r.createdAt).toLocaleString()}</small></button>`).join('');
  document.querySelectorAll('.history-item').forEach(el=>el.onclick=()=>loadHistory(Number(el.dataset.index)));
}
function loadHistory(index){
  const r=readHistory()[index];if(!r)return;
  $('idea').value=r.idea||'';$('songTitle').value=r.title||'';$('lyrics').value=r.lyrics||'';$('language').value=r.language||'Nepali';$('voice').value=r.voice||'male';$('duration').value=String(r.duration||180);$('style').value=r.style||'';
  selectedMood=r.mood||'emotional';document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('active',c.dataset.value===selectedMood));
  lastGeneration={...r};$('result').classList.add('hidden');$('historyPanel').classList.add('hidden');resetMasterUI();window.scrollTo({top:0,behavior:'smooth'});
}
renderHistory();setState(!!getApi());health();setInterval(health,15000);
