from pathlib import Path
import math

import pygame

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
    """Buraco negro (preto e laranja) aberto pela clone.

    Não causa dano: sobe até o topo da tela e puxa um pouco a Maga e os feitiços
    dela na direção dele. No chão a Maga só é puxada para os lados.
    """

    def __init__(self, origem, alvo, agora, destino=(LARGURA // 2, 130)):
        self.alvo = alvo  # quem é puxado (a Maga)
        self.posicao = pygame.Vector2(origem)
        self.destino = pygame.Vector2(destino)
        self.raio = 52
        self.criado = agora
        self.tempo = agora
        self.giro = 0.0
        self.alcance = 900         # px: além disso ele não puxa
        self.forca_maga = 1.0      # px por quadro (bem leve: a Maga anda a 5)
        self.giro_feitico = 1.1    # graus por quadro que ele curva os feitiços da Maga
        self._resto = pygame.Vector2(0, 0)

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

        falta = self.destino - self.posicao

        if falta.length() > 1.4:
            self.posicao += falta.normalize() * 1.4  # sobe devagar até o topo

        self._puxar_maga(ctx)

        for feitico in ctx.feiticos:
            if feitico.ativo and feitico.dono is self.alvo:
                feitico.ser_puxado(self, ctx)

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

    def desenhar(self, tela):
        crescimento = self.crescimento
        raio = int(self.raio * crescimento)

        if raio < 4:
            return

        lado = raio * 7
        c = lado // 2
        camada = pygame.Surface((lado, lado), pygame.SRCALPHA)

        # Brilho laranja em volta (círculos de fora para dentro, cada vez mais fortes).
        for i in range(12, 0, -1):
            pygame.draw.circle(camada, (255, 110, 20, max(5, 70 - i * 5)), (c, c), int(raio * (1.1 + i * 0.22)))

        # Braços espirais girando.
        for braco in range(4):
            pontos = []

            for j in range(26):
                t = j / 25
                angulo = math.radians(self.giro) + braco * math.tau / 4 + t * 3.4
                r = raio * (1.15 + t * 1.9)
                pontos.append((c + math.cos(angulo) * r, c + math.sin(angulo) * r * 0.62))

            pygame.draw.lines(camada, (255, 150, 40, 215), False, pontos, 4)
            pygame.draw.lines(camada, (255, 215, 130, 160), False, pontos[:14], 2)

        # Disco de acreção.
        disco = pygame.Rect(0, 0, int(raio * 4.2), int(raio * 1.25))
        disco.center = (c, c)
        pygame.draw.ellipse(camada, (255, 140, 30, 230), disco, 6)
        pygame.draw.ellipse(camada, (255, 225, 150, 255), disco.inflate(-10, -6), 2)

        # O buraco: borda laranja e centro preto, com o disco passando na frente.
        pygame.draw.circle(camada, (255, 170, 60, 255), (c, c), raio + 5)
        pygame.draw.circle(camada, (0, 0, 0, 255), (c, c), raio)
        pygame.draw.arc(camada, (255, 190, 90, 255), disco, math.radians(180), math.radians(360), 5)

        tela.blit(camada, camada.get_rect(center=(int(self.posicao.x), int(self.posicao.y))))
