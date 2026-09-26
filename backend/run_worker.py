#!/usr/bin/env python3
"""Process one queued MuseTalk v1.5 job from Google Drive with durable metadata."""
from pathlib import Path
import json, os, shutil, subprocess, uuid, time
from datetime import datetime, timezone

ROOT=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
REPO=Path("/content/MuseTalk")
PYTHON="/content/musetalk-env/bin/python"
Q=ROOT/"jobs/queued"; P=ROOT/"jobs/processing"; C=ROOT/"jobs/completed"; F=ROOT/"jobs/failed"
LOGS=ROOT/"logs"; OUT=ROOT/"outputs"
SYNC_SCRIPT=Path("/content/AI-Avatar-Studio/backend/sync_status.py")
STALE_AFTER_SECONDS=3600
WORKER_ID=os.environ.get("LAXMAN_AVATAR_WORKER_ID") or uuid.uuid4().hex[:12]

def now():
    return datetime.now(timezone.utc).isoformat()

def move(src,dst):
    dst.mkdir(parents=True,exist_ok=True)
    out=dst/src.name
    shutil.move(str(src),str(out))
    return out

def write_json(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")

def probe(path):
    cmd=["ffprobe","-v","error","-show_entries","format=duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels","-of","json",str(path)]
    r=subprocess.run(cmd,capture_output=True,text=True,check=True)
    return json.loads(r.stdout)

def validate_output(path):
    if not path.exists() or path.stat().st_size < 1024:
        raise RuntimeError("Generated MP4 is missing or empty.")
    info=probe(path)
    streams=info.get("streams",[])
    video=[s for s in streams if s.get("codec_type")=="video"]
    audio_streams=[s for s in streams if s.get("codec_type")=="audio"]
    if not video:
        raise RuntimeError("Generated file has no video stream.")
    if not audio_streams:
        raise RuntimeError("Generated file has no audio stream.")
    duration=float(info.get("format",{}).get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("Generated file has invalid duration.")
    v=video[0]
    if not v.get("width") or not v.get("height"):
        raise RuntimeError("Generated video has invalid dimensions.")
    return {"duration_seconds":duration,"width":v["width"],"height":v["height"],
            "video_codec":v.get("codec_name"),"audio_codec":audio_streams[0].get("codec_name"),
            "audio_sample_rate":audio_streams[0].get("sample_rate"),
            "size_bytes":path.stat().st_size}

def sync_status():
    if not SYNC_SCRIPT.exists():
        return
    subprocess.run([PYTHON,str(SYNC_SCRIPT)],check=False,cwd=SYNC_SCRIPT.parent)

def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def recover_stale_jobs(stale_after_seconds=STALE_AFTER_SECONDS):
    recovered=0
    now_dt=datetime.now(timezone.utc)
    for status_path in sorted(P.glob("*.status.json")):
        try:
            data=json.loads(status_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("status")!="processing":
            continue
        heartbeat=parse_time(data.get("heartbeat_at") or data.get("started_at"))
        if heartbeat is None or (now_dt-heartbeat).total_seconds() <= stale_after_seconds:
            continue
        run_id=str(data.get("id") or status_path.stem.removesuffix(".status"))
        job_path=P/f"{run_id}.json"
        if not job_path.exists():
            status_path.unlink(missing_ok=True)
            continue
        queued=Q/job_path.name
        if not queued.exists():
            shutil.move(str(job_path),str(queued))
            (LOGS/f"{run_id}.recovery.log").write_text(now()+"\nRecovered stale processing job; previous_worker="+str(data.get("worker_id"))+"\n",encoding="utf-8")
            recovered+=1
            print("RECOVERED_STALE",run_id)
        status_path.unlink(missing_ok=True)
    if recovered:
        sync_status()
    return recovered

def process_one():
    for d in (Q,P,C,F,LOGS,OUT): d.mkdir(parents=True,exist_ok=True)
    recover_stale_jobs()
    jobs=sorted(Q.glob("*.json"))
    if not jobs:
        print("QUEUE_EMPTY")
        return

    job=move(jobs[0],P)
    run_id=job.stem
    processing_meta=None
    started=now()

    cfg=None
    try:
        data=json.loads(job.read_text(encoding="utf-8"))
        if data.get("schema_version")!=1:
            raise ValueError("Unsupported job schema")
        if not data.get("id"):
            raise ValueError("Missing job id")
        run_id=data["id"]
        processing_meta=P/f"{run_id}.status.json"

        avatar=Path(data["avatar_path"])
        audio=Path(data["audio_path"])
        if not avatar.exists():
            raise FileNotFoundError(f"Avatar path does not exist: {avatar}")
        if not audio.exists():
            raise FileNotFoundError(f"Audio path does not exist: {audio}")

        write_json(processing_meta,{
            "schema_version":1,"id":run_id,"status":"processing",
            "created_at":started,"started_at":started,"heartbeat_at":started,
            "worker_id":WORKER_ID,
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
        # Isolate each inference in a private per-job result directory.
        job_out=OUT/"_jobs"/run_id
        if job_out.exists():
            shutil.rmtree(job_out)
        job_out.mkdir(parents=True,exist_ok=True)
        cmd=[
            PYTHON,"scripts/inference.py","--version","v15","--gpu_id","0",
            "--vae_type","sd-vae",
            "--unet_config",str(ROOT/"models/musetalkV15/musetalk.json"),
            "--unet_model_path",str(ROOT/"models/musetalkV15/unet.pth"),
            "--whisper_dir",str(ROOT/"models/whisper"),
            "--inference_config",str(cfg),
            "--result_dir",str(job_out),
            "--batch_size",str(data.get("batch_size",4)),
            "--fps",str(data.get("fps",24)),
            "--use_float16"
        ]

        with log.open("w",encoding="utf-8") as f:
            proc=subprocess.Popen(cmd,cwd=REPO,env=env,stdout=f,stderr=subprocess.STDOUT)
            last_heartbeat=time.monotonic()
            while proc.poll() is None:
                if time.monotonic()-last_heartbeat >= 30:
                    try:
                        status=json.loads(processing_meta.read_text(encoding="utf-8"))
                        status["heartbeat_at"]=now()
                        write_json(processing_meta,status)
                    except Exception:
                        pass
                    last_heartbeat=time.monotonic()
                time.sleep(2)
            result_returncode=proc.returncode

        cfg.unlink(missing_ok=True)
        if result_returncode!=0:
            raise RuntimeError(f"MuseTalk inference failed with exit code {result_returncode}. See {log}")

        candidates=sorted(job_out.glob("*.mp4"),key=lambda p:p.stat().st_mtime,reverse=True)
        if not candidates:
            raise RuntimeError("MuseTalk exited successfully but produced no MP4 in the isolated job output directory.")
        if len(candidates)>1:
            raise RuntimeError(f"MuseTalk produced multiple MP4 files for {run_id}; refusing ambiguous output selection.")
        output=candidates[0]

        media=validate_output(output)
        final_output=OUT/f"{run_id}.mp4"
        if output.resolve()!=final_output.resolve():
            if final_output.exists():
                final_output.unlink()
            output.rename(final_output)
        output=final_output
        shutil.rmtree(job_out,ignore_errors=True)

        completed_job=move(job,C)
        processing_meta.unlink(missing_ok=True)
        result_meta=C/f"{run_id}.result.json"
        write_json(result_meta,{
            "schema_version":1,"id":run_id,"status":"completed",
            "created_at":started,"started_at":started,"completed_at":now(),
            "avatar_id":data.get("avatar_id"),"voice_id":data.get("voice_id"),
            "output_path":str(output),"output_name":output.name,
            "output_size_bytes":media["size_bytes"],
            "media":media,
            "log_path":str(log),"job_path":str(completed_job),
            "note":data.get("note","")
        })
        sync_status()
        print("COMPLETED",run_id)
        print("OUTPUT",output)

    except Exception as e:
        try:
            cfg.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            if 'job_out' in locals(): shutil.rmtree(job_out,ignore_errors=True)
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
        sync_status()
        raise

def main():
    import argparse
    parser=argparse.ArgumentParser(description="Laxman AI Avatar Studio MuseTalk worker")
    parser.add_argument("--loop",action="store_true",help="Keep watching Drive queue for new jobs")
    parser.add_argument("--poll-seconds",type=int,default=10,help="Queue polling interval")
    args=parser.parse_args()
    if not args.loop:
        process_one()
        return
    print("WORKER_LOOP_STARTED poll_seconds=",args.poll_seconds)
    while True:
        try:
            process_one()
        except Exception as e:
            print("JOB_ERROR",repr(e))
        time.sleep(max(2,args.poll_seconds))

if __name__=="__main__":
    main()
