"""O inimigo e o estado de uma partida (progressao de dificuldade)."""
import random

import pygame

from . import config
from . import state


def spawn_position():
    """Retorna uma posicao aleatoria fora da tela."""
    side = random.choice(["top", "bottom", "left", "right"])
    if side == "top":
        return pygame.Vector2(random.randint(0, config.WIDTH), -config.ENEMY_SIZE)
    if side == "bottom":
        return pygame.Vector2(random.randint(0, config.WIDTH), config.HEIGHT + config.ENEMY_SIZE)
    if side == "left":
        return pygame.Vector2(-config.ENEMY_SIZE, random.randint(0, config.HEIGHT))
    return pygame.Vector2(config.WIDTH + config.ENEMY_SIZE, random.randint(0, config.HEIGHT))


class Enemy:
    def __init__(self, speed):
        self.pos = spawn_position()
        self.speed = speed

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x), int(self.pos.y), config.ENEMY_SIZE, config.ENEMY_SIZE)

    def respawn(self, speed=None):
        self.pos = spawn_position()
        if speed is not None:
            self.speed = speed

    def update(self, target, dt):
        direction = target - self.pos
        if direction.length_squared() > 0:
            direction.normalize_ip()
            self.pos += direction * self.speed * dt

    def draw(self, surface):
        pygame.draw.rect(surface, config.ENEMY_COLOR, self.rect)


def new_run(target_score=None, world=None):
    """Cria os dados de uma partida zerada, de acordo com a dificuldade escolhida.

    target_score=None -> Modo Arcade (infinito, com recorde/ranking).
    target_score=N     -> Modo Historia: a partida termina em vitoria ao
                           atingir N pontos, mesmo que ainda sobrem vidas.
    world              -> id do mundo (ex: "jazzy"), so preenchido no Modo
                           Historia; controla o cenario/musica de fundo.
    """
    diff = config.DIFFICULTIES[state.settings["difficulty"]]
    enemy_speed = int(200 * diff["enemy_speed_mult"])
    return {
        "player": pygame.Vector2(config.WIDTH / 2, config.HEIGHT / 2),
        "player_size": config.PLAYER_START_SIZE,
        "enemies": [Enemy(enemy_speed)],
        "enemy_speed": enemy_speed,
        "score": 0,
        "lives": diff["start_lives"],
        "target_score": target_score,
        "world": world,
    }


def apply_progress(run):
    """Aumenta a dificuldade conforme o score sobe (o quanto, depende do nivel
    de dificuldade escolhido no menu)."""
    diff = config.DIFFICULTIES[state.settings["difficulty"]]
    score = run["score"]

    # Jogador cresce um pouco a cada 5 pontos (ate um limite).
    if score % 5 == 0 and run["player_size"] < config.PLAYER_MAX_SIZE:
        run["player_size"] += 1

    # Inimigos ficam mais rapidos a cada 12 pontos.
    if score % 12 == 0:
        run["enemy_speed"] += diff["speed_step"]
        for e in run["enemies"]:
            e.speed = run["enemy_speed"]

    # Novo inimigo a cada 8 pontos (ate o maximo da dificuldade atual).
    if score % 8 == 0 and len(run["enemies"]) < diff["max_enemies"]:
        run["enemies"].append(Enemy(run["enemy_speed"]))
