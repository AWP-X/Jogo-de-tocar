"""Geometria dos botoes de cada tela (funcoes "puras": so devolvem retangulos)
e a lista navegavel por teclado de cada uma.
"""
import pygame

from . import config
from . import state


def menu_buttons():
    w, h, gap = 260, 56, 20
    x = config.WIDTH // 2 - w // 2
    start_y = 344
    return {
        "play":    pygame.Rect(x, start_y, w, h),
        "options": pygame.Rect(x, start_y + (h + gap), w, h),
        "quit":    pygame.Rect(x, start_y + 2 * (h + gap), w, h),
    }


def difficulty_button():
    w, h = 340, 40
    x = config.WIDTH // 2 - w // 2
    y = 286
    return pygame.Rect(x, y, w, h)


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
    if current_state == "paused":
        return list(pause_buttons().items())
    if current_state == "gameover":
        return list(gameover_buttons().items())
    return []
