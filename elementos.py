from pathlib import Path
import math
import random

import pygame

import visuais
from cenario import Pedaco
from constantes import LARGURA, Y_PES_CHAO


class Cajado:
    """Cajado que acompanha o mouse no modo de feitiço."""

    def __init__(self):
        caminho = Path(__file__).resolve().parent / "imagens" / "UI" / "Cajado.png"
        imagem = pygame.image.load(str(caminho)).convert_alpha()

        self.image = pygame.transform.scale(imagem, (240, 400))
        self.rect = self.image.get_rect()

    def desenhar(self, tela):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.rect.topleft = (mouse_x - 120, mouse_y - 55)
        tela.blit(self.image, self.rect)


class BuracoNegro:
    """Buraco negro (laranja e preto) aberto pela clone, como no anime.

    Não causa dano: sobe até o topo da tela e puxa um pouco a Maga e os feitiços dela
    na direção dele. O chão do templo racha e solta pedras que são sugadas para dentro.
    """

    PIXEL = 3  # o buraco é desenhado em "pixels" de 3x3, como os sprites

    def __init__(self, origem, alvo, agora, destino=(LARGURA // 2, 130)):
        self.alvo = alvo  # quem é puxado (a Maga)
        self.posicao = pygame.Vector2(origem)
        self.destino = pygame.Vector2(destino)
        self.raio = 24
        self.criado = agora
        self.tempo = agora
        self.giro = 0.0
        self.alcance = 900         # px: além disso ele não puxa
        self.forca_maga = 1.0      # px por quadro (bem leve: a Maga anda a 5)
        self.giro_feitico = 1.1    # graus por quadro que ele curva os feitiços da Maga
        self._resto = pygame.Vector2(0, 0)

        self.pedacos = []          # pedras que saem do chão
        self.orbitas = [           # pedras girando em volta dele (como na imagem de referência)
            Pedaco(0, 0, random.uniform(11, 19), orbita=[random.uniform(60, 170), random.uniform(0, math.tau), random.choice((-1, 1)) * random.uniform(0.018, 0.04)])
            for _ in range(7)
        ]
        self._colapsou = False
        self._quadro = 0

    @property
    def crescimento(self):
        """0 -> 1 durante 1,5 s: o buraco 'abre' aos poucos."""
        return max(0.0, min(1.0, (self.tempo - self.criado) / 1500))

    def forca_em(self, ponto):
        """Vetor de puxão (px por quadro) sobre um ponto, e a distância até ele."""
        relativo = self.posicao - pygame.Vector2(ponto)
        distancia = relativo.length()

        if distancia < 1 or distancia > self.alcance:
            return pygame.Vector2(0, 0), distancia

        intensidade = (0.35 + 0.65 * (1 - distancia / self.alcance)) * self.crescimento
        return relativo.normalize() * intensidade, distancia

    def update(self, ctx):
        self.tempo = ctx.tempo
        self.giro += 3.5
        self._quadro += 1

        falta = self.destino - self.posicao

        if falta.length() > 1.4:
            self.posicao += falta.normalize() * 1.4  # sobe devagar até o topo

        self._puxar_maga(ctx)

        for feitico in ctx.feiticos:
            if feitico.ativo and feitico.dono is self.alvo:
                feitico.ser_puxado(self, ctx)

        self._atualizar_pedras(ctx)

    # ---- pedras e poeira de mana ----------------------------------------
    def _atualizar_pedras(self, ctx):
        centro = (self.posicao.x, self.posicao.y)
        particulas = getattr(ctx, "particulas", None)
        chao = getattr(ctx, "chao", None)
        k = self.crescimento

        if chao is not None and k > 0.15:
            chao.iniciar_colapso()  # o chão racha (uma única vez)

        # de tempos em tempos uma pedra do chão se solta
        if chao is not None and k > 0.4 and self._quadro % 9 == 0 and len(self.pedacos) < 12:
            x, y = chao.soltar_pedaco(random.uniform(50, LARGURA - 50))
            self.pedacos.append(Pedaco(x, y, random.uniform(10, 20), atraso=random.randint(8, 36)))

        for pedaco in self.pedacos[:]:
            if not pedaco.update(centro, 0.32 * k):
                self.pedacos.remove(pedaco)

                if particulas is not None:  # faíscas quando a pedra é engolida
                    particulas.explosao(centro[0], centro[1], 6, 2.4, 16, 1.8, [(255, 170, 60), (255, 232, 150)], cor_fim=(160, 40, 20))

        for pedra in self.orbitas:
            pedra.update(centro, 0)

        # poeira de mana (laranja) sendo sugada pelo buraco
        if particulas is not None and k > 0.3 and self._quadro % 3 == 0:
            angulo = random.uniform(0, math.tau)
            distancia = random.uniform(170, 330)
            p = particulas.emitir(
                centro[0] + math.cos(angulo) * distancia, centro[1] + math.sin(angulo) * distancia * 0.6,
                vida=70, tamanho=random.uniform(1.4, 2.4), cor=random.choice(((255, 170, 60), (255, 220, 130), (255, 110, 40))),
                cor_fim=(110, 30, 20), forma="quadrado", atrito=0.98,
            )
            p.atrai = (centro[0], centro[1], 0.1)

    def _puxar_maga(self, ctx):
        maga = self.alvo

        if not maga.vivo:
            return

        puxao, _ = self.forca_em(maga.hitbox.center)
        puxao *= self.forca_maga

        if maga.no_chao and not maga.voando:
            puxao.y = 0  # no chão só é puxada para os lados

        acumulado = self._resto + puxao
        passo_x, passo_y = int(acumulado.x), int(acumulado.y)  # só aplica pixels inteiros
        self._resto = pygame.Vector2(acumulado.x - passo_x, acumulado.y - passo_y)

        maga.rect.x += passo_x
        maga.rect.y += passo_y
        maga.rect.clamp_ip(ctx.area)

        if maga.rect.bottom > Y_PES_CHAO:
            maga.rect.bottom = Y_PES_CHAO

    # ---- desenho ---------------------------------------------------------
    def desenhar(self, tela):
        k = self.crescimento

        if k < 0.03:
            return

        centro = (int(self.posicao.x), int(self.posicao.y))

        for pedaco in self.pedacos:
            pedaco.desenhar(tela)

        visuais.brilho_elipse(tela, centro, 300 * k, 100 * k, (255, 110, 30), 8, 55)

        for pedra in self.orbitas:  # as pedras de trás passam por trás do buraco
            if pedra.atras:
                pedra.desenhar(tela)

        imagem = self._imagem(k)
        tela.blit(imagem, imagem.get_rect(center=centro))

        for pedra in self.orbitas:
            if not pedra.atras:
                pedra.desenhar(tela)

    def _imagem(self, k):
        """O buraco em si: riscos de luz, lente laranja e disco preto, tudo em pixels de 3x3."""
        S = self.PIXEL
        largura, altura = 780, 200
        camada = pygame.Surface((largura // S, altura // S), pygame.SRCALPHA)
        cx, cy = largura // (2 * S), altura // (2 * S)
        t = self.tempo / 1000
        inclinacao = 0.10 * math.sin(t * 0.9)
        cos_a, sin_a = math.cos(inclinacao), math.sin(inclinacao)

        def p(x, y):
            return (cx + (x * cos_a - y * sin_a) / S, cy + (x * sin_a + y * cos_a) / S)

        # 1) riscos longos de luz que atravessam o buraco, esmaecendo nas pontas
        for i in range(9):
            deslocamento = (i - 4) * 5.5 + math.sin(t * 3 + i) * 1.3
            comprimento = (215 + 11 * ((i * 37) % 9)) * k
            central = abs(i - 4) < 2

            for lado in (-1, 1):
                for j in range(16):
                    a, b = j / 16 * comprimento, (j + 1) / 16 * comprimento
                    alfa = int(220 * (1 - j / 16) ** 1.5)
                    cor = (255, 130 - j * 3, 40, alfa) if central else (230, 70, 40, int(alfa * 0.7))
                    pygame.draw.line(camada, cor, p(lado * a, deslocamento), p(lado * b, deslocamento), 1)

        # 2) lente (olho pontudo): vermelho por fora, laranja no meio, amarelo no centro
        comprimento_lente, altura_lente = 108 * k, 38 * k

        for escala, cor in ((1.0, (215, 55, 30, 150)), (0.72, (255, 140, 35, 215)), (0.42, (255, 228, 120, 255))):
            em_cima, embaixo = [], []

            for m in range(-12, 13):
                u = m / 12
                h = altura_lente * escala * (1 - abs(u)) ** 1.45
                x = u * comprimento_lente * (0.55 + 0.45 * escala)
                em_cima.append(p(x, -h))
                embaixo.append(p(x, h))

            pygame.draw.polygon(camada, cor, em_cima + embaixo[::-1])

        # 3) disco preto com anel laranja e um crescente de luz
        raio = self.raio * k
        pygame.draw.circle(camada, (255, 125, 40, 255), (int(cx), int(cy)), max(1, int(raio / S) + 2))
        pygame.draw.circle(camada, (0, 0, 0, 255), (int(cx), int(cy)), max(1, int(raio / S)))
        borda = pygame.Rect(0, 0, max(4, int(raio / S * 1.5)), max(4, int(raio / S * 1.5)))
        borda.center = (int(cx), int(cy))
        pygame.draw.arc(camada, (255, 214, 120, 255), borda, math.radians(105), math.radians(215), 1)  # luz de borda no alto, à esquerda

        return pygame.transform.scale(camada, (largura, altura))
