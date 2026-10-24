"""Partículas "em bits": quadradinhos e estrelinhas de 4 pontas que flutuam e somem.

Os feitiços usam isto para soltar faíscas, como nos ataques do anime. Quase tudo é
desenhado com retângulos (pixel art), sem transparência: a partícula encolhe e muda
de cor enquanto morre. As únicas exceções são os cacos de vidro ("hex" e "caco"),
que são translúcidos.

Formas: "quadrado", "estrela" (cruzinha de 4 pontas), "faisca" (risco curto na
direção do movimento), "cristal" (losango), "hex" (hexágono de vidro) e "caco"
(caco triangular de vidro).
"""

import math
import random

import pygame


def misturar(cor_a, cor_b, t):
    """Mistura duas cores: t=0 dá cor_a, t=1 dá cor_b."""
    return tuple(int(a + (b - a) * t) for a, b in zip(cor_a, cor_b))


class _Particula:
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_total", "tamanho", "cor", "cor_fim",
                 "forma", "gravidade", "atrito", "angulo", "giro", "atrai")

    def __init__(self, x, y, vx, vy, vida, tamanho, cor, cor_fim, forma, gravidade, atrito):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.vida = self.vida_total = max(1, vida)
        self.tamanho = tamanho
        self.cor, self.cor_fim = cor, cor_fim
        self.forma = forma
        self.gravidade, self.atrito = gravidade, atrito
        self.angulo = random.uniform(0, math.tau)   # só os cacos de vidro giram
        self.giro = random.uniform(-0.18, 0.18)
        self.atrai = None                           # (x, y, força): puxa a partícula (buraco negro)


class Particulas:
    def __init__(self, limite=900):
        self.limite = limite
        self.lista = []

    @property
    def vazio(self):
        return not self.lista

    def limpar(self):
        self.lista = []

    def emitir(self, x, y, vx=0.0, vy=0.0, vida=30, tamanho=3, cor=(255, 255, 255),
               cor_fim=None, forma="quadrado", gravidade=0.0, atrito=0.97):
        """Solta uma partícula. Devolve ela (para quem quiser mexer, ex.: `atrai`)."""
        if len(self.lista) >= self.limite:
            self.lista.pop(0)

        particula = _Particula(x, y, vx, vy, vida, tamanho, cor, cor_fim or cor, forma, gravidade, atrito)
        self.lista.append(particula)
        return particula

    def explosao(self, x, y, quantidade, velocidade, vida, tamanho, cor, cor_fim=None,
                 gravidade=0.0, chance_estrela=0.3, angulo=None, abertura=math.tau,
                 formas=None, atrito=0.97):
        """Solta várias partículas em leque (angulo/abertura em radianos; padrão: todas as direções).

        `cor` pode ser uma cor ou uma lista de cores (sorteia uma para cada partícula).
        `formas`: tupla de formas para sortear; se não for dada, mistura quadrados e estrelas.
        """
        cores = cor if isinstance(cor[0], (tuple, list)) else (cor,)

        for _ in range(quantidade):
            base = random.uniform(0, math.tau) if angulo is None else angulo + random.uniform(-abertura / 2, abertura / 2)
            rapidez = random.uniform(0.3, 1.0) * velocidade

            if formas:
                forma = random.choice(formas)
            else:
                forma = "estrela" if random.random() < chance_estrela else "quadrado"

            escolhida = random.choice(cores)
            self.emitir(
                x, y, math.cos(base) * rapidez, math.sin(base) * rapidez,
                int(vida * random.uniform(0.6, 1.1)), tamanho * random.uniform(0.7, 1.3),
                escolhida, cor_fim, forma, gravidade, atrito,
            )

    def update(self):
        for p in self.lista:
            if p.atrai is not None:
                alvo_x, alvo_y, forca = p.atrai
                dx, dy = alvo_x - p.x, alvo_y - p.y
                distancia = math.hypot(dx, dy)

                if distancia < 16:
                    p.vida = 0  # engolida
                    continue

                p.vx += dx / distancia * forca
                p.vy += dy / distancia * forca

            p.x += p.vx
            p.y += p.vy
            p.vy += p.gravidade
            p.vx *= p.atrito
            p.vy *= p.atrito
            p.angulo += p.giro
            p.vida -= 1

        self.lista = [p for p in self.lista if p.vida > 0]

    def desenhar(self, tela):
        for p in self.lista:
            fracao = p.vida / p.vida_total
            cor = misturar(p.cor_fim, p.cor, fracao)
            lado = max(1, round(p.tamanho * (0.35 + 0.65 * fracao)))

            # No fim da vida pisca (some e volta) como uma faísca.
            if fracao < 0.3 and p.vida % 2 == 0:
                continue

            x, y = int(p.x), int(p.y)

            if p.forma == "estrela":
                braco = lado * 2
                pygame.draw.rect(tela, cor, (x - lado // 2, y - braco, lado, braco * 2 + 1))
                pygame.draw.rect(tela, cor, (x - braco, y - lado // 2, braco * 2 + 1, lado))
                pygame.draw.rect(tela, (255, 255, 255), (x - lado // 2, y - lado // 2, lado, lado))
            elif p.forma == "faisca":
                pygame.draw.line(tela, cor, (x, y), (x - p.vx * 3.0, y - p.vy * 3.0), max(1, lado // 2))
            elif p.forma == "cristal":
                r = lado * 1.4
                pygame.draw.polygon(tela, cor, [(x, y - r * 1.6), (x + r, y), (x, y + r * 1.6), (x - r, y)])
            elif p.forma in ("hex", "caco"):
                self._desenhar_vidro(tela, p, cor, fracao)
            else:
                pygame.draw.rect(tela, cor, (x - lado // 2, y - lado // 2, lado, lado))

    @staticmethod
    def _desenhar_vidro(tela, p, cor, fracao):
        """Hexágono / caco de vidro: translúcido, com contorno claro e brilhante."""
        raio = max(3.0, p.tamanho * 3.2 * (0.5 + 0.5 * fracao))
        lados = 6 if p.forma == "hex" else 3
        lado_surf = int(raio * 2.6) + 4
        centro = lado_surf / 2
        pontos = []

        for i in range(lados):
            a = p.angulo + i * math.tau / lados
            r = raio if lados == 6 else raio * (0.65 + 0.5 * (((i * 5) + int(abs(p.giro) * 40)) % 3) / 2)
            pontos.append((centro + math.cos(a) * r, centro + math.sin(a) * r))

        folha = pygame.Surface((lado_surf, lado_surf), pygame.SRCALPHA)
        alfa = int(255 * min(1.0, fracao * 1.6))
        pygame.draw.polygon(folha, (cor[0], cor[1], cor[2], int(alfa * 0.30)), pontos)
        pygame.draw.polygon(folha, (225, 248, 255, alfa), pontos, 2)
        tela.blit(folha, (int(p.x - centro), int(p.y - centro)))
