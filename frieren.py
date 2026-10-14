from pathlib import Path
import math

import pygame

from constantes import Y_PES_CHAO
from entidade import Combatente


class Maga(Combatente):
    """Frieren, controlada pelo jogador."""

    VELOCIDADE_ANDAR = 5
    VELOCIDADE_VOO = 4

    def __init__(self, x, y):
        """x, y = posição dos pés (meio da base do sprite)."""
        super().__init__(x, y, vida_maxima=3)

        pasta_imagens = Path(__file__).resolve().parent / "imagens" / "Personagens"

        self.sprite_parada_chao = pygame.image.load(
            str(pasta_imagens / "FrierenIdle.png")
        ).convert_alpha()
        spritesheet_andando = pygame.image.load(
            str(pasta_imagens / "FrierenWalk.png")
        ).convert_alpha()
        spritesheet_voando = pygame.image.load(
            str(pasta_imagens / "FrierenFly.png")
        ).convert_alpha()

        self.sprite_parada_chao = self._ampliar(self.sprite_parada_chao)

        self.frames_voando = []
        self.frames_andando = []

        for i in range(3):
            quadro = spritesheet_voando.subsurface((i * 48, 0, 44, 64)).copy()
            self.frames_voando.append(self._ampliar(quadro))

        for i in range(5):
            quadro = spritesheet_andando.subsurface((i * 50, 0, 50, 60)).copy()
            self.frames_andando.append(self._ampliar(quadro))

        self.tempo_animacao_voo = 0
        self.tempo_animacao_andar = 0
        self.animacao_atual = None
        self.animacao_anterior = None
        self.quadro_atual = 0

        self.no_chao = True
        self.pulando = False
        self.voando = False

        self.velocidade_y = 0
        self.gravidade = 0.7
        self.forca_pulo = -14

        self.tempo_voo = 0

        self.rect = self.image.get_rect(midbottom=(x, y))
        self.definir_imagem(self.sprite_parada_chao)
        self.rect.midbottom = (x, y)

    @staticmethod
    def _ampliar(imagem, fator=3):
        largura, altura = imagem.get_size()
        return pygame.transform.scale(imagem, (largura * fator, altura * fator))

    # ---- controles -----------------------------------------------------
    def pressionar_cima(self):
        """Tecla W/seta para cima: pula no chão e, no ar, começa a voar."""
        if self.voando:
            return

        if self.no_chao:
            self.velocidade_y = self.forca_pulo
            self.no_chao = False
            self.pulando = True
        elif self.pulando:
            self.voando = True
            self.pulando = False
            self.velocidade_y = 0
            self.tempo_voo = 0

    def pousar(self):
        self.voando = False
        self.pulando = False
        self.no_chao = True
        self.velocidade_y = 0
        self.rect.bottom = Y_PES_CHAO

    # ---- atualização ---------------------------------------------------
    def update(self, ctx):
        teclas = pygame.key.get_pressed()

        esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        cima = teclas[pygame.K_w] or teclas[pygame.K_UP]
        baixo = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        movendo = esquerda or direita

        self._animar(movendo)

        if esquerda:
            self.rect.x -= self.VELOCIDADE_ANDAR

        if direita:
            self.rect.x += self.VELOCIDADE_ANDAR

        if self.voando:
            if cima:
                self.rect.y -= self.VELOCIDADE_VOO

            if baixo:
                self.rect.y += self.VELOCIDADE_VOO

            self.rect.y += int(math.sin(self.tempo_voo) * 2)

            # Descendo até o chão, a Maga pousa e volta a andar normalmente.
            if self.rect.bottom >= Y_PES_CHAO:
                self.pousar()
        else:
            self.velocidade_y += self.gravidade
            self.rect.y += int(self.velocidade_y)

            if self.rect.bottom >= Y_PES_CHAO:
                self.rect.bottom = Y_PES_CHAO
                self.velocidade_y = 0
                self.no_chao = True
                self.pulando = False
            else:
                self.no_chao = False

        self.mudar_direcao()
        self.rect.clamp_ip(ctx.area)

    def _animar(self, movendo):
        if self.voando:
            self.animacao_atual = "voar"
        elif movendo:
            self.animacao_atual = "andar"
        else:
            self.animacao_atual = "parar"

        if self.animacao_atual != self.animacao_anterior:
            self.quadro_atual = 0
            self.animacao_anterior = self.animacao_atual

        if self.animacao_atual == "andar":
            self.tempo_animacao_andar += 1

            if self.tempo_animacao_andar >= 10:
                self.quadro_atual = (self.quadro_atual + 1) % len(self.frames_andando)
                self.tempo_animacao_andar = 0

            imagem = self.frames_andando[self.quadro_atual]

        elif self.animacao_atual == "voar":
            self.tempo_animacao_voo += 1
            self.tempo_voo += 0.08

            if self.tempo_animacao_voo >= 10:
                self.quadro_atual = (self.quadro_atual + 1) % len(self.frames_voando)
                self.tempo_animacao_voo = 0

            imagem = self.frames_voando[self.quadro_atual]

        else:
            imagem = self.sprite_parada_chao
            self.quadro_atual = 0

        self.definir_imagem(imagem)
