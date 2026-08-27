"""Mystical Melody - ponto de entrada.

O codigo do jogo mora no pacote game/, organizado por responsabilidade:
  game/config.py     - constantes fixas (tamanhos, cores, geometria de UI)
  game/state.py       - configuracoes do jogador, recorde e estado da UI
  game/display.py     - janela, canvas logico, fontes, escala/letterbox
  game/audio.py       - efeitos sonoros gerados na hora
  game/visuals.py     - fundo, particulas, botao/aba/painel/slider, icones
  game/entities.py    - inimigo e estado de uma partida
  game/layout.py      - geometria dos botoes de cada tela + navegacao por teclado
  game/gameplay.py    - atualizacao da partida em andamento
  game/screens.py     - composicao visual de cada tela (menu, opcoes, HUD...)
  game/app.py         - loop principal (eventos + update + desenho)
"""
from game.app import main

if __name__ == "__main__":
    main()
