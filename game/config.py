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
ATTACK_RADIUS = 16          # um pouco menor que antes (era 20) - exige mais precisao
ATTACK_COOLDOWN = 0.22      # segundos de "recarga" apos cada golpe - sem isso, encostar o
                            # mouse num inimigo matava instantaneo e sem risco nenhum; agora
                            # da pra limpar um aglomerado inteiro num so frame

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
    ("PERFECT", 0.12, 5, (255, 205, 60)),
    ("GREAT",   0.30, 4, (110, 230, 120)),
    ("NORMAL",  0.50, 3, (255, 255, 255)),
    ("OK",      0.72, 2, (160, 160, 185)),
    ("TRASH",   1.01, 1, (170, 90, 90)),
]

# Combo: acertos seguidos em GREAT/PERFECT aumentam um multiplicador extra
# (empilha em cima do multiplicador do grau). Reseta ao tomar dano ou ao
# acertar um golpe OK/NORMAL/TRASH.
COMBO_STEP = 5          # a cada N acertos seguidos, sobe um degrau
COMBO_BONUS_PER_STEP = 0.5
COMBO_MAX_MULT = 3.0

# Inimigos ganham variedade nas fases mais avancadas do Modo Historia.
ENEMY_VARIANT_COLORS = {
    "chaser": (90, 220, 90),     # o inimigo classico (verde) - persegue direto
    "zigzag": (90, 170, 230),    # azul - persegue serpenteando, mais dificil de prever
    "fast":   (230, 200, 70),    # amarelo - mais rapido e um pouco menor
}

# Fases mais avancadas comecam com os inimigos um pouco mais rapidos, alem do
# que a dificuldade (facil/normal/dificil) ja define - 5% a mais por nivel.
LEVEL_SPEED_RAMP = 0.05

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
VOLUME_Y = 230        # volume dos efeitos (SFX)
MUSIC_VOL_Y = 300     # volume da musica de fundo - separado do SFX
SENS_Y   = 390

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
#
# Dentro do Jazzy, cada FASE e um ano marcante da historia do jazz (em ordem
# cronologica - a viagem no tempo acompanha a propria curva de dificuldade) e
# toca um estilo musical ORIGINAL proprio (nunca a gravacao real - so uma
# composicao inspirada na pegada daquela epoca, ver game/music.py). "year"/
# "era" sao so texto pra mostrar na tela; "style" e a chave que escolhe qual
# perfil de composicao usar.
WORLDS = {
    "jazzy": {
        "name": "Jazzy",
        "tagline": "O mundo que so toca jazz.",
        "music": "jazzy",
        "color": (206, 138, 58),   # tom de latao/saxofone - usado no rotulo do disco
        "orb_style": "vinyl",      # o portal vira um disco de vinil girando
        # Icones que ficam girando ao redor do portal na selecao de mundo.
        "orbit_icons": ["saxophone", "piano", "trumpet", "drum"],
        # Cada nivel tem uma meta de pontos e quais tipos de inimigo podem
        # aparecer nele (indice 0 = nivel 1) - vai introduzindo variedade aos
        # poucos em vez de todo nivel ser o mesmo inimigo so que mais rapido.
        "levels": [
            {"target": 10,  "enemies": ["chaser"],
             "year": 1945, "era": "Nascimento do Bebop", "style": "bebop45"},
            {"target": 15,  "enemies": ["chaser"],
             "year": 1953, "era": "O Concerto do Seculo (Massey Hall)", "style": "bebop53"},
            {"target": 22,  "enemies": ["chaser", "zigzag"],
             "year": 1955, "era": "O Renascimento de Miles Davis", "style": "liveswing55"},
            {"target": 30,  "enemies": ["chaser", "zigzag"],
             "year": 1956, "era": "A Consolidacao do LP", "style": "calypsohard56"},
            {"target": 40,  "enemies": ["chaser", "zigzag", "fast"],
             "year": 1957, "era": "Hard Bop e Blue Note", "style": "bluesyhard57"},
            {"target": 50,  "enemies": ["chaser", "zigzag", "fast"],
             "year": 1959, "era": "O Ano de Ouro (Kind of Blue)", "style": "goldenyear59"},
            {"target": 62,  "enemies": ["zigzag", "fast"],
             "year": 1964, "era": "A Explosao da Bossa Nova", "style": "bossa64"},
            {"target": 75,  "enemies": ["zigzag", "fast"],
             "year": 1965, "era": "O Apice do Jazz Espiritual", "style": "spiritual65"},
            {"target": 90,  "enemies": ["fast", "zigzag"],
             "year": 1969, "era": "A Revolucao do Jazz Fusion", "style": "fusion69"},
            {"target": 110, "enemies": ["fast", "zigzag", "chaser"],
             "year": 1973, "era": "O Jazz-Funk Eletronico", "style": "jazzfunk73"},
        ],
    },
}
WORLD_ORDER = ["jazzy"]

# Botoes do menu principal
MENU_LABELS = {"play": "JOGAR (ARCADE)", "historia": "MODO HISTORIA", "options": "OPCOES", "quit": "SAIR"}
MENU_ICONS  = {"play": "play", "historia": "map", "options": "settings", "quit": "power"}
