"""Composicao visual de cada tela do jogo: menu, opcoes, HUD, gameplay, pause
e game over. So desenham - a logica de clique/teclado mora em game/app.py.
"""
import math

import pygame

from . import config
from . import display
from . import entities
from . import layout
from . import music
from . import state
from . import visuals

canvas = display.canvas


def draw_menu(mouse_pos, dt):
    state.menu_time += dt

    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    visuals.draw_title_glow((config.WIDTH // 2, 155), state.menu_time)
    visuals.draw_text("MYSTICAL MELODY", display.font_title, config.WIDTH // 2, 165, center=True, shadow=True)
    visuals.draw_text("Desvie. Ataque. Sobreviva.", display.font_small, config.WIDTH // 2, 225,
                       center=True, color=config.TEXT_MUTED)
    visuals.draw_text(f"Recorde: {state.highscore}", display.font_small, config.WIDTH // 2, 260,
                       center=True, color=config.ACCENT)

    diff_label = config.DIFFICULTIES[state.settings["difficulty"]]["label"]
    visuals.draw_button(layout.difficulty_button(), f"DIFICULDADE: {diff_label}", mouse_pos,
                         "menu_difficulty", dt, focused=(0 == state.nav_index))

    for i, (key, rect) in enumerate(layout.menu_buttons().items()):
        visuals.draw_button(rect, config.MENU_LABELS[key], mouse_pos, f"menu_{key}", dt,
                             focused=(i + 1 == state.nav_index), icon=config.MENU_ICONS[key])

    visuals.draw_text("Setas + Enter, ou mouse", display.font_small, 20, config.HEIGHT - 32, color=config.TEXT_MUTED)
    visuals.draw_text("v1.0", display.font_small, config.WIDTH - 55, config.HEIGHT - 32, color=config.TEXT_MUTED)


def draw_options(mouse_pos, dt):
    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    visuals.draw_text("OPCOES", display.font_big, config.WIDTH // 2, 70, center=True, shadow=True)
    visuals.draw_text("ESC para voltar", display.font_small, config.WIDTH // 2, 104,
                       center=True, color=config.TEXT_MUTED)

    idx = 0   # acompanha a mesma ordem usada por layout.nav_items_for("options")

    for tab, rect in layout.options_tab_buttons().items():
        visuals.draw_tab(rect, config.OPTIONS_TAB_LABELS[tab], mouse_pos, f"tab_{tab}", dt,
                          active=(tab == state.options_tab), focused=(idx == state.nav_index))
        idx += 1

    panel_rect = pygame.Rect(140, 190, 1000, 370)
    visuals.draw_panel(panel_rect)

    if state.options_tab == "audio":
        visuals.draw_text("VOLUME", display.font_small, config.SLIDER_X, config.VOLUME_Y - 30, color=config.TEXT_MUTED)
        visuals.draw_slider(state.settings["volume"], config.SLIDER_X, config.VOLUME_Y, config.SLIDER_W)
        vol_text = "Mudo" if state.settings["muted"] else f"{int(state.settings['volume'] * 100)}%"
        visuals.draw_text(vol_text, display.font, config.SLIDER_X + config.SLIDER_W + 20, config.VOLUME_Y - 12)

        visuals.draw_text("SENSIBILIDADE", display.font_small, config.SLIDER_X, config.SENS_Y - 30, color=config.TEXT_MUTED)
        visuals.draw_slider(state.settings["sensibilidade"] / 3, config.SLIDER_X, config.SENS_Y, config.SLIDER_W)
        visuals.draw_text(f"{state.settings['sensibilidade']:.1f}x", display.font,
                           config.SLIDER_X + config.SLIDER_W + 20, config.SENS_Y - 12)

        b = layout.audio_buttons()
        visuals.draw_button(b["mute"], f"SOM: {'MUDO' if state.settings['muted'] else 'ATIVO'}", mouse_pos,
                             "audio_mute", dt, focused=(idx == state.nav_index))
        idx += 1
        visuals.draw_button(b["test"], "TESTAR SOM", mouse_pos, "audio_test", dt, focused=(idx == state.nav_index))
        idx += 1

    elif state.options_tab == "controles":
        visuals.draw_text("Clique numa tecla e pressione o novo botao (ESC cancela) - Atacar: Mouse (fixo)",
                           display.font_small, config.WIDTH // 2, 205, center=True, color=config.TEXT_MUTED)
        for key, rect in layout.controles_buttons().items():
            if key == "reset":
                label = "RESTAURAR PADRAO"
            elif state.rebinding == key:
                label = f"{key.upper()}: ..."
            else:
                label = f"{key.upper()}: {pygame.key.name(state.settings['keys'][key]).upper()}"
            visuals.draw_button(rect, label, mouse_pos, f"controles_{key}", dt, focused=(idx == state.nav_index))
            idx += 1

    elif state.options_tab == "video":
        res_locked = state.settings["mode"] != "windowed"
        b = layout.video_content_buttons()
        if res_locked:
            visuals.draw_button(b["res"], "RES: (modo de tela)", mouse_pos, "video_res", dt,
                                 enabled=False, focused=(idx == state.nav_index))
        else:
            w, h = state.settings["resolution"]
            visuals.draw_button(b["res"], f"RES: {w}x{h}", mouse_pos, "video_res", dt, focused=(idx == state.nav_index))
        idx += 1
        visuals.draw_button(b["mode"], f"MODO: {state.settings['mode'].upper()}", mouse_pos, "video_mode", dt,
                             focused=(idx == state.nav_index))
        idx += 1
        visuals.draw_button(b["fps"], f"FPS: {'ON' if state.settings['show_fps'] else 'OFF'}", mouse_pos,
                             "video_fps", dt, focused=(idx == state.nav_index))
        idx += 1

    elif state.options_tab == "ranking":
        visuals.draw_text("MELHORES PONTUACOES", display.font, config.WIDTH // 2, 220, center=True)
        if not state.leaderboard:
            visuals.draw_text("Ninguem pontuou ainda - jogue uma partida!", display.font_small,
                               config.WIDTH // 2, 280, center=True, color=config.TEXT_MUTED)
        else:
            y = 270
            for i, entry in enumerate(state.leaderboard, start=1):
                diff_label = config.DIFFICULTIES.get(entry["difficulty"], {}).get("label", "?")
                line = f"{i}.  {entry['name']}   -   {entry['score']} pts   ({diff_label})"
                color = config.ACCENT if i == 1 else config.WHITE
                visuals.draw_text(line, display.font, config.WIDTH // 2, y, center=True, color=color)
                y += 42

    elif state.options_tab == "creditos":
        visuals.draw_text("MYSTICAL MELODY", display.font, config.WIDTH // 2, 260, center=True)
        visuals.draw_text("Criado por Pedro Pinho e Fº Ivanildo", display.font_small, config.WIDTH // 2, 300,
                           center=True, color=config.TEXT_MUTED)
        visuals.draw_text("Feito com Python + Pygame", display.font_small, config.WIDTH // 2, 330,
                           center=True, color=config.TEXT_MUTED)
        visuals.draw_text("Icones: Feather Icons (MIT) e Twemoji (CC-BY 4.0)", display.font_small,
                           config.WIDTH // 2, 360, center=True, color=config.TEXT_MUTED)
        visuals.draw_text("Musica do Mundo Jazzy: composta por codigo, 100% original",
                           display.font_small, config.WIDTH // 2, 385, center=True, color=config.TEXT_MUTED)
        visuals.draw_text("Versao 1.0", display.font_small, config.WIDTH // 2, 420,
                           center=True, color=config.TEXT_MUTED)

    visuals.draw_button(layout.options_voltar_button(), "VOLTAR", mouse_pos, "options_voltar", dt,
                         focused=(idx == state.nav_index))


def draw_hud(run):
    if run.get("target_score") is not None:
        visuals.draw_text(f"Score: {run['score']} / {run['target_score']}", display.font, 15, 15)
    else:
        visuals.draw_text(f"Score: {run['score']}", display.font, 15, 15)
    visuals.draw_text(f"Vidas: {run['lives']}", display.font, config.WIDTH - 150, 15)
    visuals.draw_text("Mouse: Atacar", display.font_small, 15, config.HEIGHT - 30, color=config.TEXT_MUTED)
    visuals.draw_text("ESC: Pausar", display.font_small, config.WIDTH - 140, config.HEIGHT - 30, color=config.TEXT_MUTED)
    if state.settings["show_fps"]:
        visuals.draw_text(f"FPS: {int(display.clock.get_fps())}", display.font_small, config.WIDTH // 2, 15,
                           center=True, color=config.TEXT_MUTED)


def draw_jazzy_stage():
    """Fundo decorativo do Mundo Jazzy: instrumentos animados no ritmo da
    musica (mesmo tempo/compasso de game/music.py, pra ficarem sincronizados)."""
    t = pygame.time.get_ticks() / 1000.0
    beat_phase = (t % music.BEAT) / music.BEAT
    chord_phase = (t % music.CHORD_DUR) / music.CHORD_DUR

    canvas.fill(config.JAZZY_BG)

    # Bateria: uma "batida" curta a cada tempo (decai rapido, tipo taco no prato).
    drum_pulse = max(0.0, 1 - beat_phase * 4) * 14
    visuals.draw_stage_icon("drum", (config.WIDTH - 100, config.HEIGHT - 100), 90 + drum_pulse)

    # Piano: um pulso mais lento a cada troca de acorde (nasce forte, some).
    piano_pulse = max(0.0, 1 - chord_phase * 2) * 10
    visuals.draw_stage_icon("piano", (100, config.HEIGHT - 100), 96 + piano_pulse)

    # Sax e trompete balancam suavemente, fora de fase um do outro.
    sway = math.sin(t * 2 * math.pi / music.BEAT) * 8
    visuals.draw_stage_icon("saxophone", (100, 100 + sway), 78)
    visuals.draw_stage_icon("trumpet", (config.WIDTH - 100, 100 - sway), 78)


def draw_gameplay(run, attack_pos):
    if run.get("world") == "jazzy":
        draw_jazzy_stage()
    else:
        canvas.fill(config.BG_GAME)
    for enemy in run["enemies"]:
        enemy.draw(canvas)
    pygame.draw.circle(canvas, config.PLAYER_COLOR,
                        (int(run["player"].x), int(run["player"].y)),
                        int(run["player_size"]))

    # A mira pulsa em cima da batida quando ha musica tocando - da uma pista
    # visual de QUANDO acertar pra ganhar o bonus de ritmo, sem precisar so
    # confiar no ouvido.
    strength = music.beat_strength()
    radius = config.ATTACK_RADIUS
    if strength is not None:
        radius = int(config.ATTACK_RADIUS * (1.0 + 0.5 * strength))
    pygame.draw.circle(canvas, config.ATTACK_COLOR, (int(attack_pos.x), int(attack_pos.y)), radius)

    for popup in run.get("hit_popups", []):
        t = popup["age"] / entities.POPUP_LIFETIME
        alpha = int(255 * (1 - t))
        y_offset = t * entities.POPUP_RISE_SPEED
        visuals.draw_text(popup["text"], display.font, popup["pos"].x, popup["pos"].y - y_offset,
                           center=True, color=popup["color"], alpha=alpha)

    draw_hud(run)


def draw_pause(mouse_pos, dt):
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    canvas.blit(overlay, (0, 0))
    visuals.draw_text("PAUSADO", display.font_big, config.WIDTH // 2, 200, center=True, shadow=True)
    labels = {"resume": "CONTINUAR", "options": "OPCOES", "menu": "MENU"}
    for i, (key, rect) in enumerate(layout.pause_buttons().items()):
        visuals.draw_button(rect, labels[key], mouse_pos, f"pause_{key}", dt, focused=(i == state.nav_index))


def draw_gameover(mouse_pos, run, dt):
    canvas.fill(config.BG_GAME)
    visuals.draw_text("GAME OVER", display.font_big, config.WIDTH // 2, 180, center=True, shadow=True)
    visuals.draw_text(f"Pontuacao final: {run['score']}", display.font, config.WIDTH // 2, 250,
                       center=True, color=config.TEXT_MUTED)

    if run.get("target_score") is not None:
        visuals.draw_text(f"Meta do nivel: {run['target_score']} pontos", display.font, config.WIDTH // 2, 285,
                           center=True, color=config.TEXT_MUTED)
    elif run["score"] > 0 and run["score"] >= state.highscore:
        visuals.draw_text("NOVO RECORDE!", display.font, config.WIDTH // 2, 285, center=True, color=config.ACCENT)
    else:
        visuals.draw_text(f"Recorde: {state.highscore}", display.font, config.WIDTH // 2, 285,
                           center=True, color=config.TEXT_MUTED)

    for i, (key, rect) in enumerate(layout.gameover_buttons().items()):
        visuals.draw_button(rect, "JOGAR DE NOVO" if key == "retry" else "MENU", mouse_pos,
                             f"gameover_{key}", dt, focused=(i == state.nav_index))


def draw_enter_name(run, dt):
    """Tela mostrada quando a pontuacao entra pro top 5 do ranking local."""
    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    visuals.draw_text("NOVO RECORDE NO RANKING!", display.font_big, config.WIDTH // 2, 210,
                       center=True, shadow=True, color=config.ACCENT)
    visuals.draw_text(f"Pontuacao: {run['score']}", display.font, config.WIDTH // 2, 270,
                       center=True, color=config.TEXT_MUTED)
    visuals.draw_text("Digite seu nome e aperte Enter:", display.font_small, config.WIDTH // 2, 320,
                       center=True, color=config.TEXT_MUTED)

    box = pygame.Rect(0, 0, 420, 60)
    box.center = (config.WIDTH // 2, 380)
    visuals.draw_panel(box, alpha=30)
    cursor = "|" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
    visuals.draw_text(state.name_input + cursor, display.font_big, box.centerx, box.centery, center=True)

    visuals.draw_text("ESC para pular", display.font_small, config.WIDTH // 2, 450,
                       center=True, color=config.TEXT_MUTED)


def _orbit_items(center, radius, t, icons, speed=0.7):
    """Posicoes dos icones girando ao redor de um orbe, numa orbita elipsada
    (achatada na vertical) pra parecer visto de um leve angulo - cada um
    tambem devolve sua 'profundidade' (>0 na frente do orbe, <0 atras)."""
    cx, cy = center
    n = len(icons)
    items = []
    for i, name in enumerate(icons):
        angle = t * speed + i * (2 * math.pi / n)
        depth = math.sin(angle)   # -1 (bem atras) .. 1 (bem na frente)
        x = cx + math.cos(angle) * radius
        y = cy + depth * radius * 0.45
        size = 22 + depth * 7
        items.append((name, (x, y), depth, size))
    return items


def _draw_orbit(center, radius, t, icons, behind):
    for name, pos, depth, size in _orbit_items(center, radius, t, icons):
        if (depth < 0) == behind:
            visuals.draw_stage_icon(name, pos, size)


def draw_world_select(mouse_pos, dt):
    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    visuals.draw_text("MODO HISTORIA", display.font_big, config.WIDTH // 2, 90, center=True, shadow=True)
    visuals.draw_text("Escolha um mundo", display.font_small, config.WIDTH // 2, 135,
                       center=True, color=config.TEXT_MUTED)

    t = pygame.time.get_ticks() / 1000.0
    positions = layout.world_slot_positions()
    r = layout.WORLD_ORB_RADIUS
    orbit_r = r + 22
    idx = 0
    for i, (cx, cy) in enumerate(positions):
        if i < len(config.WORLD_ORDER):
            world_id = config.WORLD_ORDER[i]
            world = config.WORLDS[world_id]
            key = f"world_{world_id}"
            rect = pygame.Rect(int(cx - r), int(cy - r), r * 2, r * 2)
            hovering = rect.collidepoint(mouse_pos) or (idx == state.nav_index)
            hover_t = visuals.hover_progress_for(key, hovering, dt)

            icons = world.get("orbit_icons", [])
            _draw_orbit((cx, cy), orbit_r, t, icons, behind=True)
            _, oy, _ = visuals.draw_world_orb((cx, cy), r, world["color"], mouse_pos, hover_t,
                                               style=world.get("orb_style", "sphere"))
            _draw_orbit((cx, cy), orbit_r, t, icons, behind=False)

            visuals.draw_text(world["name"].upper(), display.font_button, cx, oy, center=True, shadow=True)
            unlocked = state.progress[world_id]["unlocked"]
            total = len(world["levels"])
            visuals.draw_text(f"{unlocked}/{total}", display.font_small, cx, oy + r + 26,
                               center=True, color=config.TEXT_MUTED)
            idx += 1
        else:
            visuals.draw_world_orb((cx, cy), r, (60, 60, 72), mouse_pos, 0.0, locked=True)
            visuals.draw_text("?", display.font_title, cx, cy, center=True, color=config.TEXT_MUTED)
            visuals.draw_text("EM BREVE", display.font_small, cx, cy + r + 26,
                               center=True, color=config.TEXT_MUTED)

    visuals.draw_button(layout.historia_voltar_button(), "VOLTAR", mouse_pos, "world_voltar", dt,
                         focused=(idx == state.nav_index))

    if state.portal_transition is not None:
        draw_portal_wipe(dt)


def draw_portal_wipe(dt):
    """Animacao de 'entrar no mundo': o orbe clicado se expande ate cobrir a
    tela (fase 1), depois o nome do mundo aparece por cima (fase 2), e ai
    troca pra selecao de nivel."""
    trans = state.portal_transition
    t = min(1.0, trans["t"] / state.PORTAL_DURATION)

    EXPAND_FRACTION = 0.7   # 70% do tempo pra crescer, 30% pro texto aparecer
    expand_t = min(1.0, t / EXPAND_FRACTION)
    eased = expand_t * expand_t * (3 - 2 * expand_t)   # smoothstep: comeca e termina suave

    cx, cy = trans["center"]
    corners = ((0, 0), (config.WIDTH, 0), (0, config.HEIGHT), (config.WIDTH, config.HEIGHT))
    max_r = max(math.hypot(cx - x, cy - y) for x, y in corners)
    r = trans["start_r"] + (max_r - trans["start_r"]) * eased

    world = config.WORLDS[state.current_world]
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(overlay, (*world["color"], 255), trans["center"], int(r))
    canvas.blit(overlay, (0, 0))

    if t > EXPAND_FRACTION:
        alpha = int(255 * (t - EXPAND_FRACTION) / (1 - EXPAND_FRACTION))
        visuals.draw_text(world["name"].upper(), display.font_title, config.WIDTH // 2, config.HEIGHT // 2,
                           center=True, color=config.WHITE, alpha=alpha)


def draw_level_select(mouse_pos, dt):
    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    world = config.WORLDS[state.current_world]
    unlocked = state.progress[state.current_world]["unlocked"]

    visuals.draw_text(f"MUNDO: {world['name'].upper()}", display.font_big, config.WIDTH // 2, 70,
                       center=True, shadow=True)
    visuals.draw_text("Escolha um nivel", display.font_small, config.WIDTH // 2, 112,
                       center=True, color=config.TEXT_MUTED)

    positions = layout.level_path_positions(state.current_world)
    r = layout.LEVEL_ORB_RADIUS

    # Trilha conectando os niveis - acesa nos trechos ja percorridos.
    for i in range(len(positions) - 1):
        color = world["color"] if (i + 2) <= unlocked else config.SLIDER_BG
        pygame.draw.line(canvas, color, positions[i], positions[i + 1], 6)

    idx = 0
    for level_num, rect in layout.level_select_buttons(state.current_world).items():
        pos = positions[level_num - 1]
        is_unlocked = level_num <= unlocked
        key = f"level_{level_num}"
        hovering = is_unlocked and (rect.collidepoint(mouse_pos) or idx == state.nav_index)
        hover_t = visuals.hover_progress_for(key, hovering, dt, play_sound=is_unlocked)

        _, oy, _ = visuals.draw_world_orb(pos, r, world["color"], mouse_pos, hover_t, locked=not is_unlocked)
        if is_unlocked:
            visuals.draw_text(str(level_num), display.font_big, pos[0], oy, center=True, shadow=True)
            target = world["levels"][level_num - 1]
            visuals.draw_text(f"{target}pts", display.font_small, pos[0], oy + r + 20,
                               center=True, color=config.TEXT_MUTED)
        else:
            visuals.draw_lock_icon(pos, r * 0.45, config.TEXT_MUTED)
        idx += 1

    visuals.draw_button(layout.historia_voltar_button(), "VOLTAR", mouse_pos, "level_voltar", dt,
                         focused=(idx == state.nav_index))


def draw_level_complete(mouse_pos, run, dt):
    canvas.blit(visuals.MENU_BG_SURF, (0, 0))
    visuals.update_particles(dt)
    visuals.draw_particles(canvas)

    world = config.WORLDS[state.current_world]
    total = len(world["levels"])
    is_last = state.current_level >= total

    if is_last:
        title = f"MUNDO {world['name'].upper()} CONCLUIDO!"
    else:
        title = f"NIVEL {state.current_level} CONCLUIDO!"
    visuals.draw_text(title, display.font_big, config.WIDTH // 2, 220, center=True, shadow=True, color=config.ACCENT)
    visuals.draw_text(f"Pontuacao: {run['score']}", display.font, config.WIDTH // 2, 290,
                       center=True, color=config.TEXT_MUTED)

    labels = {"next": "PROXIMO NIVEL", "menu": "MENU"}
    for i, (key, rect) in enumerate(layout.level_complete_buttons(is_last).items()):
        visuals.draw_button(rect, labels[key], mouse_pos, f"levelcomplete_{key}", dt, focused=(i == state.nav_index))
