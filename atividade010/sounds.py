import os
import io
import math
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
        duration = 0.12
        freq_start = 1400.0
        freq_end = 900.0
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
                # quick decaying blip with slight downward pitch sweep
                f = freq_start + (freq_end - freq_start) * (t / duration)
                env = math.exp(-12.0 * (t / duration))
                sample = int(amplitude * env * math.sin(2 * math.pi * f * t))
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
        duration = 0.12
        freq_start = 1400.0
        freq_end = 900.0
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
                f = freq_start + (freq_end - freq_start) * (t / duration)
                env = math.exp(-12.0 * (t / duration))
                sample = int(amplitude * env * math.sin(2 * math.pi * f * t))
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
    _play("ufo_shot", 0.6)
