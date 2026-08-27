"""Trilha sonora composta por codigo - sem depender de nenhum arquivo de audio
externo, entao nao ha risco nenhum de direito autoral (e o mesmo principio dos
efeitos sonoros em game/audio.py, so que aqui vira uma musica de verdade).

O Mundo Jazzy toca um loop de jazz original: uma virada de acordes classica
(ii-V-I-vi, "Dm7 - G7 - Cmaj7 - Am7"), baixo caminhante, "comping" de acordes
e bateria com swing (par de colcheias longa-curta em vez de retas).
"""
import array
import math
import random

import pygame

from . import config
from . import state

SAMPLE_RATE = 22050
BPM = 120
BEAT = 60.0 / BPM          # duracao de uma batida, em segundos
CHORD_DUR = BEAT * 2       # cada acorde da progressao dura 2 batidas

# Progressao ii-V-I-vi em Do maior (numeros MIDI; A4=69=440Hz).
# "root"/"fifth": as duas notas do baixo caminhante (batida 1 e 2).
# "pad": as notas de cima que formam o acorde (3a, 5a e 7a).
PROGRESSION = [
    {"root": 50, "fifth": 57, "pad": [53, 57, 60]},   # Dm7
    {"root": 43, "fifth": 50, "pad": [59, 62, 65]},   # G7
    {"root": 48, "fifth": 55, "pad": [64, 67, 71]},   # Cmaj7
    {"root": 45, "fifth": 52, "pad": [60, 64, 67]},   # Am7
]


def _note_freq(midi_number):
    return 440.0 * (2 ** ((midi_number - 69) / 12))


def _tone(freq, duration, amp=1.0, attack=0.01):
    """Nota com ataque rapido e decaimento linear ate o fim - da um efeito de
    "dedilhado" (baixo/piano), em vez de uma onda que liga e desliga seca."""
    n = int(SAMPLE_RATE * duration)
    buf = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < attack:
            env = t / attack
        else:
            env = max(0.0, 1 - (t - attack) / max(1e-6, duration - attack))
        buf[i] = amp * env * math.sin(2 * math.pi * freq * t)
    return buf


def _noise_burst(duration, amp=1.0):
    """Estouro curto de ruido branco, usado como chimbal (hi-hat)."""
    n = int(SAMPLE_RATE * duration)
    buf = [0.0] * n
    for i in range(n):
        env = max(0.0, 1 - (i / n))
        buf[i] = amp * env * random.uniform(-1, 1)
    return buf


def _mix(master, layer, offset_samples):
    for i, v in enumerate(layer):
        idx = offset_samples + i
        if idx < len(master):
            master[idx] += v


def _compose_jazz_loop():
    total_samples = int(SAMPLE_RATE * CHORD_DUR * len(PROGRESSION))
    master = [0.0] * total_samples

    swing_long = BEAT * (2 / 3)   # colcheia "longa" do swing
    swing_short = BEAT * (1 / 3)  # colcheia "curta" do swing

    for i, chord in enumerate(PROGRESSION):
        start = int(i * CHORD_DUR * SAMPLE_RATE)

        # Baixo caminhante: fundamental na batida 1, quinta na batida 2.
        _mix(master, _tone(_note_freq(chord["root"]), BEAT * 0.9, amp=0.55), start)
        _mix(master, _tone(_note_freq(chord["fifth"]), BEAT * 0.9, amp=0.45),
             start + int(BEAT * SAMPLE_RATE))

        # "Comping": as notas de cima do acorde sustentadas por baixo do acorde inteiro.
        for tone in chord["pad"]:
            _mix(master, _tone(_note_freq(tone), CHORD_DUR * 0.95, amp=0.10, attack=0.05), start)

        # Bumbo na batida 1.
        _mix(master, _tone(60, 0.15, amp=0.5, attack=0.002), start)

        # Chimbal com swing: 2 toques por batida (longo entao curto), 4 por acorde.
        for beat_offset in (0.0, BEAT):
            _mix(master, _noise_burst(0.05, amp=0.14), start + int(beat_offset * SAMPLE_RATE))
            _mix(master, _noise_burst(0.04, amp=0.10),
                 start + int((beat_offset + swing_long) * SAMPLE_RATE))

    return master


def _to_sound(samples):
    peak = max(0.0001, max(abs(s) for s in samples))
    scale = min(1.0, 0.9 / peak)
    buf = array.array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s * scale)) * 32000)
        buf.append(v)   # canal esquerdo
        buf.append(v)   # canal direito
    return pygame.mixer.Sound(buffer=buf.tobytes())


try:
    JAZZ_LOOP = _to_sound(_compose_jazz_loop())
except Exception:
    # Sem audio disponivel no sistema - o jogo segue em silencio.
    JAZZ_LOOP = None

WORLD_TRACKS = {"jazzy": JAZZ_LOOP}

_current_channel = None
_current_track = None


def _music_volume():
    return 0.0 if state.settings["muted"] else state.settings["volume"] * 0.5


def play_world_music(world_id):
    """Toca em loop a musica do mundo (para a anterior, se houver)."""
    global _current_channel, _current_track
    stop_music()
    track = WORLD_TRACKS.get(world_id)
    if track is None:
        return
    track.set_volume(_music_volume())
    _current_channel = track.play(loops=-1)
    _current_track = track


def stop_music(fade_ms=200):
    global _current_channel, _current_track
    if _current_channel is not None:
        _current_channel.fadeout(fade_ms)
    _current_channel = None
    _current_track = None


def update_music_volume():
    """Chamar sempre que volume/mudo mudar, pra musica acompanhar na hora."""
    if _current_track is not None:
        _current_track.set_volume(_music_volume())


# ===================== RITMO (golpe sincronizado com a musica) =====================
def _beat_distance():
    """0 (golpe em cima da batida) .. 1 (o mais longe possivel, no meio de
    duas batidas). So faz sentido enquanto ha musica tocando."""
    t = pygame.time.get_ticks() / 1000.0
    phase = t % BEAT
    return min(phase, BEAT - phase) / (BEAT / 2)


def beat_strength():
    """0..1: quao perto estamos da proxima/ultima batida agora (1 = em cima
    dela). Usado so pra dar um pulso visual - devolve None sem musica tocando."""
    if _current_channel is None:
        return None
    return 1.0 - _beat_distance()


def judge_timing():
    """Compara o instante do golpe com a batida da musica.

    Devolve None se nao ha musica tocando (o placar continua igual: +1 por
    inimigo, como sempre) - ou (nome_do_grau, multiplicador, cor) quando ha
    uma trilha ativa pra sincronizar o golpe.
    """
    if _current_channel is None:
        return None
    dist = _beat_distance()
    for name, threshold, mult, color in config.RHYTHM_TIERS:
        if dist <= threshold:
            return name, mult, color
    name, _, mult, color = config.RHYTHM_TIERS[-1]
    return name, mult, color
