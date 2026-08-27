"""Estado mutavel do jogo: configuracoes do jogador (persistidas em
settings.json), recorde e ranking local (highscore.json / leaderboard.json) e o
que a interface esta fazendo agora (aba aberta, item focado, etc.).

Outros modulos sempre acessam isso via `state.algo` (import game.state as state),
nunca importando os nomes soltos com `from game.state import x` - se fizessem
isso, escrever em `x` dali criaria uma copia local e a mudanca nao apareceria
pros outros modulos.
"""
import json
import os

import pygame

from . import config

DEFAULT_KEYS = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
}

settings = {
    "volume": 0.5,
    "muted": False,
    "sensibilidade": 1.0,
    "keys": dict(DEFAULT_KEYS),
    "resolution": (1280, 720),
    "mode": "windowed",
    "show_fps": False,
    "difficulty": "normal",
}

resolutions = [(1280, 720), (1024, 768), (800, 600)]
modes = ["windowed", "fullscreen", "borderless"]
res_index = 0
mode_index = 0

rebinding = None
dragging_volume = False
dragging_sens = False
nav_index = 0    # item selecionado via teclado (setas) nas telas de botao
menu_time = 0.0  # acumulador de tempo p/ animacoes ambientes (brilho pulsante etc.)
name_input = ""  # texto sendo digitado na tela de "novo recorde"

# "options" e reaproveitada tanto pelo menu quanto pelo pause; isso guarda pra
# onde o botao VOLTAR (e o ESC) deve mandar o jogador de volta.
options_return_to = "menu"
options_tab = "audio"

# Contexto do Modo Historia: qual mundo/nivel esta selecionado ou em jogo agora.
current_world = "jazzy"
current_level = 1   # 1-indexado


# ===================== CONFIGURACOES (persistentes) =====================
SETTINGS_FILE = os.path.join(config.PROJECT_ROOT, "settings.json")


def load_settings():
    """Aplica settings.json por cima dos padroes definidos acima. Qualquer campo
    ausente, com tipo errado ou fora do intervalo valido e ignorado (o padrao
    permanece) - um arquivo corrompido ou editado a mao nunca deve travar o jogo."""
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return

    if isinstance(data.get("volume"), (int, float)):
        settings["volume"] = max(0.0, min(1.0, float(data["volume"])))
    if isinstance(data.get("muted"), bool):
        settings["muted"] = data["muted"]
    if isinstance(data.get("sensibilidade"), (int, float)):
        settings["sensibilidade"] = max(0.1, min(3.0, float(data["sensibilidade"])))

    keys_data = data.get("keys")
    if isinstance(keys_data, dict):
        for action in DEFAULT_KEYS:
            v = keys_data.get(action)
            if isinstance(v, int):
                settings["keys"][action] = v

    res = data.get("resolution")
    if isinstance(res, (list, tuple)) and len(res) == 2:
        try:
            settings["resolution"] = (int(res[0]), int(res[1]))
        except Exception:
            pass

    if data.get("mode") in modes:
        settings["mode"] = data["mode"]
    if isinstance(data.get("show_fps"), bool):
        settings["show_fps"] = data["show_fps"]
    if data.get("difficulty") in config.DIFFICULTY_ORDER:
        settings["difficulty"] = data["difficulty"]


def save_settings():
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "volume": settings["volume"],
                "muted": settings["muted"],
                "sensibilidade": settings["sensibilidade"],
                "keys": settings["keys"],
                "resolution": list(settings["resolution"]),
                "mode": settings["mode"],
                "show_fps": settings["show_fps"],
                "difficulty": settings["difficulty"],
            }, f, indent=2)
    except Exception:
        pass   # sem permissao de escrita ou disco cheio: o jogo segue normalmente


load_settings()

# Sincroniza os indices de ciclo com o que foi carregado - senao os botoes RES e
# MODO voltariam sempre pro primeiro item, ignorando o que a pessoa escolheu.
if settings["resolution"] in resolutions:
    res_index = resolutions.index(settings["resolution"])
if settings["mode"] in modes:
    mode_index = modes.index(settings["mode"])


# ===================== RECORDE (persistente) =====================
HIGHSCORE_FILE = os.path.join(config.PROJECT_ROOT, "highscore.json")


def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(json.load(f).get("highscore", 0))
    except Exception:
        return 0


def save_highscore(value):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": value}, f)
    except Exception:
        pass   # sem permissao de escrita ou disco cheio: o jogo segue normalmente


highscore = load_highscore()


# ===================== RANKING LOCAL (top 5, com nome) =====================
LEADERBOARD_FILE = os.path.join(config.PROJECT_ROOT, "leaderboard.json")
LEADERBOARD_SIZE = 5


def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    cleaned = []
    for entry in data:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and isinstance(entry.get("score"), int):
            difficulty = entry.get("difficulty")
            if difficulty not in config.DIFFICULTY_ORDER:
                difficulty = "normal"
            cleaned.append({"name": entry["name"][:12], "score": entry["score"], "difficulty": difficulty})

    cleaned.sort(key=lambda e: e["score"], reverse=True)
    return cleaned[:LEADERBOARD_SIZE]


def save_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f, indent=2)
    except Exception:
        pass


leaderboard = load_leaderboard()


def qualifies_for_leaderboard(score):
    """True se essa pontuacao entraria no top 5 (mesmo que o ranking ainda nao
    esteja cheio)."""
    if score <= 0:
        return False
    if len(leaderboard) < LEADERBOARD_SIZE:
        return True
    return score > min(e["score"] for e in leaderboard)


def add_leaderboard_entry(name, score, difficulty):
    leaderboard.append({"name": (name.strip() or "JOGADOR")[:12], "score": score, "difficulty": difficulty})
    leaderboard.sort(key=lambda e: e["score"], reverse=True)
    del leaderboard[LEADERBOARD_SIZE:]
    save_leaderboard()


# ===================== PROGRESSO NO MODO HISTORIA =====================
PROGRESS_FILE = os.path.join(config.PROJECT_ROOT, "progress.json")


def load_progress():
    result = {w: {"unlocked": 1} for w in config.WORLD_ORDER}
    try:
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        return result

    if isinstance(data, dict):
        for world_id in config.WORLD_ORDER:
            entry = data.get(world_id)
            total = len(config.WORLDS[world_id]["levels"])
            if isinstance(entry, dict) and isinstance(entry.get("unlocked"), int):
                result[world_id]["unlocked"] = max(1, min(entry["unlocked"], total))
    return result


def save_progress():
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f, indent=2)
    except Exception:
        pass


progress = load_progress()


def unlock_level(world_id, level_num):
    """Libera o proximo nivel (1-indexado) se ainda nao estava liberado."""
    total = len(config.WORLDS[world_id]["levels"])
    next_level = min(level_num + 1, total)
    if progress[world_id]["unlocked"] < next_level:
        progress[world_id]["unlocked"] = next_level
        save_progress()
