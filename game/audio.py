"""Efeitos sonoros do jogo - gerados na hora (onda quadrada), sem depender de
arquivos de audio."""
import array

import pygame

from . import state


def _make_beep(freq, ms):
    """Gera um som simples (onda quadrada) sem precisar de arquivo."""
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


try:
    hit_sound = _make_beep(660, 60)
    hurt_sound = _make_beep(180, 150)
    hover_sound = _make_beep(880, 20)
    click_sound = _make_beep(520, 45)
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
