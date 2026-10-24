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
    Cura           (+)        dois traços cruzados em pé: recupera 1 vida de quem lançou
    OrbeGelo       (X)        dois traços em diagonal: orbe que não causa dano, mas
                              deixa o alvo congelado (mais lento) por alguns segundos

Cura e gelo são feitiços de 2 traços (veja reconhecimento.classificar_cruz).
"""

from functools import lru_cache
from pathlib import Path
import math
import random

import pygame

import visuais
from sons import SONS
from constantes import (
    LARGURA,
    ALTURA,
    Y_EXPLOSAO_CHAO,
    ROXO_RAIO,
    ROXO_CLARO_RAIO,
)

PASTA_UI = Path(__file__).resolve().parent / "imagens" / "UI"
BRANCO_GELO = (245, 252, 255)


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


def _particulas(ctx):
    """Sistema de partículas do jogo (pode não existir em contextos de teste)."""
    return getattr(ctx, "particulas", None)


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

    @classmethod
    def util(cls, dono):
        """Vale a pena lançar agora? (a cura, por exemplo, não serve com a vida cheia)"""
        return True

    def ser_puxado(self, buraco, ctx):
        """O buraco negro da clone chama isto nos feitiços da Maga. Por padrão não faz nada."""


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
                parede.absorver(ctx.tempo, ctx, (self.x, self.y))
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
        SONS.tocar_efeito("explosao")
        ctx.adicionar_feitico(
            Explosao(self.dono, self.alvo, ctx.tempo, x, y, normal, self.dano)
        )

    def ser_puxado(self, buraco, ctx):
        """O buraco negro curva um pouco a trajetória do orbe na direção dele."""
        puxao, distancia = buraco.forca_em((self.x, self.y))

        if puxao.length_squared() == 0:
            return

        desejado = math.atan2(puxao.y, puxao.x)
        limite = math.radians(buraco.giro_feitico) * (0.4 + 0.6 * (1 - distancia / buraco.alcance))
        diferenca = _diferenca_angular(desejado, self.angulo)
        self.angulo += limitar(diferenca, -limite, limite)

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
        self.sentido = sentido  # de que lado vêm os ataques
        x = dono.rect.centerx + sentido * (dono.rect.width // 2 + 55)

        self.rect = pygame.Rect(0, 0, self.LARGURA_PAREDE, self.ALTURA_PAREDE)
        self.rect.center = (int(x), dono.rect.centery)
        self.rect.clamp_ip(pygame.Rect(0, 0, LARGURA, ALTURA))

        self.superficie = self._criar_superficie()

    def _criar_superficie(self):
        """Sprite do escudo: favo de hexágonos (imagens/UI/escudo.png)."""
        imagem = carregar_imagem("escudo.png")
        return pygame.transform.smoothscale(imagem, self.rect.size)

    def absorver(self, agora, ctx=None, ponto=None):
        """Segura um golpe. Cada golpe arranca hexágonos do escudo; no último ele se estilhaça."""
        self.durabilidade -= 1
        self.flash_ate = agora + 140
        quebrou = self.durabilidade <= 0

        self._perder_hexagonos(ctx, ponto or self.rect.center, 3 if quebrou else 2)

        if quebrou:
            self.ativo = False
            self._estilhacar(ctx)

    def _perder_hexagonos(self, ctx, ponto, quantidade):
        """Apaga hexágonos do sprite perto do impacto e solta cacos de vidro."""
        local_x = limitar(ponto[0] - self.rect.left, 14, self.rect.width - 14)
        local_y = limitar(ponto[1] - self.rect.top, 14, self.rect.height - 14)

        for i in range(quantidade):
            deslocamento = (0, 0) if i == 0 else (random.uniform(-34, 34), random.uniform(-34, 34))
            centro = (local_x + deslocamento[0], local_y + deslocamento[1])
            visuais.furar_hexagono(self.superficie, centro, 21 if i == 0 else random.randint(13, 18))

        particulas = _particulas(ctx)

        if particulas is not None:
            saida = math.pi if self.sentido > 0 else 0.0  # os cacos voam para longe de quem atacou
            particulas.explosao(
                self.rect.left + local_x, self.rect.top + local_y, 12, 5.2, 46, 2.3,
                [(110, 205, 255), (180, 235, 255), (150, 220, 255)], cor_fim=(30, 80, 180),
                gravidade=0.17, formas=("hex", "caco", "caco", "cristal"), angulo=saida, abertura=math.pi * 1.0,
            )

    def _estilhacar(self, ctx):
        """O escudo quebra inteiro, como vidro: chuva de hexágonos e cacos."""
        particulas = _particulas(ctx)

        if particulas is None:
            return

        for _ in range(46):
            x = random.uniform(self.rect.left, self.rect.right)
            y = random.uniform(self.rect.top, self.rect.bottom)
            para_fora = math.atan2(y - self.rect.centery, x - self.rect.centerx) + random.uniform(-0.6, 0.6)
            velocidade = random.uniform(1.5, 6.5)
            particulas.emitir(
                x, y, math.cos(para_fora) * velocidade, math.sin(para_fora) * velocidade - 1.0,
                vida=random.randint(34, 62), tamanho=random.uniform(2.0, 3.6),
                cor=random.choice(((110, 205, 255), (170, 230, 255), (140, 215, 255))), cor_fim=(30, 80, 180),
                forma=random.choice(("hex", "hex", "caco", "caco", "cristal")), gravidade=0.2,
            )

        particulas.explosao(
            self.rect.centerx, self.rect.centery, 16, 7.0, 40, 2.0, [(255, 255, 255), (190, 238, 255)],
            cor_fim=(40, 100, 220), chance_estrela=0.7, gravidade=0.05,
        )

    def update(self, ctx):
        self.restante = self.DURACAO - self.idade(ctx)
        self.brilhando = ctx.tempo < self.flash_ate

        if self.restante <= 0:
            self.ativo = False
            particulas = _particulas(ctx)

            if particulas is not None:  # no fim natural só se apaga em faíscas
                particulas.explosao(
                    self.rect.centerx, self.rect.centery, 12, 2.5, 34, 2.0, [(190, 235, 255), (255, 255, 255)],
                    cor_fim=(40, 100, 220), formas=("cristal", "estrela"), gravidade=-0.02,
                )

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
    ALTURA_RAJADA = 84  # feixe grosso, como no anime
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
        self._cauda = 0

    # ---- lógica --------------------------------------------------------
    def update(self, ctx):
        idade = self.idade(ctx)
        total = self.CARGA + self.DISPARO + self.DESVANECE

        if idade >= total:
            self.ativo = False
            particulas = _particulas(ctx)

            if particulas is not None:
                particulas.explosao(
                    self.portal_x, self.portal_y, 16, 4.5, 36, 2.2, [(255, 255, 255), (170, 225, 255)],
                    cor_fim=(30, 70, 200), chance_estrela=0.6, atrito=0.95,
                )

            return

        # Animação do portal: abre no começo e fecha no fim.
        if idade < 250:
            self._escala_portal = 0.2 + 0.8 * idade / 250
        elif idade > total - self.DESVANECE:
            self._escala_portal = max(0.2, (total - idade) / self.DESVANECE)
        else:
            self._escala_portal = 1.0

        particulas = _particulas(ctx)

        if idade < self.CARGA:
            self._particulas_da_carga(particulas, idade)
            return

        if self.rect_total is None:
            self._disparar(ctx)

        fracao = limitar((idade - self.CARGA) / self.CRESCIMENTO, 0, 1)
        cabeca = int(self.rect_total.width * fracao)

        # No final a cauda avança em direção à ponta e a luz que fica para trás se desfaz em estrelas.
        fim_disparo = self.CARGA + self.DISPARO
        p_fim = limitar((idade - fim_disparo) / self.DESVANECE, 0, 1) if idade > fim_disparo else 0.0
        self._espessura = 1.0 - 0.75 * p_fim
        self._cauda = int(self.rect_total.width * p_fim ** 1.5)
        comprimento = max(0, cabeca - self._cauda)

        if self.sentido > 0:
            self.rect_visivel = pygame.Rect(
                self.rect_total.left + self._cauda, self.rect_total.top, comprimento, self.rect_total.height
            )
        else:
            self.rect_visivel = pygame.Rect(
                self.rect_total.right - cabeca, self.rect_total.top, comprimento, self.rect_total.height
            )

        if particulas is not None and comprimento > 4:
            self._particulas_do_feixe(particulas, fracao, p_fim)

        if not self.acertou and self.rect_visivel.colliderect(self.alvo.hitbox):
            if self.alvo.receber_dano(self.dano, ctx.tempo):
                self.acertou = True

    def _particulas_da_carga(self, particulas, idade):
        """Enquanto o portal carrega, faíscas de mana são sugadas para dentro dele."""
        if particulas is None or idade < 180:
            return

        for _ in range(1 + (idade > self.CARGA - 280)):
            angulo = random.uniform(0, math.tau)
            distancia = random.uniform(70, 140)
            vida = 18
            particulas.emitir(
                self.portal_x + math.cos(angulo) * distancia * 0.7, self.portal_y + math.sin(angulo) * distancia,
                -math.cos(angulo) * distancia * 0.7 / vida, -math.sin(angulo) * distancia / vida,
                vida=vida, tamanho=random.uniform(1.4, 2.4), cor=random.choice(((170, 225, 255), (255, 255, 255))),
                cor_fim=(20, 50, 140), forma="estrela" if random.random() < 0.3 else "quadrado", atrito=1.0,
            )

    def _particulas_do_feixe(self, particulas, fracao, p_fim):
        r = self.rect_visivel
        cores = [(255, 255, 255), (190, 235, 255), (120, 200, 255)]

        if p_fim == 0:
            # faíscas saltando das bordas do feixe enquanto ele está aceso
            for _ in range(3):
                x = random.uniform(r.left, r.right)
                y = r.centery + random.choice((-1, 1)) * r.height * random.uniform(0.35, 0.65) * self._espessura
                particulas.emitir(
                    x, y, -self.sentido * random.uniform(0.2, 1.4), (y - r.centery) / r.height * random.uniform(1.0, 3.0),
                    vida=random.randint(16, 32), tamanho=random.uniform(1.2, 2.4), cor=random.choice(cores),
                    cor_fim=(30, 70, 200), forma="estrela" if random.random() < 0.3 else "quadrado",
                )

            if fracao < 1:  # clarão na ponta enquanto o feixe corre
                ponta = r.right if self.sentido > 0 else r.left
                particulas.explosao(ponta, r.centery, 4, 4.0, 14, 2.0, cores, cor_fim=(40, 100, 230), chance_estrela=0.5)
        else:
            # cauda se desfazendo: estrelinhas do resto da luz, flutuando para trás e para cima
            cauda_x = r.left if self.sentido > 0 else r.right
            para_tras = math.pi if self.sentido > 0 else 0.0

            for _ in range(9):
                y = r.centery + random.uniform(-0.5, 0.5) * r.height * self._espessura * 1.6
                particulas.emitir(
                    cauda_x + random.uniform(-6, 6), y,
                    math.cos(para_tras + random.uniform(-1.1, 1.1)) * random.uniform(0.6, 3.2),
                    random.uniform(-2.6, 0.8), vida=random.randint(34, 58), tamanho=random.uniform(2.4, 4.2),
                    cor=random.choice(cores), cor_fim=(30, 70, 210),
                    forma="estrela" if random.random() < 0.55 else "quadrado", gravidade=-0.03, atrito=0.96,
                )

    def ser_puxado(self, buraco, ctx):
        """Enquanto o portal carrega, o buraco negro desloca um pouco a altura do disparo."""
        if self.rect_total is not None:
            return

        puxao, _ = buraco.forca_em((self.portal_x, self.portal_y))
        self._deriva = getattr(self, "_deriva", 0.0) + puxao.y
        passo = int(self._deriva)
        self._deriva -= passo
        self.portal_y = int(limitar(self.portal_y + passo, 110, ALTURA - 110))

    def _disparar(self, ctx):
        """Define até onde a rajada vai: borda da arena ou a parede mágica inimiga."""
        SONS.tocar_efeito("estrela")
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
                    parede.absorver(ctx.tempo, ctx, (parede.rect.left, self.portal_y))
            elif self.sentido < 0 and parede.rect.right <= self.portal_x:
                if parede.rect.right > inicio:
                    inicio = parede.rect.right
                    parede.absorver(ctx.tempo, ctx, (parede.rect.right, self.portal_y))

        self.rect_total = pygame.Rect(inicio, topo, max(1, fim - inicio), self.ALTURA_RAJADA)

    # ---- desenho -------------------------------------------------------
    def desenhar(self, tela):
        if self.rect_visivel is not None and self.rect_visivel.width > 2:
            afunilar = 50 + int(160 * (1 - self._espessura))
            visuais.desenhar_feixe(
                tela, self.rect_visivel, self._espessura, self.sentido, afunilar, pygame.time.get_ticks()
            )

        largura, altura = self.portal.get_size()
        escala = self._escala_portal
        visuais.brilho_elipse(
            tela, (self.portal_x, self.portal_y), largura * escala * 0.9, altura * escala * 0.9, (70, 150, 255), 8, 100
        )
        portal = pygame.transform.scale(
            self.portal, (max(2, int(largura * escala)), max(2, int(altura * escala)))
        )
        tela.blit(portal, portal.get_rect(center=(self.portal_x, self.portal_y)))

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
        self._golpeou = False
        self._som_tocado = False
        self._flash = 0.0

    def update(self, ctx):
        idade = self.idade(ctx)
        total = self.AVISO + self.GOLPE + self.DESVANECE

        if idade >= total:
            self.ativo = False
            return

        particulas = _particulas(ctx)

        if idade < self.AVISO:
            self._fase = "aviso"
            self._progresso = idade / self.AVISO

            if particulas is not None and self._aleatorio.random() < 0.5:  # estalinhos de energia no chão, carregando
                particulas.emitir(
                    self.x + self._aleatorio.uniform(-self.LARGURA_COLUNA / 2, self.LARGURA_COLUNA / 2), Y_EXPLOSAO_CHAO,
                    self._aleatorio.uniform(-0.6, 0.6), self._aleatorio.uniform(-2.5, -0.8), vida=14, tamanho=1.6,
                    cor=ROXO_CLARO_RAIO, cor_fim=(60, 20, 140), forma="faisca",
                )

            return

        self._fase = "golpe" if idade < self.AVISO + self.GOLPE else "fim"

        if not self._som_tocado:   # o trovão soa quando o raio cai, não durante o aviso
            self._som_tocado = True
            SONS.tocar_efeito("raio")
        self._progresso = limitar((idade - self.AVISO - self.GOLPE) / self.DESVANECE, 0, 1)
        self._flash = max(0.0, 1.0 - (idade - self.AVISO) / 90)

        if particulas is not None:
            self._particulas_do_raio(particulas)

        if not self.acertou and self.coluna.colliderect(self.alvo.hitbox):
            if self.alvo.receber_dano(self.dano, ctx.tempo):
                self.acertou = True

        if ctx.tempo - self._ultima_forma >= 30:
            self._ultima_forma = ctx.tempo
            self._gerar_forma()

    def _particulas_do_raio(self, particulas):
        """Faíscas elétricas: uma explosão no impacto e fagulhas saltando do raio, que caem como brasas."""
        cores = [(255, 250, 255), (215, 180, 255), (160, 100, 255)]

        if not self._golpeou:
            self._golpeou = True
            particulas.explosao(
                self.x, Y_EXPLOSAO_CHAO, 30, 8.0, 32, 2.2, cores, cor_fim=(60, 20, 150), gravidade=0.22,
                angulo=-math.pi / 2, abertura=math.pi * 0.95, formas=("faisca", "faisca", "estrela", "quadrado"),
            )

        if len(self.pontos) < 3:
            return

        quantidade = 2 if self._fase == "golpe" else 4  # no fim o raio se desfaz soltando mais fagulhas

        for _ in range(quantidade):
            x, y = self._aleatorio.choice(self.pontos[1:-1])
            lado = self._aleatorio.choice((-1, 1))
            particulas.emitir(
                x, y, lado * self._aleatorio.uniform(1.5, 5.0), self._aleatorio.uniform(-1.5, 1.0),
                vida=self._aleatorio.randint(8, 18), tamanho=self._aleatorio.uniform(1.2, 2.2),
                cor=self._aleatorio.choice(cores), cor_fim=(70, 30, 160), forma="faisca",
                gravidade=0.18 if self._fase == "fim" else 0.0,
            )

    def ser_puxado(self, buraco, ctx):
        """Durante o aviso, o buraco negro desloca um pouco o ponto onde o raio vai cair."""
        if self._fase != "aviso":
            return

        puxao, _ = buraco.forca_em((self.x, Y_EXPLOSAO_CHAO / 2))  # meio da coluna do raio
        self._deriva = getattr(self, "_deriva", 0.0) + puxao.x
        passo = int(self._deriva)
        self._deriva -= passo
        self.x = int(limitar(self.x + passo, 50, LARGURA - 50))
        self.coluna.centerx = self.x

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
        fino = 1.0 - self._progresso * 0.8
        fase_fim = self._progresso if self._fase == "fim" else 0.0
        visuais.desenhar_relampago(
            tela, self.pontos, self.ramos, fino, fase_fim, self._aleatorio,
            ROXO_RAIO, ROXO_CLARO_RAIO, Y_EXPLOSAO_CHAO, self.x, self._flash,
        )

    def ameaca_para(self, alvo, ctx):
        if self.alvo is not alvo or self.idade(ctx) >= self.AVISO - 120:
            return None

        folga = self.LARGURA_COLUNA / 2 + alvo.hitbox.width / 2 + 30

        if abs(alvo.hitbox.centerx - self.x) >= folga:
            return None

        return (1, 0) if alvo.hitbox.centerx >= self.x else (-1, 0)


# --------------------------------------------------------------------------
# Cura (cruz +)
# --------------------------------------------------------------------------
class Cura(Feitico):
    """Recupera 1 vida de quem lançou na hora; o resto é um feixe de luz verde que sobe rápido."""

    NOME = "cura"
    RECARGA = 15000
    DANO = 0
    CAMADA = 5

    CRESCIMENTO = 110   # ms que o feixe leva para subir
    SEGURA = 170        # ms aceso
    DURACAO = 800       # ms no total (o resto é a luz se desfazendo)
    LARGURA_FEIXE = 78

    def __init__(self, dono, alvo, agora, erro=0):
        super().__init__(dono, alvo, agora, erro)
        self.curou = dono.curar(1)

        if self.curou:
            SONS.tocar_efeito("cura")
        self.idade_atual = 0
        self._brilhou = False

    @classmethod
    def util(cls, dono):
        return dono.vivo and dono.vida < dono.vida_maxima

    def update(self, ctx):
        self.idade_atual = self.idade(ctx)

        if self.idade_atual >= self.DURACAO:
            self.ativo = False
            return

        particulas = _particulas(ctx)

        if particulas is None:
            return

        corpo = self.dono.hitbox
        verdes = [(190, 255, 205), (255, 255, 255), (110, 240, 150)]

        if not self._brilhou:
            self._brilhou = True
            particulas.explosao(
                corpo.centerx, corpo.bottom - 6, 20, 5.0, 30, 2.2, verdes, cor_fim=(30, 140, 80),
                angulo=-math.pi / 2, abertura=math.pi * 0.9, chance_estrela=0.5, gravidade=-0.02,
            )

        if self.CRESCIMENTO <= self.idade_atual < self.CRESCIMENTO + self.SEGURA + 250:
            for _ in range(3):  # estrelinhas verdes subindo pelo feixe
                particulas.emitir(
                    corpo.centerx + random.uniform(-self.LARGURA_FEIXE * 0.45, self.LARGURA_FEIXE * 0.45),
                    random.uniform(max(0, corpo.top - 300), corpo.bottom), random.uniform(-0.4, 0.4),
                    random.uniform(-3.2, -1.2), vida=random.randint(22, 40), tamanho=random.uniform(1.8, 3.2),
                    cor=random.choice(verdes), cor_fim=(30, 140, 80), forma="estrela" if random.random() < 0.5 else "quadrado",
                )

    def desenhar(self, tela):
        corpo = self.dono.hitbox
        idade = self.idade_atual
        p_cresce = limitar(idade / self.CRESCIMENTO, 0, 1)
        p_fim = limitar((idade - self.CRESCIMENTO - self.SEGURA) / (self.DURACAO - self.CRESCIMENTO - self.SEGURA), 0, 1)

        altura_total = corpo.bottom
        cabeca = int(altura_total * p_cresce)
        cauda = int(altura_total * p_fim ** 1.4)  # a cauda sobe e a luz vai se apagando
        altura = cabeca - cauda

        if altura > 8:
            visuais.desenhar_coluna(
                tela, corpo.centerx, corpo.bottom - cauda, altura, self.LARGURA_FEIXE, 1.0 - 0.8 * p_fim,
                60 + 140 * p_fim, pygame.time.get_ticks(), visuais.PALETA_VERDE,
            )

        if p_fim < 1:  # halo verde no chão, onde a luz nasce
            visuais.brilho_elipse(tela, (corpo.centerx, corpo.bottom - 4), 190 * (1 - 0.5 * p_fim), 46, (80, 240, 140), 8, 110)


# --------------------------------------------------------------------------
# Gelo (X)
# --------------------------------------------------------------------------
class EstilhacosGelo(Feitico):
    """Efeito visual: estilhaços de gelo quando o orbe de gelo acerta."""

    NOME = "estilhacos_gelo"
    DANO = 0
    CAMADA = 4
    DURACAO = 500

    def __init__(self, dono, alvo, agora, x, y):
        super().__init__(dono, alvo, agora)
        self.x = x
        self.y = y
        self.progresso = 0.0

    def update(self, ctx):
        self.progresso = min(1.0, self.idade(ctx) / self.DURACAO)

        if self.progresso >= 1:
            self.ativo = False

    def desenhar(self, tela):
        raio = 20 + 70 * math.sqrt(self.progresso)
        tamanho = max(2, int(10 * (1 - self.progresso)))

        for i in range(10):
            angulo = i * math.tau / 10 + 0.3
            x = self.x + math.cos(angulo) * raio
            y = self.y + math.sin(angulo) * raio
            losango = [(x, y - tamanho * 1.6), (x + tamanho, y), (x, y + tamanho * 1.6), (x - tamanho, y)]
            pygame.draw.polygon(tela, (190, 235, 255), losango)
            pygame.draw.polygon(tela, BRANCO_GELO, losango, 1)

        pygame.draw.circle(tela, (150, 215, 255), (int(self.x), int(self.y)), int(raio * 0.55), 3)


class OrbeGelo(OrbeExplosivo):
    """Floco de gelo veloz: não causa dano. Se acertar, o alvo fica congelado (bem mais lento)."""

    NOME = "gelo"
    RECARGA = 9000
    DANO = 0
    BLOQUEAVEL = True
    CAMADA = 3

    VELOCIDADE = 16
    RAIO = 20

    def update(self, ctx):
        super().update(ctx)
        particulas = _particulas(ctx)

        if particulas is not None and self.ativo:  # rastro de cristais de gelo
            for _ in range(2):
                particulas.emitir(
                    self.x + random.uniform(-8, 8), self.y + random.uniform(-8, 8),
                    random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), vida=random.randint(14, 26),
                    tamanho=random.uniform(1.8, 3.2), cor=random.choice(((255, 255, 255), (190, 235, 255), (140, 210, 255))),
                    cor_fim=(40, 90, 200), forma=random.choice(("cristal", "estrela", "quadrado")),
                )

    def _explodir(self, ctx, x, y, normal):
        """Chamado quando o floco encosta em algo. Só congela se foi o alvo."""
        self.ativo = False
        SONS.tocar_efeito("gelo")

        if self.retangulo.colliderect(self.alvo.hitbox):
            self.alvo.congelar(ctx.tempo)

        ctx.adicionar_feitico(EstilhacosGelo(self.dono, self.alvo, ctx.tempo, x, y))
        particulas = _particulas(ctx)

        if particulas is not None:
            particulas.explosao(
                x, y, 22, 6.0, 38, 2.4, [(255, 255, 255), (190, 235, 255), (130, 205, 255)], cor_fim=(40, 90, 200),
                formas=("cristal", "estrela", "quadrado", "caco"), gravidade=0.06,
            )

    def desenhar(self, tela):
        visuais.desenhar_floco(tela, (int(self.x), int(self.y)), self.RAIO + 12, pygame.time.get_ticks() / 190)


# --------------------------------------------------------------------------
# Catálogo
# --------------------------------------------------------------------------
CATALOGO = {
    classe.NOME: classe
    for classe in (OrbeExplosivo, ParedeMagica, Zoltraak, RaioRoxo, Cura, OrbeGelo)
}

# Símbolo desenhado -> feitiço
GESTOS = {
    "circulo": "orbe",
    "quadrado": "parede",
    "estrela": "zoltraak",
    "raio": "raio",
    "cura": "cura",   # cruz (+), dois traços
    "gelo": "gelo",   # X, dois traços
}

NOMES_EXIBICAO = {
    "orbe": "Orbe",
    "parede": "Parede",
    "zoltraak": "Zoltraak",
    "raio": "Raio",
    "cura": "Cura",
    "gelo": "Gelo",
}


def criar_feitico(nome, dono, alvo, agora, erro=0):
    return CATALOGO[nome](dono, alvo, agora, erro)
