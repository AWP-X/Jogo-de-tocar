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


def _noise_burst(duration, amp=1.0):
    """Estouro curto de ruido branco, usado como chimbal/caixa (percussao)."""
    n = int(SAMPLE_RATE * duration)
    buf = [0.0] * n
    for i in range(n):
        env = max(0.0, 1 - (i / n))
        buf[i] = amp * env * random.uniform(-1, 1)
    return buf


def _voice(freq, duration, harmonics, amp=1.0, attack=0.01, decay_rate=3.0,
           vibrato=0.0, noise_attack=0.0):
    """Tom com VARIOS harmonicos (em vez da senoide pura de _tone) e decaimento
    EXPONENCIAL - e o que faz soar como um instrumento acustico de verdade tocando
    em vez de um "bipe eletronico": nenhum instrumento real emite uma onda
    perfeitamente pura, e o decaimento de uma nota de piano/baixo/sopro nunca e
    uma rampa reta ate zero, e sim uma curva que cai rapido no comeco e devagar
    depois.

    harmonics: lista de (multiplicador_da_frequencia, amplitude_relativa) -
    ex.: [(1, 1.0), (2, 0.5)] soma a fundamental com o dobro dela na metade do
    volume. vibrato: oscilacao leve de altura (comum em sopros como sax/
    trompete). noise_attack: mistura um pouco de ruido so no ataque, pro
    transiente soar como o "toque" do martelo do piano ou a "mordida" da
    palheta, em vez de comecar seco."""
    n = int(SAMPLE_RATE * duration)
    buf = [0.0] * n
    total_h = sum(a for _, a in harmonics)
    for i in range(n):
        t = i / SAMPLE_RATE
        if t < attack:
            env = t / attack
        else:
            env = math.exp(-(t - attack) * decay_rate)
        vib = (1.0 + vibrato * math.sin(2 * math.pi * 5.5 * t)) if vibrato else 1.0
        s = 0.0
        for mult, hamp in harmonics:
            s += hamp * math.sin(2 * math.pi * freq * mult * vib * t)
        s /= total_h
        if noise_attack > 0 and t < 0.015:
            s += random.uniform(-1, 1) * noise_attack * (1 - t / 0.015)
        buf[i] = amp * env * s
    return buf


def _kick(duration=0.15, amp=0.45):
    """Bumbo com envelope de altura (comeca mais agudo e cai rapido pro grave)
    - o "thump" caracteristico de um bumbo de verdade, em vez de um tom fixo."""
    n = int(SAMPLE_RATE * duration)
    buf = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 45 + 120 * math.exp(-t * 18)
        env = math.exp(-t * 14)
        buf[i] = amp * env * math.sin(2 * math.pi * freq * t)
    return buf


# Perfis de harmonicos de cada "instrumento" - a diferenca de timbre entre
# piano/baixo/sax/trompete/violao vem quase toda daqui (quantos harmonicos tem
# e o peso de cada um), nao de um efeito especial.
PIANO_HARMONICS         = [(1, 1.0), (2, 0.55), (3, 0.30), (4, 0.18), (5, 0.10), (6, 0.06)]
ELECTRIC_PIANO_HARMONICS = [(1, 1.0), (2, 0.35), (4, 0.12)]   # Rhodes-like, mais redondo/sininho (fusion)
GUITAR_HARMONICS        = [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.1)]
BASS_HARMONICS          = [(1, 1.0), (2, 0.30), (3, 0.10)]
ELECTRIC_BASS_HARMONICS = [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.12)]
SAX_HARMONICS           = [(1, 1.0), (2, 0.65), (3, 0.55), (4, 0.35), (5, 0.22), (6, 0.14), (7, 0.08)]
TRUMPET_HARMONICS       = [(1, 1.0), (2, 0.75), (3, 0.6), (4, 0.45), (5, 0.30), (6, 0.18)]

LEAD_VOICES = {
    "sax":     {"harmonics": SAX_HARMONICS, "attack": 0.035, "decay_rate": 1.1,
                "vibrato": 0.006, "noise_attack": 0.10},
    "trumpet": {"harmonics": TRUMPET_HARMONICS, "attack": 0.015, "decay_rate": 1.4,
                "vibrato": 0.004, "noise_attack": 0.05},
}


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
        "bpm": 200, "swing": True, "lead": "trumpet",
        "bass": "walking", "comp": "stabs", "drum": "swing_fast",
        "progression": [(_deg(0, "maj7"), 2), (_deg(9, "min7"), 2),
                         (_deg(2, "min7"), 2), (_deg(7, "dom7"), 2)],
    },
    "bebop53": {   # 1953 - Massey Hall: bebop ainda mais afiado (ii-V-I-VI7)
        "bpm": 212, "swing": True, "lead": "sax",
        "bass": "walking", "comp": "stabs", "drum": "swing_fast",
        "progression": [(_deg(2, "min7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "dom7"), 2)],
    },
    "liveswing55": {   # 1955 - Miles em Newport / Concert by the Sea: swing relaxado, ao vivo
        "bpm": 168, "swing": True, "lead": "trumpet",
        "bass": "walking", "comp": "block", "drum": "swing_brush",
        "progression": [(_deg(0, "maj7"), 2), (_deg(5, "maj7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "min7"), 2),
                         (_deg(2, "min7"), 2), (_deg(7, "dom7"), 2)],
    },
    "calypsohard56": {   # 1956 - Saxophone Colossus: hard bop com lilt calypso, sem swing
        "bpm": 152, "swing": False, "lead": "sax",
        "bass": "calypso", "comp": "stabs", "drum": "calypso",
        "progression": [(_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(5, "dom7"), 2), (_deg(0, "dom7"), 2)],
    },
    "bluesyhard57": {   # 1957 - Blue Train: hard bop enraizado no blues (12 compassos)
        "bpm": 138, "swing": True, "lead": "sax",
        "bass": "walking", "comp": "stabs", "drum": "swing",
        "progression": [(_deg(0, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(5, "dom7"), 2), (_deg(5, "dom7"), 2),
                         (_deg(0, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(5, "dom7"), 2), (_deg(0, "dom7"), 2), (_deg(7, "dom7"), 2)],
    },
    "goldenyear59": {   # 1959 - Kind of Blue (modal) + Take Five (5/4), num so tributo
        "bpm": 112, "meter": 5, "swing": True, "lead": "trumpet",
        "bass": "ostinato5", "comp": "sustained", "drum": "five_four",
        "progression": [(_deg(0, "min7"), 5), (_deg(1, "min7"), 5)],
    },
    "bossa64": {   # 1964 - Getz/Gilberto: bossa nova, sincopada e sem swing
        "bpm": 132, "swing": False, "lead": "sax",
        "bass": "bossa", "comp": "arpeggio", "drum": "bossa",
        "progression": [(_deg(2, "min7"), 2), (_deg(7, "dom7"), 2),
                         (_deg(0, "maj7"), 2), (_deg(9, "min7"), 2)],
    },
    "spiritual65": {   # 1965 - A Love Supreme: vamp modal intenso e devocional
        "bpm": 140, "swing": True, "lead": "sax",
        "bass": "pedal_intense", "comp": "quartal", "drum": "swing_intense",
        "progression": [(_deg(0, "min7"), 4), (_deg(3, "min7"), 4),
                         (_deg(0, "min7"), 4), (_deg(5, "min7"), 4)],
    },
    "fusion69": {   # 1969 - In a Silent Way: fusion lento, espacoso, eletrico
        "bpm": 96, "swing": False, "lead": "trumpet",
        "bass": "electric_riff", "comp": "pad", "drum": "ambient_sparse",
        "progression": [(_deg(0, "maj7"), 8), (_deg(5, "maj7"), 8)],
    },
    "jazzfunk73": {   # 1973 - Head Hunters: jazz-funk denso, dancante, sintetico
        "bpm": 104, "swing": False, "lead": "sax",
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
    electric = kind in ("electric_riff", "funk_riff")
    harmonics = ELECTRIC_BASS_HARMONICS if electric else BASS_HARMONICS

    def pluck(freq, dur, amp, attack=0.008, decay_rate=2.0):
        # decaimento baixo (2ish) = a nota "canta" quase ate o fim do tempo dela,
        # como um contrabaixo dedilhado, em vez de sumir na metade.
        return _voice(freq, dur, harmonics, amp=amp, attack=attack, decay_rate=decay_rate,
                      noise_attack=0.05 if electric else 0.07)

    if kind in ("walking", "walking_blues"):
        # Baixo caminhante classico: alterna fundamental/quinta a cada batida.
        for b in range(n_beats):
            f = root_f if b % 2 == 0 else fifth_f
            _mix(master, pluck(f, beat * 0.9, amp=0.5), start + int(b * beat * SAMPLE_RATE))

    elif kind == "calypso":
        # Sincopado: acentua o "e" apos o primeiro tempo, sem cair nas batidas certinhas.
        _mix(master, pluck(root_f, beat * 0.5, amp=0.46), start)
        _mix(master, pluck(fifth_f, beat * 0.4, amp=0.38), start + int(beat * 1.5 * SAMPLE_RATE))
        if n_beats >= 4:
            _mix(master, pluck(root_f, beat * 0.5, amp=0.46), start + int(beat * 2 * SAMPLE_RATE))
            _mix(master, pluck(fifth_f, beat * 0.4, amp=0.38), start + int(beat * 3.5 * SAMPLE_RATE))

    elif kind == "pedal":
        # Baixo pedal (drone) sustentado por todo o acorde - som modal, parado no lugar.
        _mix(master, pluck(root_f, beat * beats * 0.95, amp=0.4, attack=0.08, decay_rate=0.9), start)

    elif kind == "pedal_intense":
        # Igual ao pedal, mas rearticulado a cada batida (mais tenso/insistente).
        for b in range(n_beats):
            f = root_f if b % 2 == 0 else fifth_f
            _mix(master, pluck(f, beat * 0.95, amp=0.48, attack=0.01), start + int(b * beat * SAMPLE_RATE))

    elif kind == "ostinato5":
        # Riff ORIGINAL de 5 notas (nao cita nenhuma gravacao real) - da o "chao"
        # repetitivo caracteristico de um groove em compasso incomum.
        pattern = [chord["root"], chord["root"], chord["fifth"], chord["root"], chord["root"] + 5]
        for i in range(n_beats):
            midi = pattern[i % len(pattern)]
            _mix(master, pluck(_note_freq(midi), beat * 0.85, amp=0.44),
                 start + int(i * beat * SAMPLE_RATE))

    elif kind == "bossa":
        # Bossa nova: nota no tempo 1 e uma sincopada logo antes do "tempo 3".
        _mix(master, pluck(root_f, beat * 0.7, amp=0.38), start)
        if n_beats >= 2:
            _mix(master, pluck(fifth_f, beat * 0.6, amp=0.33), start + int(beat * 1.5 * SAMPLE_RATE))

    elif kind == "electric_riff":
        # Baixo eletrico esparso e sustentado - decaimento mais lento que o
        # upright acustico, timbre com mais harmonicos (ELECTRIC_BASS_HARMONICS).
        for b in range(0, n_beats, 2):
            _mix(master, pluck(root_f, beat * 1.8, amp=0.4, attack=0.04, decay_rate=1.1),
                 start + int(b * beat * SAMPLE_RATE))

    elif kind == "funk_riff":
        # Groove sincopado e mais ocupado (16th-feel): notas curtas e percussivas
        # alternando fundamental e oitava no contratempo - bem dancante.
        pattern_beats = [0.0, 0.75, 1.5, 2.25, 3.0, 3.5]
        for b_off in pattern_beats:
            if b_off < beats:
                f = root_f if (b_off % 1.5 < 0.8) else root_f * 2
                _mix(master, pluck(f, beat * 0.3, amp=0.38, attack=0.003, decay_rate=4.0),
                     start + int(b_off * beat * SAMPLE_RATE))

    else:
        _mix(master, pluck(root_f, beat * 0.9, amp=0.48), start)


def _apply_comp(master, kind, chord, start, beat, beats):
    pad = chord["pad"]
    dur = beat * beats

    if kind == "stabs":
        # Piano: acordes curtos e picados no tempo 1 e no "e" do tempo 2 (comping
        # bebop) - decaimento rapido (decay_rate alto) + toque de ruido no
        # ataque simulando o martelo batendo na corda.
        for tone in pad:
            _mix(master, _voice(_note_freq(tone), beat * 0.4, PIANO_HARMONICS, amp=0.13,
                                 attack=0.004, decay_rate=9.0, noise_attack=0.05), start)
        if beats >= 2:
            off = start + int(beat * 1.5 * SAMPLE_RATE)
            for tone in pad:
                _mix(master, _voice(_note_freq(tone), beat * 0.4, PIANO_HARMONICS, amp=0.11,
                                     attack=0.004, decay_rate=9.0, noise_attack=0.05), off)

    elif kind == "arpeggio":
        # Violao bossa: acorde quebrado, uma nota de cada vez, com o "biting"
        # inicial da unha/palheta (noise_attack) e decaimento de corda dedilhada.
        step = dur / max(1, len(pad))
        for i, tone in enumerate(pad):
            _mix(master, _voice(_note_freq(tone), step * 0.95, GUITAR_HARMONICS, amp=0.12,
                                 attack=0.006, decay_rate=2.6, noise_attack=0.08),
                 start + int(i * step * SAMPLE_RATE))

    else:
        # Piano sustentado (ou Rhodes eletrico no "pad", usado so no fusion) -
        # decaimento lento pra soar como o acorde ficando "pendurado" no ar.
        params = {
            "block":     (PIANO_HARMONICS, 0.12, 1.3),
            "sustained": (PIANO_HARMONICS, 0.11, 1.0),
            "quartal":   (PIANO_HARMONICS, 0.14, 1.1),
            "pad":       (ELECTRIC_PIANO_HARMONICS, 0.10, 0.7),
        }
        harmonics, amp, decay_rate = params.get(kind, (PIANO_HARMONICS, 0.11, 1.2))
        attack = 0.15 if kind == "pad" else 0.05
        for tone in pad:
            _mix(master, _voice(_note_freq(tone), dur * 0.95, harmonics, amp=amp,
                                 attack=attack, decay_rate=decay_rate, noise_attack=0.03), start)


def _apply_lead(master, instrument, chord, start, beat, beats):
    """Uma frase melodica curta por cima do acorde, tocada por um sax ou
    trompete (harmonicos ricos + vibrato, bem diferente do acompanhamento) -
    e o que faz soar como uma banda tocando de verdade, nao so uma sequencia
    de acordes com baixo e bateria por baixo."""
    voice = LEAD_VOICES[instrument]
    tones = chord["pad"]   # 3a, 5a, 7a do proprio acorde - usadas como "escala" do solo
    lead_notes = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[0] + 12]
    n_notes = 2 if beats <= 3 else 3
    step = beats / n_notes
    for i in range(n_notes):
        note = lead_notes[i % len(lead_notes)]
        dur = beat * step * 0.85
        off = start + int(i * step * beat * SAMPLE_RATE)
        _mix(master, _voice(_note_freq(note), dur, voice["harmonics"], amp=0.15,
                             attack=voice["attack"], decay_rate=voice["decay_rate"],
                             vibrato=voice["vibrato"], noise_attack=voice["noise_attack"]), off)


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
            _mix(master, _kick(amp=0.45), start)   # bumbo no tempo 1

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
        _mix(master, _kick(duration=0.3, amp=0.3), start)

    elif kind == "funk":
        # Bumbo/caixa sincopados + chimbal reto em oitavas - groove denso e dancante.
        kick_beats = [0.0, 1.75, 2.5]
        snare_beats = [1.0, 3.0]
        for kb in kick_beats:
            if kb < beats:
                _mix(master, _kick(amp=0.42), start + int(kb * beat * SAMPLE_RATE))
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
        _apply_lead(master, profile["lead"], chord, start, beat, beats)
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
