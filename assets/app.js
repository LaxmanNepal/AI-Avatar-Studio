const state={avatars:[],voices:[],jobs:[],section:"dashboard"};
const $=(s)=>document.querySelector(s);
const DRIVE_ROOT="/content/drive/MyDrive/Laxman AI Avatar Studio";

async function loadData(){
  try{
    const [ar,vr]=await Promise.all([
      fetch("data/avatars.json",{cache:"no-store"}),
      fetch("data/voices.json",{cache:"no-store"})
    ]);
    const aj=await ar.json(), vj=await vr.json();
    state.avatars=aj.avatars||[];
    state.voices=vj.voices||[];
  }catch(e){state.avatars=[];state.voices=[]}
  renderAvatars();
  renderVoices();
  populateGenerateForm();
  updateMetrics();
  syncSelectedAvatar();
}

function updateMetrics(){
  const n=$("#avatarCount"); if(n)n.textContent=state.avatars.length;
  const v=$("#voiceCount"); if(v)v.textContent=state.voices.length;
  const j=$("#jobCount"); if(j)j.textContent=state.jobs.length;
}

function renderAvatars(){
  const box=$("#avatarLibrary"); if(!box)return;
  box.innerHTML=state.avatars.map((a,i)=>`
    <article class="avatar-card" tabindex="0" data-id="${escapeHtml(a.id)}">
      <div class="avatar-art"><span>AVATAR ${String(i+1).padStart(2,"0")}</span><b>▶</b></div>
      <div class="avatar-info">
        <h3>${escapeHtml(a.name)}</h3>
        <p>${escapeHtml(a.angle)} angle · ${escapeHtml(a.status)}</p>
        <button class="select-avatar" data-id="${escapeHtml(a.id)}">Use this avatar</button>
      </div>
    </article>`).join("");
  box.querySelectorAll(".select-avatar").forEach(b=>b.onclick=()=>selectAvatar(b.dataset.id));
}

function renderVoices(){
  const box=$("#voiceLibrary"); if(!box)return;
  box.innerHTML=state.voices.map(v=>`
    <div class="card" style="margin-top:12px">
      <h3>${escapeHtml(v.name)}</h3>
      <p>Your original recording is used as audio input. <span class="tag">No voice cloning</span></p>
      <p class="muted">Source: ${escapeHtml(v.source)}</p>
    </div>`).join("");
}

function populateGenerateForm(){
  const a=$("#avatarSelect");
  if(a){
    a.innerHTML='<option value="">Choose an avatar</option>';
    state.avatars.forEach(x=>{
      const o=document.createElement("option");
      o.value=x.id;o.textContent=x.name+" — "+x.angle;a.appendChild(o);
    });
    const selected=localStorage.getItem("laxman.selectedAvatar");
    if(selected)a.value=selected;
    a.onchange=()=>selectAvatar(a.value,false);
  }
  const v=$("#voiceSelect");
  if(v){
    v.innerHTML="";
    state.voices.forEach(x=>{
      const o=document.createElement("option");
      o.value=x.id;o.textContent=x.name;v.appendChild(o);
    });
  }
}

function selectAvatar(id,navigate=true){
  const a=state.avatars.find(x=>x.id===id); if(!a)return;
  localStorage.setItem("laxman.selectedAvatar",id);
  syncSelectedAvatar();
  const msg=$("#toast");
  if(msg){msg.textContent=a.name+" selected";msg.classList.add("show");setTimeout(()=>msg.classList.remove("show"),1800)}
  if(navigate)showSection("generate");
}

function syncSelectedAvatar(){
  const id=localStorage.getItem("laxman.selectedAvatar");
  const a=state.avatars.find(x=>x.id===id);
  const out=$("#selectedAvatar"); if(out)out.textContent=a?a.name:"Select an avatar";
  const s=$("#avatarSelect"); if(s&&id)s.value=id;
}

function saveJobs(){localStorage.setItem("laxman.avatarJobs",JSON.stringify(state.jobs));}
function loadJobs(){
  try{state.jobs=JSON.parse(localStorage.getItem("laxman.avatarJobs")||"[]");if(!Array.isArray(state.jobs))state.jobs=[];}catch(e){state.jobs=[]}
  renderJobs();updateMetrics();
}
function renderJobs(){
  const box=$("#jobStatus");if(!box)return;
  if(!state.jobs.length){box.innerHTML='<div class="empty">No job metadata imported yet.</div>';return;}
  box.innerHTML=state.jobs.map(j=>{
    const ok=j.status==="completed";
    const media=j.media||{};
    return `<article class="job-row"><div><b>${escapeHtml(j.id||"Unnamed job")}</b><span class="status-badge ${ok?"success":"failed"}">${escapeHtml(j.status||"unknown")}</span><div class="muted job-meta">${j.completed_at||j.failed_at||j.started_at||""}</div></div><div class="job-details">${ok?escapeHtml(String(media.width||"?"))+"×"+escapeHtml(String(media.height||"?"))+" · "+escapeHtml(String(media.duration_seconds||"?"))+"s · "+escapeHtml(String(j.output_name||"")):escapeHtml(j.error||"See worker log")}</div></article>`;
  }).join("");
}
async function importResult(file){
  const text=await file.text();const data=JSON.parse(text);
  if(!data.id||!data.status)throw new Error("Invalid result metadata: missing id/status.");
  state.jobs=[data,...state.jobs.filter(x=>x.id!==data.id)].slice(0,50);saveJobs();renderJobs();updateMetrics();
}
function showSection(name){
  state.section=name;
  document.querySelectorAll("[data-section]").forEach(x=>x.hidden=x.dataset.section!==name);
  document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x.dataset.target===name));
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
}

function downloadJob(){
  const avatarId=($("#avatarSelect")?.value)||localStorage.getItem("laxman.selectedAvatar");
  const avatar=state.avatars.find(x=>x.id===avatarId);
  const voiceId=$("#voiceSelect")?.value||state.voices[0]?.id;
  const voice=state.voices.find(x=>x.id===voiceId)||state.voices[0];
  if(!avatar){alert("Select an avatar first.");return}
  if(!avatar.drive_path){alert("This avatar has no configured private Drive path yet.");return}
  if(!voice||!voice.drive_path){alert("No voice Drive path is configured.");return}

  const note=$("#jobNote")?.value?.trim()||"";
  const batch=Math.min(8,Math.max(1,Number($("#batchSize")?.value||4)));
  const fps=Math.min(60,Math.max(1,Number($("#fps")?.value||24)));
  const job={
    schema_version:1,
    id:"job-"+new Date().toISOString().replace(/[-:.TZ]/g,"").slice(0,14)+"-"+crypto.randomUUID().slice(0,6),
    avatar_id:avatar.id,
    voice_id:voice.id,
    avatar_path:DRIVE_ROOT+"/"+avatar.drive_path,
    audio_path:DRIVE_ROOT+"/"+voice.drive_path,
    batch_size:batch,
    fps:fps,
    note:note
  };
  const blob=new Blob([JSON.stringify(job,null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=job.id+".json";a.click();URL.revokeObjectURL(a.href);
  const msg=$("#toast");
  if(msg){msg.textContent="Job JSON downloaded — place it in Drive/jobs/queued";msg.classList.add("show");setTimeout(()=>msg.classList.remove("show"),3000)}
}

document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".nav[data-target]").forEach(b=>b.onclick=()=>showSection(b.dataset.target));
  document.querySelectorAll("[data-go]").forEach(b=>b.onclick=()=>showSection(b.dataset.go));
  if($("#avatarCount")){loadData();loadJobs();}
  const form=$("#generateForm");
  if(form)form.onsubmit=e=>{e.preventDefault();downloadJob()};
  const importer=$("#resultImport");
  if(importer)importer.onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{await importResult(file);showSection("outputs")}catch(err){alert(err.message)}e.target.value=""};
  showSection("dashboard");
});