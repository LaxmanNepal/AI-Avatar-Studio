const state={avatars:[],section:"dashboard"};
const $=(s)=>document.querySelector(s);
const DRIVE_ROOT="/content/drive/MyDrive/Laxman AI Avatar Studio";
async function loadData(){
  try{const r=await fetch("data/avatars.json",{cache:"no-store"});const j=await r.json();state.avatars=j.avatars||[];}
  catch(e){state.avatars=[]}
  renderAvatars(); updateMetrics();
}
function updateMetrics(){const n=$("#avatarCount");if(n)n.textContent=state.avatars.length;const v=$("#voiceCount");if(v)v.textContent="1";}
function renderAvatars(){
  const box=$("#avatarLibrary");if(!box)return;
  box.innerHTML=state.avatars.map((a,i)=>`<article class="avatar-card" tabindex="0" data-id="${a.id}"><div class="avatar-art"><span>AVATAR ${String(i+1).padStart(2,"0")}</span><b>▶</b></div><div class="avatar-info"><h3>${escapeHtml(a.name)}</h3><p>${escapeHtml(a.angle)} angle · ${escapeHtml(a.status)}</p><button class="select-avatar" data-id="${a.id}">Use this avatar</button></div></article>`).join("");
  box.querySelectorAll(".select-avatar").forEach(b=>b.onclick=()=>selectAvatar(b.dataset.id));
}
function selectAvatar(id){const a=state.avatars.find(x=>x.id===id);if(!a)return;localStorage.setItem("laxman.selectedAvatar",id);syncSelectedAvatar();const msg=$("#toast");if(msg){msg.textContent=a.name+" selected";msg.classList.add("show");setTimeout(()=>msg.classList.remove("show"),1800)}showSection("generate");}
function syncSelectedAvatar(){const id=localStorage.getItem("laxman.selectedAvatar");const a=state.avatars.find(x=>x.id===id);const out=$("#selectedAvatar");if(out)out.textContent=a?a.name:"Select an avatar";const s=$("#avatarSelect");if(s&&id)s.value=id;}
function showSection(name){state.section=name;document.querySelectorAll("[data-section]").forEach(x=>x.hidden=x.dataset.section!==name);document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x.dataset.target===name));}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));}
function downloadJob(){
  const id=localStorage.getItem("laxman.selectedAvatar");
  const avatar=state.avatars.find(x=>x.id===id);
  if(!avatar){alert("Select an avatar first.");return;}
  const avatarPath=avatar.id==="avatar-01"?DRIVE_ROOT+"/temp/laxman_avatar_test.mp4":DRIVE_ROOT+"/avatars/";
  const job={schema_version:1,id:"job-"+new Date().toISOString().replace(/[-:.TZ]/g,"").slice(0,14),avatar_path:avatarPath,audio_path:DRIVE_ROOT+"/temp/laxman_voice_musetalk.wav",batch_size:4};
  const blob=new Blob([JSON.stringify(job,null,2)],{type:"application/json"});
  const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=job.id+".json";a.click();URL.revokeObjectURL(a.href);
  const msg=$("#toast");if(msg){msg.textContent="Job JSON downloaded — place it in Drive/jobs/queued";msg.classList.add("show");setTimeout(()=>msg.classList.remove("show"),3000);}
}
document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".nav[data-target]").forEach(b=>b.onclick=()=>showSection(b.dataset.target));
  document.querySelectorAll("[data-go]").forEach(b=>b.onclick=()=>showSection(b.dataset.go));
  if($("#avatarCount"))loadData();
  const form=$("#generateForm");
  if(form)form.onsubmit=e=>{e.preventDefault();downloadJob();};
  showSection("dashboard");
});