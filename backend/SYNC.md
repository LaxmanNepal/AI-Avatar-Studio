# Status synchronization

`sync_status.py` creates a sanitized manifest at:

`Google Drive/Laxman AI Avatar Studio/sync/studio-status.json`

The manifest is intentionally safe for a future public transport layer. It contains job state and non-sensitive media metadata only. It never publishes Drive paths, local paths, logs, raw errors, credentials, source audio paths, source avatar paths, or video bytes.

## Current transport

The dashboard remains static and does **not** fetch Google Drive directly. The manifest can be imported manually now, or connected later to a public HTTPS transport after its security is configured.

## Recommended operation

Run after each worker cycle or from a scheduled Colab cell:

`python /content/AI-Avatar-Studio/backend/sync_status.py`

Do not make the Drive sync folder public unless the sanitized manifest has been reviewed.
