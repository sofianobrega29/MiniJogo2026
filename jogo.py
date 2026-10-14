<<<<<<< Updated upstream
=======
from enum import Enum
>>>>>>> Stashed changes
from pathlib import Path
import math

import pygame

import reconhecimento
from clone import Feiticeira
<<<<<<< Updated upstream
from sons import SistemaSonoro

pygame.init()

BASE_DIR = Path(__file__).resolve().parent

# Imagens das telas inicial, vitória e derrota
fundo_vitoria = pygame.image.load(
    str(BASE_DIR / "imagens" / "capa_vitória.png")
).convert()

fundo_derrota = pygame.image.load(
    str(BASE_DIR / "imagens" / "capa_derrota.png")
).convert()

fundo_inicial = pygame.image.load(
    str(BASE_DIR / "imagens" / "capa_inicial.png")
).convert()

fundo_vitoria = pygame.transform.scale(
    fundo_vitoria, (LARGURA, ALTURA)
)
fundo_derrota = pygame.transform.scale(
    fundo_derrota, (LARGURA, ALTURA)
)
fundo_inicial = pygame.transform.scale(
    fundo_inicial, (LARGURA, ALTURA)
)

audio = SistemaSonoro()
audio.iniciar_musica()
audio.diminuir_volume()

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

RELOGIO = pygame.time.Clock()

fundo_primeira_pessoa = pygame.image.load(
    str(BASE_DIR / "imagens/Fundo/Arena.png")
).convert()

fundo_terceira_pessoa = pygame.image.load(
    str(BASE_DIR / "imagens/Fundo/ParedeArena2D.jpeg")
).convert()

vida_img = pygame.image.load(
    str(BASE_DIR / "imagens/UI/vida.png")
).convert_alpha()

vida_img = pygame.transform.scale(vida_img, (45, 30))

vidas_clone_img = {
    i: pygame.image.load(
        str(BASE_DIR / f"imagens/UI/inimigo_{i}.png")
    ).convert_alpha()
    for i in range(1, 12)
}

vidas_clone_img[0] = pygame.image.load(
    str(BASE_DIR / "imagens/UI/inimigo_vazio.png")
).convert_alpha()

fundo_primeira_pessoa = pygame.transform.scale(
    fundo_primeira_pessoa, (LARGURA, ALTURA)
=======
from constantes import (
    LARGURA,
    ALTURA,
    FPS,
    ALTURA_CHAO,
    Y_PES_CHAO,
    BRANCO,
    AZUL_MAGICO,
    DEBUG_HITBOX,
>>>>>>> Stashed changes
)
from elementos import Cajado
from feiticos import CATALOGO, GESTOS, NOMES_EXIBICAO
from frieren import Maga

PASTA_IMAGENS = Path(__file__).resolve().parent / "imagens"

ROXO = (125, 55, 210)
ROXO_CLARO = (190, 130, 255)


<<<<<<< Updated upstream
def reproduzir_video_vitoria(tela):
    """Reproduz o vídeo de vitória, incluindo o áudio original."""

    if not CAMINHO_VIDEO_VITORIA.is_file():
        print(
            f"Vídeo de vitória não encontrado: "
            f"{CAMINHO_VIDEO_VITORIA}"
        )
        return True

    caminho_audio_temporario = None

    try:
        with VideoFileClip(str(CAMINHO_VIDEO_VITORIA)) as video:
            if video.audio is not None:
                arquivo_temporario = tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    delete=False
                )
                caminho_audio_temporario = arquivo_temporario.name
                arquivo_temporario.close()

                video.audio.write_audiofile(
                    caminho_audio_temporario,
                    fps=44100,
                    nbytes=2,
                    codec="pcm_s16le",
                    logger=None
                )

            pygame.mixer.music.stop()

            if caminho_audio_temporario is not None:
                pygame.mixer.music.load(caminho_audio_temporario)
                pygame.mixer.music.play()

            relogio_video = pygame.time.Clock()
            inicio = pygame.time.get_ticks()
            fps = video.fps if video.fps and video.fps > 0 else 30

            while True:
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.mixer.music.stop()
                        return False

                tempo = (
                    pygame.time.get_ticks() - inicio
                ) / 1000.0

                if tempo >= video.duration:
                    break

                quadro = np.array(
                    video.get_frame(tempo),
                    dtype=np.uint8
                )

                superficie = pygame.surfarray.make_surface(
                    np.transpose(quadro, (1, 0, 2))
                )

                superficie = pygame.transform.scale(
                    superficie,
                    tela.get_size()
                )

                tela.blit(superficie, (0, 0))
                pygame.display.flip()
                relogio_video.tick(fps)

            pygame.mixer.music.stop()
            return True

    except Exception as erro:
        print(f"Erro ao reproduzir o vídeo de vitória: {erro}")
        return True

    finally:
        if (
            caminho_audio_temporario is not None
            and os.path.exists(caminho_audio_temporario)
        ):
            try:
                os.remove(caminho_audio_temporario)
            except OSError:
                pass
=======
class Estado(Enum):
    JOGANDO = "jogando"
    VITORIA = "vitoria"
    DERROTA = "derrota"
>>>>>>> Stashed changes


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

<<<<<<< Updated upstream
    if razao_percurso > 3.45:
        return "estrela"

    if 0.65 <= proporcao <= 1.45:
        if razao_percurso >= 2.45:
            return "quadrado"

        return "circulo"

    return None


def desenhar_vidas_maga(tela, maga):
    tela.blit(
        fonte_pequena.render("MAGA", True, BRANCO),
        (20, 15)
    )

    for i in range(max(0, maga.vida)):
        tela.blit(vida_img, (20 + i * 50, 45))


def desenhar_barra_vida_clone(tela, clone):
    x, y = LARGURA - 380, 35

    vidas = max(0, min(clone.vida, clone.vida_maxima))

    texto = fonte_pequena.render(
        f"FEITICEIRA CLONE: {vidas}/{clone.vida_maxima}",
        True,
        BRANCO
    )

    tela.blit(texto, (x, 5))
    tela.blit(vidas_clone_img[vidas], (x, y))


def novo_jogo():
    maga = Maga(150, ALTURA - 200)

    # Passa o sistema de áudio para a clone.
    clone = Feiticeira(950, 180, audio)

    return maga, clone, Cajado()


maga, feiticeira, cajado = novo_jogo()

modo_feitico = False
desenhando = False
pontos_magicos = []

projeteis = []
rajadas = []
parede_maga = None

estado_jogo = "jogando"
tempo_fim = 0

botao_menu = pygame.Rect(
    LARGURA // 2 - 170,
    ALTURA // 2 + 45,
    340,
    60
)

ultimo_toque_w_voando = 0
rodando = True


while rodando:
    dt = RELOGIO.tick(60)
    agora = pygame.time.get_ticks()

    if maga.rect.centerx < feiticeira.rect.centerx:
        maga.direcao = "direita"
        feiticeira.direcao = "esquerda"
    else:
        maga.direcao = "esquerda"
        feiticeira.direcao = "direita"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
            break

        if estado_jogo in ("vitoria", "derrota"):
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and botao_menu.collidepoint(event.pos)
            ):
                rodando = False

            elif (
                event.type == pygame.KEYDOWN
                and event.key in (
=======
                clicou = (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                    and self.botao_menu.collidepoint(evento.pos)
                )
                apertou = evento.type == pygame.KEYDOWN and evento.key in (
>>>>>>> Stashed changes
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                )

                if clicou or apertou:
                    return "menu"

<<<<<<< Updated upstream
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f and not modo_feitico:
                modo_feitico = True
                pontos_magicos = []

            if (
                not modo_feitico
                and event.key in (pygame.K_w, pygame.K_UP)
            ):
                if maga.voando:
                    if (
                        ultimo_toque_w_voando
                        and agora - ultimo_toque_w_voando <= 400
                    ):
                        maga.voando = False
                        maga.pulando = True
                        maga.no_chao = False
                        maga.velocidade_y = 0
                        ultimo_toque_w_voando = 0
                    else:
                        ultimo_toque_w_voando = agora

                elif maga.no_chao:
                    maga.velocidade_y = maga.forca_pulo
                    maga.no_chao = False
                    maga.pulando = True
                    maga.contagem_w = 0

                elif maga.pulando and not maga.voando:
                    maga.voando = True
                    maga.pulando = False
                    maga.velocidade_y = 0
                    maga.tempo_voo = 0
                    ultimo_toque_w_voando = 0

        if modo_feitico:
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                desenhando = True
                pontos_magicos = [event.pos]

            elif (
                event.type == pygame.MOUSEMOTION
                and desenhando
            ):
                pontos_magicos.append(event.pos)

            elif (
                event.type == pygame.MOUSEBUTTONUP
                and event.button == 1
                and desenhando
            ):
                desenhando = False
                simbolo = reconhecer_simbolo(pontos_magicos)

                if simbolo == "circulo":
                    projeteis.append(
                        ProjetilMagico(
                            maga.rect.center,
                            feiticeira.rect.center,
                            tipo="explosao"
                        )
                    )

                elif simbolo == "quadrado":
                    parede_maga = ParedeMagica(maga)

                elif simbolo == "estrela":
                    rajadas.append(
                        RajadaZoltraak(
                            maga.rect.center,
                            feiticeira.rect.center
                        )
                    )
                    audio.tocar_efeito("zoltrak")

                elif simbolo == "raio":
                    rajadas.append(
                        RajadaZoltraak(
                            maga.rect.center,
                            feiticeira.rect.center,
                            velocidade=22
                        )
                    )
                    rajadas[-1].tipo_raio = True

                modo_feitico = False
                pontos_magicos = []

    if not rodando:
        break

    if estado_jogo == "jogando":
        if parede_maga and not parede_maga.ativa():
            parede_maga = None

        if not modo_feitico and maga.vida > 0:
            maga.update(TELA)

        if feiticeira.vida > 0:
            feiticeira.update(maga, projeteis)
            feiticeira.atualizar_magias(maga)

        for p in projeteis[:]:
            if (
                pygame.time.get_ticks() < feiticeira.escudo_ate
                and p.rect.colliderect(
                    feiticeira.rect.inflate(32, 30)
                )
            ):
                p.ativo = False
            else:
                p.update(feiticeira)

            if not p.ativo:
                projeteis.remove(p)

        for r in rajadas[:]:
            if (
                pygame.time.get_ticks() < feiticeira.escudo_ate
                and r.rect.colliderect(
                    feiticeira.rect.inflate(32, 30)
                )
            ):
                r.ativo = False
            else:
                r.update(feiticeira)

            if not r.ativo:
                rajadas.remove(r)

        for tiro in feiticeira.projeteis[:]:
            tiro.update()

            if not TELA.get_rect().colliderect(tiro.rect):
                feiticeira.projeteis.remove(tiro)
=======
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
                    pontos = [(int(inicio.x), int(inicio.y))]
=======
        if self.estado != Estado.JOGANDO:
            self._desenhar_tela_final()
>>>>>>> Stashed changes

    def _desenhar_chao(self):
        pygame.draw.rect(
            self.tela, (255, 231, 176), (0, ALTURA - ALTURA_CHAO, LARGURA, ALTURA_CHAO)
        )

        for x in range(0, LARGURA, 60):
            pygame.draw.line(
                self.tela, (45, 42, 50), (x, ALTURA - ALTURA_CHAO), (x, ALTURA), 2
            )

<<<<<<< Updated upstream
    else:
        # As imagens já contêm o texto; não desenha botões ou textos extras.
        if estado_jogo == "vitoria":
            TELA.blit(fundo_vitoria, (0, 0))
        else:
            TELA.blit(fundo_derrota, (0, 0))

        restante = max(
            0,
            DURACAO_TELA_FINAL - (agora - tempo_fim)
        )

        if restante <= 0:
            rodando = False

    pygame.display.flip()

pygame.quit()
=======
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
>>>>>>> Stashed changes
