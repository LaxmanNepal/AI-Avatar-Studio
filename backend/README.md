# Laxman AI Avatar Studio — Colab Backend

## What is complete

- MuseTalk v1.5 worker
- Private Google Drive media/model storage
- Reproducible Colab environment bootstrap
- One-shot generation mode
- Continuous queue mode
- Per-job output isolation
- MP4/audio/video validation
- Heartbeat + stale-job recovery
- Sanitized Drive status manifest
- Self-healing preflight launcher
- First real end-to-end generation cell in the notebook
- Final daily startup and validation cells

## First-time / fresh Colab runtime

Open `notebooks/MuseTalk-Laxman.ipynb` in Google Colab and run cells from top to bottom.

The notebook will:
1. Mount Google Drive.
2. Restore the GitHub codebase.
3. Rebuild the MuseTalk environment.
4. Verify GPU/CUDA/MMLab.
5. Link persistent models from Drive.
6. Verify private assets.
7. Create a real test job using the existing test avatar and original voice.
8. Run the job once through `start_worker.py --once`.
9. Verify the generated MP4 and result metadata.
10. Provide continuous production mode.

## Daily production

After setup, use the final daily startup cell. Set `BOOTSTRAP=True` only when the Python environment is missing or needs rebuilding.

New job JSON files belong in:

`Google Drive/Laxman AI Avatar Studio/jobs/queued/`

Completed MP4 files are written to:

`Google Drive/Laxman AI Avatar Studio/outputs/`

Completed/failed metadata is stored under the corresponding job folders.

## Important boundary

GitHub does not directly access the private Drive. The browser dashboard creates a private job JSON for you to place into Drive. It does not upload your media or expose Drive credentials.

A code/preflight pass is not proof that a GPU generation succeeded. The notebook's Phase 24 must actually finish and create an MP4 before the generation pipeline is considered runtime-verified.

Never commit private face videos, voice recordings, generated videos, model weights, tokens, or credentials to GitHub.
