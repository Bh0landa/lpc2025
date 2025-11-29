import os
import io
import math
import random
import struct
import wave
import pygame as pg

# Módulo simples de efeitos sonoros
# Gera sons em memoria para evitar dependencias de ficheiros

_initialized = False
_sfx = {}


def init():
    # Inicializa o mixer do pygame e prepara os efeitos em memoria
    global _initialized, _sfx
    if _initialized:
        return
    try:
        pg.mixer.init()
    except Exception:
        # Se o mixer falhar, marcamos como inicializado para evitar tentativas repetidas
        _initialized = True
        return

    # Chaves dos efeitos que geramos em memoria
    keys = ["shot", "explosion", "ufo_spawn", "ufo_shot"]

    # Gera buffers WAV em memoria e cria objetos Sound
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
    # Toca um efeito se disponível, inicializando o sistema se preciso
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
    # Gera um ficheiro WAV mono 16 bits em disco para debug ou testes
    # Ajustes especiais para efeitos curtos como 'shot' (pitch sweep + decay)
    framerate = 22050
    amplitude = 16000
    if key == "shot":
        # Classic Robotron-style: short, bright pulse with quick rising pitch
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
                # Classic Robotron: strong square-like pulse + harmonics + quick pitch sweep
                f = freq_start + (freq_end - freq_start) * (t / duration)
                # agressive envelope for short, punchy blip
                env = math.exp(-20.0 * (t / duration))
                # square pulse (harsh) to get many harmonics
                base = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
                # add a couple harmonics for body
                h1 = 0.6 * math.sin(2 * math.pi * (2 * f) * t)
                h2 = 0.35 * math.sin(2 * math.pi * (3 * f) * t)
                # tiny noise transient at attack
                noise = (random.random() * 2.0 - 1.0) * math.exp(-80.0 * (t / duration))
                raw = 0.92 * base + h1 + h2 + 0.18 * noise
                # light bit crushing (8-bit feel)
                qlevels = 128.0
                qval = math.floor((raw + 1.0) * 0.5 * qlevels) / qlevels * 2.0 - 1.0
                sample = int(amplitude * env * 0.95 * qval)
            elif key == "explosion":
                env = max(0.0, 1.0 - t / duration)
                sample = int(
                    amplitude
                    * env
                    * math.sin(2 * math.pi * base_freq * t)
                    * (1.0 - t / duration)
                )
            else:
                env = 1.0 - 0.6 * (t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * base_freq * t))

            data = struct.pack("<h", max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b"")


def _synthesize_wav_bytes(key: str) -> io.BytesIO:
    # Gera um WAV na memoria e devolve um BytesIO pronto para leitura
    framerate = 22050
    amplitude = 16000
    if key == "shot":
        # Arcade-lofi Robotron-like blip: short pulse with fast rising pitch,
        # added noise transient and light bit-crush for 'chip' character
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
                # fast pitch sweep
                f = freq_start + (freq_end - freq_start) * (t / duration)
                # sharp exponential envelope for a punchy blip
                env = math.exp(-22.0 * (t / duration))
                # square-ish pulse (harsh) plus a sine harmonic for body
                s = math.sin(2 * math.pi * f * t)
                pulse = 1.0 if s >= 0 else -1.0
                body = 0.85 * pulse + 0.45 * math.sin(2 * math.pi * 1.8 * f * t)
                # short noise burst at the attack to emulate harsh arcade drivers
                noise = (random.random() * 2.0 - 1.0) * math.exp(-60.0 * (t / duration))
                raw = body + 0.25 * noise
                # apply envelope
                val = env * raw
                # bit-crush / quantize to 8-bit-like steps to make it arcade-y
                levels = 256.0
                q = math.floor((val + 1.0) * 0.5 * levels) / levels * 2.0 - 1.0
                # final gentle scaling
                sample = int(amplitude * 0.9 * q)
            elif key == "explosion":
                env = max(0.0, 1.0 - t / duration)
                sample = int(
                    amplitude
                    * env
                    * math.sin(2 * math.pi * base_freq * t)
                    * (1.0 - t / duration)
                )
            else:
                env = 1.0 - 0.6 * (t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * base_freq * t))

            data = struct.pack("<h", max(-32767, min(32767, sample)))
            wf.writeframesraw(data)
        wf.writeframes(b"")
    buf.seek(0)
    return buf


def _synthesize_samples_numpy(key: str):
    # Assinatura mantida para compatibilidade, numpy nao e utilizado
    raise RuntimeError("numpy-based synthesis not available")


def play_shot():
    # Funcoes simples para tocar efeitos especificos
    _play("shot", 0.6)


def play_explosion():
    _play("explosion", 0.8)


def play_ufo_spawn():
    _play("ufo_spawn", 0.6)


def play_ufo_shot():
    # Use the same shot sound as the player so both sound identical
    _play("shot", 0.6)
