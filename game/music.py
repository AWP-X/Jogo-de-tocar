"""Trilha sonora composta por codigo - sem depender de nenhum arquivo de audio
externo, entao nao ha risco nenhum de direito autoral (e o mesmo principio dos
efeitos sonoros em game/audio.py, so que aqui vira uma musica de verdade).

O Mundo Jazzy toca um loop de jazz original: uma virada de acordes classica
(ii-V-I-vi, "Dm7 - G7 - Cmaj7 - Am7"), baixo caminhante, "comping" de acordes
e bateria com swing (par de colcheias longa-curta em vez de retas). Existem 3
variantes de andamento (calmo/medio/intenso) - fases mais avancadas tocam a
musica mais rapido, dando uma sensacao real de progressao dentro do mundo.
"""
import array
import math
import random

import pygame

from . import config
from . import state

SAMPLE_RATE = 22050

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


def _compose_jazz_loop(bpm):
    beat = 60.0 / bpm
    chord_dur = beat * 2   # cada acorde da progressao dura 2 batidas

    total_samples = int(SAMPLE_RATE * chord_dur * len(PROGRESSION))
    master = [0.0] * total_samples

    swing_long = beat * (2 / 3)   # colcheia "longa" do swing

    for i, chord in enumerate(PROGRESSION):
        start = int(i * chord_dur * SAMPLE_RATE)

        # Baixo caminhante: fundamental na batida 1, quinta na batida 2.
        _mix(master, _tone(_note_freq(chord["root"]), beat * 0.9, amp=0.55), start)
        _mix(master, _tone(_note_freq(chord["fifth"]), beat * 0.9, amp=0.45),
             start + int(beat * SAMPLE_RATE))

        # "Comping": as notas de cima do acorde sustentadas por baixo do acorde inteiro.
        for tone in chord["pad"]:
            _mix(master, _tone(_note_freq(tone), chord_dur * 0.95, amp=0.10, attack=0.05), start)

        # Bumbo na batida 1.
        _mix(master, _tone(60, 0.15, amp=0.5, attack=0.002), start)

        # Chimbal com swing: 2 toques por batida (longo entao curto), 4 por acorde.
        for beat_offset in (0.0, beat):
            _mix(master, _noise_burst(0.05, amp=0.14), start + int(beat_offset * SAMPLE_RATE))
            _mix(master, _noise_burst(0.04, amp=0.10),
                 start + int((beat_offset + swing_long) * SAMPLE_RATE))

    return master, beat, chord_dur


def _to_sound(samples):
    peak = max(0.0001, max(abs(s) for s in samples))
    scale = min(1.0, 0.9 / peak)
    buf = array.array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s * scale)) * 32000)
        buf.append(v)   # canal esquerdo
        buf.append(v)   # canal direito
    return pygame.mixer.Sound(buffer=buf.tobytes())


# Tres andamentos do mesmo loop - as fases mais avancadas tocam mais rapido,
# dando uma sensacao real de progressao dentro do Mundo Jazzy (o BPM sobe,
# nao so a velocidade dos inimigos).
TEMPO_TIERS = ("calmo", "medio", "intenso")
_TEMPO_BPM = {"calmo": 104, "medio": 122, "intenso": 142}

try:
    _TRACKS = {}
    for _tier in TEMPO_TIERS:
        _samples, _beat, _chord_dur = _compose_jazz_loop(_TEMPO_BPM[_tier])
        _TRACKS[_tier] = {"sound": _to_sound(_samples), "beat": _beat, "chord_dur": _chord_dur}
except Exception:
    # Sem audio disponivel no sistema - o jogo segue em silencio.
    _TRACKS = {}

# Compatibilidade: JAZZ_LOOP e o andamento medio (usado se algo pedir a
# trilha do Jazzy diretamente, sem escolher andamento).
JAZZ_LOOP = _TRACKS.get("medio", {}).get("sound")
WORLD_TRACKS = {"jazzy": JAZZ_LOOP}

# Valores da trilha ATUALMENTE tocando - comecam no andamento medio antes de
# qualquer musica ser iniciada. game/screens.py le esses dois diretamente
# (music.BEAT / music.CHORD_DUR) pra sincronizar o palco animado do Jazzy.
BEAT = _TRACKS.get("medio", {}).get("beat", 60.0 / 122)
CHORD_DUR = _TRACKS.get("medio", {}).get("chord_dur", BEAT * 2)

_current_channel = None
_current_track = None
_start_time = None   # quando a musica atual comecou (pygame.time.get_ticks()/1000) - e
                      # a referencia real do "tempo 0" da batida, nao o uptime do jogo.


def _tier_for_level(level_num):
    """Fases iniciais tocam calmo, do meio tocam medio, finais tocam intenso."""
    if level_num is None:
        return "medio"
    if level_num <= 3:
        return "calmo"
    if level_num <= 7:
        return "medio"
    return "intenso"


def _music_volume():
    return 0.0 if state.settings["muted"] else state.settings["volume"] * 0.5


def play_world_music(world_id, level_num=None):
    """Toca em loop a musica do mundo (para a anterior, se houver). O andamento
    depende da fase: fases mais avancadas tocam mais rapido."""
    global _current_channel, _current_track, _start_time, BEAT, CHORD_DUR

    stop_music()
    if world_id != "jazzy" or not _TRACKS:
        return

    tier = _tier_for_level(level_num)
    track_info = _TRACKS[tier]
    track_info["sound"].set_volume(_music_volume())
    _current_channel = track_info["sound"].play(loops=-1)
    _current_track = track_info["sound"]
    BEAT = track_info["beat"]
    CHORD_DUR = track_info["chord_dur"]
    _start_time = pygame.time.get_ticks() / 1000.0


def stop_music(fade_ms=200):
    global _current_channel, _current_track, _start_time
    if _current_channel is not None:
        _current_channel.fadeout(fade_ms)
    _current_channel = None
    _current_track = None
    _start_time = None


def update_music_volume():
    """Chamar sempre que volume/mudo mudar, pra musica acompanhar na hora."""
    if _current_track is not None:
        _current_track.set_volume(_music_volume())


# ===================== RITMO (golpe sincronizado com a musica) =====================
def _beat_distance():
    """0 (golpe em cima da batida) .. 1 (o mais longe possivel, no meio de
    duas batidas). Contado a partir do instante em que a musica ATUAL comecou
    a tocar (_start_time) - nao do relogio interno do jogo, senao a "batida"
    calculada nunca bateria com o que realmente se ouve."""
    t = (pygame.time.get_ticks() / 1000.0) - _start_time
    phase = t % BEAT
    return min(phase, BEAT - phase) / (BEAT / 2)


def beat_strength():
    """0..1: quao perto estamos da proxima/ultima batida agora (1 = em cima
    dela). Usado so pra dar um pulso visual - devolve None sem musica tocando."""
    if _current_channel is None or _start_time is None:
        return None
    return 1.0 - _beat_distance()


def judge_timing():
    """Compara o instante do golpe com a batida da musica.

    Devolve None se nao ha musica tocando (o placar continua igual: +1 por
    inimigo, como sempre) - ou (nome_do_grau, multiplicador, cor) quando ha
    uma trilha ativa pra sincronizar o golpe.
    """
    if _current_channel is None or _start_time is None:
        return None
    dist = _beat_distance()
    for name, threshold, mult, color in config.RHYTHM_TIERS:
        if dist <= threshold:
            return name, mult, color
    name, _, mult, color = config.RHYTHM_TIERS[-1]
    return name, mult, color
