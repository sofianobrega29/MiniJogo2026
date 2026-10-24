"""Efeitos visuais do modo cajado: o traço do mouse vira uma trilha de energia mágica."""

import math
import random

import pygame


def _cor_ao_longo(t):
    """Cor da trilha: azul-mana -> ciano -> branco, do começo ao fim do traço (só azul e branco)."""
    pontos = ((60, 130, 255), (130, 220, 255), (245, 252, 255))
    t = max(0.0, min(1.0, t)) * 2
    i = min(int(t), 1)
    f = t - i
    a, b = pontos[i], pontos[i + 1]
    return tuple(int(a[c] + (b[c] - a[c]) * f) for c in range(3))


class TracoMagico:
    """Desenha traços com brilho em camadas, cor que muda e faíscas que flutuam e somem."""

    def __init__(self):
        self.camada = None
        self.faiscas = []

    def limpar(self):
        self.faiscas = []

    def emitir(self, ponto, quantidade=3):
        """Solta algumas faíscas em volta de um ponto do traço."""
        for _ in range(quantidade):
            angulo = random.uniform(0, math.tau)
            velocidade = random.uniform(0.3, 1.8)
            self.faiscas.append({
                "x": ponto[0] + random.uniform(-4, 4),
                "y": ponto[1] + random.uniform(-4, 4),
                "vx": math.cos(angulo) * velocidade,
                "vy": math.sin(angulo) * velocidade - 0.35,  # sobem um pouco
                "vida": random.randint(25, 55),
                "maximo": 55,
                "tamanho": random.uniform(2, 5),
                "estrela": random.random() < 0.35,
                "cristal": random.random() < 0.14,   # caquinhos de cristal de mana
                "cor": random.random(),
            })

    def atualizar(self):
        for faisca in self.faiscas[:]:
            faisca["x"] += faisca["vx"]
            faisca["y"] += faisca["vy"]
            faisca["vx"] *= 0.97
            faisca["vy"] *= 0.97
            faisca["vida"] -= 1

            if faisca["vida"] <= 0:
                self.faiscas.remove(faisca)

        if len(self.faiscas) > 400:
            del self.faiscas[: len(self.faiscas) - 400]

    def _desenhar_traco(self, camada, pontos, intensidade=1.0):
        if len(pontos) < 2:
            return

        passo = max(1, len(pontos) // 140)
        pts = pontos[::passo] + ([pontos[-1]] if (len(pontos) - 1) % passo else [])
        n = len(pts) - 1

        # Camadas de fora para dentro: aura larga e fraca ... núcleo branco fino.
        for largura, alfa in ((22, 35), (14, 85), (8, 170)):
            for i in range(n):
                cor = _cor_ao_longo(i / max(1, n)) + (int(alfa * intensidade),)
                pygame.draw.line(camada, cor, pts[i], pts[i + 1], largura)
                pygame.draw.circle(camada, cor, (int(pts[i + 1][0]), int(pts[i + 1][1])), largura // 2)

        pygame.draw.lines(camada, (255, 255, 255, int(235 * intensidade)), False, pts, 3)

    def desenhar(self, tela, tracos_parados, traco_atual):
        """tracos_parados: traços já soltos (esperando o 2º traço); traco_atual: o que está sendo desenhado."""
        if self.camada is None or self.camada.get_size() != tela.get_size():
            self.camada = pygame.Surface(tela.get_size(), pygame.SRCALPHA)

        camada = self.camada
        camada.fill((0, 0, 0, 0))

        for traco in tracos_parados:
            self._desenhar_traco(camada, traco, 0.8)

        self._desenhar_traco(camada, traco_atual)

        # Cabeça brilhante pulsando na ponta do traço.
        if traco_atual:
            cx, cy = int(traco_atual[-1][0]), int(traco_atual[-1][1])
            pulso = 1 + 0.25 * math.sin(pygame.time.get_ticks() / 70)

            for raio, alfa in ((int(26 * pulso), 45), (int(16 * pulso), 110), (int(8 * pulso), 220)):
                pygame.draw.circle(camada, (170, 225, 255, alfa), (cx, cy), raio)

        # Faíscas (pontinhos e estrelinhas de 4 pontas) que piscam e somem.
        agora = pygame.time.get_ticks()

        for faisca in self.faiscas:
            vida = faisca["vida"] / faisca["maximo"]
            pisca = 0.6 + 0.4 * math.sin(agora / 60 + faisca["cor"] * 10)
            alfa = int(255 * min(1.0, vida * 1.6) * pisca)
            cor = _cor_ao_longo(faisca["cor"]) + (max(0, alfa),)
            x, y = int(faisca["x"]), int(faisca["y"])
            r = faisca["tamanho"] * (0.5 + vida)

            if faisca["cristal"]:
                c = faisca["tamanho"] * 3.2 * (0.5 + vida)
                forma = [(x, y - c * 1.5), (x + c * 0.7, y), (x, y + c * 1.5), (x - c * 0.7, y)]
                pygame.draw.polygon(camada, (90, 170, 255, int(alfa * 0.55)), forma)
                pygame.draw.polygon(camada, (235, 248, 255, max(0, alfa)), forma, 2)
            elif faisca["estrela"]:
                pygame.draw.polygon(camada, cor, [
                    (x, y - r * 2), (x + r * 0.5, y - r * 0.5), (x + r * 2, y),
                    (x + r * 0.5, y + r * 0.5), (x, y + r * 2), (x - r * 0.5, y + r * 0.5),
                    (x - r * 2, y), (x - r * 0.5, y - r * 0.5),
                ])
            else:
                pygame.draw.circle(camada, cor, (x, y), max(1, int(r)))

        tela.blit(camada, (0, 0))
