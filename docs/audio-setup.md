# Audio Setup Guide

## Overview

Pure digital audio path — no external DAC needed:

```
RPi5 → I²S (digital) → MAX98357A (DAC + amp) → Speaker
```

## Step-by-Step Setup

### 1. Enable I²S Overlay

```bash
sudo nano /boot/firmware/config.txt
```

Add:
```
dtoverlay=hifiberry-dac
```

Reboot: `sudo reboot`

### 2. Verify Device

```bash
aplay -l
```

Look for `snd_rpi_hifiberry_dac` — should be card 0.

### 3. Test Sound

```bash
speaker-test -D plughw:0 -c 2 -t wav
```

### 4. Configure Mono Mix

```bash
sudo nano /etc/asound.conf
```

```
pcm.!default {
    type plug
    slave.pcm "mono"
}

pcm.mono {
    type route
    slave.pcm "plughw:0"
    ttable.0.0 1
    ttable.1.0 1
}
```

### 5. Fix Sound Card Ordering

```bash
sudo nano /etc/modprobe.d/alsa-base.conf
```

```
options snd_soc_rpi_simple_soundcard index=0
options vc4 index=1
```

### 6. Disable PipeWire (optional)

```bash
systemctl --user mask pipewire.socket pipewire-pulse.socket pipewire pipewire-pulse wireplumber
```

## Environment Variables (start.sh)

```bash
export SDL_AUDIODRIVER=alsa
export AUDIODEV=plughw:0
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No sound | SD pin floating | Connect SD → VIN |
| No sound | Wrong card number | Check `aplay -l`, update asound.conf |
| No sound | PipeWire holding device | `systemctl --user stop pipewire*` |
| Only left channel | GAIN pulled to GND | Use ALSA mono mix (ttable) |
| ffpyplayer silent | Missing env var | `export AUDIODEV=plughw:0` |
