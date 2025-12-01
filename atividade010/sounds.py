#!/usr/bin/env python3
# Module `sounds.py` — short description of this module.
import os
import io
import math
import random
import struct
import wave
import pygame as pg


# Internal state: whether the sound system has been initialized
_initialized = False
# Cache for synthesized/loaded sound objects by key
_sfx = {}


# Function `init()` — initialize the pygame mixer and prepare SFX in memory.
def init():
    global _initialized, _sfx
    if _initialized:
        return
    try:
        pg.mixer.init()
    except Exception:
        _initialized = True
        return

    keys = ["shot", "explosion", "ufo_spawn", "ufo_shot"]
    # Available sound keys: map these names to synthesized SFX used by the game.
    # - 'shot': short player shot sound (brief pulse + harmonics + noise)
    # - 'explosion': low-frequency damped sine to simulate an explosion
    # - 'ufo_spawn': mid-frequency brief tone for UFO entrance
    # - 'ufo_shot': mid/high tone for enemy shot

    for key in keys:
        sound_obj = None
        try:
            buf = _synthesize_wav_bytes(key)
            buf.seek(0)
            sound_obj = pg.mixer.Sound(file=buf)
        except Exception:
            sound_obj = None
        _sfx[key] = sound_obj

    _initialized = True


# Function `_play(key, volume)` — play a cached sound by key, initializing system if needed.
def _play(key: str, volume: float = 0.8):
    if not _initialized:
        init()
    snd = _sfx.get(key)
    if snd:
        try:
            snd.set_volume(volume)
            snd.play()
        except Exception:
            pass


# Function `_synthesize_wav(path, key)` — synthesize a WAV file on disk for the given key.
# This is primarily used for debugging or exporting generated sounds.
def _synthesize_wav(path: str, key: str):
    framerate = 22050
    amplitude = 16000
    # framerate: samples per second; amplitude is max sample magnitude (16-bit)
    if key == "shot":
        duration = 0.06
        freq_start = 800.0
        freq_end = 3000.0
    else:
        duration = 0.25

    freqs = {
        "explosion": 80,
        "ufo_spawn": 600,
        "ufo_shot": 1000,
    }
    base_freq = freqs.get(key, 440)
    nframes = int(duration * framerate)

    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        for i in range(nframes):
            t = i / framerate
            if key == "shot":
                # Slide frequency from freq_start to freq_end over the short duration
                f = freq_start + (freq_end - freq_start) * (t / duration)
                # Fast exponential decay envelope to create a percussive pulse
                env = math.exp(-20.0 * (t / duration))
                # Pulse-wave base (simple bipolar square-ish pulse)
                base = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
                # Add harmonic partials to enrich timbre
                h1 = 0.6 * math.sin(2 * math.pi * (2 * f) * t)
                h2 = 0.35 * math.sin(2 * math.pi * (3 * f) * t)
                # Short, rapidly-decaying noise component for 'bite'
                noise = (random.random() * 2.0 - 1.0) * math.exp(
                    -80.0 * (t / duration)
                )
                # Mix components and apply small quantization to emulate lo-fi pulse
                raw = 0.92 * base + h1 + h2 + 0.18 * noise
                qlevels = 128.0
                qval = (
                    math.floor((raw + 1.0) * 0.5 * qlevels) / qlevels * 2.0
                    - 1.0
                )
                sample = int(amplitude * env * 0.95 * qval)
            elif key == "explosion":
                # Explosion: low base frequency with a decaying amplitude
                env = max(0.0, 1.0 - t / duration)
                # Additional falloff term (1.0 - t/duration) emphasizes initial transient
                sample = int(
                    amplitude
                    * env
                    * math.sin(2 * math.pi * base_freq * t)
                    * (1.0 - t / duration)
                )
            else:
                # Default tone (ufo spawn/shot): simple sine with gentle linear decay
                env = 1.0 - 0.6 * (t / duration)
                sample = int(
                    amplitude * env * math.sin(2 * math.pi * base_freq * t)
                )

            data = struct.pack("<h", max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b"")


def _synthesize_wav_bytes(key: str) -> io.BytesIO:
    framerate = 22050
    amplitude = 16000
    if key == "shot":
        duration = 0.06
        freq_start = 1200.0
        freq_end = 3000.0
    else:
        duration = 0.25

    freqs = {
        "explosion": 80,
        "ufo_spawn": 600,
        "ufo_shot": 1000,
    }
    base_freq = freqs.get(key, 440)
    nframes = int(duration * framerate)
    buf = io.BytesIO()

    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        for i in range(nframes):
            t = i / framerate
            if key == "shot":
                # Sliding frequency and exponential decay to model a short shot
                f = freq_start + (freq_end - freq_start) * (t / duration)
                env = math.exp(-22.0 * (t / duration))
                # Use a pulse-like core plus a secondary harmonic to add character
                s = math.sin(2 * math.pi * f * t)
                pulse = 1.0 if s >= 0 else -1.0
                body = 0.85 * pulse + 0.45 * math.sin(
                    2 * math.pi * 1.8 * f * t
                )
                # Decaying noise adds texture; decays faster than tone
                noise = (random.random() * 2.0 - 1.0) * math.exp(
                    -60.0 * (t / duration)
                )
                raw = body + 0.25 * noise
                # Apply a small quantization to emulate sampled/retro sound
                val = env * raw
                levels = 256.0
                q = math.floor((val + 1.0) * 0.5 * levels) / levels * 2.0 - 1.0
                sample = int(amplitude * 0.9 * q)
            elif key == "explosion":
                # Explosion: low-frequency sinusoid with amplitude shaping
                env = max(0.0, 1.0 - t / duration)
                sample = int(
                    amplitude
                    * env
                    * math.sin(2 * math.pi * base_freq * t)
                    * (1.0 - t / duration)
                )
            else:
                # Default UFO tone: sustain-like envelope with gentle falloff
                env = 1.0 - 0.6 * (t / duration)
                sample = int(
                    amplitude * env * math.sin(2 * math.pi * base_freq * t)
                )

            data = struct.pack("<h", max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b"")
    buf.seek(0)
    return buf


def _synthesize_samples_numpy(key: str):
    # Placeholder for an alternative synthesis path that would use numpy.
    # Not available in this environment; raise an explicit error.
    raise RuntimeError("numpy-based synthesis not available")


def play_shot():
    # Play the player's shot sound effect.
    _play("shot", 0.6)


def play_explosion():
    # Play an explosion sound effect.
    _play("explosion", 0.8)


def play_ufo_spawn():
    # Play the UFO spawn sound.
    _play("ufo_spawn", 0.6)


def play_ufo_shot():
    # Play the UFO's shot sound (reuses player shot sound by design).
    _play("shot", 0.6)
