"""Efeitos visuais de fundo (degrade, particulas, brilho) e as pecas basicas de
UI reaproveitadas em todas as telas: texto, botao, aba, painel, slider e icones.
"""
import math
import os
import random

import pygame

from . import audio
from . import config
from . import display

canvas = display.canvas


# ===================== FUNDO =====================
def _make_gradient(width, height, top_color, bottom_color):
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * t),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * t),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * t),
        )
        pygame.draw.line(surf, color, (0, y), (width, y))
    return surf


# Pre-renderizado uma vez so (o canvas logico tem tamanho fixo).
MENU_BG_SURF = _make_gradient(config.WIDTH, config.HEIGHT, config.BG_TOP, config.BG_BOTTOM)

# Particulas flutuantes de fundo (poeirinhas)
NUM_PARTICLES = 50
particles = [
    {
        "pos": pygame.Vector2(random.uniform(0, config.WIDTH), random.uniform(0, config.HEIGHT)),
        "speed": random.uniform(8, 30),
        "radius": random.uniform(1, 2.5),
        "alpha": random.randint(30, 110),
    }
    for _ in range(NUM_PARTICLES)
]


def update_particles(dt):
    for p in particles:
        p["pos"].y -= p["speed"] * dt
        if p["pos"].y < -5:
            p["pos"].y = config.HEIGHT + 5
            p["pos"].x = random.uniform(0, config.WIDTH)


def draw_particles(surface):
    for p in particles:
        r = p["radius"]
        size = int(r * 2) + 2
        dot = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*config.ACCENT, p["alpha"]), (size // 2, size // 2), r)
        surface.blit(dot, (p["pos"].x - size / 2, p["pos"].y - size / 2))


def _make_radial_glow(radius, color):
    """Bola de luz suave (falso "bloom"), desenhada uma vez e reaproveitada."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(80 * (1 - r / radius) ** 2)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


TITLE_GLOW = _make_radial_glow(220, config.ACCENT)


def draw_title_glow(center, t):
    """Brilho pulsante atras do titulo do menu (t = tempo acumulado em segundos)."""
    pulse = 0.7 + 0.3 * math.sin(t * 1.6)
    glow = TITLE_GLOW.copy()
    glow.set_alpha(int(255 * pulse))
    canvas.blit(glow, (center[0] - TITLE_GLOW.get_width() // 2, center[1] - TITLE_GLOW.get_height() // 2))


# ===================== ANIMACAO DE HOVER =====================
# Guarda um progresso 0..1 por chave (interpolado com o dt) - usado pelos botoes/abas.
button_hover_t = {}
_was_hovering = {}


def _hover_progress(key, hovering, dt, speed=9):
    current = button_hover_t.get(key, 0.0)
    target = 1.0 if hovering else 0.0
    current += (target - current) * min(1, dt * speed)
    button_hover_t[key] = current
    return current


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ===================== TEXTO =====================
def draw_text(text, fnt, x, y, center=False, color=config.WHITE, shadow=False):
    if shadow:
        shadow_render = fnt.render(text, True, config.BLACK)
        shadow_render.set_alpha(120)
        srect = shadow_render.get_rect()
        if center:
            srect.center = (x + 3, y + 3)
        else:
            srect.topleft = (x + 3, y + 3)
        canvas.blit(shadow_render, srect)

    render = fnt.render(text, True, color)
    rect = render.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    canvas.blit(render, rect)


# ===================== ICONES =====================
def _resource_path(*parts):
    return os.path.join(config.PROJECT_ROOT, *parts)


def _load_icon_svgs():
    """Icones reais baixados como SVG (Feather Icons, MIT, pros icones de botao
    monocromaticos; Twemoji, CC-BY 4.0, pros instrumentos coloridos do palco
    do Mundo Jazzy) - o pygame consegue rasterizar SVG nativamente. Se o
    arquivo nao existir, o icone so nao aparece."""
    names = ("play", "settings", "power", "map", "saxophone", "piano", "trumpet", "drum")
    surfaces = {}
    for name in names:
        try:
            surfaces[name] = pygame.image.load(_resource_path("assets", "icons", f"{name}.svg")).convert_alpha()
        except Exception:
            surfaces[name] = None
    return surfaces


ICON_SURFACES = _load_icon_svgs()
_icon_cache = {}


def draw_icon(icon, center, color, size=10):
    """Desenha um icone carregado de assets/icons, escalado e tingido na cor pedida."""
    base = ICON_SURFACES.get(icon)
    if base is None:
        return

    cache_key = (icon, size, color)
    tinted = _icon_cache.get(cache_key)
    if tinted is None:
        tinted = pygame.transform.smoothscale(base, (size * 2, size * 2))
        tinted = tinted.copy()
        tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _icon_cache[cache_key] = tinted

    rect = tinted.get_rect(center=(int(center[0]), int(center[1])))
    canvas.blit(tinted, rect)


def draw_stage_icon(icon, center, size, alpha=255):
    """Desenha um icone COLORIDO sem tingir (ao contrario de draw_icon, que
    tinge icones monocromaticos) - usado nos cenarios decorativos dos mundos."""
    base = ICON_SURFACES.get(icon)
    if base is None:
        return
    size = max(1, int(size))
    scaled = pygame.transform.smoothscale(base, (size, size))
    if alpha < 255:
        scaled.set_alpha(max(0, alpha))
    rect = scaled.get_rect(center=(int(center[0]), int(center[1])))
    canvas.blit(scaled, rect)


# ===================== BOTAO / ABA / PAINEL / SLIDER =====================
def draw_button(rect, label, mouse_pos, key, dt, enabled=True, focused=False, icon=None):
    """Botao com hover animado (cresce/clareia suavemente), foco de teclado e barra de destaque."""
    hovering = enabled and (rect.collidepoint(mouse_pos) or focused)
    if hovering and not _was_hovering.get(key, False):
        audio.play(audio.hover_sound)
    _was_hovering[key] = hovering

    t = _hover_progress(key, hovering, dt) if enabled else 0.0

    grown = rect.inflate(int(8 * t), int(8 * t))

    shadow = pygame.Surface(grown.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=10)
    canvas.blit(shadow, grown.move(0, 4).topleft)

    color = config.BTN_DISABLED if not enabled else _lerp_color(config.BTN_NORMAL, config.BTN_HOVER, t)
    pygame.draw.rect(canvas, color, grown, border_radius=10)

    if enabled and t > 0.01:
        bar_h = int(grown.height * 0.6 * t)
        bar = pygame.Rect(grown.left + 6, grown.centery - bar_h // 2, 4, bar_h)
        pygame.draw.rect(canvas, config.ACCENT, bar, border_radius=2)

        border = pygame.Surface(grown.size, pygame.SRCALPHA)
        pygame.draw.rect(border, (*config.ACCENT, int(140 * t)), border.get_rect(), width=2, border_radius=10)
        canvas.blit(border, grown.topleft)

    label_color = config.WHITE if enabled else config.TEXT_MUTED
    if icon:
        draw_icon(icon, (grown.left + 34, grown.centery), label_color)
        text_surf = display.font_button.render(label, True, label_color)
        text_rect = text_surf.get_rect(midleft=(grown.left + 58, grown.centery))
        canvas.blit(text_surf, text_rect)
    else:
        draw_text(label, display.font_button, grown.centerx, grown.centery, center=True, color=label_color)


def draw_tab(rect, label, mouse_pos, key, dt, active, focused=False):
    """Item de aba (estilo sublinhado), usado no topo do painel de Opcoes."""
    hovering = rect.collidepoint(mouse_pos) or focused
    if hovering and not _was_hovering.get(key, False):
        audio.play(audio.hover_sound)
    _was_hovering[key] = hovering

    t = _hover_progress(key, hovering, dt)

    color = config.WHITE if (active or hovering) else config.TEXT_MUTED
    draw_text(label, display.font_button, rect.centerx, rect.centery, center=True, color=color)

    underline_w = rect.width if active else int(rect.width * t)
    if underline_w > 0:
        underline = pygame.Rect(0, 0, underline_w, 3)
        underline.midtop = (rect.centerx, rect.bottom - 8)
        pygame.draw.rect(canvas, config.ACCENT, underline, border_radius=2)


def draw_panel(rect, alpha=18):
    """Cartao translucido com borda suave, usado pra agrupar controles."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*config.PANEL_BORDER, alpha), panel.get_rect(), border_radius=14)
    pygame.draw.rect(panel, (*config.PANEL_BORDER, 40), panel.get_rect(), width=1, border_radius=14)
    canvas.blit(panel, rect.topleft)


def draw_slider(value_ratio, x, y, w):
    value_ratio = max(0.0, min(1.0, value_ratio))
    track = pygame.Rect(x, y - 3, w, 6)
    pygame.draw.rect(canvas, config.SLIDER_BG, track, border_radius=3)
    fill_w = int(w * value_ratio)
    if fill_w > 0:
        pygame.draw.rect(canvas, config.ACCENT, (x, y - 3, fill_w, 6), border_radius=3)
    handle_x = x + fill_w
    pygame.draw.circle(canvas, config.WHITE, (handle_x, y), 9)
    pygame.draw.circle(canvas, config.ACCENT, (handle_x, y), 9, 2)
