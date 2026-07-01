const $ = (s, r = document) => r.querySelector(s);
const el = (h) => { const t = document.createElement("template"); t.innerHTML = h.trim(); return t.content.firstChild; };
let STATUS = null, OUT_ROOT = "", SEP = "/";

const ICONS = {
  setup:'<path d="M12 2v4M12 18v4M2 12h4M18 12h4"/><circle cx="12" cy="12" r="4"/>',
  tts:'<path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
  transcribe:'<path d="M4 6h16M4 12h10M4 18h7"/>',
  image:'<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5L5 21"/>',
  kenburns:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M9 9l6 3-6 3z"/>',
  music:'<circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/><path d="M9 18V5l12-2v13"/>',
  video:'<rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10l6-3v10l-6-3z"/>',
  analyze:'<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
};
const icon = (k) => `<svg viewBox="0 0 24 24" class="ic">${ICONS[k]||""}</svg>`;

const FORMS = {
  setup:{title:"Welcome",screen:renderSetup},
  tts:{title:"Voiceover",tool:"tts",gpu:"optional",
    blurb:"Type a script and turn it into a spoken audio track.",
    fields:[{k:"text",t:"textarea",label:"Script",ph:"Welcome to my video. Today we'll..."},
      {k:"voice",t:"text",label:"Voice",value:"en_US-amy-medium",hint:"more at huggingface.co/rhasspy/piper-voices"},
      {k:"out",t:"out",label:"Save as",value:"public/audio/voiceover.wav"}]},
  transcribe:{title:"Captions & transcript",tool:"transcribe",gpu:"optional",
    blurb:"Pick an audio or video file and get subtitles plus word-level timings.",
    fields:[{k:"input",t:"file",label:"Audio or video file"},
      {k:"model",t:"seg",label:"Quality",value:"base",opts:["tiny","base","small","medium"]},
      {k:"out",t:"out",label:"Save as (no extension)",value:"public/captions/captions"}]},
  image:{title:"Image",tool:"image",gpu:"recommended",needs:"image",
    blurb:"Describe a picture and generate it on your GPU.",
    fields:[{k:"prompt",t:"textarea",label:"Describe the image",ph:"cinematic city skyline at dusk, drone shot"},
      {k:"model",t:"seg",label:"Model",value:"sdxl",opts:["sdxl","flux-schnell"],
        hint:"SDXL fits a 12GB GPU; FLUX needs more"},
      {k:"size",t:"size",label:"Size"},
      {k:"out",t:"out",label:"Save as",value:"public/images/image.png"}]},
  kenburns:{title:"Motion clip",tool:"kenburns",gpu:"no",
    blurb:"Turn a still image into a slow pan-and-zoom clip. Fast, no GPU needed.",
    fields:[{k:"image",t:"file",label:"Image file"},
      {k:"seconds",t:"slider",label:"Length",value:6,min:2,max:20,unit:"s"},
      {k:"out",t:"out",label:"Save as",value:"public/clips/clip.mp4"}]},
  music:{title:"Music",tool:"music",gpu:"recommended",needs:"music",
    blurb:"Generate a background music bed from a short description.",
    fields:[{k:"prompt",t:"text",label:"Describe the music",ph:"warm lo-fi jazz, soft piano"},
      {k:"duration",t:"slider",label:"Length",value:20,min:5,max:60,unit:"s"},
      {k:"model",t:"seg",label:"Model",value:"small",opts:["small","medium"]},
      {k:"out",t:"out",label:"Save as",value:"public/music/bed.wav"}]},
  video:{title:"Video clip",tool:"video",gpu:"required",needs:"video",
    blurb:"Create a short moving clip from text. Heavy and experimental; prefer a Motion clip when you can.",
    fields:[{k:"prompt",t:"text",label:"Describe the clip",ph:"a paper plane gliding over a desk"},
      {k:"out",t:"out",label:"Save as",value:"public/clips/generated.mp4"}]},
  analyze:{title:"Analyze footage",tool:"analyze",gpu:"no",
    blurb:"Find scene cuts in a video and view one frame per scene.",
    fields:[{k:"input",t:"file",label:"Video file"},
      {k:"outdir",t:"out",label:"Save report to",value:"analysis"}]},
};
const ORDER=["setup","tts","transcribe","image","kenburns","music","video","analyze"];

async function boot(){
  STATUS=await fetch("/api/status").then(r=>r.json());
  OUT_ROOT=STATUS.output_root||""; SEP=STATUS.os==="windows"?"\\":"/";
  renderChrome(); renderRail(); show(current||"setup");
}
let current=null;

function renderChrome(){
  $("#outputPath").textContent=OUT_ROOT;
  $("#outputBtn").onclick=openModal;
  $("#revealBtn").onclick=async()=>{ try{await api("/api/reveal",{path:"."}); toast("Opened folder");}catch(e){toast(e.message,true);} };
  const cuda=STATUS.accelerator==="cuda",ff=STATUS.binaries.ffmpeg;
  $("#chips").innerHTML=
    `<span class="chip"><span class="dot ${cuda?'ok':'no'}"></span><b>${cuda?'GPU':STATUS.accelerator==='mps'?'Apple GPU':'CPU'}</b></span>`+
    `<span class="chip"><span class="dot ${ff?'ok':'no'}"></span>ffmpeg</span>`;
  $("#clearJobs").onclick=()=>{document.querySelectorAll(".job.finished").forEach(e=>e.remove());if(!$("#jobs").children.length)emptyJobs();};
  $("#modalCancel").onclick=closeModal;
  $("#modalSave").onclick=saveOutput;
}

function renderRail(){
  const s=$("#steps");s.innerHTML='<div class="railhead">Steps</div>';
  ORDER.forEach((k,i)=>{
    const f=FORMS[k];let stat="";
    if(f.needs)stat=`<span class="stat ${STATUS.features[f.needs]?'ok':'missing'}"></span>`;
    const b=el(`<button class="step" data-k="${k}"><span class="si">${icon(k)}</span><span class="slabel">${f.title}</span>${stat}</button>`);
    b.onclick=()=>show(k);s.appendChild(b);
  });
}

function show(k){
  current=k;
  document.querySelectorAll(".step").forEach(s=>s.classList.toggle("active",s.dataset.k===k));
  const f=FORMS[k];
  if(f.screen)return f.screen();
  renderForm(k,f);
}

function gpuBadge(g){return `<span class="badge gpu-${g}">${g==='no'?'no GPU':'GPU '+g}</span>`;}
function joinPath(rel){return OUT_ROOT?OUT_ROOT+SEP+rel.replace(/\//g,SEP):rel;}

function renderSetup(){
  const s=STATUS,acc=s.accelerator;
  const accMsg=acc==="cpu"
    ?"You're on CPU. Voiceover, captions, motion clips, analysis and assembly all work. Image and music will be slow; video isn't practical."
    :"A GPU was detected, so every tool is available.";
  const ff=!s.binaries.ffmpeg;
  const cards=["image","music","video"].map(n=>{
    const ok=s.features[n],t=FORMS[Object.keys(FORMS).find(k=>FORMS[k].needs===n)];
    return `<div class="card"><h3>${t.title} <span class="pill ${ok?'ok':'no'}">${ok?'ready':'not installed'}</span></h3>
      <p>${t.blurb}</p>${ok?'':`<button class="ghost" style="margin-top:11px" onclick="installFeature('${n}')">Install ${n}</button>`}</div>`;
  }).join("");
  $("#screen").innerHTML=`<div class="eyebrow">Start here</div>
    <h2>Make a video, step by step ${icon('setup')}</h2>
    <p class="lede">Everything runs on your own machine. Work down the steps on the left. Voiceover and captions work right away; the heavier tools install when you first use them.</p>
    ${ff?`<div class="note warn">FFmpeg isn't installed and most steps need it. Install it, then reload.<br>Windows: <code>winget install Gyan.FFmpeg</code></div>`:''}
    <div class="note cool">${accMsg}</div>
    <h3 style="margin:26px 0 6px;font-size:16px">Optional tools</h3>
    <p class="lede" style="margin-bottom:14px">These download large model files on first use. Install only what you need.</p>
    <div class="cards">${cards}</div>`;
}

function renderForm(k,f){
  const needsMissing=f.needs&&!STATUS.features[f.needs];
  $("#screen").innerHTML=`<div class="eyebrow">${f.tool}</div>
    <h2>${f.title} ${gpuBadge(f.gpu)}</h2><p class="lede">${f.blurb}</p>
    ${needsMissing?`<div class="note warn">Not installed yet. The first time you generate, the model files download automatically (can be several GB).</div>`:''}
    <div id="fields">${f.fields.map(fieldHTML).join("")}</div>
    <button id="go" class="primary">${icon('kenburns')} Generate</button>
    <div id="result"></div>`;
  f.fields.forEach(fl=>wireField(fl));
  $("#go").onclick=()=>submit(k,f);
}

function fieldHTML(fl){
  const id=`f_${fl.k}`,lab=`<label>${fl.label}${fl.hint?`<span class="hint">${fl.hint}</span>`:''}</label>`;
  if(fl.t==="textarea")return `<div class="field">${lab}<textarea id="${id}" placeholder="${fl.ph||''}"></textarea></div>`;
  if(fl.t==="text")return `<div class="field">${lab}<input id="${id}" class="inp" value="${fl.value||''}" placeholder="${fl.ph||''}"></div>`;
  if(fl.t==="seg")return `<div class="field">${lab}<div class="seg" id="${id}">${fl.opts.map(o=>`<button data-v="${o}" class="${o===fl.value?'on':''}">${o}</button>`).join("")}</div></div>`;
  if(fl.t==="slider")return `<div class="field">${lab}<div class="slider"><input id="${id}" type="range" min="${fl.min}" max="${fl.max}" value="${fl.value}"><span class="val" id="${id}_v">${fl.value}${fl.unit||''}</span></div></div>`;
  if(fl.t==="size")return `<div class="field">${lab}<div class="row"><input id="f_width" class="inp" type="number" value="1024"><input id="f_height" class="inp" type="number" value="1024"></div></div>`;
  if(fl.t==="file")return `<div class="field">${lab}<label class="drop" id="drop_${fl.k}"><input id="${id}" type="file"><span class="dl">Click to choose a file, or drag it here</span></label></div>`;
  if(fl.t==="out")return `<div class="field">${lab}<input id="${id}" class="inp mono" value="${fl.value||''}" spellcheck="false"><div class="pathline">${icon('setup')}<span class="mono" id="${id}_abs"></span></div></div>`;
  return "";
}

const VALS={},UPLOADED={};
function wireField(fl){
  const id=`f_${fl.k}`;
  if(fl.t==="seg"){VALS[fl.k]=fl.value;const g=$("#"+id);g.querySelectorAll("button").forEach(b=>b.onclick=()=>{g.querySelectorAll("button").forEach(x=>x.classList.remove("on"));b.classList.add("on");VALS[fl.k]=b.dataset.v;});}
  if(fl.t==="slider"){const i=$("#"+id),v=$("#"+id+"_v");i.oninput=()=>v.textContent=i.value+(fl.unit||"");}
  if(fl.t==="out"){const i=$("#"+id),a=$("#"+id+"_abs");const upd=()=>a.textContent=joinPath(i.value);upd();i.oninput=upd;}
  if(fl.t==="file"){
    const drop=$("#drop_"+fl.k),inp=$("#"+id);
    const setf=async(file)=>{drop.querySelector(".dl").textContent="Uploading…";
      const fd=new FormData();fd.append("file",file);
      try{const r=await fetch("/api/upload",{method:"POST",body:fd}).then(r=>r.json());
        UPLOADED[fl.k]=r.path;drop.classList.add("has");drop.querySelector(".dl").innerHTML=`<b>${file.name}</b> ready`;}
      catch(e){toast("Upload failed",true);drop.querySelector(".dl").textContent="Click to choose a file";}};
    inp.onchange=()=>inp.files[0]&&setf(inp.files[0]);
    drop.ondragover=e=>{e.preventDefault();drop.style.borderColor="var(--accent)";};
    drop.ondragleave=()=>drop.style.borderColor="";
    drop.ondrop=e=>{e.preventDefault();e.dataTransfer.files[0]&&setf(e.dataTransfer.files[0]);};
  }
}

async function api(url,body){
  const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const j=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(j.detail?(typeof j.detail==="string"?j.detail:JSON.stringify(j.detail)):("HTTP "+r.status));
  return j;
}

async function submit(k,f){
  const p={};
  for(const fl of f.fields){
    if(fl.t==="file")p[fl.k]=UPLOADED[fl.k]||"";
    else if(fl.t==="seg")p[fl.k]=VALS[fl.k];
    else if(fl.t==="size"){p.width=$("#f_width").value;p.height=$("#f_height").value;}
    else p[fl.k]=$("#f_"+fl.k)?.value;
  }
  const btn=$("#go");btn.disabled=true;btn.innerHTML=`<span class="spinner"></span> Working…`;
  try{
    const r=await api("/api/run",{tool:f.tool,label:f.title,params:p});
    trackJob(r.job,r.command,f.tool,p.outdir||p.out);
    toast(`${f.title} started`);
  }catch(e){toast(e.message,true);}
  setTimeout(()=>{btn.disabled=false;btn.innerHTML=`${icon('kenburns')} Generate`;},600);
}

async function installFeature(n){
  try{const r=await api("/api/run",{tool:"install",label:"Install "+n,params:{feature:n}});
    trackJob(r.job,r.command,"install");toast("Installing "+n+" — watch Activity");}
  catch(e){toast(e.message,true);}
}

/* jobs */
const TRACK={};
function emptyJobs(){$("#jobs").innerHTML='<p class="empty">No activity yet.<br>Pick a step and generate.</p>';}
function trackJob(id,cmd,tool,outhint){
  TRACK[id]={tool,outhint};
  $("#jobs .empty")?.remove();
  const j=el(`<div class="job" id="job_${id}">
    <div class="jhead"><span class="st running"></span><span class="lbl">Working…</span></div>
    <div class="bar"><i></i></div>
    <div class="log mono"></div><div class="cmd mono">${cmd}</div></div>`);
  j.querySelector(".jhead").onclick=()=>j.classList.toggle("open");
  $("#jobs").prepend(j);
  if(!TRACK._poll){TRACK._poll=true;pollJobs();}
}
async function pollJobs(){
  for(const id of Object.keys(TRACK)){
    if(id==="_poll")continue;
    const j=await fetch("/api/jobs/"+id).then(r=>r.json()).catch(()=>null);if(!j)continue;
    const e=$("#job_"+id);if(!e)continue;
    e.className="job"+(j.status!=="running"?" finished "+j.status:"");if(e.classList.contains("open"))e.classList.add("open");
    e.querySelector(".st").className="st "+j.status;
    e.querySelector(".lbl").textContent=j.label+(j.status==="running"?" — working":j.status==="done"?" — done":" — failed");
    e.querySelector(".log").textContent=(j.log||[]).slice(-50).join("\n");
    if(j.status!=="running"&&!e.dataset.fin){e.dataset.fin="1";onFinish(id,j);}
  }
  setTimeout(pollJobs,1100);
}
function onFinish(id,j){
  const t=TRACK[id];
  if(t.tool==="install"){toast(j.status==="done"?"Install finished":"Install failed",j.status!=="done");boot();return;}
  if(j.status!=="done"){toast(j.label+" failed — open the job to see why",true);return;}
  if(current!==t.tool)return; // only show inline result if still on that screen
  const res=$("#result");if(!res)return;
  if(t.tool==="analyze")return showAnalysis(res,t.outhint);
  const out=(j.output||"").trim();const url="/api/file?path="+encodeURIComponent(out);
  const ext=out.split(".").pop().toLowerCase();let media="";
  if(["wav","mp3","m4a"].includes(ext))media=`<audio controls src="${url}"></audio>`;
  else if(["png","jpg","jpeg","webp"].includes(ext))media=`<img src="${url}">`;
  else if(["mp4","mov","webm"].includes(ext))media=`<video controls src="${url}"></video>`;
  res.innerHTML=`<div class="result"><h3>Done</h3>${media}<div class="path mono">${out}</div>
    <div class="acts"><a class="ghost" href="${url}" download>Download</a>
    <button class="ghost" onclick="reveal('${out.replace(/\\/g,'\\\\')}')">Show in folder</button></div></div>`;
}
async function showAnalysis(res,outdir){
  res.innerHTML=`<div class="result"><h3>Scenes</h3><p class="lede">Loading frames…</p></div>`;
  try{
    const d=await fetch("/api/analysis?path="+encodeURIComponent(outdir)).then(r=>r.json());
    const cells=d.scenes.map(s=>`<div class="scene">${s.frame_url?`<img src="${s.frame_url}">`:''}
      <div class="meta"><span>scene ${s.scene+1}</span><b>${fmt(s.start_s)}–${fmt(s.end_s)}</b></div></div>`).join("");
    res.querySelector(".result").innerHTML=`<h3>Scenes <span class="badge gpu-no">${d.count} found</span></h3>
      <div class="gallery">${cells}</div>
      <div class="acts"><button class="ghost" onclick="reveal('${outdir.replace(/\\/g,'\\\\')}')">Show in folder</button></div>`;
  }catch(e){res.querySelector(".result").innerHTML=`<h3>Scenes</h3><p class="lede">Couldn't load results: ${e.message}</p>`;}
}
function fmt(s){const m=Math.floor(s/60),x=Math.floor(s%60);return `${m}:${String(x).padStart(2,'0')}`;}
async function reveal(p){try{await api("/api/reveal",{path:p});toast("Opened folder");}catch(e){toast(e.message,true);}}

/* output modal */
function openModal(){$("#modalInput").value=OUT_ROOT;$("#modal").classList.remove("hidden");$("#modalInput").focus();}
function closeModal(){$("#modal").classList.add("hidden");}
async function saveOutput(){
  const v=$("#modalInput").value.trim();if(!v)return;
  try{const r=await api("/api/config",{output_root:v});OUT_ROOT=r.output_root;$("#outputPath").textContent=OUT_ROOT;closeModal();toast("Output folder updated");
    if(current&&!FORMS[current].screen)show(current);}
  catch(e){toast(e.message,true);}
}

/* toasts */
function toast(msg,err){const t=el(`<div class="toast ${err?'err':''}">${msg}</div>`);$("#toasts").appendChild(t);
  setTimeout(()=>{t.style.opacity="0";setTimeout(()=>t.remove(),300);},err?4200:2600);}

boot();
