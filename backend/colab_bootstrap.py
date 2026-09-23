#!/usr/bin/env python3
"""Reproducible Google Colab bootstrap for Laxman AI Avatar Studio."""
from pathlib import Path
import os, subprocess

PYTHON="/content/musetalk-env/bin/python"
PIP="/content/musetalk-env/bin/pip"
REPO=Path("/content/MuseTalk")
DRIVE=Path("/content/drive/MyDrive/Laxman AI Avatar Studio")
MODELS=DRIVE/"models"

def run(cmd,cwd=None,env=None):
    print("$"," ".join(map(str,cmd))); subprocess.run(cmd,cwd=cwd,env=env,check=True)

def main():
    if not Path(PYTHON).exists():
        run(["apt-get","update","-qq"])
        run(["apt-get","install","-y","-qq","python3.10","python3.10-venv"])
        run(["python3.10","-m","venv","/content/musetalk-env"])
        run([PIP,"install","-U","pip","setuptools","wheel"])
    if not (REPO/"scripts/inference.py").exists():
        run(["git","clone","https://github.com/TMElyralab/MuseTalk.git",str(REPO)])
    run([PIP,"install","torch==2.0.1","torchvision==0.15.2","torchaudio==2.0.2","--index-url","https://download.pytorch.org/whl/cu118"])
    run([PIP,"install","-r","requirements.txt"],cwd=REPO)
    run([PIP,"install","-U","openmim"])
    run([PIP,"install","mmengine"])
    run([PIP,"install","mmcv==2.0.1","-f","https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html"])
    run([PIP,"install","chumpy==0.70","--no-build-isolation"])
    run([PIP,"install","mmdet==3.1.0","mmpose==1.1.0"])
    target=REPO/"models"
    if target.is_symlink(): target.unlink()
    elif target.exists():
        import shutil; shutil.rmtree(target)
    target.symlink_to(MODELS,target_is_directory=True)
    env=os.environ.copy(); env["PYTHONPATH"]=str(REPO); env["MPLBACKEND"]="Agg"
    run([PYTHON,"-c","import torch,mmcv,mmengine,mmdet,mmpose; print('Torch',torch.__version__); print('CUDA',torch.cuda.is_available()); print('GPU',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'); print('MMCV',mmcv.__version__)"],env=env)
    print("BOOTSTRAP COMPLETE")

if __name__=="__main__": main()
