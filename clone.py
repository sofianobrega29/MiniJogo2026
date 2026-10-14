from pathlib import Path
import math
import random

import pygame

from constantes import LARGURA, ALTURA
from entidade import Combatente
from feiticos import limitar


def interpolar(facil, dificil, dificuldade):
    return facil + (dificil - facil) * dificuldade


class Feiticeira(Combatente):
    """O clone da Maga: faz tudo o que a Frieren faz, mas de forma automática.

    Quanto menos vida ela tem, maior a `dificuldade` (de 0 a 1) e mais ela:
        - ataca rápido e com mira melhor;
        - desvia dos feitiços da Maga;
        - usa a parede mágica para se defender;
        - libera mais feitiços (raio com 8 vidas, zoltraak com 5).

    Os valores de cada nível estão em PARAMETROS, no formato (início, fim):
    o primeiro vale com a vida cheia e o segundo com 1 de vida.
    """

    VIDA_MAXIMA = 11
    VIDA_LIBERA_RAIO = 8
    VIDA_LIBERA_ZOLTRAAK = 5
    TEMPO_REGENERACAO = 5000  # ms sem levar dano para recuperar 1 vida

    PARAMETROS = {
        "intervalo_acao": (2600, 800),   # ms entre um ataque e outro
        "velocidade": (3.0, 6.5),        # pixels por quadro
        "chance_desvio": (0.10, 0.70),   # chance de tentar desviar de um feitiço
        "chance_defesa": (0.0, 0.30),    # chance de erguer a parede (se ela estiver pronta)
        "erro_mira": (1.0, 0.0),         # 1 = mira bem ruim, 0 = mira perfeita
        "fator_recarga": (1.6, 0.7),     # multiplica a recarga dos feitiços
        "tempo_reacao": (450, 120),      # ms entre perceber o perigo e começar a desviar
    }

    # Quanto cada feitiço pode errar a mira quando o erro_mira é 1.
    ERRO_MAXIMO = {"orbe": 28, "raio": 170, "zoltraak": 150}  # graus, pixels, pixels

    PESOS_ATAQUE = {"orbe": 5, "raio": 2, "zoltraak": 1.5}

    def __init__(self, x, y):
        super().__init__(x, y, vida_maxima=self.VIDA_MAXIMA)
        self.dano_maximo = 1  # os feitiços do clone tiram no máximo 1 vida da Maga

        pasta_imagens = Path(__file__).resolve().parent / "imagens" / "Personagens"
        spritesheet = pygame.image.load(str(pasta_imagens / "CloneFly.png")).convert_alpha()

        self.frames_voando = []

        for i in range(3):
            quadro = spritesheet.subsurface((i * 48, 0, 44, 64)).copy()
            largura, altura = quadro.get_size()
            self.frames_voando.append(
                pygame.transform.scale(quadro, (largura * 3, altura * 3))
            )

        self.direcao = "esquerda"
        self.tempo_animacao = 0
        self.quadro_atual = 0
        self.tempo_voo = 0
        self.canto_atual = 0
        self.ultimo_canto = 0
        self.ultimo_dano = 0

        self.limite_esquerdo = 80
        self.limite_direito = LARGURA - 140
        self.limite_superior = 100
        self.limite_inferior = ALTURA - 220

        self.proxima_acao = 1500
        self.desvio = None            # (x, y) de destino do desvio atual
        self.desvio_inicio = 0
        self.desvio_fim = 0
        self._avaliados = set()       # feitiços inimigos a que já reagiu

        self.definir_imagem(self.frames_voando[0])
        self.rect.topleft = (x, y)

    # ---- dificuldade ---------------------------------------------------
    @property
    def dificuldade(self):
        """0 com a vida cheia, 1 com 1 de vida."""
        if self.vida_maxima <= 1:
            return 1.0

        return limitar((self.vida_maxima - self.vida) / (self.vida_maxima - 1), 0.0, 1.0)

    def valor(self, nome):
        facil, dificil = self.PARAMETROS[nome]
        return interpolar(facil, dificil, self.dificuldade)

    def feiticos_liberados(self):
        liberados = ["orbe"]

        if self.vida <= self.VIDA_LIBERA_RAIO:
            liberados.append("raio")

        if self.vida <= self.VIDA_LIBERA_ZOLTRAAK:
            liberados.append("zoltraak")

        return liberados

    # ---- ciclo principal -----------------------------------------------
    def ao_receber_dano(self, agora):
        self.ultimo_dano = agora
        self.proxima_acao = max(self.proxima_acao, agora + 400)  # pequena pausa ao ser atingida

    def update(self, ctx):
        self.tempo_voo += 0.06

        self._regenerar(ctx.tempo)
        self._animar()
        self._reagir_a_ameacas(ctx)
        self._atacar(ctx)
        self._mover(ctx)
        self.mudar_direcao()

    def _regenerar(self, agora):
        if self.vida < self.vida_maxima and agora - self.ultimo_dano >= self.TEMPO_REGENERACAO:
            self.vida += 1
            self.ultimo_dano = agora

    def _animar(self):
        self.tempo_animacao += 1

        if self.tempo_animacao >= 30:
            self.quadro_atual = (self.quadro_atual + 1) % len(self.frames_voando)
            self.tempo_animacao = 0

        self.definir_imagem(self.frames_voando[self.quadro_atual])

    # ---- ataque --------------------------------------------------------
    def _atacar(self, ctx):
        if ctx.tempo < self.proxima_acao:
            return

        escolhido = self._escolher_feitico(ctx.tempo)

        if escolhido is None:
            self.proxima_acao = ctx.tempo + 300
            return

        erro = random.uniform(-1, 1) * self.ERRO_MAXIMO[escolhido] * self.valor("erro_mira")
        self.conjurar(escolhido, ctx, self.valor("fator_recarga"), erro)

        intervalo = self.valor("intervalo_acao") * random.uniform(0.8, 1.25)
        self.proxima_acao = ctx.tempo + int(intervalo)

    def _escolher_feitico(self, agora):
        opcoes = [
            nome
            for nome in self.feiticos_liberados()
            if self.pode_conjurar(nome, agora)
        ]

        if not opcoes:
            return None

        pesos = [self.PESOS_ATAQUE[nome] for nome in opcoes]
        return random.choices(opcoes, weights=pesos)[0]

    # ---- defesa e desvio -----------------------------------------------
    def _reagir_a_ameacas(self, ctx):
        self._avaliados = {f for f in self._avaliados if f.ativo}

        for feitico in ctx.feiticos:
            if feitico.dono is self or not feitico.ativo or feitico in self._avaliados:
                continue

            fuga = feitico.ameaca_para(self, ctx)

            if fuga is None:
                continue

            # Cada feitiço só é avaliado uma vez: ou ela reage, ou deixa passar.
            self._avaliados.add(feitico)
            self._decidir_reacao(feitico, fuga, ctx)

    def _decidir_reacao(self, feitico, fuga, ctx):
        if feitico.BLOQUEAVEL and self.pode_conjurar("parede", ctx.tempo):
            if random.random() < self.valor("chance_defesa"):
                self.conjurar("parede", ctx, self.valor("fator_recarga"))
                return

        if random.random() < self.valor("chance_desvio"):
            self._iniciar_desvio(fuga, ctx.tempo)

    def _iniciar_desvio(self, fuga, agora):
        distancia = 210
        melhor = None

        # Testa fugir para o lado indicado e para o oposto; fica com o que dá mais espaço.
        for sinal in (1, -1):
            x = limitar(self.rect.x + fuga[0] * distancia * sinal, self.limite_esquerdo, self.limite_direito)
            y = limitar(self.rect.y + fuga[1] * distancia * sinal, self.limite_superior, self.limite_inferior)
            deslocamento = math.hypot(x - self.rect.x, y - self.rect.y)

            if sinal == 1 and deslocamento >= distancia * 0.6:
                melhor = (x, y, deslocamento)
                break

            if melhor is None or deslocamento > melhor[2]:
                melhor = (x, y, deslocamento)

        self.desvio = (melhor[0], melhor[1])
        self.desvio_inicio = agora + int(self.valor("tempo_reacao"))
        self.desvio_fim = self.desvio_inicio + 900

    # ---- movimento -----------------------------------------------------
    def _mover(self, ctx):
        velocidade = self.valor("velocidade")

        if self.desvio is not None:
            if ctx.tempo >= self.desvio_fim:
                self.desvio = None
            elif ctx.tempo >= self.desvio_inicio:
                # Chega ao ponto de desvio e fica lá até o perigo passar.
                self._ir_para(self.desvio[0], self.desvio[1], velocidade * 2.2)
                return

        self._mover_normal(ctx, velocidade)

    def _mover_normal(self, ctx, velocidade):
        maga = self.oponente
        agora = ctx.tempo

        if maga.voando:
            alvo_x = self.limite_esquerdo if maga.rect.centerx > LARGURA // 2 else self.limite_direito

            if agora - self.ultimo_canto >= 1500:
                self.canto_atual = 1 - self.canto_atual
                self.ultimo_canto = agora

            alvo_y = self.limite_superior if self.canto_atual == 0 else self.limite_inferior
        else:
            alvo_x = self.limite_direito if maga.rect.centerx < LARGURA // 2 else self.limite_esquerdo
            alvo_y = 180 + math.sin(self.tempo_voo) * 25

        self._ir_para(alvo_x, alvo_y, velocidade)

    def _ir_para(self, x, y, velocidade):
        """Anda em direção ao ponto (x, y). Devolve True quando chega."""
        passo_x = limitar(x - self.rect.x, -velocidade, velocidade)
        passo_y = limitar(y - self.rect.y, -velocidade, velocidade)

        self.rect.x += int(round(passo_x))
        self.rect.y += int(round(passo_y))

        return abs(x - self.rect.x) < 6 and abs(y - self.rect.y) < 6
