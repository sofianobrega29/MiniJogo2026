"""Cenário: o chão de pedra do templo, que racha quando o buraco negro aparece."""

import math
import random

import pygame

from constantes import LARGURA, ALTURA, ALTURA_CHAO

COR_REJUNTE = (40, 31, 40)
COR_PEDRA_CLARA = (238, 224, 192)   # as pedras que voam (como nas imagens do anime)
COR_PEDRA_SOMBRA = (196, 176, 146)
COR_CONTORNO = (24, 18, 30)


def _mais_claro(cor, quanto):
    return tuple(min(255, c + quanto) for c in cor)


def _mais_escuro(cor, quanto):
    return tuple(max(0, c - quanto) for c in cor)


class ChaoTemplo:
    """Lajes de pedra desenhadas uma vez; os estragos ficam numa camada à parte."""

    def __init__(self):
        self.topo = ALTURA - ALTURA_CHAO
        self.base = self._montar_base()
        self.danos = pygame.Surface((LARGURA, ALTURA_CHAO), pygame.SRCALPHA)
        self.rachado = False
        self._sorteio = random.Random(99)

    # ---- montagem -------------------------------------------------------
    def _montar_base(self):
        sorteio = random.Random(7)
        base = pygame.Surface((LARGURA, ALTURA_CHAO))
        base.fill(COR_REJUNTE)

        # duas fileiras de lajes em "tijolo corrido"; a da frente é maior (perspectiva)
        for indice, (y, altura) in enumerate(((0, 46), (46, ALTURA_CHAO - 46))):
            x = -sorteio.randint(0, 70) if indice == 0 else -sorteio.randint(30, 120)

            while x < LARGURA:
                largura = sorteio.randint(92, 150) if indice == 0 else sorteio.randint(120, 196)
                self._laje(base, pygame.Rect(x + 2, y + 2, largura - 3, altura - 3), sorteio)
                x += largura

        # a sombra da parede cai sobre o início do chão
        sombra = pygame.Surface((LARGURA, ALTURA_CHAO), pygame.SRCALPHA)

        for i in range(30):
            pygame.draw.line(sombra, (10, 6, 18, int(130 * (1 - i / 30) ** 1.6)), (0, i), (LARGURA, i))

        base.blit(sombra, (0, 0))
        return base

    def _laje(self, base, retangulo, sorteio):
        variacao = sorteio.randint(-14, 14)
        cor = (172 + variacao, 154 + variacao, 138 + variacao)
        pygame.draw.rect(base, cor, retangulo, border_radius=4)

        # manchas e grãos da pedra
        for _ in range(34):
            x = sorteio.randint(retangulo.left + 3, retangulo.right - 5)
            y = sorteio.randint(retangulo.top + 3, retangulo.bottom - 5)
            tom = _mais_claro(cor, 16) if sorteio.random() < 0.5 else _mais_escuro(cor, 18)
            pygame.draw.rect(base, tom, (x, y, 2, 2))

        # luz no alto e na esquerda, sombra embaixo e na direita (relevo)
        claro, escuro = _mais_claro(cor, 30), _mais_escuro(cor, 40)
        pygame.draw.line(base, claro, retangulo.topleft, (retangulo.right - 2, retangulo.top), 2)
        pygame.draw.line(base, claro, retangulo.topleft, (retangulo.left, retangulo.bottom - 2), 2)
        pygame.draw.line(base, escuro, (retangulo.left + 2, retangulo.bottom - 1), (retangulo.right - 1, retangulo.bottom - 1), 2)
        pygame.draw.line(base, escuro, (retangulo.right - 1, retangulo.top + 2), (retangulo.right - 1, retangulo.bottom - 1), 2)

        if sorteio.random() < 0.34:  # trinca antiga na laje
            x, y = sorteio.randint(retangulo.left + 8, retangulo.right - 8), retangulo.top + 2
            pontos = [(x, y)]

            for _ in range(sorteio.randint(3, 5)):
                x += sorteio.randint(-9, 9)
                y += sorteio.randint(8, 16)
                pontos.append((x, min(y, retangulo.bottom - 3)))

            pygame.draw.lines(base, _mais_escuro(cor, 62), False, pontos, 2)

        if sorteio.random() < 0.4:  # canto lascado
            canto = sorteio.choice((retangulo.topleft, retangulo.topright, retangulo.bottomright))
            dx = 1 if canto[0] == retangulo.left else -1
            dy = 1 if canto[1] == retangulo.top else -1
            pygame.draw.polygon(base, COR_REJUNTE, [canto, (canto[0] + dx * 11, canto[1]), (canto[0], canto[1] + dy * 9)])

    # ---- estragos -------------------------------------------------------
    def iniciar_colapso(self):
        """O buraco negro chegou: o chão racha em vários pontos."""
        if self.rachado:
            return

        self.rachado = True

        for _ in range(7):
            x = self._sorteio.uniform(40, LARGURA - 40)
            y = self._sorteio.uniform(8, ALTURA_CHAO - 12)
            direcao = self._sorteio.uniform(-0.5, 0.5) + (math.pi if self._sorteio.random() < 0.5 else 0)
            self._rachadura(x, y, direcao, self._sorteio.randint(110, 260))

    def _rachadura(self, x, y, direcao, comprimento):
        pontos = [(x, y)]
        andado = 0

        while andado < comprimento:
            passo = self._sorteio.uniform(14, 28)
            direcao += self._sorteio.uniform(-0.7, 0.7)
            x += math.cos(direcao) * passo
            y += math.sin(direcao) * passo * 0.7
            y = max(2, min(ALTURA_CHAO - 2, y))
            pontos.append((x, y))
            andado += passo

            if self._sorteio.random() < 0.10:  # ramo menor
                self._rachadura(x, y, direcao + self._sorteio.choice((-1, 1)) * 0.9, comprimento * 0.3)

        pygame.draw.lines(self.danos, (214, 196, 168, 110), False, [(px - 1, py - 1) for px, py in pontos], 1)
        pygame.draw.lines(self.danos, (50, 38, 46, 255), False, pontos, 2)

    def soltar_pedaco(self, x):
        """Abre uma cratera onde uma pedra se soltou. Devolve a posição (em tela) da pedra."""
        y_local = self._sorteio.uniform(18, ALTURA_CHAO - 14)
        raio = self._sorteio.uniform(9, 16)
        pontos = []

        for i in range(9):
            a = i * math.tau / 9 + self._sorteio.uniform(-0.2, 0.2)
            r = raio * self._sorteio.uniform(0.75, 1.15)
            pontos.append((x + math.cos(a) * r, y_local + math.sin(a) * r * 0.6))

        pygame.draw.polygon(self.danos, (206, 186, 156, 255), [(px - 1, py - 2) for px, py in pontos])  # borda levantada
        pygame.draw.polygon(self.danos, (52, 40, 48, 255), pontos)
        miolo = [(x + (px - x) * 0.55, y_local + (py - y_local) * 0.55) for px, py in pontos]
        pygame.draw.polygon(self.danos, (26, 18, 26, 255), miolo)

        if self._sorteio.random() < 0.5:  # uma rachadura curta saindo da cratera
            self._rachadura(x, y_local, self._sorteio.uniform(0, math.tau), 30)

        return x, self.topo + y_local

    # ---- desenho --------------------------------------------------------
    def desenhar(self, tela):
        tela.blit(self.base, (0, self.topo))
        tela.blit(self.danos, (0, self.topo))


class Pedaco:
    """Pedra do chão do templo: se solta, flutua e é sugada pelo buraco negro (ou orbita ele)."""

    def __init__(self, x, y, tamanho, atraso=0, orbita=None):
        self.x, self.y = x, y
        self.tamanho = tamanho
        self.atraso = atraso
        self.vx = self.vy = 0.0
        self.angulo = random.uniform(0, math.tau)
        self.giro = random.uniform(-0.12, 0.12)
        self.escala = 1.0
        self.orbita = orbita  # None (vem do chão) ou [raio, ângulo, velocidade angular]

        n = random.randint(6, 8)
        self.forma = [(i * math.tau / n + random.uniform(-0.25, 0.25), random.uniform(0.62, 1.0)) for i in range(n)]

    @property
    def atras(self):
        """Em órbita: a pedra está na metade de trás (passa por trás do buraco)."""
        return self.orbita is not None and math.sin(self.orbita[1]) < 0

    def update(self, centro, forca):
        """Devolve False quando a pedra foi engolida."""
        if self.orbita is not None:
            raio, ang, vel = self.orbita
            ang += vel
            raio -= 0.12

            if raio < 20:  # engolida: volta para longe e recomeça a orbitar
                raio = random.uniform(120, 170)
                ang = random.uniform(0, math.tau)

            self.orbita = [raio, ang, vel]
            self.x = centro[0] + math.cos(ang) * raio * 1.35
            self.y = centro[1] + math.sin(ang) * raio * 0.5
            self.angulo += self.giro
            self.escala = max(0.35, min(1.0, raio / 70))
            return True

        if self.atraso > 0:  # ainda no chão: treme antes de se soltar
            self.atraso -= 1
            self.x += random.uniform(-1.2, 1.2)
            self.y += random.uniform(-0.6, 0.6)
            return True

        dx, dy = centro[0] - self.x, centro[1] - self.y
        distancia = math.hypot(dx, dy)

        if distancia < 18:
            return False

        # acelera na direção do buraco, com um pouco de curva (espiral)
        self.vx += dx / distancia * forca - dy / distancia * forca * 0.5
        self.vy += dy / distancia * forca + dx / distancia * forca * 0.5
        self.vx *= 0.985
        self.vy *= 0.985
        self.x += self.vx
        self.y += self.vy
        self.angulo += self.giro
        self.escala = max(0.3, min(1.0, distancia / 150))
        return True

    def desenhar(self, tela):
        raio = self.tamanho * self.escala
        pontos = [
            (self.x + math.cos(a + self.angulo) * raio * r, self.y + math.sin(a + self.angulo) * raio * r)
            for a, r in self.forma
        ]
        sombra = [pontos[0], pontos[1], pontos[2], pontos[3], (self.x, self.y)]  # faceta escura (volume)
        pygame.draw.polygon(tela, COR_PEDRA_CLARA, pontos)
        pygame.draw.polygon(tela, COR_PEDRA_SOMBRA, sombra)
        pygame.draw.polygon(tela, COR_CONTORNO, pontos, 2)
