"""Loop principal: eventos (mouse/teclado), atualizacao e desenho de cada tela.

Este e o unico modulo que "conhece" todos os outros - ele os liga.
"""
import pygame

from . import audio
from . import config
from . import display
from . import entities
from . import gameplay
from . import layout
from . import music
from . import screens
from . import state


def main():
    display.apply_video()   # aplica resolucao/modo salvos (se houver) antes de abrir o menu

    # Primeira vez que o jogo abre: mostra "Como Jogar" antes do menu, ja que o
    # ataque por proximidade do mouse nao e obvio sem alguem explicar.
    if state.settings["seen_tutorial"]:
        current_state = "menu"
    else:
        current_state = "tutorial"
        state.tutorial_return_to = "menu"
    prev_state = current_state
    run = entities.new_run()
    running = True

    FADE_TIME = 0.22
    fade_timer = 0.0
    last_mouse_pos = None

    def activate(pos):
        """Executa a acao do botao em 'pos'. Reaproveitado tanto pelo clique do mouse
        quanto pelo Enter/Espaco do teclado, pra nao duplicar a logica de cada tela."""
        nonlocal current_state, run, running

        if state.portal_transition is not None:
            return False   # ignora cliques/Enter ate a animacao de entrada terminar

        acted = False

        if current_state == "menu":
            if layout.difficulty_button().collidepoint(pos):
                order = config.DIFFICULTY_ORDER
                idx = (order.index(state.settings["difficulty"]) + 1) % len(order)
                state.settings["difficulty"] = order[idx]
                state.save_settings()
                acted = True
            else:
                b = layout.menu_buttons()
                if b["play"].collidepoint(pos):
                    music.stop_music()
                    run = entities.new_run()
                    current_state = "playing"
                    acted = True
                elif b["historia"].collidepoint(pos):
                    current_state = "world_select"
                    acted = True
                elif b["options"].collidepoint(pos):
                    state.options_return_to = "menu"
                    current_state = "options"
                    acted = True
                elif b["quit"].collidepoint(pos):
                    running = False
                    acted = True
                elif layout.menu_help_button().collidepoint(pos):
                    state.tutorial_return_to = "menu"
                    current_state = "tutorial"
                    acted = True

        elif current_state == "tutorial":
            if layout.tutorial_button().collidepoint(pos):
                state.settings["seen_tutorial"] = True
                state.save_settings()
                current_state = state.tutorial_return_to
                acted = True

        elif current_state == "world_select":
            if layout.historia_voltar_button().collidepoint(pos):
                current_state = "menu"
                acted = True
            else:
                for world_id, rect in layout.world_buttons().items():
                    if rect.collidepoint(pos):
                        # Nao troca de tela ainda - a animacao de "entrar no
                        # portal" cuida disso quando terminar (ver UPDATE).
                        state.current_world = world_id
                        state.portal_transition = {"center": rect.center, "start_r": rect.width // 2, "t": 0.0}
                        acted = True
                        break

        elif current_state == "level_select":
            if layout.historia_voltar_button().collidepoint(pos):
                current_state = "world_select"
                acted = True
            else:
                world = config.WORLDS[state.current_world]
                unlocked = state.progress[state.current_world]["unlocked"]
                for level_num, rect in layout.level_select_buttons(state.current_world).items():
                    if rect.collidepoint(pos) and level_num <= unlocked:
                        state.current_level = level_num
                        level_data = world["levels"][level_num - 1]
                        run = entities.new_run(target_score=level_data["target"], world=state.current_world,
                                                level_num=level_num, enemy_kinds=level_data["enemies"])
                        music.play_world_music(state.current_world, level_num=level_num)
                        current_state = "playing"
                        acted = True
                        break

        elif current_state == "level_complete":
            world = config.WORLDS[state.current_world]
            total = len(world["levels"])
            is_last = state.current_level >= total
            b = layout.level_complete_buttons(is_last)
            if not is_last and b["next"].collidepoint(pos):
                state.current_level += 1
                level_data = world["levels"][state.current_level - 1]
                run = entities.new_run(target_score=level_data["target"], world=state.current_world,
                                        level_num=state.current_level, enemy_kinds=level_data["enemies"])
                music.play_world_music(state.current_world, level_num=state.current_level)
                current_state = "playing"
                acted = True
            elif b["menu"].collidepoint(pos):
                current_state = "menu"
                acted = True

        elif current_state == "options":
            if layout.options_voltar_button().collidepoint(pos):
                current_state = state.options_return_to
                acted = True
            else:
                tabs = layout.options_tab_buttons()
                matched_tab = next((k for k, r in tabs.items() if r.collidepoint(pos)), None)
                if matched_tab:
                    if matched_tab != state.options_tab:
                        state.rebinding = None   # trocar de aba cancela uma reatribuicao em andamento
                        state.nav_index = 0
                    state.options_tab = matched_tab
                    acted = True
                elif state.options_tab == "audio":
                    b = layout.audio_buttons()
                    if b["mute"].collidepoint(pos):
                        state.settings["muted"] = not state.settings["muted"]
                        state.save_settings()
                        music.update_music_volume()
                        acted = True
                    elif b["test"].collidepoint(pos):
                        audio.play(audio.hit_sound)
                        acted = True
                elif state.options_tab == "controles":
                    b = layout.controles_buttons()
                    if b["reset"].collidepoint(pos):
                        state.settings["keys"] = dict(state.DEFAULT_KEYS)
                        state.rebinding = None
                        state.save_settings()
                        acted = True
                    else:
                        for key in ("up", "down", "left", "right"):
                            if b[key].collidepoint(pos):
                                state.rebinding = key
                                acted = True
                                break
                elif state.options_tab == "video":
                    b = layout.video_content_buttons()
                    if b["res"].collidepoint(pos) and state.settings["mode"] == "windowed":
                        state.res_index = (state.res_index + 1) % len(state.resolutions)
                        state.settings["resolution"] = state.resolutions[state.res_index]
                        display.apply_video()
                        state.save_settings()
                        acted = True
                    elif b["mode"].collidepoint(pos):
                        state.mode_index = (state.mode_index + 1) % len(state.modes)
                        state.settings["mode"] = state.modes[state.mode_index]
                        display.apply_video()
                        state.save_settings()
                        acted = True
                    elif b["fps"].collidepoint(pos):
                        state.settings["show_fps"] = not state.settings["show_fps"]
                        state.save_settings()
                        acted = True

        elif current_state == "paused":
            b = layout.pause_buttons()
            if b["resume"].collidepoint(pos):
                current_state = "playing"
                acted = True
            elif b["options"].collidepoint(pos):
                state.options_return_to = "paused"
                current_state = "options"
                acted = True
            elif b["menu"].collidepoint(pos):
                music.stop_music()
                current_state = "menu"
                acted = True

        elif current_state == "gameover":
            b = layout.gameover_buttons()
            if b["retry"].collidepoint(pos):
                # Preserva o modo da tentativa anterior: Arcade continua Arcade,
                # e um nivel do Modo Historia tenta o mesmo nivel de novo (mesmos
                # inimigos, mesmo andamento de musica).
                run = entities.new_run(target_score=run["target_score"], world=run["world"],
                                        level_num=run["level_num"], enemy_kinds=run["enemy_kinds"])
                if run["world"] is not None:
                    music.play_world_music(run["world"], level_num=run["level_num"])
                current_state = "playing"
                acted = True
            elif b["menu"].collidepoint(pos):
                current_state = "menu"
                acted = True

        if acted:
            audio.play(audio.click_sound)
        return acted

    while running:
        dt = display.clock.tick(config.FPS) / 1000
        mouse_pos = display.mouse_to_canvas()

        # --------------- EVENTOS ---------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif current_state == "enter_name" and event.type == pygame.KEYDOWN:
                # Tela de digitar nome: captura TODO keydown enquanto ativa, sem
                # deixar as regras de navegacao/rebind das outras telas competirem.
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    state.add_leaderboard_entry(state.name_input, run["score"], state.settings["difficulty"])
                    current_state = "gameover"
                elif event.key == pygame.K_ESCAPE:
                    state.add_leaderboard_entry("JOGADOR", run["score"], state.settings["difficulty"])
                    current_state = "gameover"
                elif event.key == pygame.K_BACKSPACE:
                    state.name_input = state.name_input[:-1]
                elif event.unicode and event.unicode.isprintable() and len(state.name_input) < 12:
                    state.name_input += event.unicode

            elif event.type == pygame.KEYDOWN and state.rebinding:
                if event.key == pygame.K_ESCAPE:
                    state.rebinding = None   # ESC cancela a reatribuicao sem mudar nada
                else:
                    # Se a tecla nova ja pertence a outra acao, troca as duas (evita duas
                    # direcoes presas na mesma tecla).
                    old_key = state.settings["keys"][state.rebinding]
                    conflict = next((a for a, k in state.settings["keys"].items()
                                      if k == event.key and a != state.rebinding), None)
                    state.settings["keys"][state.rebinding] = event.key
                    if conflict:
                        state.settings["keys"][conflict] = old_key
                    state.rebinding = None
                    state.save_settings()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if current_state == "playing":
                    current_state = "paused"
                elif current_state == "paused":
                    current_state = "playing"
                elif current_state == "options":
                    current_state = state.options_return_to
                elif current_state == "tutorial":
                    state.settings["seen_tutorial"] = True
                    state.save_settings()
                    current_state = state.tutorial_return_to
                elif current_state == "world_select":
                    current_state = "menu"
                elif current_state == "level_select":
                    current_state = "world_select"

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                items = layout.nav_items_for(current_state)
                if items:
                    state.nav_index = (state.nav_index - 1) % len(items)

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                items = layout.nav_items_for(current_state)
                if items:
                    state.nav_index = (state.nav_index + 1) % len(items)

            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                items = layout.nav_items_for(current_state)
                if items:
                    _, target_rect = items[state.nav_index % len(items)]
                    activate(target_rect.center)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_state == "options" and state.options_tab == "audio":
                    if (abs(mouse_pos[1] - config.VOLUME_Y) < 20
                            and config.SLIDER_X <= mouse_pos[0] <= config.SLIDER_X + config.SLIDER_W):
                        state.dragging_volume = True
                    if (abs(mouse_pos[1] - config.MUSIC_VOL_Y) < 20
                            and config.SLIDER_X <= mouse_pos[0] <= config.SLIDER_X + config.SLIDER_W):
                        state.dragging_music = True
                    if (abs(mouse_pos[1] - config.SENS_Y) < 20
                            and config.SLIDER_X <= mouse_pos[0] <= config.SLIDER_X + config.SLIDER_W):
                        state.dragging_sens = True
                activate(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if state.dragging_volume or state.dragging_music or state.dragging_sens:
                    state.save_settings()
                state.dragging_volume = False
                state.dragging_music = False
                state.dragging_sens = False

        # O foco de teclado acompanha o mouse, mas so quando ele de fato se move -
        # senao um mouse parado em cima de um botao trava a navegacao por seta.
        mouse_moved = (last_mouse_pos is None
                       or abs(mouse_pos[0] - last_mouse_pos[0]) > 0.5
                       or abs(mouse_pos[1] - last_mouse_pos[1]) > 0.5)
        last_mouse_pos = mouse_pos
        if mouse_moved:
            for i, (_, rect) in enumerate(layout.nav_items_for(current_state)):
                if rect.collidepoint(mouse_pos):
                    state.nav_index = i
                    break

        # Arraste dos sliders (so na aba de audio)
        if current_state == "options" and state.options_tab == "audio":
            if state.dragging_volume:
                state.settings["volume"] = max(0.0, min(1.0, (mouse_pos[0] - config.SLIDER_X) / config.SLIDER_W))
            if state.dragging_music:
                state.settings["music_volume"] = max(0.0, min(1.0, (mouse_pos[0] - config.SLIDER_X) / config.SLIDER_W))
                music.update_music_volume()   # da pra ouvir o ajuste na hora se ja tiver musica tocando
            if state.dragging_sens:
                state.settings["sensibilidade"] = max(
                    0.1, min(3.0, (mouse_pos[0] - config.SLIDER_X) / config.SLIDER_W * 3))

        # --------------- UPDATE ---------------
        if state.portal_transition is not None:
            state.portal_transition["t"] += dt
            if state.portal_transition["t"] >= state.PORTAL_DURATION:
                state.portal_transition = None
                current_state = "level_select"

        attack_pos = None
        if current_state == "playing":
            attack_pos = gameplay.update_gameplay(run, mouse_pos, dt)

            if run["target_score"] is not None and run["score"] >= run["target_score"]:
                # Modo Historia: bateu a meta do nivel -> vitoria, libera o proximo.
                music.stop_music()
                state.unlock_level(state.current_world, state.current_level)
                state.record_level_stars(state.current_world, state.current_level,
                                          entities.compute_stars(run))
                state.record_level_time(state.current_world, state.current_level, run["elapsed"])
                current_state = "level_complete"

            elif run["lives"] <= 0:
                music.stop_music()
                if run["target_score"] is None:
                    # Modo Arcade: recorde e ranking, como sempre.
                    if run["score"] > state.highscore:
                        state.highscore = run["score"]
                        state.save_highscore(state.highscore)
                    if state.qualifies_for_leaderboard(run["score"]):
                        state.name_input = ""
                        current_state = "enter_name"
                    else:
                        current_state = "gameover"
                else:
                    # Modo Historia: nao bateu a meta a tempo - so tenta de novo.
                    current_state = "gameover"

        # Transicao (flash rapido) toda vez que a tela muda + reset do foco de teclado
        if current_state != prev_state:
            fade_timer = FADE_TIME
            state.nav_index = 0
            prev_state = current_state
        elif fade_timer > 0:
            fade_timer = max(0.0, fade_timer - dt)

        # --------------- DRAW ---------------
        if current_state == "menu":
            screens.draw_menu(mouse_pos, dt)
        elif current_state == "tutorial":
            screens.draw_tutorial(mouse_pos, dt)
        elif current_state == "options":
            screens.draw_options(mouse_pos, dt)
        elif current_state == "world_select":
            screens.draw_world_select(mouse_pos, dt)
        elif current_state == "level_select":
            screens.draw_level_select(mouse_pos, dt)
        elif current_state == "level_complete":
            screens.draw_level_complete(mouse_pos, run, dt)
        elif current_state == "playing":
            screens.draw_gameplay(run, attack_pos)
        elif current_state == "paused":
            screens.draw_gameplay(run, pygame.Vector2(mouse_pos))
            screens.draw_pause(mouse_pos, dt)
        elif current_state == "gameover":
            screens.draw_gameover(mouse_pos, run, dt)
        elif current_state == "enter_name":
            screens.draw_enter_name(run, dt)

        if fade_timer > 0:
            alpha = int(255 * (fade_timer / FADE_TIME))
            fade_overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, alpha))
            display.canvas.blit(fade_overlay, (0, 0))

        display.present()

    pygame.quit()
