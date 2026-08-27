"""O inimigo e o estado de uma partida (progressao de dificuldade)."""
import math
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
    """kind controla o comportamento:
    - "chaser": persegue direto (o inimigo classico).
    - "zigzag": persegue serpenteando de um lado a outro, mais dificil de prever.
    - "fast":   igual ao chaser, mas menor e naturalmente mais rapido (definido
                em new_run/apply_progress via um multiplicador de velocidade).
    """

    def __init__(self, speed, kind="chaser"):
        self.pos = spawn_position()
        self.speed = speed
        self.kind = kind
        self.age = random.uniform(0, 10)   # desfasa o zigue-zague entre inimigos

    @property
    def size(self):
        return int(config.ENEMY_SIZE * 0.75) if self.kind == "fast" else config.ENEMY_SIZE

    @property
    def rect(self):
        s = self.size
        return pygame.Rect(int(self.pos.x), int(self.pos.y), s, s)

    def respawn(self, speed=None):
        self.pos = spawn_position()
        if speed is not None:
            self.speed = speed

    def update(self, target, dt):
        self.age += dt
        direction = target - self.pos
        if direction.length_squared() == 0:
            return
        direction.normalize_ip()

        if self.kind == "zigzag":
            perp = pygame.Vector2(-direction.y, direction.x)
            wobble = math.sin(self.age * 6.0) * 0.7
            direction = direction + perp * wobble
            if direction.length_squared() > 0:
                direction.normalize_ip()

        speed = self.speed * 1.15 if self.kind == "fast" else self.speed
        self.pos += direction * speed * dt

    def draw(self, surface):
        color = config.ENEMY_VARIANT_COLORS.get(self.kind, config.ENEMY_COLOR)
        pygame.draw.rect(surface, color, self.rect)


def _random_kind(enemy_kinds):
    return random.choice(enemy_kinds) if enemy_kinds else "chaser"


def new_run(target_score=None, world=None, level_num=None, enemy_kinds=None):
    """Cria os dados de uma partida zerada, de acordo com a dificuldade escolhida.

    target_score=None -> Modo Arcade (infinito, com recorde/ranking).
    target_score=N     -> Modo Historia: a partida termina em vitoria ao
                           atingir N pontos, mesmo que ainda sobrem vidas.
    world              -> id do mundo (ex: "jazzy"), so preenchido no Modo
                           Historia; controla o cenario/musica de fundo.
    level_num          -> numero da fase (1-indexado); fases mais avancadas
                           comecam com os inimigos um pouco mais rapidos.
    enemy_kinds        -> tipos de inimigo que podem aparecer nessa fase (ver
                           config.WORLDS[...]["levels"]); None = so "chaser".
    """
    diff = config.DIFFICULTIES[state.settings["difficulty"]]
    level_ramp = 1.0 + config.LEVEL_SPEED_RAMP * ((level_num or 1) - 1)
    enemy_speed = int(200 * diff["enemy_speed_mult"] * level_ramp)
    kinds = enemy_kinds or ["chaser"]
    return {
        "player": pygame.Vector2(config.WIDTH / 2, config.HEIGHT / 2),
        "player_size": config.PLAYER_START_SIZE,
        "enemies": [Enemy(enemy_speed, _random_kind(kinds))],
        "enemy_speed": enemy_speed,
        "score": 0,
        "lives": diff["start_lives"],
        "target_score": target_score,
        "world": world,
        "level_num": level_num,
        "enemy_kinds": kinds,
        "combo": 0,          # acertos seguidos em GREAT/PERFECT (ver config.COMBO_*)
        "hit_popups": [],    # textos flutuantes de "PERFECT!"/"GREAT!"/etc.
    }


def apply_progress(run, old_score):
    """Aumenta a dificuldade conforme o score sobe (o quanto, depende do nivel
    de dificuldade escolhido no menu).

    Recebe old_score (o placar ANTES do golpe que acabou de acontecer) porque,
    com o ritmo, um unico golpe pode valer de 1 a 5 pontos - "score % 5 == 0"
    deixaria de disparar se um golpe pulasse por cima do multiplo exato. Em vez
    disso comparamos quantos multiplos de cada intervalo foram ultrapassados.
    """
    diff = config.DIFFICULTIES[state.settings["difficulty"]]
    score = run["score"]

    # Jogador cresce um pouco a cada 5 pontos (ate um limite).
    if score // 5 > old_score // 5 and run["player_size"] < config.PLAYER_MAX_SIZE:
        run["player_size"] += 1

    # Inimigos ficam mais rapidos a cada 12 pontos.
    if score // 12 > old_score // 12:
        run["enemy_speed"] += diff["speed_step"]
        for e in run["enemies"]:
            e.speed = run["enemy_speed"]

    # Novo inimigo a cada 8 pontos (ate o maximo da dificuldade atual).
    if score // 8 > old_score // 8 and len(run["enemies"]) < diff["max_enemies"]:
        run["enemies"].append(Enemy(run["enemy_speed"], _random_kind(run.get("enemy_kinds"))))


def compute_stars(run):
    """Avaliacao de 1 a 3 estrelas ao vencer uma fase do Modo Historia, com
    base em quantas vidas sobraram (quanto menos dano tomado, melhor)."""
    diff = config.DIFFICULTIES[state.settings["difficulty"]]
    start_lives = diff["start_lives"]
    if run["lives"] >= start_lives:
        return 3
    if run["lives"] >= math.ceil(start_lives / 2):
        return 2
    return 1


# ===================== TEXTOS FLUTUANTES (feedback de ritmo) =====================
POPUP_LIFETIME = 0.7      # segundos ate sumir
POPUP_RISE_SPEED = 70     # pixels por segundo, subindo


def spawn_hit_popup(run, pos, text, color):
    run["hit_popups"].append({"pos": pygame.Vector2(pos), "text": text, "color": color, "age": 0.0})


def update_hit_popups(run, dt):
    for popup in run["hit_popups"]:
        popup["age"] += dt
    run["hit_popups"][:] = [p for p in run["hit_popups"] if p["age"] < POPUP_LIFETIME]
