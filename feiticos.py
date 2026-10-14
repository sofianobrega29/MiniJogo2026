"""Feitiços do jogo.

Todo feitiço herda de `Feitico` e é usado tanto pela Maga quanto pelo clone:
quem lança é o `dono` e quem sofre o efeito é o `alvo`.

Cada feitiço implementa:
    update(ctx)           -> avança o feitiço (ctx é o Jogo: tempo, area, feiticos)
    desenhar(tela)        -> desenha o feitiço
    ameaca_para(alvo,ctx) -> se for perigoso para `alvo`, devolve um vetor (x, y)
                             apontando para onde fugir; senão, None (a IA do clone usa)

Os feitiços são:
    OrbeExplosivo  (círculo)  projétil que explode ao tocar chão, parede ou alvo
    ParedeMagica   (quadrado) defesa temporária na frente de quem lançou
    Zoltraak       (estrela)  portal que dispara uma rajada de energia
    RaioRoxo       (Z)        raio que cai do céu depois de um aviso
"""

from functools import lru_cache
from pathlib import Path
import math
import random

import pygame

from constantes import (
    LARGURA,
    ALTURA,
    Y_EXPLOSAO_CHAO,
    ROXO_RAIO,
    ROXO_CLARO_RAIO,
)

PASTA_UI = Path(__file__).resolve().parent / "imagens" / "UI"


# --------------------------------------------------------------------------
# Funções auxiliares
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def carregar_imagem(nome, fator=1):
    """Carrega uma imagem de imagens/UI (com cache) e amplia sem borrar o pixel art."""
    imagem = pygame.image.load(str(PASTA_UI / nome)).convert_alpha()

    if fator != 1:
        largura, altura = imagem.get_size()
        imagem = pygame.transform.scale(
            imagem, (int(largura * fator), int(altura * fator))
        )

    return imagem


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def circulo_toca_retangulo(cx, cy, raio, retangulo):
    mais_proximo_x = limitar(cx, retangulo.left, retangulo.right)
    mais_proximo_y = limitar(cy, retangulo.top, retangulo.bottom)
    return math.hypot(cx - mais_proximo_x, cy - mais_proximo_y) <= raio


def _diferenca_angular(destino, origem):
    """Menor diferença entre dois ângulos em radianos, no intervalo (-pi, pi]."""
    diferenca = (destino - origem + math.pi) % (2 * math.pi) - math.pi
    return diferenca


# --------------------------------------------------------------------------
# Classe base
# --------------------------------------------------------------------------
class Feitico:
    NOME = ""
    RECARGA = 1000   # ms até poder lançar de novo
    DANO = 1
    BLOQUEAVEL = False  # a parede mágica consegue barrar este feitiço?
    CAMADA = 1       # ordem de desenho (menor = mais ao fundo)

    def __init__(self, dono, alvo, agora, erro=0):
        self.dono = dono
        self.alvo = alvo
        self.nascimento = agora
        self.erro = erro  # imprecisão da mira (usada pelo clone no começo da luta)
        self.ativo = True

    def idade(self, ctx):
        return ctx.tempo - self.nascimento

    @property
    def dano(self):
        limite = getattr(self.dono, "dano_maximo", None)
        return self.DANO if limite is None else min(self.DANO, limite)

    def paredes_inimigas(self, ctx):
        return [
            f
            for f in ctx.feiticos
            if isinstance(f, ParedeMagica) and f.ativo and f.dono is not self.dono
        ]

    def update(self, ctx):
        raise NotImplementedError

    def desenhar(self, tela):
        raise NotImplementedError

    def ameaca_para(self, alvo, ctx):
        return None


# --------------------------------------------------------------------------
# Ataque 1: orbe explosivo (círculo)
# --------------------------------------------------------------------------
class Explosao(Feitico):
    """Explosão em área criada quando o orbe encosta em algo."""

    NOME = "explosao"
    CAMADA = 4
    DURACAO = 450
    RAIO_DANO = 95

    def __init__(self, dono, alvo, agora, x, y, normal, dano):
        super().__init__(dono, alvo, agora)
        self.x = x
        self.y = y
        self.normal = normal  # direção (unitária) em que a cúpula "abre", saindo da superfície
        self.dano_explosao = dano
        self.aplicou_dano = False
        self.progresso = 0.0

        # A imagem original é uma meia-cúpula com a base reta embaixo.
        # Giramos para que a base fique encostada na superfície atingida.
        graus = math.degrees(math.atan2(-normal[0], -normal[1]))
        original = carregar_imagem("pixilart-drawing (2).png")
        self.meia_altura = original.get_height() / 2
        self.base = pygame.transform.rotate(original, graus)

    @property
    def dano(self):
        return self.dano_explosao

    def update(self, ctx):
        self.progresso = min(1.0, self.idade(ctx) / self.DURACAO)

        if self.progresso >= 1:
            self.ativo = False
            return

        if not self.aplicou_dano:
            self.aplicou_dano = True

            if circulo_toca_retangulo(self.x, self.y, self.RAIO_DANO, self.alvo.hitbox):
                self.alvo.receber_dano(self.dano, ctx.tempo)

    def desenhar(self, tela):
        progresso = self.progresso
        fator = 5 + 5 * math.sqrt(progresso)
        largura, altura = self.base.get_size()
        imagem = pygame.transform.scale(
            self.base, (max(1, int(largura * fator)), max(1, int(altura * fator)))
        )
        imagem.set_alpha(int(255 * (1 - progresso)))

        # A base da cúpula fica na superfície; o centro da imagem avança pela normal
        # metade da altura (já ampliada) da cúpula.
        avanco = self.meia_altura * fator
        centro = (
            self.x + self.normal[0] * avanco,
            self.y + self.normal[1] * avanco,
        )
        tela.blit(imagem, imagem.get_rect(center=(int(centro[0]), int(centro[1]))))

        raio_anel = int(self.RAIO_DANO * (0.3 + 0.7 * progresso))
        pygame.draw.circle(tela, (255, 90, 90), (int(self.x), int(self.y)), raio_anel, 4)

        if progresso < 0.4:
            pygame.draw.circle(
                tela,
                (255, 220, 200),
                (int(self.x), int(self.y)),
                int(40 * (1 - progresso / 0.4)) + 6,
            )


class OrbeExplosivo(Feitico):
    NOME = "orbe"
    RECARGA = 900
    DANO = 1
    BLOQUEAVEL = True
    CAMADA = 3

    VELOCIDADE = 11
    RAIO = 24
    GIRO_MAXIMO = math.radians(2.4)  # quanto ele consegue curvar por quadro
    TEMPO_TELEGUIADO = 600           # ms; depois segue reto (aí dá para desviar)

    def __init__(self, dono, alvo, agora, erro=0):
        super().__init__(dono, alvo, agora, erro)
        self.x, self.y = dono.hitbox.center
        alvo_x, alvo_y = alvo.hitbox.center
        self.angulo = math.atan2(alvo_y - self.y, alvo_x - self.x) + math.radians(erro)
        self.imagem = carregar_imagem("pixilart-drawing (1).png", 3)
        self.rastro = []

    @property
    def retangulo(self):
        return pygame.Rect(
            int(self.x - self.RAIO), int(self.y - self.RAIO), self.RAIO * 2, self.RAIO * 2
        )

    def update(self, ctx):
        if self.idade(ctx) < self.TEMPO_TELEGUIADO:
            alvo_x, alvo_y = self.alvo.hitbox.center
            desejado = math.atan2(alvo_y - self.y, alvo_x - self.x)
            diferenca = _diferenca_angular(desejado, self.angulo)
            self.angulo += limitar(diferenca, -self.GIRO_MAXIMO, self.GIRO_MAXIMO)

        self.rastro.append((self.x, self.y))
        self.rastro = self.rastro[-7:]

        dx = math.cos(self.angulo)
        dy = math.sin(self.angulo)
        self.x += dx * self.VELOCIDADE
        self.y += dy * self.VELOCIDADE

        # 1) parede mágica do inimigo
        for parede in self.paredes_inimigas(ctx):
            if parede.rect.colliderect(self.retangulo):
                parede.absorver(ctx.tempo)
                self._explodir(ctx, self.x, self.y, (-dx, -dy))
                return

        # 2) o próprio alvo
        if self.retangulo.colliderect(self.alvo.hitbox):
            self._explodir(ctx, self.x, self.y, (-dx, -dy))
            return

        # 3) chão e paredes da arena
        if self.y + self.RAIO >= Y_EXPLOSAO_CHAO:
            self._explodir(ctx, self.x, Y_EXPLOSAO_CHAO, (0, -1))
        elif self.x - self.RAIO <= ctx.area.left:
            self._explodir(ctx, ctx.area.left, self.y, (1, 0))
        elif self.x + self.RAIO >= ctx.area.right:
            self._explodir(ctx, ctx.area.right, self.y, (-1, 0))
        elif self.y - self.RAIO <= ctx.area.top:
            self._explodir(ctx, self.x, ctx.area.top, (0, 1))

    def _explodir(self, ctx, x, y, normal):
        self.ativo = False
        ctx.adicionar_feitico(
            Explosao(self.dono, self.alvo, ctx.tempo, x, y, normal, self.dano)
        )

    def desenhar(self, tela):
        for i, (rx, ry) in enumerate(self.rastro):
            raio = 4 + i * 2
            cor = (120 + i * 15, 20, 30)
            pygame.draw.circle(tela, cor, (int(rx), int(ry)), raio)

        tela.blit(self.imagem, self.imagem.get_rect(center=(int(self.x), int(self.y))))

    def ameaca_para(self, alvo, ctx):
        if self.alvo is not alvo:
            return None

        alvo_x, alvo_y = alvo.hitbox.center
        vetor_x = alvo_x - self.x
        vetor_y = alvo_y - self.y
        dx = math.cos(self.angulo)
        dy = math.sin(self.angulo)

        distancia = math.hypot(vetor_x, vetor_y)
        aproximando = vetor_x * dx + vetor_y * dy > 0

        if distancia > 400 or not aproximando:
            return None

        # Foge na perpendicular da trajetória, para o lado em que o alvo já está.
        perpendicular = (-dy, dx)
        lado = vetor_x * perpendicular[0] + vetor_y * perpendicular[1]

        if lado < 0:
            perpendicular = (-perpendicular[0], -perpendicular[1])

        return perpendicular


# --------------------------------------------------------------------------
# Defesa: parede mágica (quadrado)
# --------------------------------------------------------------------------
class ParedeMagica(Feitico):
    NOME = "parede"
    RECARGA = 6000
    DANO = 0
    CAMADA = 0

    DURACAO = 4000
    LARGURA_PAREDE = 84
    ALTURA_PAREDE = 250
    RESISTENCIA = 3  # quantos golpes ela aguenta antes de quebrar

    def __init__(self, dono, alvo, agora, erro=0):
        super().__init__(dono, alvo, agora, erro)
        self.durabilidade = self.RESISTENCIA
        self.flash_ate = 0
        self.restante = self.DURACAO
        self.brilhando = False

        sentido = 1 if alvo.rect.centerx >= dono.rect.centerx else -1
        x = dono.rect.centerx + sentido * (dono.rect.width // 2 + 55)

        self.rect = pygame.Rect(0, 0, self.LARGURA_PAREDE, self.ALTURA_PAREDE)
        self.rect.center = (int(x), dono.rect.centery)
        self.rect.clamp_ip(pygame.Rect(0, 0, LARGURA, ALTURA))

        self.superficie = self._criar_superficie()

    def _criar_superficie(self):
        """Sprite do escudo: favo de hexágonos (imagens/UI/escudo.png)."""
        imagem = carregar_imagem("escudo.png")
        return pygame.transform.smoothscale(imagem, self.rect.size)

    def absorver(self, agora):
        self.durabilidade -= 1
        self.flash_ate = agora + 140

        if self.durabilidade <= 0:
            self.ativo = False

    def update(self, ctx):
        self.restante = self.DURACAO - self.idade(ctx)
        self.brilhando = ctx.tempo < self.flash_ate

        if self.restante <= 0:
            self.ativo = False

    def desenhar(self, tela):
        restante = self.restante
        alfa = 255 if restante > 500 else int(255 * max(0, restante) / 500)

        if restante < 1200 and (restante // 120) % 2 == 0:
            alfa = int(alfa * 0.55)  # pisca avisando que vai acabar

        imagem = self.superficie.copy()
        imagem.set_alpha(alfa)
        tela.blit(imagem, self.rect)

        if self.brilhando:
            clarao = self.superficie.copy()
            clarao.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_MAX)  # sprite todo branco
            tela.blit(clarao, self.rect)

        # Rachaduras conforme perde resistência.
        for i in range(self.RESISTENCIA - self.durabilidade):
            y = self.rect.top + 60 + i * 70
            pontos = [
                (self.rect.left + 4, y),
                (self.rect.centerx + 4, y + 16),
                (self.rect.centerx - 6, y + 32),
                (self.rect.right - 4, y + 50),
            ]
            pygame.draw.lines(tela, (255, 255, 255), False, pontos, 2)


# --------------------------------------------------------------------------
# Ataque 2: zoltraak (estrela)
# --------------------------------------------------------------------------
class Zoltraak(Feitico):
    NOME = "zoltraak"
    RECARGA = 7000
    DANO = 3
    BLOQUEAVEL = True
    CAMADA = 1

    CARGA = 700        # ms com o portal aberto antes de disparar
    DISPARO = 550      # ms com a rajada ativa
    DESVANECE = 250    # ms de encerramento
    ALTURA_RAJADA = 56
    CRESCIMENTO = 120  # ms que a rajada leva para chegar ao fim do alcance

    def __init__(self, dono, alvo, agora, erro=0):
        super().__init__(dono, alvo, agora, erro)

        self.sentido = 1 if alvo.rect.centerx >= dono.rect.centerx else -1
        self.portal_x = int(
            limitar(dono.rect.centerx + self.sentido * (dono.rect.width // 2 + 60), 60, LARGURA - 60)
        )
        self.portal_y = int(limitar(alvo.hitbox.centery + erro, 110, ALTURA - 110))

        self.portal = carregar_imagem("zoltrak-pixilart.png", 5)
        self.sprite_rajada = carregar_imagem("zoltrak-pixilart (1).png")

        self.rect_total = None   # alcance total da rajada (definido ao disparar)
        self.rect_visivel = None  # parte da rajada já visível
        self.acertou = False
        self._escala_portal = 0.2
        self._espessura = 1.0

    # ---- lógica --------------------------------------------------------
    def update(self, ctx):
        idade = self.idade(ctx)
        total = self.CARGA + self.DISPARO + self.DESVANECE

        if idade >= total:
            self.ativo = False
            return

        # Animação do portal: abre no começo e fecha no fim.
        if idade < 250:
            self._escala_portal = 0.2 + 0.8 * idade / 250
        elif idade > total - self.DESVANECE:
            self._escala_portal = max(0.2, (total - idade) / self.DESVANECE)
        else:
            self._escala_portal = 1.0

        if idade < self.CARGA:
            return

        if self.rect_total is None:
            self._disparar(ctx)

        fracao = limitar((idade - self.CARGA) / self.CRESCIMENTO, 0, 1)
        comprimento = int(self.rect_total.width * fracao)

        if self.sentido > 0:
            self.rect_visivel = pygame.Rect(
                self.rect_total.left, self.rect_total.top, comprimento, self.rect_total.height
            )
        else:
            self.rect_visivel = pygame.Rect(
                self.rect_total.right - comprimento,
                self.rect_total.top,
                comprimento,
                self.rect_total.height,
            )

        if idade > self.CARGA + self.DISPARO:
            self._espessura = max(0.15, (total - idade) / self.DESVANECE)

        if not self.acertou and self.rect_visivel.colliderect(self.alvo.hitbox):
            if self.alvo.receber_dano(self.dano, ctx.tempo):
                self.acertou = True

    def _disparar(self, ctx):
        """Define até onde a rajada vai: borda da arena ou a parede mágica inimiga."""
        topo = self.portal_y - self.ALTURA_RAJADA // 2
        faixa = pygame.Rect(0, topo, LARGURA, self.ALTURA_RAJADA)

        if self.sentido > 0:
            inicio, fim = self.portal_x, ctx.area.right
        else:
            inicio, fim = ctx.area.left, self.portal_x

        for parede in self.paredes_inimigas(ctx):
            if not parede.rect.colliderect(faixa):
                continue

            if self.sentido > 0 and parede.rect.left >= self.portal_x:
                if parede.rect.left < fim:
                    fim = parede.rect.left
                    parede.absorver(ctx.tempo)
            elif self.sentido < 0 and parede.rect.right <= self.portal_x:
                if parede.rect.right > inicio:
                    inicio = parede.rect.right
                    parede.absorver(ctx.tempo)

        self.rect_total = pygame.Rect(inicio, topo, max(1, fim - inicio), self.ALTURA_RAJADA)

    # ---- desenho -------------------------------------------------------
    def desenhar(self, tela):
        if self.rect_visivel is not None and self.rect_visivel.width > 2:
            self._desenhar_rajada(tela)

        largura, altura = self.portal.get_size()
        escala = self._escala_portal
        portal = pygame.transform.scale(
            self.portal, (max(2, int(largura * escala)), max(2, int(altura * escala)))
        )
        tela.blit(portal, portal.get_rect(center=(self.portal_x, self.portal_y)))

    def _desenhar_rajada(self, tela):
        retangulo = self.rect_visivel
        altura = max(4, int(retangulo.height * self._espessura))
        comprimento = retangulo.width

        largura_ponta = 12
        largura_corpo = max(1, comprimento - largura_ponta)

        corpo = self.sprite_rajada.subsurface((0, 0, 16, 20))
        ponta = self.sprite_rajada.subsurface((16, 0, 4, 20))

        superficie = pygame.Surface((comprimento, altura), pygame.SRCALPHA)
        superficie.blit(pygame.transform.scale(corpo, (largura_corpo, altura)), (0, 0))

        if comprimento > largura_ponta:
            superficie.blit(
                pygame.transform.scale(ponta, (largura_ponta, altura)),
                (comprimento - largura_ponta, 0),
            )

        if self.sentido < 0:
            superficie = pygame.transform.flip(superficie, True, False)

        if self.sentido > 0:
            posicao = superficie.get_rect(midleft=retangulo.midleft)
        else:
            posicao = superficie.get_rect(midright=retangulo.midright)

        tela.blit(superficie, posicao)

    def ameaca_para(self, alvo, ctx):
        if self.alvo is not alvo or self.idade(ctx) >= self.CARGA:
            return None

        do_lado_certo = self.sentido * (alvo.hitbox.centerx - self.portal_x) > 0
        margem = self.ALTURA_RAJADA / 2 + alvo.hitbox.height / 2 + 25
        proximo = abs(alvo.hitbox.centery - self.portal_y) < margem

        if not (do_lado_certo and proximo):
            return None

        return (0, -1) if alvo.hitbox.centery <= self.portal_y else (0, 1)


# --------------------------------------------------------------------------
# Ataque 3: raio roxo (Z)
# --------------------------------------------------------------------------
class RaioRoxo(Feitico):
    NOME = "raio"
    RECARGA = 3000
    DANO = 2
    BLOQUEAVEL = False  # cai do céu, a parede não protege
    CAMADA = 2

    AVISO = 550      # ms mostrando onde o raio vai cair
    GOLPE = 250      # ms com o raio ativo
    DESVANECE = 200
    LARGURA_COLUNA = 90

    def __init__(self, dono, alvo, agora, erro=0):
        super().__init__(dono, alvo, agora, erro)
        self.x = int(limitar(alvo.hitbox.centerx + erro, 50, LARGURA - 50))
        self.coluna = pygame.Rect(
            self.x - self.LARGURA_COLUNA // 2, 0, self.LARGURA_COLUNA, Y_EXPLOSAO_CHAO
        )
        self.acertou = False
        self.pontos = []
        self.ramos = []
        self._ultima_forma = -1000
        self._fase = "aviso"
        self._progresso = 0.0
        self._aleatorio = random.Random()
        self.marcador = pygame.Surface(self.coluna.size, pygame.SRCALPHA)

    def update(self, ctx):
        idade = self.idade(ctx)
        total = self.AVISO + self.GOLPE + self.DESVANECE

        if idade >= total:
            self.ativo = False
            return

        if idade < self.AVISO:
            self._fase = "aviso"
            self._progresso = idade / self.AVISO
            return

        self._fase = "golpe" if idade < self.AVISO + self.GOLPE else "fim"
        self._progresso = limitar((idade - self.AVISO - self.GOLPE) / self.DESVANECE, 0, 1)

        if not self.acertou and self.coluna.colliderect(self.alvo.hitbox):
            if self.alvo.receber_dano(self.dano, ctx.tempo):
                self.acertou = True

        if ctx.tempo - self._ultima_forma >= 45:
            self._ultima_forma = ctx.tempo
            self._gerar_forma()

    def _gerar_forma(self):
        """Sorteia um traçado em zigue-zague de cima até o chão."""
        sorteio = self._aleatorio
        segmentos = 14
        passo = Y_EXPLOSAO_CHAO / segmentos

        self.pontos = [(self.x + sorteio.randint(-8, 8), 0)]

        for i in range(1, segmentos):
            desvio = sorteio.randint(-34, 34)
            self.pontos.append((self.x + desvio, int(i * passo)))

        self.pontos.append((self.x, Y_EXPLOSAO_CHAO))

        # Alguns ramos menores saindo do raio principal.
        self.ramos = []

        for _ in range(2):
            indice = sorteio.randint(3, segmentos - 4)
            ponto = self.pontos[indice]
            lado = sorteio.choice((-1, 1))
            self.ramos.append([
                ponto,
                (ponto[0] + lado * sorteio.randint(25, 45), ponto[1] + sorteio.randint(25, 45)),
                (ponto[0] + lado * sorteio.randint(50, 85), ponto[1] + sorteio.randint(55, 100)),
            ])

    def desenhar(self, tela):
        if self._fase == "aviso":
            self._desenhar_aviso(tela)
        else:
            self._desenhar_raio(tela)

    def _desenhar_aviso(self, tela):
        intensidade = self._progresso

        self.marcador.fill((ROXO_RAIO[0], ROXO_RAIO[1], ROXO_RAIO[2], int(25 + 60 * intensidade)))
        tela.blit(self.marcador, self.coluna.topleft)

        for y in range(0, Y_EXPLOSAO_CHAO, 36):
            pygame.draw.line(tela, ROXO_CLARO_RAIO, (self.x, y), (self.x, y + 18), 3)

        largura = int(self.LARGURA_COLUNA * (0.5 + 0.5 * intensidade))
        marca = pygame.Rect(0, 0, largura, 26)
        marca.center = (self.x, Y_EXPLOSAO_CHAO)
        pygame.draw.ellipse(tela, ROXO_RAIO, marca, 4)

    def _desenhar_raio(self, tela):
        if len(self.pontos) < 2:
            return

        fino = 1.0 - self._progresso * 0.8

        for largura, cor in (
            (int(26 * fino), (95, 35, 190)),
            (int(14 * fino), ROXO_RAIO),
            (max(2, int(5 * fino)), (245, 235, 255)),
        ):
            pygame.draw.lines(tela, cor, False, self.pontos, max(1, largura))

        for ramo in self.ramos:
            pygame.draw.lines(tela, ROXO_CLARO_RAIO, False, ramo, max(1, int(4 * fino)))

        impacto = pygame.Rect(0, 0, int(150 * fino), int(40 * fino))
        impacto.center = (self.x, Y_EXPLOSAO_CHAO)
        pygame.draw.ellipse(tela, ROXO_CLARO_RAIO, impacto)

    def ameaca_para(self, alvo, ctx):
        if self.alvo is not alvo or self.idade(ctx) >= self.AVISO - 120:
            return None

        folga = self.LARGURA_COLUNA / 2 + alvo.hitbox.width / 2 + 30

        if abs(alvo.hitbox.centerx - self.x) >= folga:
            return None

        return (1, 0) if alvo.hitbox.centerx >= self.x else (-1, 0)


# --------------------------------------------------------------------------
# Catálogo
# --------------------------------------------------------------------------
CATALOGO = {
    classe.NOME: classe
    for classe in (OrbeExplosivo, ParedeMagica, Zoltraak, RaioRoxo)
}

# Símbolo desenhado -> feitiço
GESTOS = {
    "circulo": "orbe",
    "quadrado": "parede",
    "estrela": "zoltraak",
    "raio": "raio",
}

NOMES_EXIBICAO = {
    "orbe": "Orbe",
    "parede": "Parede",
    "zoltraak": "Zoltraak",
    "raio": "Raio",
}


def criar_feitico(nome, dono, alvo, agora, erro=0):
    return CATALOGO[nome](dono, alvo, agora, erro)
