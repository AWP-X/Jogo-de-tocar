"""Pacote do jogo Mystical Melody - o ponto de entrada real fica em main.py, na raiz.

pygame.init() roda aqui, na inicializacao do PACOTE, pra garantir que qualquer
submodulo (audio, music, display, ...) encontre o mixer pronto assim que for
importado - nao importa em que ordem os `from . import x` aconteçam em cada
arquivo. Antes, essa chamada morava em game/display.py; se algum outro modulo
fosse importado primeiro (como aconteceu com game/audio.py), os sons eram
criados com o mixer ainda fechado e falhavam em silencio.
"""
import pygame

pygame.mixer.pre_init(22050, -16, 2, 512)
pygame.init()
