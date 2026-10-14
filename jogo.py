#jogo.py
from pathlib import Path
import math
import os
import tempfile

import numpy as np
import pygame
from moviepy import VideoFileClip

from constantes import *
from elementos import Cajado, ProjetilMagico, RajadaZoltraak, ParedeMagica
from frieren import Maga
from clone import Feiticeira
from sons import SistemaSonoro


pygame.init()

BASE_DIR = Path(__file__).resolve().parent

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
)

fundo_terceira_pessoa = pygame.transform.scale(
    fundo_terceira_pessoa, (LARGURA, ALTURA - 120)
)

fonte = pygame.font.SysFont("arial", 54, bold=True)
fonte_menor = pygame.font.SysFont("arial", 28)
fonte_pequena = pygame.font.SysFont("arial", 22)

CHAO_Y = ALTURA - 120
DURACAO_TELA_FINAL = 8000

CAMINHO_VIDEO_VITORIA = (
    BASE_DIR / "imagens" / "vitoria-derrota" / "vitoria.mp4"
)


def reproduzir_video_vitoria(tela):
    """Reproduz o vídeo de vitória, incluindo o áudio original."""

    if not CAMINHO_VIDEO_VITORIA.is_file():
        print(f"Vídeo de vitória não encontrado: {CAMINHO_VIDEO_VITORIA}")
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

            # Interrompe a música de fundo antes do áudio do vídeo.
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

                tempo = (pygame.time.get_ticks() - inicio) / 1000.0

                if tempo >= video.duration:
                    break

                quadro = np.array(video.get_frame(tempo), dtype=np.uint8)

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


def desenhar_chao(tela):
    pygame.draw.rect(
        tela,
        (255, 231, 176),
        (0, CHAO_Y, LARGURA, 120)
    )

    for x in range(0, LARGURA, 60):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (x, CHAO_Y),
            (x, ALTURA),
            2
        )

    for y in range(CHAO_Y, ALTURA, 40):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (0, y),
            (LARGURA, y),
            2
        )


def distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def comprimento_traco(pontos):
    return sum(
        distancia(pontos[i - 1], pontos[i])
        for i in range(1, len(pontos))
    )


def reconhecer_simbolo(pontos):
    if len(pontos) < 12:
        return None

    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]

    largura = max(xs) - min(xs)
    altura = max(ys) - min(ys)

    if largura < 45 or altura < 35:
        return None

    fechamento = distancia(pontos[0], pontos[-1])
    diagonal = math.hypot(largura, altura)
    percurso = comprimento_traco(pontos)
    proporcao = largura / max(altura, 1)

    if fechamento > diagonal * 0.20 and largura > altura * 1.15:
        segmentos = [
            pontos[0],
            pontos[len(pontos) // 3],
            pontos[2 * len(pontos) // 3],
            pontos[-1]
        ]

        if (
            segmentos[0][1] < segmentos[1][1]
            and segmentos[1][1] > segmentos[2][1]
            and segmentos[2][1] < segmentos[3][1]
        ):
            return "raio"

        if (
            segmentos[0][1] > segmentos[1][1]
            and segmentos[1][1] < segmentos[2][1]
            and segmentos[2][1] > segmentos[3][1]
        ):
            return "raio"

        if abs(pontos[0][1] - pontos[-1][1]) < altura * 0.45:
            return "raio"

    if fechamento > diagonal * 0.25:
        return None

    razao_percurso = percurso / max(diagonal, 1)

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
                    pygame.K_RETURN,
                    pygame.K_ESCAPE,
                    pygame.K_SPACE
                )
            ):
                rodando = False

            continue

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_F10:
                feiticeira.vida = 0

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
                continue

            bloqueado = (
                parede_maga is not None
                and parede_maga.ativa()
                and tiro.rect.colliderect(parede_maga.rect)
            )

            if bloqueado:
                feiticeira.projeteis.remove(tiro)

            elif maga.vida > 0 and tiro.rect.colliderect(maga.rect):
                maga.vida = max(0, maga.vida - tiro.dano)
                feiticeira.projeteis.remove(tiro)

        if feiticeira.vida <= 0:
            feiticeira.vida = 0
            estado_jogo = "vitoria"

            # Exibe o vídeo de vitória uma única vez.
            if not reproduzir_video_vitoria(TELA):
                rodando = False
                break

            tempo_fim = pygame.time.get_ticks()

        elif maga.vida <= 0:
            maga.vida = 0
            estado_jogo = "derrota"
            tempo_fim = agora

    if estado_jogo == "jogando":
        if modo_feitico:
            TELA.blit(fundo_primeira_pessoa, (0, 0))

            if len(pontos_magicos) > 1:
                pygame.draw.lines(
                    TELA,
                    AZUL_MAGICO,
                    False,
                    pontos_magicos,
                    5
                )

            cajado.desenhar(TELA)

            dica = fonte_pequena.render(
                "Desenhe: círculo = explosão | quadrado = defesa | "
                "estrela = Zoltraak | Z = raio",
                True,
                BRANCO
            )

            TELA.blit(dica, (20, ALTURA - 40))

        else:
            TELA.blit(fundo_terceira_pessoa, (0, 0))
            desenhar_chao(TELA)

            TELA.blit(maga.image, maga.rect)

            if feiticeira.vida > 0:
                TELA.blit(feiticeira.image, feiticeira.rect)
                feiticeira.desenhar_magias(TELA)

            for p in projeteis:
                p.desenhar(TELA)

            for r in rajadas:
                if getattr(r, "tipo_raio", False):
                    inicio = pygame.Vector2(r.posicao)

                    pontos = [
                        (int(inicio.x), int(inicio.y))
                    ]

                    for i in range(1, 5):
                        pontos.append((
                            int(
                                inicio.x
                                - r.direcao.x * i * 14
                                + (18 if i % 2 else -18)
                            ),
                            int(
                                inicio.y
                                - r.direcao.y * i * 14
                            )
                        ))

                    pygame.draw.lines(
                        TELA,
                        (150, 45, 255),
                        False,
                        pontos,
                        9
                    )

                    pygame.draw.lines(
                        TELA,
                        (235, 210, 255),
                        False,
                        pontos,
                        3
                    )

                else:
                    r.desenhar(TELA)

            for tiro in feiticeira.projeteis:
                tiro.desenhar(TELA)

            if parede_maga and parede_maga.ativa():
                parede_maga.desenhar(TELA)

            desenhar_vidas_maga(TELA, maga)
            desenhar_barra_vida_clone(TELA, feiticeira)

            estado_voo = "Voando" if maga.voando else "No chão"

            TELA.blit(
                fonte_pequena.render(
                    f"Estado da maga: {estado_voo}",
                    True,
                    BRANCO
                ),
                (20, 90)
            )

    else:
        TELA.blit(fundo_terceira_pessoa, (0, 0))
        desenhar_chao(TELA)

        if maga.vida > 0:
            TELA.blit(maga.image, maga.rect)

        if feiticeira.vida > 0:
            TELA.blit(feiticeira.image, feiticeira.rect)

        overlay = pygame.Surface(
            (LARGURA, ALTURA),
            pygame.SRCALPHA
        )

        overlay.fill((10, 8, 20, 205))
        TELA.blit(overlay, (0, 0))

        venceu = estado_jogo == "vitoria"

        titulo = fonte.render(
            "VITÓRIA!" if venceu else "VOCÊ FOI DERROTADO",
            True,
            (100, 255, 150) if venceu else (255, 90, 100)
        )

        TELA.blit(
            titulo,
            titulo.get_rect(
                center=(LARGURA // 2, ALTURA // 2 - 70)
            )
        )

        subtitulo = fonte_menor.render(
            "Você venceu o clone!"
            if venceu
            else "A clone foi mais forte desta vez.",
            True,
            BRANCO
        )

        TELA.blit(
            subtitulo,
            subtitulo.get_rect(
                center=(LARGURA // 2, ALTURA // 2 - 15)
            )
        )

        cor_botao = (
            (90, 50, 150)
            if botao_menu.collidepoint(pygame.mouse.get_pos())
            else (65, 35, 115)
        )

        pygame.draw.rect(
            TELA,
            cor_botao,
            botao_menu,
            border_radius=12
        )

        pygame.draw.rect(
            TELA,
            (220, 200, 255),
            botao_menu,
            2,
            border_radius=12
        )

        texto = fonte_menor.render(
            "Voltar ao menu",
            True,
            BRANCO
        )

        TELA.blit(
            texto,
            texto.get_rect(center=botao_menu.center)
        )

        restante = max(
            0,
            DURACAO_TELA_FINAL - (agora - tempo_fim)
        )

        TELA.blit(
            fonte_pequena.render(
                f"Retorno automático em {math.ceil(restante / 1000)} s",
                True,
                BRANCO
            ),
            (LARGURA // 2 - 105, ALTURA // 2 + 125)
        )

        if agora - tempo_fim >= DURACAO_TELA_FINAL:
            rodando = False

    pygame.display.flip()


pygame.quit()