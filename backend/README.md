# Colab backend contract

The GitHub dashboard is a static control panel. GPU inference runs in Google Colab.

## Persistent data

Google Drive:
- Laxman AI Avatar Studio/avatars
- Laxman AI Avatar Studio/voices
- Laxman AI Avatar Studio/models
- Laxman AI Avatar Studio/outputs
- Laxman AI Avatar Studio/temp

## Job contract

A future backend worker should accept:
- avatar_id
- voice_id
- script or audio path
- output filename
- MuseTalk version

It should return:
- queued / processing / completed / failed
- output Drive path
- error message when failed

Never put private media, credentials, model weights or Drive tokens into GitHub.