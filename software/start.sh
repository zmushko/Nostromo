#!/bin/bash
# Nostromo Systems — startup script
export ANTHROPIC_API_KEY="your-key-here"
export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=alsa
export AUDIODEV=plughw:2
cd /home/pi/mother

mkdir -p logs

while true; do
    python3 main.py --fullscreen 2>> logs/nostromo.log
    echo "$(date): exited ($?), restarting in 3s..." >> logs/nostromo.log
    sleep 3
done
