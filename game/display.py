"""Janela, canvas logico, fontes e a escala/letterbox entre os dois.

Inicializa o pygame e cria a janela assim que este modulo e importado pela
primeira vez - por isso ele deve ser um dos primeiros a ser importado (o
game/app.py cuida disso).
"""
import pygame

from . import config
from . import state

pygame.mixer.pre_init(22050, -16, 2, 512)
pygame.init()

screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
pygame.display.set_caption("Mystical Melody")
clock = pygame.time.Clock()

# Canvas logico: desenhamos tudo aqui e depois escalamos pra janela real.
canvas = pygame.Surface((config.WIDTH, config.HEIGHT))


def _load_font(names, size, bold=False):
    """Tenta carregar uma fonte do sistema (visual mais profissional); cai pra padrao se nao achar."""
    for name in names:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            continue
    return pygame.font.Font(None, size)


font_title  = _load_font(["segoeui", "arial"], 80, bold=True)
font_big    = _load_font(["segoeui", "arial"], 46, bold=True)
font        = _load_font(["segoeui", "arial"], 28)
font_small  = _load_font(["segoeui", "arial"], 20)
font_button = _load_font(["segoeui", "arial"], 24, bold=True)


def apply_video():
    """Recria a janela real de acordo com settings['mode']/['resolution'].

    Se a combinacao pedida falhar (ex: uma resolucao de tela cheia que o
    monitor nao suporta), volta pro modo janela padrao em vez de derrubar
    o jogo com uma excecao nao tratada.
    """
    global screen
    mode = state.settings["mode"]
    try:
        if mode == "fullscreen":
            screen = pygame.display.set_mode(state.settings["resolution"], pygame.FULLSCREEN)
        elif mode == "borderless":
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        else:
            screen = pygame.display.set_mode(state.settings["resolution"])
    except pygame.error:
        state.settings["mode"] = "windowed"
        state.settings["resolution"] = (config.WIDTH, config.HEIGHT)
        state.save_settings()
        screen = pygame.display.set_mode(state.settings["resolution"])


def _scale_params():
    win_w, win_h = screen.get_size()
    scale = min(win_w / config.WIDTH, win_h / config.HEIGHT)
    draw_w, draw_h = int(config.WIDTH * scale), int(config.HEIGHT * scale)
    off_x = (win_w - draw_w) // 2
    off_y = (win_h - draw_h) // 2
    return scale, off_x, off_y, draw_w, draw_h


def present():
    """Escala o canvas logico pra janela mantendo a proporcao (letterbox)."""
    scale, off_x, off_y, draw_w, draw_h = _scale_params()
    scaled = pygame.transform.scale(canvas, (draw_w, draw_h))
    screen.fill(config.BLACK)
    screen.blit(scaled, (off_x, off_y))
    pygame.display.flip()


def mouse_to_canvas():
    """Converte a posicao do mouse da janela para coordenadas do canvas logico."""
    mx, my = pygame.mouse.get_pos()
    scale, off_x, off_y, _, _ = _scale_params()
    return ((mx - off_x) / scale, (my - off_y) / scale)
