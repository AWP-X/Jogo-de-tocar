"""Geometria dos botoes de cada tela (funcoes "puras": so devolvem retangulos)
e a lista navegavel por teclado de cada uma.
"""
import pygame

from . import config
from . import state


MENU_BUTTON_ORDER = ["play", "historia", "options", "quit"]


def menu_buttons():
    w, h, gap = 260, 56, 20
    x = config.WIDTH // 2 - w // 2
    start_y = 344
    return {key: pygame.Rect(x, start_y + i * (h + gap), w, h) for i, key in enumerate(MENU_BUTTON_ORDER)}


def difficulty_button():
    w, h = 340, 40
    x = config.WIDTH // 2 - w // 2
    y = 286
    return pygame.Rect(x, y, w, h)


# ---- Modo Historia: selecao de mundo (portais circulares) e de nivel (trilha) ----
def historia_voltar_button():
    return pygame.Rect(config.WIDTH // 2 - 150, 655, 300, 50)


WORLD_SLOTS = 8      # quantos "portais" aparecem na grade (os que sobram sao so "em breve")
WORLD_ORB_RADIUS = 68


def world_slot_positions():
    """Posicoes fixas dos WORLD_SLOTS circulos (grade 4x2), independente de
    quantos mundos ja existem de verdade - os excedentes viram '?' de bloqueado."""
    cols, rows = 4, 2
    r = WORLD_ORB_RADIUS
    gap_x, gap_y = 70, 80
    grid_w = cols * (r * 2) + (cols - 1) * gap_x
    grid_h = rows * (r * 2) + (rows - 1) * gap_y
    x0 = config.WIDTH // 2 - grid_w // 2 + r
    y0 = config.HEIGHT // 2 - grid_h // 2 + r + 10
    return [(x0 + col * (r * 2 + gap_x), y0 + row * (r * 2 + gap_y))
            for row in range(rows) for col in range(cols)]


def world_buttons():
    """So os mundos DE VERDADE (focaveis/clicaveis) - os slots vazios sao
    apenas decorativos e desenhados a parte em screens.draw_world_select."""
    positions = world_slot_positions()
    r = WORLD_ORB_RADIUS
    return {wid: pygame.Rect(int(cx - r), int(cy - r), r * 2, r * 2)
            for wid, (cx, cy) in zip(config.WORLD_ORDER, positions)}


LEVEL_ORB_RADIUS = 52


def level_path_positions(world_id):
    """Posicoes dos nos de nivel numa trilha em zigue-zague (tipo mapa de fases)."""
    total = len(config.WORLDS[world_id]["levels"])
    cols = 5
    col_w = 220
    x0 = config.WIDTH // 2 - (cols - 1) * col_w // 2
    y_bottom, y_top = 540, 290
    positions = []
    for i in range(total):
        row, col = divmod(i, cols)
        going_right = (row % 2 == 0)
        display_col = col if going_right else (cols - 1 - col)
        x = x0 + display_col * col_w
        y = y_bottom if row % 2 == 0 else y_top
        positions.append((x, y))
    return positions


def level_select_buttons(world_id):
    r = LEVEL_ORB_RADIUS
    return {i + 1: pygame.Rect(int(x - r), int(y - r), r * 2, r * 2)
            for i, (x, y) in enumerate(level_path_positions(world_id))}


def level_complete_buttons(is_last):
    if is_last:
        return {"menu": pygame.Rect(config.WIDTH // 2 - 150, 420, 300, 50)}
    return {
        "next": pygame.Rect(config.WIDTH // 2 - 150, 380, 300, 50),
        "menu": pygame.Rect(config.WIDTH // 2 - 150, 450, 300, 50),
    }


# ---- Opcoes: painel unico com abas (Audio / Controles / Video / Ranking / Creditos) ----
def options_tab_buttons():
    w, gap = 180, 16
    total = len(config.OPTIONS_TABS) * w + (len(config.OPTIONS_TABS) - 1) * gap
    x0 = config.WIDTH // 2 - total // 2
    y = 130
    return {tab: pygame.Rect(x0 + i * (w + gap), y, w, 44) for i, tab in enumerate(config.OPTIONS_TABS)}


def options_voltar_button():
    return pygame.Rect(config.WIDTH // 2 - 150, 580, 300, 50)


def audio_buttons():
    w, h, gap = 220, 50, 20
    total = w * 2 + gap
    x0 = config.WIDTH // 2 - total // 2
    y = 440
    return {
        "mute": pygame.Rect(x0, y, w, h),
        "test": pygame.Rect(x0 + w + gap, y, w, h),
    }


def controles_buttons():
    w, h, gap = 300, 50, 15
    x = config.WIDTH // 2 - w // 2
    y0 = 235
    return {
        "up":    pygame.Rect(x, y0, w, h),
        "down":  pygame.Rect(x, y0 + (h + gap), w, h),
        "left":  pygame.Rect(x, y0 + 2 * (h + gap), w, h),
        "right": pygame.Rect(x, y0 + 3 * (h + gap), w, h),
        "reset": pygame.Rect(x, y0 + 4 * (h + gap), w, h),
    }


def video_content_buttons():
    w, h, gap = 300, 50, 20
    x = config.WIDTH // 2 - w // 2
    y0 = 250
    return {
        "res":  pygame.Rect(x, y0, w, h),
        "mode": pygame.Rect(x, y0 + (h + gap), w, h),
        "fps":  pygame.Rect(x, y0 + 2 * (h + gap), w, h),
    }


def pause_buttons():
    return {
        "resume":  pygame.Rect(config.WIDTH // 2 - 150, 300, 300, 50),
        "options": pygame.Rect(config.WIDTH // 2 - 150, 370, 300, 50),
        "menu":    pygame.Rect(config.WIDTH // 2 - 150, 440, 300, 50),
    }


def gameover_buttons():
    return {
        "retry": pygame.Rect(config.WIDTH // 2 - 150, 380, 300, 50),
        "menu":  pygame.Rect(config.WIDTH // 2 - 150, 450, 300, 50),
    }


def nav_items_for(current_state):
    """Lista ordenada (chave, rect) navegavel por teclado na tela atual."""
    if current_state == "menu":
        items = [("difficulty", difficulty_button())]
        items += list(menu_buttons().items())
        return items
    if current_state == "options":
        items = [(f"tab_{k}", r) for k, r in options_tab_buttons().items()]
        if state.options_tab == "audio":
            items += list(audio_buttons().items())
        elif state.options_tab == "controles":
            items += list(controles_buttons().items())
        elif state.options_tab == "video":
            items += list(video_content_buttons().items())
        items.append(("voltar", options_voltar_button()))
        return items
    if current_state == "world_select":
        items = list(world_buttons().items())
        items.append(("voltar", historia_voltar_button()))
        return items
    if current_state == "level_select":
        items = list(level_select_buttons(state.current_world).items())
        items.append(("voltar", historia_voltar_button()))
        return items
    if current_state == "level_complete":
        total = len(config.WORLDS[state.current_world]["levels"])
        is_last = state.current_level >= total
        return list(level_complete_buttons(is_last).items())
    if current_state == "paused":
        return list(pause_buttons().items())
    if current_state == "gameover":
        return list(gameover_buttons().items())
    return []
