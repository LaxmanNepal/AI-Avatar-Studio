#!/usr/bin/env python3
"""Process one queued MuseTalk v1.5 job from Google Drive."""
from pathlib import Path
import json, os, shutil, subprocess, uuid
from datetime import datetime, timezone

ROOT=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
REPO=Path("/content/MuseTalk"); PYTHON="/content/musetalk-env/bin/python"
Q=ROOT/"jobs/queued"; P=ROOT/"jobs/processing"; C=ROOT/"jobs/completed"; F=ROOT/"jobs/failed"

def move(src,dst): dst.mkdir(parents=True,exist_ok=True); out=dst/src.name; shutil.move(str(src),str(out)); return out
def main():
    for d in (Q,P,C,F,ROOT/"logs",ROOT/"outputs"): d.mkdir(parents=True,exist_ok=True)
    jobs=sorted(Q.glob("*.json"))
    if not jobs: print("QUEUE_EMPTY"); return
    job=move(jobs[0],P)
    try:
        data=json.loads(job.read_text())
        if data.get("schema_version")!=1: raise ValueError("Unsupported job schema")
        avatar=Path(data["avatar_path"]); audio=Path(data["audio_path"])
        if not avatar.exists() or not audio.exists(): raise FileNotFoundError("Avatar or audio path does not exist")
        run_id=data.get("id","job-"+uuid.uuid4().hex[:10])
        cfg=REPO/"configs/inference"/f"{run_id}.yaml"; cfg.parent.mkdir(parents=True,exist_ok=True)
        cfg.write_text("task_0:\n  video_path: "+json.dumps(str(avatar))+"\n  audio_path: "+json.dumps(str(audio))+"\n  bbox_shift: 0\n")
        env=os.environ.copy(); env["PYTHONPATH"]=str(REPO); env["MPLBACKEND"]="Agg"
        cmd=[PYTHON,"scripts/inference.py","--version","v15","--gpu_id","0","--vae_type","sd-vae","--unet_config",str(ROOT/"models/musetalkV15/musetalk.json"),"--unet_model_path",str(ROOT/"models/musetalkV15/unet.pth"),"--whisper_dir",str(ROOT/"models/whisper"),"--inference_config",str(cfg),"--result_dir",str(ROOT/"outputs"),"--batch_size",str(data.get("batch_size",4)),"--use_float16"]
        log=ROOT/"logs"/f"{run_id}.log"
        with log.open("w") as f: subprocess.run(cmd,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        cfg.unlink(missing_ok=True); done=move(job,C); print("COMPLETED",run_id,done)
    except Exception as e:
        failed=move(job,F); (failed.with_suffix(".error.txt")).write_text(datetime.now(timezone.utc).isoformat()+"\n"+repr(e)); raise

if __name__=="__main__": main()
