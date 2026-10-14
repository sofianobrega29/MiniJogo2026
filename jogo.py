from enum import Enum
from pathlib import Path
import math

import pygame

import reconhecimento
from clone import Feiticeira
from constantes import (
    LARGURA,
    ALTURA,
    FPS,
    ALTURA_CHAO,
    Y_PES_CHAO,
    BRANCO,
    AZUL_MAGICO,
    DEBUG_HITBOX,
)
from elementos import Cajado
from feiticos import CATALOGO, GESTOS, NOMES_EXIBICAO
from frieren import Maga

PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens"

ROXO = (125, 55, 210)
ROXO_CLARO = (190, 130, 255)


class Estado(Enum):
    JOGANDO = "jogando"
    VITORIA = "vitoria"
    DERROTA = "derrota"


class Jogo:
    """Uma partida completa: Maga contra a Feiticeira clone.

    Uso:
        resultado = Jogo(tela, relogio).executar()
        # resultado é "menu" (partida terminou) ou "sair" (fechou a janela)

    A classe também serve de "contexto" para os personagens e feitiços, que
    leem daqui: tempo (ms de jogo), area (retângulo da arena), feiticos (lista)
    e adicionar_feitico().
    """

    TEMPO_VOLTA_MENU = 6000      # ms na tela final antes de voltar ao menu sozinho
    TEMPO_MINIMO_FINAL = 700     # ms em que cliques/teclas são ignorados na tela final
    PAUSAR_MUNDO_NO_CAJADO = True  # True: o tempo para enquanto a Maga desenha o símbolo

    def __init__(self, tela, relogio):
        self.tela = tela
        self.relogio = relogio
        self.area = pygame.Rect(0, 0, LARGURA, ALTURA)

        self._carregar_recursos()
        self.reiniciar()

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------
    def _carregar_recursos(self):
        fundo_primeira = pygame.image.load(str(PASTA_IMAGENS / "Fundo" / "Arena.png")).convert()
        fundo_terceira = pygame.image.load(
            str(PASTA_IMAGENS / "Fundo" / "ParedeArena2D.jpeg")
        ).convert()
        vida = pygame.image.load(str(PASTA_IMAGENS / "UI" / "vida.png")).convert_alpha()

        self.fundo_primeira_pessoa = pygame.transform.scale(fundo_primeira, (LARGURA, ALTURA))
        self.fundo_terceira_pessoa = pygame.transform.scale(
            fundo_terceira, (LARGURA, ALTURA - ALTURA_CHAO)
        )
        self.icone_vida = pygame.transform.scale(vida, (45, 30))

        self.fonte_menor = pygame.font.SysFont(None, 28)
        self.fonte_dica = pygame.font.SysFont(None, 30)
        self.fonte_mensagem = pygame.font.SysFont(None, 44)
        self.fonte_titulo = pygame.font.SysFont("arial", 84, bold=True)
        self.fonte_subtitulo = pygame.font.SysFont("arial", 30)
        self.fonte_botao = pygame.font.SysFont("arial", 34, bold=True)

        self.cajado = Cajado()
        self.botao_menu = pygame.Rect(LARGURA // 2 - 170, ALTURA // 2 + 80, 340, 70)

    def reiniciar(self):
        self.tempo = 0           # tempo de jogo (ms); para quando o mundo está pausado
        self.tempo_real = 0      # tempo que sempre anda (mensagens, tela final)
        self.estado = Estado.JOGANDO
        self.tempo_no_final = 0

        self.maga = Maga(230, Y_PES_CHAO)
        self.clone = Feiticeira(950, 180)
        self.maga.oponente = self.clone
        self.clone.oponente = self.maga

        self.todos_sprites = pygame.sprite.Group()
        self.todos_sprites.add(self.maga, self.clone)

        self.feiticos = []

        self.modo_feitico = False
        self.desenhando = False
        self.pontos_magicos = []

        self.mensagem = ""
        self.mensagem_ate = 0

    def adicionar_feitico(self, feitico):
        self.feiticos.append(feitico)

    # ------------------------------------------------------------------
    # Laço principal
    # ------------------------------------------------------------------
    def executar(self):
        while True:
            dt = min(self.relogio.tick(FPS), 50)

            resultado = self.processar_eventos()

            if resultado:
                return resultado

            self.atualizar(dt)

            if self.estado != Estado.JOGANDO and self.tempo_no_final >= self.TEMPO_VOLTA_MENU:
                return "menu"

            self.desenhar()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def processar_eventos(self):
        """Devolve "sair", "menu" ou None."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if self.estado != Estado.JOGANDO:
                if self.tempo_no_final < self.TEMPO_MINIMO_FINAL:
                    continue

                clicou = (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and self.botao_menu.collidepoint(evento.pos)
                )
                apertou = evento.type == pygame.KEYDOWN and evento.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                )

                if clicou or apertou:
                    return "menu"

                continue

            if evento.type == pygame.KEYDOWN:
                self._tecla_pressionada(evento.key)

            if self.modo_feitico:
                self._mouse_no_modo_feitico(evento)

        return None

    def _tecla_pressionada(self, tecla):
        if tecla == pygame.K_f:
            if self.modo_feitico:
                self._sair_do_modo_feitico()
            else:
                self.modo_feitico = True
                self.desenhando = False
                self.pontos_magicos = []

        elif tecla == pygame.K_ESCAPE and self.modo_feitico:
            self._sair_do_modo_feitico()

        elif tecla in (pygame.K_w, pygame.K_UP) and not self.modo_feitico:
            self.maga.pressionar_cima()

    def _sair_do_modo_feitico(self):
        self.modo_feitico = False
        self.desenhando = False
        self.pontos_magicos = []

    def _mouse_no_modo_feitico(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.desenhando = True
            self.pontos_magicos = [evento.pos]

        elif evento.type == pygame.MOUSEMOTION and self.desenhando:
            self.pontos_magicos.append(evento.pos)

        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.desenhando:
            self._lancar_feitico_desenhado()

    def _lancar_feitico_desenhado(self):
        gesto = reconhecimento.reconhecer(self.pontos_magicos)
        self._sair_do_modo_feitico()

        if gesto is None:
            self._avisar("Símbolo não reconhecido. Tente de novo.")
            return

        nome = GESTOS[gesto]

        if self.maga.conjurar(nome, self) is not None:
            self._avisar(f"{NOMES_EXIBICAO[nome]}!")
            return

        restante = self.maga.recarga_restante(nome, self.tempo)
        self._avisar(f"{NOMES_EXIBICAO[nome]} recarregando ({math.ceil(restante / 1000)}s)")

    def _avisar(self, texto, duracao=1600):
        self.mensagem = texto
        self.mensagem_ate = self.tempo_real + duracao

    # ------------------------------------------------------------------
    # Atualização
    # ------------------------------------------------------------------
    def atualizar(self, dt):
        self.tempo_real += dt

        if self.estado != Estado.JOGANDO:
            self.tempo_no_final += dt
            return

        if self.modo_feitico and self.PAUSAR_MUNDO_NO_CAJADO:
            return

        self.tempo += dt
        self._atualizar_direcoes()

        self.maga.update(self)

        if self.clone.vivo:
            self.clone.update(self)

        for feitico in list(self.feiticos):
            feitico.update(self)

        self.feiticos = [f for f in self.feiticos if f.ativo]
        self._verificar_fim()

    def _atualizar_direcoes(self):
        if self.maga.rect.centerx < self.clone.rect.centerx:
            self.maga.direcao = "direita"
            self.clone.direcao = "esquerda"
        else:
            self.maga.direcao = "esquerda"
            self.clone.direcao = "direita"

    def _verificar_fim(self):
        if not self.maga.vivo:
            self._terminar(Estado.DERROTA)
        elif not self.clone.vivo:
            self.clone.kill()
            self._terminar(Estado.VITORIA)

    def _terminar(self, estado):
        self.estado = estado
        self.tempo_no_final = 0
        self._sair_do_modo_feitico()

    # ------------------------------------------------------------------
    # Desenho
    # ------------------------------------------------------------------
    def desenhar(self):
        if self.modo_feitico:
            self._desenhar_cajado()
        else:
            self._desenhar_arena()

        self._desenhar_interface()

        if self.estado != Estado.JOGANDO:
            self._desenhar_tela_final()

    def _desenhar_chao(self):
        pygame.draw.rect(
            self.tela, (255, 231, 176), (0, ALTURA - ALTURA_CHAO, LARGURA, ALTURA_CHAO)
        )

        for x in range(0, LARGURA, 60):
            pygame.draw.line(
                self.tela, (45, 42, 50), (x, ALTURA - ALTURA_CHAO), (x, ALTURA), 2
            )

        for y in range(ALTURA - ALTURA_CHAO, ALTURA, 40):
            pygame.draw.line(self.tela, (45, 42, 50), (0, y), (LARGURA, y), 2)

    def _desenhar_arena(self):
        self.tela.blit(self.fundo_terceira_pessoa, (0, 0))
        self._desenhar_chao()

        for sprite in self.todos_sprites:
            if sprite.visivel(self.tempo):
                self.tela.blit(sprite.image, sprite.rect)

            if DEBUG_HITBOX:
                pygame.draw.rect(self.tela, (0, 255, 0), sprite.hitbox, 2)

        for feitico in sorted(self.feiticos, key=lambda f: f.CAMADA):
            feitico.desenhar(self.tela)

    def _desenhar_cajado(self):
        self.tela.blit(self.fundo_primeira_pessoa, (0, 0))

        if len(self.pontos_magicos) > 1:
            pygame.draw.lines(self.tela, AZUL_MAGICO, False, self.pontos_magicos, 5)

        self.cajado.desenhar(self.tela)

        texto = "Desenhe: círculo = orbe | quadrado = parede | estrela = zoltraak | Z = raio"
        self._texto_com_fundo(texto, self.fonte_dica, (LARGURA // 2, ALTURA - 70))
        self._texto_com_fundo(
            "F ou ESC para cancelar", self.fonte_menor, (LARGURA // 2, ALTURA - 35)
        )

    def _texto_com_fundo(self, texto, fonte, centro):
        imagem = fonte.render(texto, True, BRANCO)
        retangulo = imagem.get_rect(center=centro)

        fundo = pygame.Surface((retangulo.width + 24, retangulo.height + 12), pygame.SRCALPHA)
        fundo.fill((10, 8, 20, 190))
        self.tela.blit(fundo, fundo.get_rect(center=centro))
        self.tela.blit(imagem, retangulo)

    # ---- interface -----------------------------------------------------
    def _desenhar_interface(self):
        self._desenhar_vidas_maga()
        self._desenhar_barra_vida_clone()
        self._desenhar_painel_feiticos()

        if not self.modo_feitico:
            estado_voo = "Voando" if self.maga.voando else "No chão"
            texto = self.fonte_menor.render(f"Estado da maga: {estado_voo}", True, BRANCO)
            self.tela.blit(texto, (20, 90))

        if self.tempo_real < self.mensagem_ate and self.mensagem:
            self._texto_com_fundo(self.mensagem, self.fonte_mensagem, (LARGURA // 2, 130))

    def _desenhar_vidas_maga(self):
        self.tela.blit(self.fonte_menor.render("MAGA", True, BRANCO), (20, 15))

        for i in range(max(0, self.maga.vida)):
            self.tela.blit(self.icone_vida, (20 + i * 50, 45))

    def _desenhar_barra_vida_clone(self):
        clone = self.clone
        largura_barra = 350
        altura_barra = 26
        x = LARGURA - largura_barra - 30
        y = 35

        vidas = max(0, min(clone.vida, clone.vida_maxima))
        proporcao = vidas / clone.vida_maxima if clone.vida_maxima > 0 else 0

        texto = self.fonte_menor.render(
            f"FEITICEIRA CLONE: {vidas}/{clone.vida_maxima}", True, BRANCO
        )
        self.tela.blit(texto, (x, 5))

        pygame.draw.rect(self.tela, (45, 35, 55), (x, y, largura_barra, altura_barra), border_radius=8)

        if int(largura_barra * proporcao) > 0:
            pygame.draw.rect(
                self.tela,
                (180, 50, 220),
                (x, y, int(largura_barra * proporcao), altura_barra),
                border_radius=8,
            )

        pygame.draw.rect(
            self.tela, (230, 210, 240), (x, y, largura_barra, altura_barra), width=2, border_radius=8
        )

    def _desenhar_painel_feiticos(self):
        """Quatro quadradinhos (um por feitiço) mostrando a recarga."""
        ordem = ["orbe", "parede", "zoltraak", "raio"]
        largura, altura, espaco = 118, 50, 6
        x = (LARGURA - (len(ordem) * largura + (len(ordem) - 1) * espaco)) // 2

        for nome in ordem:
            caixa = pygame.Rect(x, 12, largura, altura)
            restante = self.maga.recarga_restante(nome, self.tempo)
            pronto = restante == 0

            pygame.draw.rect(self.tela, (28, 20, 45), caixa, border_radius=8)

            if not pronto:
                fracao = restante / CATALOGO[nome].RECARGA
                preenchimento = pygame.Rect(caixa.x, caixa.y, int(caixa.width * (1 - fracao)), caixa.height)
                pygame.draw.rect(self.tela, (70, 50, 110), preenchimento, border_radius=8)

            cor = ROXO_CLARO if pronto else (150, 140, 165)
            pygame.draw.rect(self.tela, cor, caixa, width=2, border_radius=8)

            self._desenhar_icone(nome, (caixa.x + 24, caixa.centery), cor)
            rotulo = self.fonte_menor.render(NOMES_EXIBICAO[nome], True, BRANCO if pronto else (150, 140, 165))
            self.tela.blit(rotulo, rotulo.get_rect(midleft=(caixa.x + 46, caixa.centery)))

            x += largura + espaco

    def _desenhar_icone(self, nome, centro, cor):
        cx, cy = centro

        if nome == "orbe":
            pygame.draw.circle(self.tela, cor, centro, 10, 2)
        elif nome == "parede":
            pygame.draw.rect(self.tela, cor, (cx - 10, cy - 10, 20, 20), 2)
        elif nome == "zoltraak":
            pontas = [
                (cx + 12 * math.cos(math.radians(-90 + 72 * k)), cy + 12 * math.sin(math.radians(-90 + 72 * k)))
                for k in (0, 2, 4, 1, 3, 0)
            ]
            pygame.draw.lines(self.tela, cor, False, pontas, 2)
        else:
            pygame.draw.lines(
                self.tela,
                cor,
                False,
                [(cx - 9, cy - 9), (cx + 9, cy - 9), (cx - 9, cy + 9), (cx + 9, cy + 9)],
                2,
            )

    # ---- tela final ----------------------------------------------------
    def _desenhar_tela_final(self):
        escurecer = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        escurecer.fill((10, 10, 20, 205))
        self.tela.blit(escurecer, (0, 0))

        if self.estado == Estado.VITORIA:
            titulo, cor = "VITÓRIA!", (80, 255, 130)
            subtitulo = "Você derrotou a clone!"
        else:
            titulo, cor = "DERROTA", (255, 85, 85)
            subtitulo = "A Maga foi derrotada..."

        self._texto_centralizado(titulo, self.fonte_titulo, cor, (LARGURA // 2, ALTURA // 2 - 120))
        self._texto_centralizado(subtitulo, self.fonte_subtitulo, BRANCO, (LARGURA // 2, ALTURA // 2 - 40))

        restante = max(0, math.ceil((self.TEMPO_VOLTA_MENU - self.tempo_no_final) / 1000))
        self._texto_centralizado(
            f"Voltando ao menu em {restante}s...",
            self.fonte_menor,
            (190, 180, 205),
            (LARGURA // 2, ALTURA // 2 + 25),
        )

        mouse = pygame.mouse.get_pos()
        cor_botao = ROXO_CLARO if self.botao_menu.collidepoint(mouse) else ROXO
        pygame.draw.rect(self.tela, cor_botao, self.botao_menu, border_radius=14)
        pygame.draw.rect(self.tela, BRANCO, self.botao_menu, width=2, border_radius=14)
        self._texto_centralizado(
            "VOLTAR AO MENU", self.fonte_botao, BRANCO, self.botao_menu.center
        )

    def _texto_centralizado(self, texto, fonte, cor, centro):
        imagem = fonte.render(texto, True, cor)
        self.tela.blit(imagem, imagem.get_rect(center=centro))


if __name__ == "__main__":
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Confronto Mágico")
    Jogo(tela, pygame.time.Clock()).executar()
    pygame.quit()
