# Colab backend

GitHub stores code/config only. Google Drive stores private avatars, the original voice, model weights, jobs, logs and generated videos.

Drive queue:
- jobs/queued
- jobs/processing
- jobs/completed
- jobs/failed

Open notebooks/MuseTalk-Laxman.ipynb in Colab. Bootstrap is safe to rerun after a runtime reset. Then place a version-1 JSON job in jobs/queued and run the worker cell. The worker processes one job, writes output to outputs/, and moves the job to completed or failed.

Never commit face videos, voice recordings, generated videos, model weights, tokens or credentials to GitHub.
