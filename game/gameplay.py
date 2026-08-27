"""Atualizacao por frame da partida em andamento: movimento, ataque e colisoes."""
import pygame

from . import audio
from . import config
from . import entities
from . import music
from . import state


def update_gameplay(run, mouse_pos, dt):
    # Movimento do jogador
    keys = pygame.key.get_pressed()
    speed = config.PLAYER_SPEED * state.settings["sensibilidade"] * dt
    k = state.settings["keys"]
    if keys[k["up"]]:    run["player"].y -= speed
    if keys[k["down"]]:  run["player"].y += speed
    if keys[k["left"]]:  run["player"].x -= speed
    if keys[k["right"]]: run["player"].x += speed

    size = run["player_size"]
    run["player"].x = max(size, min(run["player"].x, config.WIDTH - size))
    run["player"].y = max(size, min(run["player"].y, config.HEIGHT - size))

    # Hitbox do jogador agora acompanha o tamanho real
    player_rect = pygame.Rect(run["player"].x - size, run["player"].y - size, size * 2, size * 2)

    attack_pos = pygame.Vector2(mouse_pos)
    attack_rect = pygame.Rect(attack_pos.x - config.ATTACK_RADIUS, attack_pos.y - config.ATTACK_RADIUS,
                               config.ATTACK_RADIUS * 2, config.ATTACK_RADIUS * 2)

    # Iteramos sobre uma copia: apply_progress pode adicionar inimigos na lista
    for enemy in run["enemies"][:]:
        enemy.update(run["player"], dt)

        if attack_rect.colliderect(enemy.rect):
            hit_pos = pygame.Vector2(enemy.rect.center)
            enemy.respawn(run["enemy_speed"])
            old_score = run["score"]

            judgment = music.judge_timing()
            if judgment is not None:
                # Ha musica tocando (Modo Historia): o golpe rende mais ou
                # menos pontos dependendo de quao em cima da batida ele caiu.
                tier_name, mult, color = judgment
                run["score"] += mult
                entities.spawn_hit_popup(run, hit_pos, tier_name, color)
            else:
                run["score"] += 1   # Modo Arcade (sem musica): sempre +1, como antes

            entities.apply_progress(run, old_score)
            audio.play(audio.hit_sound)
        elif player_rect.colliderect(enemy.rect):
            run["lives"] -= 1
            enemy.respawn(run["enemy_speed"])
            audio.play(audio.hurt_sound)

    entities.update_hit_popups(run, dt)
    return attack_pos
