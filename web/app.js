const $ = (id) => document.getElementById(id);
const API_KEY = 'laxman-lofi-api-url';
const KEY_KEY = 'laxman-lofi-api-key';
let selectedMood = 'emotional';

function getApi(){ return (localStorage.getItem(API_KEY) || '').replace(/\/$/,''); }
function setState(online){ $('apiState').textContent = online ? 'API online' : 'API offline'; $('apiState').className = `status ${online?'online':'offline'}`; }

$('settingsBtn').onclick = () => { $('apiUrl').value = getApi(); $('apiKey').value = localStorage.getItem(KEY_KEY)||''; $('settingsDialog').showModal(); };
$('saveSettings').onclick = () => { localStorage.setItem(API_KEY,$('apiUrl').value.trim()); localStorage.setItem(KEY_KEY,$('apiKey').value.trim()); setState(!!getApi()); };

for(const chip of document.querySelectorAll('.chip')) chip.onclick=()=>{ document.querySelectorAll('.chip').forEach(c=>c.classList.remove('active')); chip.classList.add('active'); selectedMood=chip.dataset.value; };

$('newBtn').onclick=()=>{ $('result').classList.add('hidden'); $('audio').removeAttribute('src'); window.scrollTo({top:0,behavior:'smooth'}); };
$('formatBtn').onclick=()=>{
  const lyrics=$('lyrics').value.trim();
  if(!lyrics) return;
  if(!/^\[verse\]/im.test(lyrics)) $('lyrics').value='[verse]\n'+lyrics;
  if(!/\[chorus\]/im.test($('lyrics').value)) $('lyrics').value+='\n\n[chorus]\n';
};

async function health(){
  const url=getApi(); if(!url){setState(false);return;}
  try{const r=await fetch(`${url}/health`,{headers:authHeaders()});setState(r.ok);}catch{setState(false);}
}
function authHeaders(){ const k=localStorage.getItem(KEY_KEY)||''; return k?{'Authorization':`Bearer ${k}`}:{ }; }
function stylePrompt(){
  const bpm={slow:'65–75 BPM',mid:'75–85 BPM',upbeat:'85–100 BPM'}[$('tempo').value];
  const vocal=$('voice').value==='instrumental'?'instrumental only':`${$('voice').value} vocal`;
  return `${$('style').value}, ${selectedMood} mood, ${bpm}, ${vocal}, ${$('language').value} music, original composition, intimate late-night lofi production`;
}

$('generateBtn').onclick=async()=>{
  const api=getApi();
  if(!api){ $('settingsDialog').showModal(); return; }
  const lyrics=$('lyrics').value.trim();
  if($('voice').value!=='instrumental' && !lyrics){ alert('Add your original lyrics first. V1 intentionally does not invent lyrics silently.'); return; }
  const btn=$('generateBtn'); btn.disabled=true; $('progress').classList.remove('hidden'); $('progressText').textContent='Sending generation request…';
  try{
    const payload={prompt:stylePrompt(),lyrics,audio_duration:Number($('duration').value),duration:Number($('duration').value),language:$('language').value.toLowerCase(),vocal_language:$('language').value.toLowerCase(),audio_format:'wav',sample_mode:false,thinking:false};
    const res=await fetch(`${api}/release_task`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify(payload)});
    if(!res.ok) throw new Error(`Generation server returned ${res.status}`);
    const body=await res.json(); const task=body.data||body; const taskId=task.task_id||task.id;
    if(!taskId) throw new Error('No task ID returned by server.');
    let result=null;
    for(let i=0;i<120;i++){
      await new Promise(r=>setTimeout(r,2500));
      $('progressText').textContent=`Generating… ${Math.min(99,Math.round((i+1)/120*100))}%`;
      const q=await fetch(`${api}/query_result`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify({task_id_list:[taskId]})});
      if(!q.ok) continue;
      const qb=await q.json(); const item=(qb.data||[])[0];
      if(item?.status===2) throw new Error('The generation server reported a failed task.');
      if(item?.status===1){result=item;break;}
    }
    if(!result) throw new Error('Generation timed out. Check the Colab server and try again.');
    let parsed=result.result; if(typeof parsed==='string'){try{parsed=JSON.parse(parsed);}catch{}}
    const first=Array.isArray(parsed)?parsed[0]:parsed;
    const file=first?.file||first?.audio_url||first?.url;
    if(!file) throw new Error('Generation finished but no audio file was returned.');
    const audioUrl=file.startsWith('http')?file:`${api}${file}`;
    $('audio').src=audioUrl; $('download').href=audioUrl; $('result').classList.remove('hidden'); $('seed').textContent=first?.metas?.seed||'server-generated'; $('metaDuration').textContent=(first?.metas?.duration||$('duration').value)+' sec'; $('result').scrollIntoView({behavior:'smooth'});
  }catch(err){ alert(err.message||String(err)); }
  finally{btn.disabled=false;$('progress').classList.add('hidden');}
};

setState(!!getApi()); health();
setInterval(health,15000);
