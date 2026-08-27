"""Efeitos sonoros do jogo - gerados na hora, sem depender de arquivos de audio."""
import array
import math
import random

import pygame

from . import state


def _make_beep(freq, ms):
    """Onda quadrada classica - usada nos sons de combate (arcade "de proposito")."""
    sample_rate = 22050
    n = int(sample_rate * ms / 1000)
    amp = 12000
    samples_per_cycle = sample_rate / freq
    buf = array.array("h")
    for i in range(n):
        v = amp if (i % samples_per_cycle) < (samples_per_cycle / 2) else -amp
        buf.append(v)   # canal esquerdo
        buf.append(v)   # canal direito
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _make_switch_tock(freq, ms, amp=9000, noise_amt=0.10, decay=55):
    """Som curto e abafado, tipo tecla mecanica com switch silencioso: um
    'toque' grave que morre rapido (decaimento exponencial, nao um tom
    sustentado) com uma pitada de ruido pra dar textura de mecanismo - usado
    nos sons de UI (hover/clique) em vez do bipe de onda quadrada."""
    sample_rate = 22050
    n = int(sample_rate * ms / 1000)
    buf = array.array("h")
    for i in range(n):
        t = i / sample_rate
        env = math.exp(-t * decay)
        tone = math.sin(2 * math.pi * freq * t)
        noise = random.uniform(-1, 1) * noise_amt
        v = int(amp * env * (tone + noise))
        v = max(-32000, min(32000, v))
        buf.append(v)
        buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())


try:
    hit_sound = _make_beep(660, 60)
    hurt_sound = _make_beep(180, 150)
    hover_sound = _make_switch_tock(210, 30, amp=5500, noise_amt=0.08, decay=75)
    click_sound = _make_switch_tock(150, 42, amp=8000, noise_amt=0.12, decay=48)
except Exception:
    # Se nao houver audio disponivel, o jogo segue em silencio.
    hit_sound = None
    hurt_sound = None
    hover_sound = None
    click_sound = None


def play(sound):
    if sound is not None and not state.settings["muted"]:
        sound.set_volume(state.settings["volume"])
        sound.play()
