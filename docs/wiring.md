# Wiring Guide

## I²S Audio (RPi5 → MAX98357A)

Solder to GPIO header **underside** (WaveShare uses top SPI pins, no conflict).

```
RPi5 GPIO              MAX98357A
─────────              ─────────
Pin 4  (5V)     ───→   VIN
Pin 6  (GND)    ───→   GND
Pin 12 (GPIO18) ───→   BCLK    ⚠️ Internal row, 6th from top!
Pin 35 (GPIO19) ───→   LRC
Pin 40 (GPIO21) ───→   DIN
```

### Pin Configuration

- **GAIN** → Leave floating. Mono mode: (L+R)/2 at 9dB gain.
- **SD** (Shutdown) → Connect to **VIN**. Enables the amplifier permanently.

### Common Mistakes

- Pin 12 is in the **internal** row — easy to miss by one pin
- Verify BCLK with oscilloscope: ~1.5MHz square wave during playback
- If no sound: check SD pin is connected to VIN
- If only left channel: GAIN may be pulled to GND on PCB despite labeling. Use ALSA mono mix.

## ALSA Configuration

See [audio-setup.md](audio-setup.md) for complete audio configuration guide.
