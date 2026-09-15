const $ = (id) => document.getElementById(id);
const API_KEY = 'laxman-lofi-api-url';
const KEY_KEY = 'laxman-lofi-api-key';
let selectedMood = 'emotional';

function getApi(){ return (localStorage.getItem(API_KEY) || '').replace(/\/$/,''); }
function setState(online){ $('apiState').textContent = online ? 'API online' : 'API offline'; $('apiState').className = `status ${online?'online':'offline'}`; }
function authHeaders(){ const k=localStorage.getItem(KEY_KEY)||''; return k?{'Authorization':`Bearer ${k}`}:{}; }

$('settingsBtn').onclick = () => { $('apiUrl').value = getApi(); $('apiKey').value = localStorage.getItem(KEY_KEY)||''; $('settingsDialog').showModal(); };
$('saveSettings').onclick = () => { localStorage.setItem(API_KEY,$('apiUrl').value.trim()); localStorage.setItem(KEY_KEY,$('apiKey').value.trim()); setState(!!getApi()); health(); };
for(const chip of document.querySelectorAll('.chip')) chip.onclick=()=>{ document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); selectedMood=chip.dataset.value; };
$('newBtn').onclick=()=>{ $('result').classList.add('hidden'); $('audio').removeAttribute('src'); window.scrollTo({top:0,behavior:'smooth'}); };
$('formatBtn').onclick=()=>{ const lyrics=$('lyrics').value.trim(); if(!lyrics)return; if(!/^\[verse\]/im.test(lyrics))$('lyrics').value='[verse]\n'+lyrics; if(!/\[chorus\]/im.test($('lyrics').value))$('lyrics').value+='\n\n[chorus]\n'; };

async function health(){ const url=getApi(); if(!url){setState(false);return;} try{const r=await fetch(`${url}/health`,{headers:authHeaders()});setState(r.ok);}catch{setState(false);} }
function stylePrompt(){ const bpm={slow:'65–75 BPM',mid:'75–85 BPM',upbeat:'85–100 BPM'}[$('tempo').value]; const vocal=$('voice').value==='instrumental'?'instrumental only':`${$('voice').value} vocal`; const idea=$('idea').value.trim(); return `${idea ? `Song story: ${idea}. ` : ''}${$('style').value}, ${selectedMood} mood, ${bpm}, ${vocal}, ${$('language').value} music, original composition, intimate late-night lofi production`; }

$('generateBtn').onclick=async()=>{
  const api=getApi(); if(!api){$('settingsDialog').showModal();return;}
  const lyrics=$('lyrics').value.trim(); if($('voice').value!=='instrumental'&&!lyrics){alert('Add your original lyrics first. V1 intentionally does not invent lyrics silently.');return;}
  const btn=$('generateBtn');btn.disabled=true;$('progress').classList.remove('hidden');$('progressText').textContent='Generating on your GPU server…';
  try{
    const payload={prompt:stylePrompt(),lyrics,audio_duration:Number($('duration').value),duration:Number($('duration').value),voice_mode:$('voice').value,language:$('language').value};
    const res=await fetch(`${api}/generate`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
    if(!res.ok){let detail='Generation server error';try{const e=await res.json();detail=e.detail||detail;}catch{}throw new Error(detail);}
    const body=await res.json(); if(body.status!=='success'||!body.audio_base64)throw new Error('Server returned no audio.');
    const mime=body.mime_type||'audio/wav'; const audioUrl=`data:${mime};base64,${body.audio_base64}`;
    $('audio').src=audioUrl;$('download').href=audioUrl;$('download').download=`laxman-lofi-${Date.now()}.wav`;$('result').classList.remove('hidden');$('seed').textContent=body.seed??'—';$('metaDuration').textContent=(body.duration||$('duration').value)+' sec';$('result').scrollIntoView({behavior:'smooth'});
  }catch(err){alert(err.message||String(err));}
  finally{btn.disabled=false;$('progress').classList.add('hidden');}
};
setState(!!getApi());health();setInterval(health,15000);
