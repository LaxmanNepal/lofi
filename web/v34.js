(() => {
  const result=document.querySelector('#result'); if(!result) return;
  const style=document.createElement('style');
  style.textContent=`.v34-sync{grid-column:1/-1}.v34-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.v34-grid label{display:flex;flex-direction:column;gap:6px}.v34-status{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.v34-preview{width:100%;margin-top:12px;border-radius:16px;background:#000;display:none}.v34-actions{display:flex;gap:8px;flex-wrap:wrap}@media(max-width:800px){.v34-sync{grid-column:auto}.v34-grid{grid-template-columns:1fr}}`;
  document.head.appendChild(style);
  const card=document.createElement('div'); card.className='v14-card v34-sync';
  card.innerHTML=`<span class="step">16</span><h3>🎬 Final Synchronized Lyric Video</h3><p>Render the reviewed V3.3 timestamps directly into the final 1080p karaoke video. ASR timing is preserved; edited timestamps become the source of truth.</p><div class="v34-grid"><label>Theme<select id="v34Theme"><option value="night">Night</option><option value="warm">Warm</option><option value="minimal">Minimal</option><option value="nepal">Nepal</option></select></label><label>Karaoke<select id="v34Karaoke"><option value="true" selected>Word highlight</option><option value="false">Static lyrics</option></select></label><label>Waveform<select id="v34Wave"><option value="true" selected>On</option><option value="false">Off</option></select></label></div><div class="v34-status"><button id="v34Render" class="v14-btn primary">Render synchronized video</button><span id="v34State" class="v34-badge">Analyze and review timing first</span></div><video id="v34Preview" class="v34-preview" controls playsinline></video><div id="v34Actions" class="v34-actions hidden"><a id="v34Download" class="download" download>Download final lyric video</a></div>`;
  result.appendChild(card);
  const $=id=>document.getElementById(id), api=()=>getApi();
  $('v34Render').onclick=async()=>{
    if(!lastGeneration?.outputId){alert('Generate a vocal song first.');return}
    if(!lastGeneration?.lyricTiming?.segments?.length){alert('Run ASR timing in Exact Lyric Sync Studio and review/apply the timestamps first.');return}
    if(!api()){$('settingsDialog').showModal();return}
    const b=$('v34Render'); b.disabled=true; b.textContent='Rendering…'; $('v34State').textContent='Building final 1080p synchronized lyric video…';
    try{
      const timing=lastGeneration.lyricTiming.segments.map(x=>({text:String(x.text||'').trim(),start:Number(x.start),end:Number(x.end),source:x.source||'reviewed',confidence:x.confidence,words:x.words||[]})).filter(x=>x.text&&Number.isFinite(x.start)&&Number.isFinite(x.end)&&x.end>x.start);
      if(!timing.length) throw new Error('No valid timing rows remain after review.');
      const r=await fetch(`${api()}/lyric-video`,{method:'POST',headers:{'Content-Type':'application/json',...authHeaders()},body:JSON.stringify({output_id:lastGeneration.outputId,title:lastGeneration.title||$('songTitle')?.value||'Laxman Lofi',lyrics:$('lyrics')?.value||lastGeneration.lyrics||'',cover_base64:lastGeneration.coverBase64||null,timing,theme:$('v34Theme').value,karaoke:$('v34Karaoke').value==='true',intro_seconds:2,outro_seconds:2,waveform:$('v34Wave').value==='true'})});
      const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Lyric video render failed');
      lastGeneration.lyricVideo={...d,reviewed:true};
      const src=`data:${d.mime_type};base64,${d.video_base64}`; $('v34Preview').src=src; $('v34Preview').style.display='block'; $('v34Download').href=src; $('v34Download').download=d.file_name; $('v34Actions').classList.remove('hidden'); $('v34State').textContent=`Rendered ✓ · ${d.lines} lines · ${d.timing_source}`;
    }catch(e){$('v34State').textContent='Render failed';alert(e.message)}finally{b.disabled=false;b.textContent='Render synchronized video'}
  };
  const q=document.createElement('script');q.src='./v35.js';document.body.appendChild(q);
})();
