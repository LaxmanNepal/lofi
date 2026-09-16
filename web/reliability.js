(()=>{
  const btn=document.getElementById('generateBtn');
  if(!btn)return;
  const style=document.createElement('style');
  style.textContent=`.generation-ready{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:8px}.generation-ready .pill{padding:5px 9px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);font-size:12px}.generation-ready .ok{border-color:rgba(70,220,140,.45)}.generation-ready .bad{border-color:rgba(255,100,100,.45)}.generation-error{margin-top:8px;white-space:pre-wrap;word-break:break-word}`;
  document.head.appendChild(style);
  const box=document.createElement('div');
  box.className='generation-ready';
  box.innerHTML='<span class="pill">Generation readiness: checking…</span>';
  btn.parentElement?.appendChild(box);
  const pill=box.querySelector('.pill');
  let cache=null,checking=false;
  const api=()=>typeof getApi==='function'?getApi():'';
  const headers=()=>typeof authHeaders==='function'?authHeaders():{};
  function render(h){
    cache=h;
    if(!h){pill.className='pill bad';pill.textContent='Generation backend offline';return;}
    const ready=h.ready_for_generation!==false && h.cuda!==false;
    const gpu=h.gpu_name||h.device||'GPU status unknown';
    const bf=h.bf16===true?'BF16':'FP32';
    const off=h.cpu_offload?'offload':'no offload';
    pill.className='pill '+(ready?'ok':'bad');
    pill.textContent=`${ready?'Ready':'Not ready'} · ${gpu} · ${bf} · ${off}`;
  }
  async function check(force=false){
    if(checking)return cache;
    const base=api();
    if(!base){render(null);return null;}
    if(cache&&!force)return cache;
    checking=true;
    try{
      const r=await fetch(base+'/health',{headers:headers(),cache:'no-store'});
      let h=null;try{h=await r.json()}catch{}
      if(!r.ok)throw new Error(h?.detail||`Health check failed (${r.status})`);
      render(h);return h;
    }catch(e){render(null);return null}
    finally{checking=false}
  }
  window.laxmanLofiCheckGeneration=()=>check(true);
  document.addEventListener('click',async e=>{
    if(e.target!==btn)return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const h=await check(true);
    const ready=h&&h.ready_for_generation!==false&&h.cuda!==false;
    if(!ready){
      const msg=document.createElement('div');msg.className='generation-error hint';msg.textContent='Generation stopped before sending a GPU job. Open Settings and verify the Colab API URL/key, then check /health. If the API is online but the model is unavailable, inspect the Colab log: /content/laxman-lofi-api.log';
      box.appendChild(msg);setTimeout(()=>msg.remove(),10000);return;
    }
    btn.disabled=true;
    try{
      if(typeof window.__laxmanOriginalGenerate==='function')await window.__laxmanOriginalGenerate();
    }finally{btn.disabled=false}
  },true);
  // Capture the original property handler once, then replace it with a callable wrapper.
  if(typeof btn.onclick==='function'){
    const original=btn.onclick;
    window.__laxmanOriginalGenerate=async()=>original.call(btn,new MouseEvent('click',{bubbles:false}));
    btn.onclick=null;
  }
  check(true);
})();