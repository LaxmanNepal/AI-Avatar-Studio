#!/usr/bin/env python3
"""Self-healing Colab launcher for Laxman AI Avatar Studio."""
from pathlib import Path
import argparse, os, subprocess, sys

ROOT=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
REPO=Path("/content/AI-Avatar-Studio")
PYTHON="/content/musetalk-env/bin/python"

def run(cmd, check=True):
    print("$"," ".join(map(str,cmd)),flush=True)
    return subprocess.run(cmd,check=check)

def preflight():
    required=[
        ROOT/"models/musetalkV15/unet.pth",
        ROOT/"models/musetalkV15/musetalk.json",
        ROOT/"models/sd-vae/config.json",
        ROOT/"models/sd-vae/diffusion_pytorch_model.bin",
        ROOT/"models/whisper/config.json",
        ROOT/"models/whisper/pytorch_model.bin",
        ROOT/"temp/laxman_avatar_test.mp4",
        ROOT/"temp/laxman_voice_musetalk.wav",
    ]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("PREFLIGHT_FAILED missing: "+", ".join(missing))
    if not Path(PYTHON).exists():
        raise SystemExit("PREFLIGHT_FAILED Python environment is missing. Run colab_bootstrap.py first.")
    env=os.environ.copy(); env["PYTHONPATH"]=str(Path("/content/MuseTalk"))
    r=run([PYTHON,"-c","import torch,mmcv,mmengine,mmdet,mmpose; assert torch.cuda.is_available(); print('GPU:',torch.cuda.get_device_name(0)); print('Torch:',torch.__version__); print('MMCV:',mmcv.__version__)"],check=False)
    if r.returncode:
        raise SystemExit("PREFLIGHT_FAILED Python/CUDA/MMLab verification failed.")
    r=run([PYTHON,"/content/MuseTalk/scripts/inference.py","--help"],check=False)
    if r.returncode:
        raise SystemExit("PREFLIGHT_FAILED MuseTalk inference CLI verification failed.")
    print("PREFLIGHT_READY",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bootstrap",action="store_true",help="Rebuild missing Colab environment before starting")
    ap.add_argument("--poll-seconds",type=int,default=10)
    ap.add_argument("--once",action="store_true",help="Process one queued job and exit")
    args=ap.parse_args()
    if not REPO.exists():
        raise SystemExit("Repository missing. Run the notebook restore cell first.")
    if args.bootstrap:
        run(["python3.10",str(REPO/"backend/colab_bootstrap.py")])
    preflight()
    worker=[ "python",str(REPO/"backend/run_worker.py") ]
    if args.once:
        run(worker)
    else:
        run(worker+["--loop","--poll-seconds",str(max(2,args.poll_seconds))])

if __name__=="__main__":
    main()
