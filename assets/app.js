const state={avatars:[],section:"dashboard"};
const $=(s)=>document.querySelector(s);
async function loadData(){
  try{
    const r=await fetch("data/avatars.json",{cache:"no-store"});
    const j=await r.json(); state.avatars=j.avatars||[];
  }catch(e){state.avatars=[]}
  renderAvatars(); updateMetrics();
}
function updateMetrics(){
  const n=$("#avatarCount"); if(n)n.textContent=state.avatars.length;
  const v=$("#voiceCount"); if(v)v.textContent="1";
}
function renderAvatars(){
  const box=$("#avatarLibrary"); if(!box)return;
  box.innerHTML=state.avatars.map((a,i)=>`
    <article class="avatar-card" tabindex="0" data-id="${a.id}">
      <div class="avatar-art"><span>AVATAR ${String(i+1).padStart(2,"0")}</span><b>▶</b></div>
      <div class="avatar-info"><h3>${escapeHtml(a.name)}</h3><p>${escapeHtml(a.angle)} angle · ${escapeHtml(a.status)}</p>
      <button class="select-avatar" data-id="${a.id}">Use this avatar</button></div>
    </article>`).join("");
  box.querySelectorAll(".select-avatar").forEach(b=>b.onclick=()=>selectAvatar(b.dataset.id));
}
function selectAvatar(id){
  const a=state.avatars.find(x=>x.id===id); if(!a)return;
  localStorage.setItem("laxman.selectedAvatar",id);
  const msg=$("#toast"); if(msg){msg.textContent=a.name+" selected";msg.classList.add("show");setTimeout(()=>msg.classList.remove("show"),1800)}
  showSection("generate");
}
function showSection(name){
  state.section=name;
  document.querySelectorAll("[data-section]").forEach(x=>x.hidden=x.dataset.section!==name);
  document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x.dataset.target===name));
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".nav[data-target]").forEach(b=>b.onclick=()=>showSection(b.dataset.target));
  document.querySelectorAll("[data-go]").forEach(b=>b.onclick=()=>showSection(b.dataset.go));
  $("#avatarCount")&&loadData();
  $("#selectedAvatar")&&(async()=>{const id=localStorage.getItem("laxman.selectedAvatar");const r=await fetch("data/avatars.json");const j=await r.json();const a=(j.avatars||[]).find(x=>x.id===id);$("#selectedAvatar").textContent=a?a.name:"Select an avatar";})();
  const form=$("#generateForm"); if(form)form.onsubmit=e=>{e.preventDefault();const id=localStorage.getItem("laxman.selectedAvatar"); if(!id){alert("Select an avatar first.");return} alert("Job prepared. Connect the Colab backend to process it.");};
  showSection("dashboard");
});