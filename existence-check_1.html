<div id="app"></div>
<style>
  #app{font-family:ui-sans-serif,-apple-system,"Segoe UI",sans-serif;max-width:820px;margin:0 auto;color:#1c1917}
  h1{font-size:19px;margin:0 0 2px;letter-spacing:-.01em}
  .sub{font-size:12px;color:#78716c;line-height:1.5}
  .clockbar{display:flex;align-items:center;gap:12px;margin:14px 0 4px;padding:10px 12px;border:1px solid #e7e5e4;border-radius:8px;background:#fafaf9}
  .clock{font-size:22px;font-variant-numeric:tabular-nums;font-weight:600;letter-spacing:-.02em}
  .clock.warn{color:#b45309}.clock.over{color:#b91c1c}
  .clocklbl{font-size:11px;color:#a8a29e;text-transform:uppercase;letter-spacing:.05em}
  button{font:inherit;font-size:12px;padding:6px 11px;border:1px solid #d6d3d1;background:#fff;border-radius:6px;cursor:pointer;color:#1c1917}
  button:hover{background:#f5f5f4}
  button.solid{background:#1c1917;color:#fff;border-color:#1c1917}
  button.solid:hover{background:#44403c}
  .push{margin-left:auto;display:flex;gap:6px}
  .rules{font-size:12px;color:#57534e;background:#fafaf9;border-left:2px solid #d6d3d1;padding:8px 12px;margin:12px 0 18px;line-height:1.6}
  .rules b{color:#1c1917}
  .card{border:1px solid #e7e5e4;border-radius:8px;padding:12px 14px;margin-bottom:10px}
  .card.active{border-color:#1c1917;box-shadow:0 0 0 3px #f5f5f4}
  .card.done{background:#fafaf9}
  .crow{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
  .idx{font-size:11px;color:#a8a29e;font-variant-numeric:tabular-nums;width:34px;flex:none}
  .name{font-size:14px;font-weight:600;flex:1;min-width:150px}
  .name small{display:block;font-weight:400;font-size:11px;color:#a8a29e;margin-top:1px}
  .seg{display:flex;border:1px solid #d6d3d1;border-radius:6px;overflow:hidden;flex:none}
  .seg button{border:0;border-radius:0;padding:5px 12px;font-size:11px;font-weight:600;letter-spacing:.03em}
  .seg button+button{border-left:1px solid #e7e5e4}
  .seg button.on[data-v="YES"]{background:#166534;color:#fff}
  .seg button.on[data-v="NO"]{background:#1c1917;color:#fff}
  .seg button.on[data-v="TAGS"]{background:#92400e;color:#fff}
  .mini{font-size:11px;color:#a8a29e;font-variant-numeric:tabular-nums;width:44px;text-align:right;flex:none}
  .mini.warn{color:#b45309}.mini.over{color:#b91c1c;font-weight:600}
  .fields{margin-top:9px;display:none}
  .card.open .fields{display:block}
  input,textarea{width:100%;box-sizing:border-box;font:inherit;font-size:12.5px;padding:6px 8px;border:1px solid #e7e5e4;border-radius:6px;background:#fff;color:#1c1917;margin-bottom:6px}
  input:focus,textarea:focus{outline:none;border-color:#a8a29e}
  input.bad{border-color:#fca5a5;background:#fef2f2}
  textarea{resize:vertical;min-height:44px;line-height:1.45}
  .q{font-size:11px;color:#78716c;margin:0 0 3px}
  .hint{font-size:11px;color:#a8a29e;margin:-3px 0 8px;line-height:1.45}
  .close{margin-top:22px;border-top:1px solid #e7e5e4;padding-top:14px}
  .close h2{font-size:13px;margin:0 0 6px;letter-spacing:.03em;text-transform:uppercase}
  .verdict{font-size:12.5px;color:#57534e;background:#fafaf9;padding:8px 11px;border-radius:6px;margin-bottom:8px;line-height:1.5}
  .out{margin-top:18px;display:none}
  .out.show{display:block}
  .out textarea{min-height:230px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;line-height:1.5}
  .foot{font-size:11px;color:#a8a29e;margin-top:14px;line-height:1.5}
</style>
<script>
(function(){
const TOOLS=[
 {n:"LangSmith",s:"docs.smith.langchain.com"},
 {n:"Helicone",s:"docs.helicone.ai"},
 {n:"Langfuse",s:"langfuse.com/docs"},
 {n:"Phoenix / Arize",s:"docs.arize.com — check OSS Phoenix first, note if cloud-only"},
 {n:"OTel LLM tracing",s:"OpenLLMetry / OpenInference semantic conventions"}
];
const S=TOOLS.map(()=>({v:"",url:"",note:"",sec:0,run:false,open:false}));
const C={sec:3600,run:false,line:""};
const app=document.getElementById('app');

app.innerHTML=`
<h1>Existence check — per-subagent token attribution</h1>
<div class="sub">Does the tool show token/dollar totals grouped by <b>sub-agent</b>, ranked by cost? Not "does it do observability."</div>

<div class="clockbar">
  <div><div class="clocklbl">Box remaining</div><div class="clock" id="big">60:00</div></div>
  <div class="push">
    <button class="solid" id="go">Start box</button>
    <button id="rs">Reset</button>
  </div>
</div>

<div class="rules">
<b>YES</b> only if grouped by a sub-agent-level dimension <b>and</b> it's a shipped view <b>and</b> you have a URL.<br>
Per-model, per-trace, per-session, per-user, per-API-key → <b>NO</b>. Requires your own tags + your own query → <b>TAGS-ONLY</b>, which counts as NO.<br>
Docs pages and product screenshots only. No blogs, no videos, no changelogs. Three searches per tool: <b>cost</b>, <b>token</b>, <b>agent</b>.<br>
Can't tell in 10 minutes → <b>NO</b>.
</div>

${TOOLS.map((t,i)=>`
<div class="card" id="c${i}">
  <div class="crow">
    <span class="idx">${i+1}/5</span>
    <span class="name">${t.n}<small>${t.s}</small></span>
    <span class="seg">
      <button data-i="${i}" data-v="YES">YES</button>
      <button data-i="${i}" data-v="TAGS">TAGS-ONLY</button>
      <button data-i="${i}" data-v="NO">NO</button>
    </span>
    <span class="mini" id="m${i}">10:00</span>
    <button data-t="${i}" id="t${i}">Start</button>
  </div>
  <div class="fields">
    <div class="q">Proof URL — the docs page or screenshot that settles it. Blank = NO.</div>
    <input id="u${i}" placeholder="https://…">
    <div class="q">Note — what it actually groups by, or what's missing.</div>
    <textarea id="n${i}" placeholder="e.g. cost dashboard breaks down by model and API key only; no agent dimension"></textarea>
  </div>
</div>`).join('')}

<div class="close">
  <h2>Closing line — write at 7:20, stop searching</h2>
  <div class="verdict" id="vd">Mark all five to get your prompt.</div>
  <textarea id="cl" placeholder="One sentence."></textarea>
  <div class="hint">Any YES → name the one thing they do NOT do; that's what you build at 7:45. All NO/TAGS-ONLY → "No tool ships this; building it."</div>
  <button class="solid" id="gen">Generate existence-check.md</button>
</div>

<div class="out" id="out">
  <div class="q">Select all and copy into <b>existence-check.md</b>.</div>
  <textarea id="md" readonly></textarea>
</div>
<div class="foot">Nothing is saved when this closes — generate and copy the markdown before you shut it.</div>`;

const fmt=s=>{const a=Math.abs(s);return (s<0?"-":"")+Math.floor(a/60)+":"+String(a%60).padStart(2,'0');};

function paint(){
  const b=document.getElementById('big');
  b.textContent=fmt(C.sec);
  b.className='clock'+(C.sec<0?' over':C.sec<600?' warn':'');
  S.forEach((s,i)=>{
    const m=document.getElementById('m'+i), r=600-s.sec;
    m.textContent=fmt(r);
    m.className='mini'+(r<0?' over':r<120?' warn':'');
    document.getElementById('t'+i).textContent=s.run?'Pause':(s.sec?'Resume':'Start');
    const c=document.getElementById('c'+i);
    c.classList.toggle('active',s.run);
    c.classList.toggle('done',!!s.v);
    c.classList.toggle('open',s.open);
  });
  const done=S.filter(s=>s.v).length;
  const vd=document.getElementById('vd');
  if(done<5){vd.textContent=`${done} of 5 marked. Mark all five to get your prompt.`;}
  else if(S.some(s=>s.v==='YES')){
    vd.innerHTML=`<b>${S.filter(s=>s.v==='YES').map((s,i)=>TOOLS[S.indexOf(s)].n).join(', ')}</b> shipped it. Write the one thing they do NOT do — most likely repeated-context detection. Build that.`;
  } else {vd.innerHTML=`<b>Nothing ships it.</b> Write: "No tool ships this; building it." Then close the laptop.`;}
}

setInterval(()=>{
  if(C.run)C.sec--;
  S.forEach(s=>{if(s.run)s.sec++;});
  if(C.run||S.some(s=>s.run))paint();
},1000);

app.addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b)return;
  if(b.id==='go'){C.run=!C.run;b.textContent=C.run?'Pause box':'Resume box';paint();return;}
  if(b.id==='rs'){C.sec=3600;C.run=false;document.getElementById('go').textContent='Start box';
    S.forEach(s=>{s.sec=0;s.run=false;});paint();return;}
  if(b.dataset.t!==undefined){
    const i=+b.dataset.t;
    if(!S[i].run){S.forEach(s=>s.run=false);S[i].run=true;S[i].open=true;if(!C.run){C.run=true;document.getElementById('go').textContent='Pause box';}}
    else S[i].run=false;
    paint();return;
  }
  if(b.dataset.v){
    const i=+b.dataset.i;
    S[i].v = S[i].v===b.dataset.v ? "" : b.dataset.v;
    S[i].run=false; S[i].open=true;
    b.parentNode.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x.dataset.v===S[i].v));
    paint();return;
  }
  if(b.id==='gen'){
    S.forEach((s,i)=>{s.url=document.getElementById('u'+i).value.trim();s.note=document.getElementById('n'+i).value.trim();
      document.getElementById('u'+i).classList.toggle('bad',s.v==='YES'&&!s.url);});
    C.line=document.getElementById('cl').value.trim();
    const rows=S.map((s,i)=>{
      let v=s.v||'NO';
      if(v==='YES'&&!s.url)v='NO';
      const label=v==='TAGS'?'NO (tags-only)':v;
      return `| ${TOOLS[i].n} | ${label} | ${s.url||'—'} | ${(s.note||'—').replace(/\|/g,'\\|').replace(/\n/g,' ')} |`;
    }).join('\n');
    document.getElementById('md').value=
`# Existence check — per-subagent token attribution, ranked by cost

**Question:** does the tool show token/dollar totals grouped by SUB-AGENT, ordered by cost?
**Pass:** shipped view + sub-agent-level dimension + proof URL. No URL = NO. Tags-only = NO.
**Run:** Mon Jul 27, 18:30–19:30 box.

| Tool | Y/N | Proof URL | Note |
|---|---|---|---|
${rows}

## Verdict
${C.line||'_(unwritten)_'}
`;
    document.getElementById('out').classList.add('show');
    document.getElementById('md').scrollIntoView({behavior:'smooth',block:'nearest'});
    return;
  }
});
paint();
})();
</script>
