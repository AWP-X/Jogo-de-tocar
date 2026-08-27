"""Trilha sonora composta por codigo - sem depender de nenhum arquivo de audio
externo, entao nao ha risco nenhum de direito autoral (o mesmo principio dos
efeitos sonoros em game/audio.py, so que aqui vira uma musica de verdade).

Cada FASE do Mundo Jazzy corresponde a um ano marcante da historia do jazz (ver
config.WORLDS["jazzy"]["levels"]) e toca um estilo ORIGINAL proprio - nunca a
gravacao real de ninguem, so uma composicao inspirada na pegada daquela epoca
(andamento, escolha de acordes, forma como o baixo/o "comping"/a bateria se
movem). Isso e feito com um pequeno "motor" generico (_compose) parametrizado
por um "perfil de estilo" (STYLE_PROFILES) em vez de 10 funcoes separadas -
cada perfil descreve andamento, compasso, se ha swing, e que tipo de baixo/
acompanhamento/bateria usar.
"""
import array
import math
import random

import pygame

from . import config
from . import state

SAMPLE_RATE = 22050


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
    """Estouro curto de ruido branco, usado como chimbal/caixa (percussao)."""
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


def _to_sound(samples):
    peak = max(0.0001, max(abs(s) for s in samples))
    scale = min(1.0, 0.9 / peak)
    buf = array.array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s * scale)) * 32000)
        buf.append(v)   # canal esquerdo
        buf.append(v)   # canal direito
    return pygame.mixer.Sound(buffer=buf.tobytes())


# ===================== HARMONIA (construcao de acordes por grau) =====================
# Todas as progressoes sao escritas como deslocamento em semitons a partir de
# um "tom" de referencia (TONIC) - assim da pra montar qualquer acorde diatonico
# (I, ii, iii, IV, V, vi) so dizendo quantos semitons ele fica acima do tom.
TONIC = 48   # C3 - so uma referencia de registro, nao precisa ser "Do" de verdade


def _chord(semitones_from_tonic, quality="min7"):
    root = TONIC + semitones_from_tonic
    thirds  = {"maj7": 4, "min7": 3, "dom7": 4, "min7b5": 3}
    fifths  = {"maj7": 7, "min7": 7, "dom7": 7, "min7b5": 6}
    sevenths = {"maj7": 11, "min7": 10, "dom7": 10, "min7b5": 10}
    third = root + thirds.get(quality, 3)
    fifth = root + fifths.get(quality, 7)
    seventh = root + sevenths.get(quality, 10)
    return {"root": root, "fifth": fifth, "pad": [third, fifth, seventh]}


def _deg(semitones, quality):
    return _chord(semitones, quality)


# ===================== PERFIS DE ESTILO (um por fase/ano) =====================
# progression: lista de (acorde, duracao_em_batidas). meter: so informativo (o
# "5" do 1959 e o que da a sensacao de compasso incomum, mesmo a batida em si
# sendo sempre um pulso regular de quarter-note - ver _apply_bass "ostinato5").
STYLE_PROFILES = {
    "bebop45": {   # 1945 - Nascimento do Bebop: rapido, harmonia em cascata (I-vi-ii-V)
        "bpm": 200, "swing": True,
        "bass": "walking", "comp": "stabs", "drum": "swing_fast",
        "progression": [(_deg(0, "maj7"), 2), (_deg(9, "min7"), 2),
                         (_deg(2, "min7"), 2), (_deg(7, "dom7"), 2)],
    },
    "bebop53": {   # 1953 - Massey Hall: bebop ainda mais afiado (ii-V-I-VI7)
        "bpm": 212, "swing": True,
        "bass": "walking", "comp": "stabs", "drum": "swing_fast",
        "progression": [(_deg(2, "min7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "dom7"), 2)],
    },
    "liveswing55": {   # 1955 - Miles em Newport / Concert by the Sea: swing relaxado, ao vivo
        "bpm": 168, "swing": True,
        "bass": "walking", "comp": "block", "drum": "swing_brush",
        "progression": [(_deg(0, "maj7"), 2), (_deg(5, "maj7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "min7"), 2),
                         (_deg(2, "min7"), 2), (_deg(7, "dom7"), 2)],
    },
    "calypsohard56": {   # 1956 - Saxophone Colossus: hard bop com lilt calypso, sem swing
        "bpm": 152, "swing": False,
        "bass": "calypso", "comp": "stabs", "drum": "calypso",
        "progression": [(_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(5, "dom7"), 2), (_deg(0, "dom7"), 2)],
    },
    "bluesyhard57": {   # 1957 - Blue Train: hard bop enraizado no blues (12 compassos)
        "bpm": 138, "swing": True,
        "bass": "walking", "comp": "stabs", "drum": "swing",
        "progression": [(_deg(0, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(5, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2)],
    },
    "goldenyear59": {   # 1959 - Kind of Blue (modal) + Take Five (5/4), num so tributo
        "bpm": 112, "meter": 5, "swing": True,
        "bass": "ostinato5", "comp": "sustained", "drum": "five_four",
        "progression": [(_deg(0, "min7"), 5), (_deg(1, "min7"), 5)],
    },
    "bossa64": {   # 1964 - Getz/Gilberto: bossa nova, sincopada e sem swing
        "bpm": 132, "swing": False,
        "bass": "bossa", "comp": "arpeggio", "drum": "bossa",
        "progression": [(_deg(2, "min7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "min7"), 2)],
    },
    "spiritual65": {   # 1965 - A Love Supreme: vamp modal intenso e devocional
        "bpm": 140, "swing": True,
        "bass": "pedal_intense", "comp": "quartal", "drum": "swing_intense",
        "progression": [(_deg(0, "min7"), 4), (_deg(3, "min7"), 4),
                         (_deg(0, "min7"), 4), (_deg(5, "min7"), 4)],
    },
    "fusion69": {   # 1969 - In a Silent Way: fusion lento, espacoso, eletrico
        "bpm": 96, "swing": False,
        "bass": "electric_riff", "comp": "pad", "drum": "ambient_sparse",
        "progression": [(_deg(0, "maj7"), 8), (_deg(5, "maj7"), 8)],
    },
    "jazzfunk73": {   # 1973 - Head Hunters: jazz-funk denso, dancante, sintetico
        "bpm": 104, "swing": False,
        "bass": "funk_riff", "comp": "stabs", "drum": "funk",
        "progression": [(_deg(0, "min7"), 4), (_deg(3, "dom7"), 4),
                         (_deg(0, "min7"), 4), (_deg(10, "dom7"), 4)],
    },
}


# ===================== PADROES DE BAIXO / ACOMPANHAMENTO / BATERIA =====================
def _apply_bass(master, kind, chord, start, beat, beats):
    root_f = _note_freq(chord["root"])
    fifth_f = _note_freq(chord["fifth"])
    n_beats = int(round(beats))

    if kind in ("walking", "walking_blues"):
        # Baixo caminhante classico: alterna fundamental/quinta a cada batida.
        for b in range(n_beats):
            f = root_f if b % 2 == 0 else fifth_f
            _mix(master, _tone(f, beat * 0.9, amp=0.55), start + int(b * beat * SAMPLE_RATE))

    elif kind == "calypso":
        # Sincopado: acentua o "e" apos o primeiro tempo, sem cair nas batidas certinhas.
        _mix(master, _tone(root_f, beat * 0.5, amp=0.5), start)
        _mix(master, _tone(fifth_f, beat * 0.4, amp=0.4), start + int(beat * 1.5 * SAMPLE_RATE))
        if n_beats >= 4:
            _mix(master, _tone(root_f, beat * 0.5, amp=0.5), start + int(beat * 2 * SAMPLE_RATE))
            _mix(master, _tone(fifth_f, beat * 0.4, amp=0.4), start + int(beat * 3.5 * SAMPLE_RATE))

    elif kind == "pedal":
        # Baixo pedal (drone) sustentado por todo o acorde - som modal, parado no lugar.
        _mix(master, _tone(root_f, beat * beats * 0.95, amp=0.42, attack=0.08), start)

    elif kind == "pedal_intense":
        # Igual ao pedal, mas rearticulado a cada batida (mais tenso/insistente).
        for b in range(n_beats):
            f = root_f if b % 2 == 0 else fifth_f
            _mix(master, _tone(f, beat * 0.95, amp=0.5, attack=0.01), start + int(b * beat * SAMPLE_RATE))

    elif kind == "ostinato5":
        # Riff ORIGINAL de 5 notas (nao cita nenhuma gravacao real) - da o "chao"
        # repetitivo caracteristico de um groove em compasso incomum.
        pattern = [chord["root"], chord["root"], chord["fifth"], chord["root"], chord["root"] + 5]
        for i in range(n_beats):
            midi = pattern[i % len(pattern)]
            _mix(master, _tone(_note_freq(midi), beat * 0.85, amp=0.46),
                 start + int(i * beat * SAMPLE_RATE))

    elif kind == "bossa":
        # Bossa nova: nota no tempo 1 e uma sincopada logo antes do "tempo 3".
        _mix(master, _tone(root_f, beat * 0.7, amp=0.4), start)
        if n_beats >= 2:
            _mix(master, _tone(fifth_f, beat * 0.6, amp=0.35), start + int(beat * 1.5 * SAMPLE_RATE))

    elif kind == "electric_riff":
        # Baixo eletrico esparso e sustentado, com uma leve "mordida" de oitava
        # (2 senoides proximas) simulando o timbre mais denso de um baixo eletrico.
        for b in range(0, n_beats, 2):
            _mix(master, _tone(root_f, beat * 1.8, amp=0.42, attack=0.05), start + int(b * beat * SAMPLE_RATE))
            _mix(master, _tone(root_f * 2, beat * 0.4, amp=0.10), start + int(b * beat * SAMPLE_RATE))

    elif kind == "funk_riff":
        # Groove sincopado e mais ocupado (16th-feel): fundamental curta e
        # percussiva com uma oitava "puxando" no contratempo - bem dancante.
        pattern_beats = [0.0, 0.75, 1.5, 2.25, 3.0, 3.5]
        for b_off in pattern_beats:
            if b_off < beats:
                f = root_f if (b_off % 1.5 < 0.8) else root_f * 2
                _mix(master, _tone(f, beat * 0.3, amp=0.4, attack=0.003),
                     start + int(b_off * beat * SAMPLE_RATE))

    else:
        _mix(master, _tone(root_f, beat * 0.9, amp=0.5), start)


def _apply_comp(master, kind, chord, start, beat, beats):
    pad = chord["pad"]
    dur = beat * beats

    if kind == "stabs":
        # Acordes curtos e picados no tempo 1 e no "e" do tempo 2 (comping bebop).
        for tone in pad:
            _mix(master, _tone(_note_freq(tone), beat * 0.25, amp=0.12, attack=0.005), start)
        if beats >= 2:
            off = start + int(beat * 1.5 * SAMPLE_RATE)
            for tone in pad:
                _mix(master, _tone(_note_freq(tone), beat * 0.25, amp=0.10, attack=0.005), off)

    elif kind == "arpeggio":
        # Violao bossa: acorde quebrado, uma nota de cada vez.
        step = dur / max(1, len(pad))
        for i, tone in enumerate(pad):
            _mix(master, _tone(_note_freq(tone), step * 0.9, amp=0.11, attack=0.02),
                 start + int(i * step * SAMPLE_RATE))

    else:
        amp = {"block": 0.11, "sustained": 0.10, "quartal": 0.13, "pad": 0.09}.get(kind, 0.10)
        attack = 0.15 if kind == "pad" else 0.05
        for tone in pad:
            _mix(master, _tone(_note_freq(tone), dur * 0.95, amp=amp, attack=attack), start)


def _apply_drums(master, kind, start, beat, beats, swing_long):
    n_beats = int(round(beats))

    if kind in ("swing_fast", "swing", "swing_brush", "swing_soft", "swing_intense"):
        amp = {"swing_fast": 0.15, "swing": 0.14, "swing_brush": 0.09,
               "swing_soft": 0.08, "swing_intense": 0.18}[kind]
        for b in range(n_beats):
            off = start + int(b * beat * SAMPLE_RATE)
            _mix(master, _noise_burst(0.05, amp=amp), off)
            _mix(master, _noise_burst(0.04, amp=amp * 0.7), off + int(swing_long * SAMPLE_RATE))
        if kind in ("swing_fast", "swing_intense"):
            _mix(master, _tone(60, 0.15, amp=0.45, attack=0.002), start)   # bumbo no tempo 1

    elif kind == "calypso":
        for b in range(n_beats):
            off = start + int(b * beat * SAMPLE_RATE)
            _mix(master, _noise_burst(0.04, amp=0.11), off + int(beat * 0.5 * SAMPLE_RATE))

    elif kind == "five_four":
        for b in range(n_beats):
            off = start + int(b * beat * SAMPLE_RATE)
            _mix(master, _noise_burst(0.05, amp=0.16 if b == 0 else 0.10), off)

    elif kind == "bossa":
        for b in range(n_beats):
            off = start + int(b * beat * SAMPLE_RATE)
            _mix(master, _noise_burst(0.035, amp=0.09), off)
            _mix(master, _noise_burst(0.03, amp=0.07), off + int(beat * 0.5 * SAMPLE_RATE))

    elif kind == "ambient_sparse":
        # So um bumbo abafado no tempo 1 de cada acorde - clima espacoso, sem chimbal.
        _mix(master, _tone(55, 0.3, amp=0.3, attack=0.02), start)

    elif kind == "funk":
        # Bumbo/caixa sincopados + chimbal reto em oitavas - groove denso e dancante.
        kick_beats = [0.0, 1.75, 2.5]
        snare_beats = [1.0, 3.0]
        for kb in kick_beats:
            if kb < beats:
                _mix(master, _tone(58, 0.12, amp=0.42, attack=0.002), start + int(kb * beat * SAMPLE_RATE))
        for sb in snare_beats:
            if sb < beats:
                _mix(master, _noise_burst(0.08, amp=0.17), start + int(sb * beat * SAMPLE_RATE))
        for b in range(n_beats * 2):
            _mix(master, _noise_burst(0.025, amp=0.06), start + int(b * beat * 0.5 * SAMPLE_RATE))


def _compose(profile):
    """Motor generico: monta baixo + acompanhamento + bateria em cima da
    'progression' do perfil, seguindo o andamento (bpm) e o swing dele."""
    bpm = profile["bpm"]
    beat = 60.0 / bpm
    swing = profile.get("swing", True)
    swing_long = beat * (2 / 3) if swing else beat * 0.5

    progression = profile["progression"]
    total_beats = sum(beats for _, beats in progression)
    total_samples = int(SAMPLE_RATE * beat * total_beats)
    master = [0.0] * total_samples

    cursor_beats = 0.0
    for chord, beats in progression:
        start = int(cursor_beats * beat * SAMPLE_RATE)
        _apply_comp(master, profile["comp"], chord, start, beat, beats)
        _apply_bass(master, profile["bass"], chord, start, beat, beats)
        _apply_drums(master, profile["drum"], start, beat, beats, swing_long)
        cursor_beats += beats

    avg_chord_dur = beat * (total_beats / len(progression))
    return master, beat, avg_chord_dur


try:
    _TRACKS = {}
    for _style, _profile in STYLE_PROFILES.items():
        _samples, _beat, _chord_dur = _compose(_profile)
        _TRACKS[_style] = {"sound": _to_sound(_samples), "beat": _beat, "chord_dur": _chord_dur}
except Exception:
    # Sem audio disponivel no sistema - o jogo segue em silencio.
    _TRACKS = {}

_DEFAULT_STYLE = "bebop45"

# Valores da trilha ATUALMENTE tocando - game/screens.py le esses dois direto
# (music.BEAT / music.CHORD_DUR) pra sincronizar o palco animado do Jazzy.
BEAT = _TRACKS.get(_DEFAULT_STYLE, {}).get("beat", 60.0 / 112)
CHORD_DUR = _TRACKS.get(_DEFAULT_STYLE, {}).get("chord_dur", BEAT * 2)

# Canal 0 reservado SO pra musica (pygame.mixer.set_reserved tira ele da lista
# que os efeitos sonoros (game/audio.py) usam pra escolher canal livre) - sem
# isso, um hit_sound tocado bem na hora que ha muitos inimigos sendo acertados
# em sequencia podia "roubar" o canal da musica e corta-la no meio do nada.
try:
    pygame.mixer.set_reserved(1)
    MUSIC_CHANNEL = pygame.mixer.Channel(0)
except Exception:
    MUSIC_CHANNEL = None

_current_channel = None
_current_track = None
_start_time = None   # quando a musica atual comecou (pygame.time.get_ticks()/1000) - e
                      # a referencia real do "tempo 0" da batida, nao o uptime do jogo.


def _style_for_level(world_id, level_num):
    """Cada fase do Jazzy tem seu proprio estilo (ver config.WORLDS); sem fase
    especifica (ex: chamado fora do Modo Historia) cai no estilo padrao."""
    if world_id == "jazzy" and level_num is not None:
        levels = config.WORLDS["jazzy"]["levels"]
        if 1 <= level_num <= len(levels):
            return levels[level_num - 1].get("style", _DEFAULT_STYLE)
    return _DEFAULT_STYLE


def _music_volume():
    return 0.0 if state.settings["muted"] else state.settings["music_volume"]


def play_world_music(world_id, level_num=None):
    """Toca em loop a musica da fase (para a anterior, se houver) - cada fase
    do Jazzy tem seu proprio estilo/andamento (ver _style_for_level)."""
    global _current_channel, _current_track, _start_time, BEAT, CHORD_DUR

    stop_music()
    if world_id != "jazzy" or not _TRACKS:
        return

    style = _style_for_level(world_id, level_num)
    track_info = _TRACKS.get(style) or _TRACKS.get(_DEFAULT_STYLE)
    if track_info is None or MUSIC_CHANNEL is None:
        return
    track_info["sound"].set_volume(_music_volume())
    MUSIC_CHANNEL.play(track_info["sound"], loops=-1)
    _current_channel = MUSIC_CHANNEL
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
