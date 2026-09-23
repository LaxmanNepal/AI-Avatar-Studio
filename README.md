# Laxman AI Avatar Studio

Private personal AI video workspace.

## Architecture

- **GitHub:** permanent dashboard, source code, configuration and Colab notebooks.
- **Google Drive:** private avatars, original voice, model weights, temporary files and generated MP4s.
- **Google Colab:** temporary GPU worker for MuseTalk processing.

## Privacy boundary

Do not commit personal avatar videos, voice recordings, generated videos, access tokens, API keys or model weights to this repository.

## Current avatar slots

1. Technical presenter — front angle
2. Studio desk — alternate angle
3. Technology video — alternate angle

## Backend

The dashboard is intentionally independent of the GPU runtime. The Colab worker can be restarted without losing the dashboard or private media library.

## Status

Phase 1 dashboard foundation is installed.