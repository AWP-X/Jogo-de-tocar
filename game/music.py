"""Trilha sonora do Mundo Jazzy: faixas de jazz REAIS, gravadas de verdade -
uma por fase, escolhidas pra combinar com o clima/andamento de cada ano da
historia do jazz (ver config.WORLDS["jazzy"]["levels"]).

Sao todas de Kevin MacLeod (incompetech.com), sob licenca Creative Commons
Attribution 3.0 (CC BY 3.0) - de uso livre (inclusive comercial), desde que
o autor seja creditado (ver a aba Opcoes > Creditos). Os arquivos ficam em
assets/music/.

Como sao gravacoes de verdade (nao uma composicao onde o andamento e definido
de antemao), o BPM de cada uma foi estimado automaticamente a partir do
proprio audio (energia + autocorrelacao) antes de entrar no jogo - por isso
"bpm" aparece como um numero fixo em cada fase, em vez de calculado na hora.
"""
import os

import pygame

from . import config
from . import state

MUSIC_DIR = os.path.join(config.PROJECT_ROOT, "assets", "music")

# Canal 0 reservado SO pra musica (pygame.mixer.set_reserved tira ele da
# lista que os efeitos sonoros - game/audio.py - usam pra escolher canal
# livre) - sem isso, um hit_sound tocado bem na hora de varios acertos em
# sequencia podia "roubar" o canal da musica e corta-la no meio do nada.
try:
    pygame.mixer.set_reserved(1)
    MUSIC_CHANNEL = pygame.mixer.Channel(0)
except Exception:
    MUSIC_CHANNEL = None

_track_cache = {}


def _load_track(filename):
    """Carrega (e guarda em cache) o arquivo de audio de uma fase. Se o
    arquivo nao existir ou nao puder ser lido, devolve None - a fase toca
    sem musica de fundo em vez do jogo travar ou dar erro."""
    if filename in _track_cache:
        return _track_cache[filename]
    try:
        sound = pygame.mixer.Sound(os.path.join(MUSIC_DIR, filename))
    except Exception:
        sound = None
    _track_cache[filename] = sound
    return sound


# Valores da trilha ATUALMENTE tocando - comecam num andamento generico antes
# de qualquer musica ser iniciada. game/screens.py le esses dois direto
# (music.BEAT / music.CHORD_DUR) pra sincronizar o palco animado do Jazzy.
BEAT = 60.0 / 112
CHORD_DUR = BEAT * 2

_current_channel = None
_current_track = None
_start_time = None   # quando a musica atual comecou (pygame.time.get_ticks()/1000) - e
                      # a referencia real do "tempo 0" da batida, nao o uptime do jogo.


def _music_volume():
    return 0.0 if state.settings["muted"] else state.settings["music_volume"]


def play_world_music(world_id, level_num=None):
    """Toca em loop a faixa da fase (para a anterior, se houver) - cada fase
    do Jazzy tem sua propria gravacao e seu proprio andamento (ver
    config.WORLDS["jazzy"]["levels"])."""
    global _current_channel, _current_track, _start_time, BEAT, CHORD_DUR

    stop_music()
    if world_id != "jazzy" or MUSIC_CHANNEL is None:
        return

    levels = config.WORLDS["jazzy"]["levels"]
    if level_num is None or not (1 <= level_num <= len(levels)):
        return
    level_data = levels[level_num - 1]

    sound = _load_track(level_data["track"])
    if sound is None:
        return
    sound.set_volume(_music_volume())
    MUSIC_CHANNEL.play(sound, loops=-1)
    _current_channel = MUSIC_CHANNEL
    _current_track = sound
    BEAT = 60.0 / level_data.get("bpm", 112)
    CHORD_DUR = BEAT * 2
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
    calculada nunca bateria com o que realmente se ouve.

    Como o BPM de uma gravacao real e uma ESTIMATIVA (nao um valor exato como
    numa composicao propria), o acerto "no tempo" aqui e aproximado - fica
    proximo o suficiente do pulso real da musica pra dar uma boa pista visual/
    sonora, mas sem a precisao milimetrica de quando o jogo compunha a propria
    trilha."""
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
