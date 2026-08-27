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


def hover_progress_for(key, hovering, dt, play_sound=True):
    """Versao publica de _hover_progress, pra elementos customizados (como os
    orbes de mundo/nivel) que nao passam por draw_button/draw_tab."""
    if hovering and not _was_hovering.get(key, False) and play_sound:
        audio.play(audio.hover_sound)
    _was_hovering[key] = hovering
    return _hover_progress(key, hovering, dt)


# ===================== TEXTO =====================
def draw_text(text, fnt, x, y, center=False, color=config.WHITE, shadow=False, alpha=None):
    if shadow:
        shadow_render = fnt.render(text, True, config.BLACK)
        shadow_render.set_alpha(120 if alpha is None else max(0, min(120, int(alpha))))
        srect = shadow_render.get_rect()
        if center:
            srect.center = (x + 3, y + 3)
        else:
            srect.topleft = (x + 3, y + 3)
        canvas.blit(shadow_render, srect)

    render = fnt.render(text, True, color)
    if alpha is not None:
        render.set_alpha(max(0, min(255, int(alpha))))
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
    names = ("play", "settings", "power", "map", "lock", "saxophone", "piano", "trumpet", "drum")
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


# ===================== ORBES 2.5D (selecao de mundo/nivel) =====================
_orb_cache = {}


def _get_orb_base(radius, color):
    """Esfera pre-renderizada (sombreada como se a luz viesse de cima-esquerda),
    cacheada por (raio, cor) - so a posicao do brilho movel muda por frame."""
    key = ("sphere", radius, color)
    surf = _orb_cache.get(key)
    if surf is not None:
        return surf

    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (radius, radius), radius)
    _apply_sphere_shading(surf, radius)

    _orb_cache[key] = surf
    return surf


def _apply_sphere_shading(surf, radius):
    """Sombreamento (luz vindo de cima-esquerda) + aro de contra-luz, aplicado
    por cima de qualquer textura circular ja desenhada em `surf`. Multiplica
    por um degrade CINZA OPACO (nunca vaza alpha pra fora do circulo base,
    porque BLEND_RGBA_MULT com alpha=0 la fora continua dando alpha=0)."""
    size = surf.get_width()
    shade = pygame.Surface((size, size), pygame.SRCALPHA)
    shade.fill((255, 255, 255, 255))
    hl_center = (int(radius * 0.62), int(radius * 0.58))
    for rr in range(radius, 0, -2):
        t = rr / radius
        gray = int(255 - 120 * t)
        pygame.draw.circle(shade, (gray, gray, gray, 255), hl_center, rr)
    surf.blit(shade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    pygame.draw.circle(surf, (255, 255, 255, 40), (radius, radius), radius, 3)


def _get_vinyl_orb_base(radius, label_color):
    """Disco de vinil: corpo escuro com sulcos concentricos e um rotulo
    colorido no centro (onde o nome do mundo e escrito por cima, depois)."""
    key = ("vinyl", radius, label_color)
    surf = _orb_cache.get(key)
    if surf is not None:
        return surf

    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (22, 20, 24), (radius, radius), radius)

    # Sulcos: aneis finos alternando um tom bem sutil de cinza.
    groove_start = int(radius * 0.42)
    for rr in range(radius - 4, groove_start, -3):
        tone = 34 if (rr // 3) % 2 == 0 else 24
        pygame.draw.circle(surf, (tone, tone, tone + 3), (radius, radius), rr, 1)

    # Rotulo central (cor do mundo) + furinho.
    label_r = int(radius * 0.38)
    pygame.draw.circle(surf, label_color, (radius, radius), label_r)
    pygame.draw.circle(surf, (20, 20, 24), (radius, radius), max(2, int(radius * 0.05)))

    _apply_sphere_shading(surf, radius)

    _orb_cache[key] = surf
    return surf


def _draw_vinyl_shine(center, r):
    """Reflexo girando sobre o disco - um traco de luz cruzando o centro que
    roda com o tempo, dando a sensacao de vinil rodando na vitrola."""
    cx, cy = center
    t = pygame.time.get_ticks() / 1000.0
    angle = t * 1.4
    width = max(2, int(r * 0.05))
    shine = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    for offset in (0, math.pi):
        a = angle + offset
        end = (r + math.cos(a) * r * 0.94, r + math.sin(a) * r * 0.94)
        pygame.draw.line(shine, (255, 255, 255, 45), (r, r), end, width)
    canvas.blit(shine, (int(cx - r), int(cy - r)))


def draw_world_orb(center, radius, color, mouse_pos, hover_t, locked=False, style="sphere"):
    """Portal circular com efeito 2.5D: sombra projetada, esfera sombreada e
    um brilho que acompanha o mouse (parallax), alem de leve elevacao no hover.

    Devolve (x, y, raio) do centro onde a esfera acabou desenhada - util pra
    quem quiser escrever um numero/texto por cima, ja ajustado pela elevacao.
    """
    cx, cy = center
    lift = hover_t * 10
    draw_cy = cy - lift
    r = int(radius * (1.0 + 0.10 * hover_t))

    # Sombra projetada no "chao" (fixa em cy, nao sobe com o orbe).
    shadow_w, shadow_h = int(r * 1.5), max(6, int(r * 0.5))
    shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 100), shadow.get_rect())
    canvas.blit(shadow, (cx - shadow_w // 2, int(cy + radius * 0.55)))

    if locked:
        orb = _get_orb_base(r, (60, 60, 72))
    elif style == "vinyl":
        orb = _get_vinyl_orb_base(r, color)
    else:
        orb = _get_orb_base(r, color)
    orb_rect = orb.get_rect(center=(int(cx), int(draw_cy)))
    canvas.blit(orb, orb_rect)

    if not locked:
        if style == "vinyl":
            _draw_vinyl_shine((cx, draw_cy), r)

        dx, dy = mouse_pos[0] - cx, mouse_pos[1] - draw_cy
        dist = math.hypot(dx, dy)
        max_shift = r * 0.2
        if dist > 1:
            shift_x = (dx / dist) * min(max_shift, dist * 0.12)
            shift_y = (dy / dist) * min(max_shift, dist * 0.12)
        else:
            shift_x = shift_y = 0.0
        hl_r = max(2, int(r * 0.22))
        highlight = pygame.Surface((hl_r * 2, hl_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255, 255, 255, 90), (hl_r, hl_r), hl_r)
        hpos = (cx - r * 0.35 + shift_x, draw_cy - r * 0.4 + shift_y)
        canvas.blit(highlight, highlight.get_rect(center=hpos))

    return (cx, draw_cy, r)


def draw_lock_icon(center, size, color):
    """Cadeado - agora um icone vetorial de verdade (Feather Icons), tingido
    na cor pedida do mesmo jeito que os icones de botao."""
    draw_icon("lock", center, color, size=max(4, int(size * 0.5)))


def _star_points(center, outer_r, inner_r):
    """5 pontas de estrela alternando raio externo/interno - comeca apontando
    pra cima. Desenhada na hora (poligono), sem depender de nenhuma fonte ter
    o glifo de estrela - varias fontes do sistema nao tem (viram caixinha
    vazia), entao um poligono e mais confiavel."""
    cx, cy = center
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return points


def draw_star(center, size, filled, color=(255, 205, 60), empty_color=(70, 68, 82)):
    """Uma estrela de 5 pontas: preenchida (conquistada) ou so o contorno
    (ainda nao conquistada)."""
    pts = _star_points(center, size, size * 0.42)
    if filled:
        pygame.draw.polygon(canvas, color, pts)
    else:
        pygame.draw.polygon(canvas, empty_color, pts, width=2)


def draw_star_rating(center, stars, size=11, gap=6, color=(255, 205, 60), empty_color=(70, 68, 82)):
    """Desenha 3 estrelas lado a lado, centralizadas em `center` - as
    primeiras `stars` vem preenchidas, o resto so contorno."""
    cx, cy = center
    total_w = 3 * (size * 2) + 2 * gap
    x0 = cx - total_w / 2 + size
    for i in range(3):
        star_center = (x0 + i * (size * 2 + gap), cy)
        draw_star(star_center, size, filled=(i < stars), color=color, empty_color=empty_color)
