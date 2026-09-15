const $ = (id) => document.getElementById(id);
const API_KEY = 'laxman-lofi-api-url';
const KEY_KEY = 'laxman-lofi-api-key';
const HISTORY_KEY = 'laxman-lofi-history-v1';
const PRESET_KEY = 'laxman-lofi-presets-v1';
let selectedMood = 'emotional';
let lastGeneration = null;
let batchRunning = false;

function getApi(){ return (localStorage.getItem(API_KEY) || '').replace(/\/$/,''); }
function setState(online){ $('apiState').textContent = online ? 'API online' : 'API offline'; $('apiState').className = `status ${online?'online':'offline'}`; }
function authHeaders(){ const k=localStorage.getItem(KEY_KEY)||''; return k?{'Authorization':`Bearer ${k}`}:{ }; }
function readHistory(){ try{return JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');}catch{return[];} }
function writeHistory(items){ localStorage.setItem(HISTORY_KEY,JSON.stringify(items.slice(0,30))); }
function escapeHtml(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function safeFilename(s){return String(s||'laxman-lofi').replace(/[^a-z0-9\u0900-\u097F\- _]/gi,'').trim().replace(/\s+/g,'-').slice(0,80)||'laxman-lofi';}
function downloadDataUrl(dataUrl, filename){const a=document.createElement('a');a.href=dataUrl;a.download=filename;document.body.appendChild(a);a.click();a.remove();}

$('settingsBtn').onclick=()=>{ $('apiUrl').value=getApi(); $('apiKey').value=localStorage.getItem(KEY_KEY)||''; $('settingsDialog').showModal(); };
$('saveSettings').onclick=()=>{ localStorage.setItem(API_KEY,$('apiUrl').value.trim()); localStorage.setItem(KEY_KEY,$('apiKey').value.trim()); setState(!!getApi()); health(); };
$('historyBtn').onclick=()=>{ $('historyPanel').classList.toggle('hidden'); renderHistory(); if(!$('historyPanel').classList.contains('hidden')) $('historyPanel').scrollIntoView({behavior:'smooth'}); };
$('clearHistory').onclick=()=>{ if(confirm('Clear all saved generation records from this browser?')){writeHistory([]);renderHistory();} };
for(const chip of document.querySelectorAll('.chip')) chip.onclick=()=>{ document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); selectedMood=chip.dataset.value; };
$('newBtn').onclick=()=>{ $('result').classList.add('hidden'); $('audio').removeAttribute('src'); $('songTitle').value=''; $('lyrics').value=''; lastGeneration=null; resetMasterUI(); $('idea').focus(); window.scrollTo({top:0,behavior:'smooth'}); };
$('formatBtn').onclick=()=>{ let v=$('lyrics').value.trim(); if(!v)return; if(!/^\[verse\]/im.test(v))v='[verse]\n'+v; $('lyrics').value=v; };

async function health(){ const url=getApi(); if(!url){setState(false);return;} try{const r=await fetch(`${url}/health`,{headers:authHeaders()});setState(r.ok);}catch{setState(false);} }
function stylePrompt(){ const bpm={slow:'65–75 BPM',mid:'75–85 BPM',upbeat:'85–100 BPM'}[$('tempo').value]; const vocal=$('voice').value==='instrumental'?'instrumental only':`${$('voice').value} vocal`; const idea=$('idea').value.trim(); return `${idea ? `Song story: ${idea}. ` : ''}${$('style').value}, ${selectedMood} mood, ${bpm}, ${vocal}, ${$('language').value} music, original composition, intimate late-night lofi production`; }
function updateHistoryRecord(record){const history=readHistory();const idx=history.findIndex(x=>x.id===record.id);if(idx>=0){history[idx]={...history[idx},...record};writeHistory(history);renderHistory();}}

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

async function generateSongFromCurrent(options={}){
  const api=getApi(); if(!api)throw new Error('Set the API URL in Settings first.');
  const lyrics=$('lyrics').value.trim(); if($('voice').value!=='instrumental'&&!lyrics)throw new Error('Create AI lyrics or write your own lyrics first.');
  const prompt=stylePrompt();
  const payload={prompt,lyrics,audio_duration:Number($('duration').value),duration:Number($('duration').value),voice_mode:$('voice').value,language:$('language').value};
  const res=await fetch(`${api}/generate`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
  if(!res.ok){let d='Generation server error';try{const e=await res.json();d=e.detail||d;}catch{}throw new Error(d);}
  const body=await res.json(); if(body.status!=='success'||!body.audio_base64||!body.output_id)throw new Error('Server returned no audio record.');
  const audioUrl=`data:${body.mime_type||'audio/wav'};base64,${body.audio_base64}`;
  const record={id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),title:$('songTitle').value.trim()||'Untitled Lofi',idea:$('idea').value.trim(),mood:selectedMood,language:$('language').value,voice:$('voice').value,duration:Number($('duration').value),style:$('style').value,prompt,lyrics,seed:body.seed??null,model:body.model||'ACE-Step v1',outputId:body.output_id,createdAt:new Date().toISOString(),batchId:options.batchId||null};
  if(!options.batch){
    lastGeneration={...record,audioUrl};
    const history=readHistory().filter(x=>x.id!==record.id);history.unshift(record);writeHistory(history);renderHistory();resetMasterUI();
    $('audio').src=audioUrl; $('download').href=audioUrl; $('download').download=`${safeFilename(record.title)}.wav`; $('resultTitle').textContent=record.title; $('result').classList.remove('hidden'); $('seed').textContent=record.seed??'—'; $('metaDuration').textContent=(body.duration||record.duration)+' sec'; $('result').scrollIntoView({behavior:'smooth'});
  }
  return {record,audioUrl,body};
}

$('generateBtn').onclick=async()=>{
  const btn=$('generateBtn');btn.disabled=true;$('progress').classList.remove('hidden');$('progressText').textContent='Generating music on your GPU server…';
  try{await generateSongFromCurrent();}catch(err){alert(err.message||String(err));}
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
    const wavUrl=`data:${body.wav_mime_type};base64,${body.wav_base64}`;
    const mp3Url=`data:${body.mp3_mime_type};base64,${body.mp3_base64}`;
    $('masterWav').href=wavUrl;$('masterWav').download=`${safeFilename(lastGeneration.title)}-MASTER.wav`;
    $('masterMp3').href=mp3Url;$('masterMp3').download=`${safeFilename(lastGeneration.title)}-320kbps.mp3`;
    $('masterLinks').classList.remove('hidden');$('masterState').textContent='Master ready ✓';$('masterState').className='status online';
    lastGeneration.master={target:body.target,sampleRate:body.sample_rate,wavBitDepth:body.wav_bit_depth,mp3Bitrate:body.mp3_bitrate,fadeIn:body.fade_in,fadeOut:body.fade_out,createdAt:new Date().toISOString()};updateHistoryRecord({id:lastGeneration.id,master:lastGeneration.master});
  }catch(err){$('masterState').textContent='Mastering failed';$('masterState').className='status offline';alert(err.message||String(err));}
  finally{btn.disabled=false;}
};

function resetMasterUI(){ $('masterState').textContent='Not mastered';$('masterState').className='status offline';$('masterLinks').classList.add('hidden');$('masterWav').removeAttribute('href');$('masterMp3').removeAttribute('href'); }
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
  $('historyList').innerHTML=list.map((r,i)=>`<button class="history-item" data-index="${i}"><div><strong>${escapeHtml(r.title)}</strong><span>${escapeHtml(r.mood)} · ${escapeHtml(r.language)} · ${r.duration}s${r.master?' · mastered':''}${r.batchId?' · batch':''}</span></div><small>${new Date(r.createdAt).toLocaleString()}</small></button>`).join('');
  document.querySelectorAll('.history-item').forEach(el=>el.onclick=()=>loadHistory(Number(el.dataset.index)));
}
function loadHistory(index){
  const r=readHistory()[index];if(!r)return;
  $('idea').value=r.idea||'';$('songTitle').value=r.title||'';$('lyrics').value=r.lyrics||'';$('language').value=r.language||'Nepali';$('voice').value=r.voice||'male';$('duration').value=String(r.duration||180);$('style').value=r.style||'';
  selectedMood=r.mood||'emotional';document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('active',c.dataset.value===selectedMood));
  lastGeneration={...r};$('result').classList.add('hidden');$('historyPanel').classList.add('hidden');resetMasterUI();window.scrollTo({top:0,behavior:'smooth'});
}

const DEFAULT_PRESETS=[
  {id:'pardeshi',name:'🇳🇵 Pardeshi',mood:'lonely',language:'Nepali',voice:'male',duration:180,tempo:'slow',style:'soft piano, mellow acoustic guitar, dusty vinyl, subtle rain ambience, restrained drums, spacious late-night mix',idea:'परदेशमा राति काम गर्दा घर, आमा र नेपाल सम्झिने एक नेपालीको मन।'},
  {id:'romantic',name:'❤️ Romantic',mood:'romantic',language:'Nepali',voice:'male',duration:180,tempo:'mid',style:'warm piano, clean electric guitar, soft drums, intimate vocal, dreamy vinyl texture, spacious modern lofi mix',idea:'टाढा रहेको मायालु व्यक्तिलाई सम्झिँदै, अधुरो प्रेम र फेरि भेट्ने आशाको कथा।'},
  {id:'rainy',name:'🌧️ Rainy Night',mood:'rainy',language:'Nepali',voice:'male',duration:180,tempo:'slow',style:'felt piano, rain ambience, soft guitar harmonics, tape hiss, deep mellow bass, minimal drums, midnight atmosphere',idea:'झ्यालमा परेको पानी सुन्दै पुराना सम्झना र एक्लोपनामा बितेको वर्षाको रात।'},
  {id:'nepal',name:'🏔️ Nepal Atmosphere',mood:'peaceful',language:'Nepali',voice:'male',duration:180,tempo:'mid',style:'warm sarangi-inspired textures, acoustic guitar, soft piano, organic percussion, vinyl warmth, cinematic Nepali atmosphere',idea:'हेटौंडा वा गाउँको साँझ, चिया, पहाडको हावा र घरको शान्त सम्झना।'}
];
function readPresets(){try{return JSON.parse(localStorage.getItem(PRESET_KEY)||'[]');}catch{return[];}}
function writePresets(items){localStorage.setItem(PRESET_KEY,JSON.stringify(items.slice(0,20)));}
function applyPreset(p){
  selectedMood=p.mood||'emotional';document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('active',c.dataset.value===selectedMood));
  $('language').value=p.language||'Nepali';$('voice').value=p.voice||'male';$('duration').value=String(p.duration||180);$('tempo').value=p.tempo||'mid';$('style').value=p.style||'';
  if(p.idea)$('idea').value=p.idea;$('lyrics').value='';$('songTitle').value='';
  $('idea').focus();
}
function renderPresets(){
  const custom=readPresets();const all=[...DEFAULT_PRESETS,...custom];
  $('presetList').innerHTML=all.map((p,i)=>`<button class="chip preset-chip" data-preset-index="${i}">${escapeHtml(p.name)}</button>`).join('');
  document.querySelectorAll('.preset-chip').forEach((el,i)=>el.onclick=()=>applyPreset(all[i]));
}
$('savePresetBtn').onclick=()=>{
  const name=prompt('Preset name:',`${$('songTitle').value.trim()||'My'} preset`);if(!name)return;
  const p={id:`custom-${Date.now()}`,name:name.trim(),mood:selectedMood,language:$('language').value,voice:$('voice').value,duration:Number($('duration').value),tempo:$('tempo').value,style:$('style').value,idea:$('idea').value.trim()};
  const items=readPresets().filter(x=>x.name!==p.name);items.unshift(p);writePresets(items);renderPresets();
};

function getBatchStories(){return $('batchStories').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean).slice(0,20);}
function updateBatchCount(){const n=getBatchStories().length;$('batchCount').textContent=`${n} stor${n===1?'y':'ies'}`;$('batchCount').className=`status ${n?'online':''}`;}
$('batchStories').addEventListener('input',updateBatchCount);
$('batchAddCurrent').onclick=()=>{const idea=$('idea').value.trim();if(!idea)return alert('Write a current story first.');const list=getBatchStories();if(!list.includes(idea))list.push(idea);$('batchStories').value=list.slice(0,20).join('\n');updateBatchCount();};
$('batchClear').onclick=()=>{$('batchStories').value='';$('batchResults').innerHTML='';updateBatchCount();};
function renderBatchResult(item,index){
  const row=document.createElement('div');row.className='batch-result';row.innerHTML=`<div><strong>${index+1}. ${escapeHtml(item.title)}</strong><span>${item.status}${item.seed!=null?` · seed ${escapeHtml(item.seed)}`:''}</span></div>`;
  if(item.audioUrl){const a=document.createElement('a');a.className='download';a.href=item.audioUrl;a.download=`${safeFilename(item.title)}.wav`;a.textContent='Download WAV';row.appendChild(a);}
  $('batchResults').appendChild(row);
}
$('batchGenerate').onclick=async()=>{
  if(batchRunning)return;
  const api=getApi();if(!api){$('settingsDialog').showModal();return;}
  const stories=getBatchStories();if(!stories.length){alert('Add at least one story, one per line.');return;}
  batchRunning=true;$('batchGenerate').disabled=true;$('batchProgress').classList.remove('hidden');$('batchResults').innerHTML='';
  const batchId=`batch-${Date.now()}`;
  try{
    for(let i=0;i<stories.length;i++){
      const story=stories[i];$('batchProgressText').textContent=`Generating ${i+1} of ${stories.length}…`;
      $('idea').value=story;$('lyrics').value='';$('songTitle').value='';
      const composeRes=await fetch(`${api}/compose`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify({idea:story,mood:selectedMood,language:$('language').value,voice:$('voice').value,duration:Number($('duration').value),style:$('style').value})});
      if(!composeRes.ok){let d='Lyric AI error';try{const e=await composeRes.json();d=e.detail||d;}catch{}throw new Error(`Story ${i+1}: ${d}`);}
      const lyric=await composeRes.json();$('songTitle').value=lyric.title||`Lofi ${i+1}`;$('lyrics').value=lyric.lyrics||'';if(lyric.music_prompt)$('style').value=lyric.music_prompt;
      const generated=await generateSongFromCurrent({batch:true,batchId});
      const item={title:generated.record.title,status:'ready ✓',seed:generated.record.seed,audioUrl:generated.audioUrl};renderBatchResult(item,i);
      const history=readHistory().filter(x=>x.id!==generated.record.id);history.unshift(generated.record);writeHistory(history);renderHistory();
    }
    $('batchProgressText').textContent=`Batch complete ✓ · ${stories.length} songs generated`;
  }catch(err){$('batchProgressText').textContent='Batch stopped';alert(err.message||String(err));}
  finally{batchRunning=false;$('batchGenerate').disabled=false;setTimeout(()=>$('batchProgress').classList.add('hidden'),1200);}
};

renderHistory();renderPresets();updateBatchCount();setState(!!getApi());health();setInterval(health,15000);
