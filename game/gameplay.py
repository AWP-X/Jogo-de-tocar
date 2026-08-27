"""Atualizacao por frame da partida em andamento: movimento, ataque e colisoes."""
import pygame

from . import audio
from . import config
from . import entities
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
            enemy.respawn(run["enemy_speed"])
            run["score"] += 1
            entities.apply_progress(run)
            audio.play(audio.hit_sound)
        elif player_rect.colliderect(enemy.rect):
            run["lives"] -= 1
            enemy.respawn(run["enemy_speed"])
            audio.play(audio.hurt_sound)

    return attack_pos
