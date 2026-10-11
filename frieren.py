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
        self.sprite_parada_chao = pygame.transform.flip(self.sprite_parada_chao, True, False)
        self.spritesheet_voando = pygame.transform.flip(self.spritesheet_voando, True, False)

        self.sprite_parada_chao = pygame.transform.scale_by(self.sprite_parada_chao, 3)

        self.frames_voando = []

        for i in range(3):
            quadro = self.spritesheet_voando.subsurface((i * 48, 0, 44, 64)).copy()
            quadro = pygame.transform.scale_by(quadro, 3)
            self.frames_voando.append(quadro)


        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = pygame.Rect(0, 0 , 30, 40)    
        self.tempo_animacao = 0
        self.quadro_atual = 0

        self.image = self.sprite_parada_chao

        self.contagem_w = 0
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
            self.tempo_animacao += 1
            self.tempo_voo += 0.08

            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                self.rect.y -= 4

            if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                self.rect.y += 4

            if self.tempo_animacao >= 30:
                self.quadro_atual = (self.quadro_atual + 1) % len(self.frames_voando)
                self.tempo_animacao = 0

            self.image = self.frames_voando[self.quadro_atual]

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
