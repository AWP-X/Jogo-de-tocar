"""Constantes fixas do jogo: tamanhos, cores e geometria de UI.

Nada aqui muda em tempo de execucao - para o estado que muda enquanto o jogo
roda (configuracoes do jogador, recorde, aba aberta etc.), veja game/state.py.
"""
import os
import sys


def _project_root():
    """Raiz do projeto (onde ficam main.py, assets/ e o highscore.json).
    Funciona tanto rodando os .py quanto empacotado com PyInstaller (nesse caso
    os arquivos ficam extraidos em sys._MEIPASS, uma pasta temporaria)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_ROOT = _project_root()

# ===================== TELA =====================
WIDTH, HEIGHT = 1280, 720          # resolucao LOGICA: tudo eh desenhado nesse tamanho
FPS = 60

# ===================== GAMEPLAY =====================
PLAYER_SPEED = 300
PLAYER_START_SIZE = 20
PLAYER_MAX_SIZE = 40
ENEMY_SIZE = 40
ATTACK_RADIUS = 20

# Dificuldade: cada nivel ajusta vidas iniciais, velocidade dos inimigos (base e
# incremento por progressao) e o teto de inimigos simultaneos.
DIFFICULTIES = {
    "facil":   {"label": "FACIL",   "start_lives": 4, "enemy_speed_mult": 0.8, "speed_step": 15, "max_enemies": 5},
    "normal":  {"label": "NORMAL",  "start_lives": 3, "enemy_speed_mult": 1.0, "speed_step": 20, "max_enemies": 6},
    "dificil": {"label": "DIFICIL", "start_lives": 2, "enemy_speed_mult": 1.3, "speed_step": 28, "max_enemies": 8},
}
DIFFICULTY_ORDER = ["facil", "normal", "dificil"]

# ===================== RITMO (mata um inimigo no tempo da musica) =====================
# So vale quando ha musica tocando (Modo Historia). "threshold" e a distancia
# maxima ate a batida mais proxima (0 = golpe em cima da batida, 1 = o mais
# longe possivel, bem no meio de duas batidas) - lista do melhor grau (janela
# mais apertada) pro pior (qualquer coisa que sobrar cai em Trash).
RHYTHM_TIERS = [
    ("PERFECT", 0.15, 5, (255, 205, 60)),
    ("GREAT",   0.35, 4, (110, 230, 120)),
    ("NORMAL",  0.55, 3, (255, 255, 255)),
    ("OK",      0.75, 2, (160, 160, 185)),
    ("TRASH",   1.01, 1, (170, 90, 90)),
]

# ===================== CORES =====================
WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
BG_GAME      = (15, 15, 25)
JAZZY_BG     = (32, 12, 24)   # tom vinho escuro, clima de clube de jazz

# Paleta "profissional" do menu/opcoes (tema neon escuro)
BG_TOP       = (9, 8, 22)
BG_BOTTOM    = (26, 14, 48)
ACCENT       = (130, 95, 255)
PANEL_BORDER = (255, 255, 255)
TEXT_MUTED   = (160, 160, 185)

BTN_NORMAL   = (36, 34, 58)
BTN_HOVER    = (66, 56, 120)
BTN_DISABLED = (60, 60, 70)
PLAYER_COLOR = (255, 70, 70)
ENEMY_COLOR  = (90, 220, 90)
ATTACK_COLOR = (90, 220, 220)
SLIDER_BG    = (50, 48, 70)

# ===================== GEOMETRIA DE UI =====================
# Sliders (usada pra desenhar E pra detectar clique/arraste)
SLIDER_X = 300
SLIDER_W = 450
VOLUME_Y = 250
SENS_Y   = 360

# Abas do painel de Opcoes
OPTIONS_TABS = ["audio", "controles", "video", "ranking", "creditos"]
OPTIONS_TAB_LABELS = {
    "audio": "AUDIO", "controles": "CONTROLES", "video": "VIDEO",
    "ranking": "RANKING", "creditos": "CREDITOS",
}

# ===================== MUNDOS / MODO HISTORIA =====================
# Cada mundo toca um genero musical diferente. Por enquanto so existe o Jazzy;
# a lista foi pensada pra crescer (Rock, Eletronico, etc.) sem precisar mexer
# em nada alem de acrescentar uma entrada aqui.
WORLDS = {
    "jazzy": {
        "name": "Jazzy",
        "tagline": "O mundo que so toca jazz.",
        "music": "jazzy",
        "color": (206, 138, 58),   # tom de latao/saxofone - usado no rotulo do disco
        "orb_style": "vinyl",      # o portal vira um disco de vinil girando
        # Icones que ficam girando ao redor do portal na selecao de mundo.
        "orbit_icons": ["saxophone", "piano", "trumpet", "drum"],
        # Pontuacao alvo de cada nivel (indice 0 = nivel 1).
        "levels": [10, 15, 22, 30, 40, 50, 62, 75, 90, 110],
    },
}
WORLD_ORDER = ["jazzy"]

# Botoes do menu principal
MENU_LABELS = {"play": "JOGAR (ARCADE)", "historia": "MODO HISTORIA", "options": "OPCOES", "quit": "SAIR"}
MENU_ICONS  = {"play": "play", "historia": "map", "options": "settings", "quit": "power"}
