#!/usr/bin/env python3
"""Process one queued MuseTalk v1.5 job from Google Drive with durable metadata."""
from pathlib import Path
import json, os, shutil, subprocess, uuid
from datetime import datetime, timezone

ROOT=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
REPO=Path("/content/MuseTalk")
PYTHON="/content/musetalk-env/bin/python"
Q=ROOT/"jobs/queued"; P=ROOT/"jobs/processing"; C=ROOT/"jobs/completed"; F=ROOT/"jobs/failed"
LOGS=ROOT/"logs"; OUT=ROOT/"outputs"

def now():
    return datetime.now(timezone.utc).isoformat()

def move(src,dst):
    dst.mkdir(parents=True,exist_ok=True)
    out=dst/src.name
    shutil.move(str(src),str(out))
    return out

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")

def main():
    for d in (Q,P,C,F,LOGS,OUT): d.mkdir(parents=True,exist_ok=True)
    jobs=sorted(Q.glob("*.json"))
    if not jobs:
        print("QUEUE_EMPTY")
        return

    job=move(jobs[0],P)
    run_id=job.stem
    processing_meta=P/f"{run_id}.status.json"
    started=now()

    try:
        data=json.loads(job.read_text(encoding="utf-8"))
        if data.get("schema_version")!=1:
            raise ValueError("Unsupported job schema")
        if not data.get("id"):
            raise ValueError("Missing job id")
        run_id=data["id"]

        avatar=Path(data["avatar_path"])
        audio=Path(data["audio_path"])
        if not avatar.exists():
            raise FileNotFoundError(f"Avatar path does not exist: {avatar}")
        if not audio.exists():
            raise FileNotFoundError(f"Audio path does not exist: {audio}")

        write_json(processing_meta,{
            "schema_version":1,"id":run_id,"status":"processing",
            "created_at":started,"started_at":started,
            "avatar_id":data.get("avatar_id"),"voice_id":data.get("voice_id"),
            "avatar_path":str(avatar),"audio_path":str(audio)
        })

        cfg=REPO/"configs/inference"/f"{run_id}.yaml"
        cfg.parent.mkdir(parents=True,exist_ok=True)
        cfg.write_text(
            "task_0:\n"
            "  video_path: "+json.dumps(str(avatar))+"\n"
            "  audio_path: "+json.dumps(str(audio))+"\n"
            "  bbox_shift: 0\n",encoding="utf-8"
        )

        env=os.environ.copy()
        env["PYTHONPATH"]=str(REPO)
        env["MPLBACKEND"]="Agg"
        log=LOGS/f"{run_id}.log"
        cmd=[
            PYTHON,"scripts/inference.py","--version","v15","--gpu_id","0",
            "--vae_type","sd-vae",
            "--unet_config",str(ROOT/"models/musetalkV15/musetalk.json"),
            "--unet_model_path",str(ROOT/"models/musetalkV15/unet.pth"),
            "--whisper_dir",str(ROOT/"models/whisper"),
            "--inference_config",str(cfg),
            "--result_dir",str(OUT),
            "--batch_size",str(data.get("batch_size",4)),
            "--fps",str(data.get("fps",24)),
            "--use_float16"
        ]

        with log.open("w",encoding="utf-8") as f:
            result=subprocess.run(cmd,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT,check=False)

        cfg.unlink(missing_ok=True)
        if result.returncode!=0:
            raise RuntimeError(f"MuseTalk inference failed with exit code {result.returncode}. See {log}")

        candidates=sorted(OUT.glob("*.mp4"),key=lambda p:p.stat().st_mtime,reverse=True)
        output=candidates[0] if candidates else None
        if output is None:
            raise RuntimeError("MuseTalk exited successfully but no MP4 was found in outputs/")

        completed_job=move(job,C)
        processing_meta.unlink(missing_ok=True)
        result_meta=C/f"{run_id}.result.json"
        write_json(result_meta,{
            "schema_version":1,"id":run_id,"status":"completed",
            "created_at":started,"started_at":started,"completed_at":now(),
            "avatar_id":data.get("avatar_id"),"voice_id":data.get("voice_id"),
            "output_path":str(output),"output_name":output.name,
            "output_size_bytes":output.stat().st_size,
            "log_path":str(log),"job_path":str(completed_job),
            "note":data.get("note","")
        })
        print("COMPLETED",run_id)
        print("OUTPUT",output)

    except Exception as e:
        try:
            cfg.unlink(missing_ok=True)
        except Exception:
            pass
        processing_meta.unlink(missing_ok=True)
        failed=move(job,F)
        error_path=failed.with_suffix(".error.txt")
        error_path.write_text(now()+"\n"+repr(e),encoding="utf-8")
        write_json(F/f"{run_id}.result.json",{
            "schema_version":1,"id":run_id,"status":"failed",
            "created_at":started,"failed_at":now(),
            "error":repr(e),"error_path":str(error_path),
            "log_path":str(LOGS/f"{run_id}.log") if (LOGS/f"{run_id}.log").exists() else None,
            "job_path":str(failed)
        })
        raise

if __name__=="__main__":
    main()
