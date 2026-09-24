#!/usr/bin/env python3
"""Build a sanitized public status manifest from private Drive job metadata."""
from pathlib import Path
import json
from datetime import datetime, timezone

ROOT=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
SYNC=ROOT/"sync"
OUT=SYNC/"studio-status.json"
C=ROOT/"jobs/completed"; F=ROOT/"jobs/failed"; P=ROOT/"jobs/processing"

def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def public_result(data):
    if not isinstance(data,dict) or not data.get("id") or not data.get("status"):
        return None
    item={
        "id":data["id"],
        "status":data["status"],
        "avatar_id":data.get("avatar_id"),
        "voice_id":data.get("voice_id"),
        "created_at":data.get("created_at"),
        "started_at":data.get("started_at"),
    }
    if data.get("status")=="completed":
        item["completed_at"]=data.get("completed_at")
        item["output_name"]=data.get("output_name")
        item["media"]=data.get("media",{})
    elif data.get("status")=="failed":
        item["failed_at"]=data.get("failed_at")
        item["error_code"]="job_failed"
    return item

def build():
    SYNC.mkdir(parents=True,exist_ok=True)
    items=[]
    for folder in (C,F):
        for path in folder.glob("*.result.json"):
            item=public_result(load(path))
            if item: items.append(item)
    for path in P.glob("*.status.json"):
        item=public_result(load(path))
        if item:
            item["status"]="processing"
            items.append(item)
    items.sort(key=lambda x:x.get("created_at") or "",reverse=True)
    payload={
        "schema_version":1,
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "privacy":{"contains_private_paths":False,"contains_credentials":False,"contains_media":False},
        "jobs":items[:100]
    }
    OUT.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    print("SYNC_WRITTEN",OUT)
    print("JOBS",len(items))

if __name__=="__main__":
    build()
