from pathlib import Path
import pygame
import math
from constantes import *

class Entidade (pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 80), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))

class Maga (Entidade):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vida = 3

        base_dir = Path(__file__).resolve().parent
        pasta_imagens = base_dir / "imagens" / "Personagens"

        self.sprite_parada_chao = pygame.image.load(str(pasta_imagens / "FrierenIdle.png")).convert_alpha()
        self.spritesheet_voando = pygame.image.load(str(pasta_imagens / "FrierenFly.png")).convert_alpha()

        self.image = self.sprite_parada_chao


        self.no_chao = True
        self.pulando = False
        self.voando = False

        self.velocidade_y = 0
        self.gravidade = 0.7
        self.forca_pulo = -14

        self.tempo_voo = 0
        self.altura_base = y

    def update(self, tela):
        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.rect.x -= 5

        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.rect.x += 5

        if self.voando:
            self.image = self.spritesheet_voando
            self.tempo_voo += 0.08

            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                self.rect.y -= 4

            if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                self.rect.y += 4

            # Animação suave de flutuação.
            oscilacao = math.sin(self.tempo_voo) * 5
            self.rect.y += int(oscilacao)

        else:
            self.image = self.sprite_parada_chao
            self.velocidade_y += self.gravidade
            self.rect.y += int(self.velocidade_y)

            limite_chao = ALTURA - 120 - self.rect.height

            if self.rect.bottom >= ALTURA - 120:
                self.rect.bottom = ALTURA - 120
                self.velocidade_y = 0
                self.no_chao = True
                self.pulando = False

            else:
                self.no_chao = False

        self.rect.clamp_ip(tela.get_rect())