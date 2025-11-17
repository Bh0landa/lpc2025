import os
import io
import math
import struct
import wave
import pygame as pg

# Simple sound effects module. Generates sounds in memory

_initialized = False
_sfx = {}


def init():
    global _initialized, _sfx
    if _initialized:
        return
    try:
        pg.mixer.init()
    except Exception:
        # If the mixer fails to initialize for any reason, continue without sound
        _initialized = True
        return
    # Try to generate sounds in-memory (no external file dependency)
    keys = ["shot", "explosion", "ufo_spawn", "ufo_shot"]
    # Generate WAVs in memory (BytesIO) for all effects — no external file dependency
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


def _synthesize_wav(path: str, key: str):
    # Generate a simple tone per key and save as a mono 16-bit WAV
    duration = 0.25
    framerate = 22050
    amplitude = 16000
    freqs = {
        "shot": 1500,
        "explosion": 80,
        "ufo_spawn": 600,
        "ufo_shot": 1000,
    }
    freq = freqs.get(key, 440)
    nframes = int(duration * framerate)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        for i in range(nframes):
            t = i / framerate
            # simple envelope for 'explosion': faster decay
            if key == "explosion":
                env = max(0.0, 1.0 - t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * freq * t) * (1.0 - t / duration))
            else:
                env = 1.0 - 0.6 * (t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * freq * t))
            data = struct.pack('<h', max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b'')


def _synthesize_wav_bytes(key: str) -> io.BytesIO:
    #Generate a WAV in memory (BytesIO) and return the buffer ready for reading.
    duration = 0.25
    framerate = 22050
    amplitude = 16000
    freqs = {
        "shot": 1500,
        "explosion": 80,
        "ufo_spawn": 600,
        "ufo_shot": 1000,
    }
    freq = freqs.get(key, 440)
    nframes = int(duration * framerate)
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        for i in range(nframes):
            t = i / framerate
            if key == "explosion":
                env = max(0.0, 1.0 - t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * freq * t) * (1.0 - t / duration))
            else:
                env = 1.0 - 0.6 * (t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * freq * t))
            data = struct.pack('<h', max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b'')
    buf.seek(0)
    return buf


def _synthesize_samples_numpy(key: str):
    #Return an int16 mono ndarray with samples of the generated sound.
    # function removed: keep signature for compatibility, but numpy is not used
    raise RuntimeError("numpy-based synthesis not available")


def play_shot():
    _play("shot", 0.6)


def play_explosion():
    _play("explosion", 0.8)


def play_ufo_spawn():
    _play("ufo_spawn", 0.6)


def play_ufo_shot():
    _play("ufo_shot", 0.6)
