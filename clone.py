
from pathlib import Path
import pygame
import math
from constantes import *
from frieren import Entidade

class Cloneataque:
    def __init__(self, origem, alvo):
        self.x, self.y = origem

        # Direção do projétil até à Maga
        dx = alvo[0] - origem[0]
        dy = alvo[1] - origem[1]
        distancia = math.hypot(dx, dy)

        if distancia != 0:
            self.dx = dx / distancia
            self.dy = dy / distancia
        else:
            self.dx = 1
            self.dy = 0

        self.velocidade = 6
        self.dano = 1
        self.raio = 9

        self.rect = pygame.Rect(
            self.x - self.raio,
            self.y - self.raio,
            self.raio * 2,
            self.raio * 2
        )
    def update(self):
        self.x += self.dx * self.velocidade
        self.y += self.dy * self.velocidade

        self.rect.center = (int(self.x), int(self.y))

    def desenhar(self, tela):
        # Projétil mágico roxo
        pygame.draw.circle(
            tela,
            (190, 50, 255),
            self.rect.center,
            self.raio
        )

        pygame.draw.circle(
            tela,
            (240, 200, 255),
            self.rect.center,
            4
        )


class Feiticeira(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y)

        base_dir = Path(__file__).resolve().parent
        pasta_imagens = base_dir / "imagens" / "Personagens"

        self.vida = 11
        self.vida_maxima = 11
        self.ultimo_dano = pygame.time.get_ticks()
        self.Tempo_regeneracao = 3000
        self.projeteis = []
        self.ultimo_ataque = pygame.time.get_ticks()
        self.cooldown_ataque = 1200

        self.spritesheet_voando = pygame.image.load(
            str(pasta_imagens / "CloneFly.png")
        ).convert_alpha()

        self.frames_voando = []

        for i in range(3):
            quadro = self.spritesheet_voando.subsurface(
                (i * 48, 0, 44, 64)
            ).copy()

            quadro = pygame.transform.scale_by(quadro, 3)
            self.frames_voando.append(quadro)

        self.tempo_animacao = 0
        self.quadro_atual = 0

        self.direcao = "esquerda"

        self.velocidade = 3
        self.tempo_voo = 0
        self.canto_atual = 0
        self.ultimo_canto = pygame.time.get_ticks()

        self.limite_esquerdo = 80
        self.limite_direito = LARGURA - 140
        self.limite_superior = 100
        self.limite_inferior = ALTURA - 220

        self.imagem_original = self.frames_voando[0]
        self.image = self.imagem_original
        self.rect = self.image.get_rect(topleft=(x, y))

        self.mudar_direcao()

    def mudar_direcao(self):
        if self.direcao == "direita":
            self.image = pygame.transform.flip(
                self.imagem_original, True, False
            )
        else:
            self.image = self.imagem_original

    def update(self, maga):
        agora = pygame.time.get_ticks()
        self.tempo_voo += 0.06

        self.tempo_animacao += 1

        agora = pygame.time.get_ticks()

        if agora - self.ultimo_dano >= self.Tempo_regeneracao:
            if self.vida < self.vida_maxima:
                self.vida += 1

            self.ultimo_dano = agora
        if agora - self.ultimo_ataque >= self.cooldown_ataque:
            self.projeteis.append(
                Cloneataque(
            self.rect.center,
            maga.rect.center
        )
    )

            self.ultimo_ataque = agora

        if self.tempo_animacao >= 30:
            self.quadro_atual = (
                self.quadro_atual + 1
            ) % len(self.frames_voando)

            self.tempo_animacao = 0

        self.imagem_original = self.frames_voando[
            self.quadro_atual
        ]

        if maga.voando:
            if maga.rect.centerx > LARGURA // 2:
                alvo_x = self.limite_esquerdo
            else:
                alvo_x = self.limite_direito

            if self.rect.x < alvo_x:
                self.rect.x += self.velocidade
            elif self.rect.x > alvo_x:
                self.rect.x -= self.velocidade

            if agora - self.ultimo_canto >= 1500:
                self.canto_atual = 1 - self.canto_atual
                self.ultimo_canto = agora

            if self.canto_atual == 0:
                alvo_y = self.limite_superior
            else:
                alvo_y = self.limite_inferior

            if self.rect.y < alvo_y:
                self.rect.y += self.velocidade
            elif self.rect.y > alvo_y:
                self.rect.y -= self.velocidade

        else:
            if maga.rect.centerx < LARGURA // 2:
                alvo_x = self.limite_direito
            else:
                alvo_x = self.limite_esquerdo

            if self.rect.x < alvo_x:
                self.rect.x += self.velocidade
            elif self.rect.x > alvo_x:
                self.rect.x -= self.velocidade

            self.rect.y = int(
                180 + math.sin(self.tempo_voo) * 25
            )

        self.mudar_direcao()
