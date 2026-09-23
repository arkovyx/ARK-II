#!/bin/bash
cd ~/dev/ark-ii
source .venv/bin/activate
python src/voice_bar.py >> /tmp/ark_voice.log 2>&1
