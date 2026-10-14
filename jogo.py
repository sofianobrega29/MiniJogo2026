
from constantes import *
from elementos import *
from frieren import Maga
from clone import Feiticeira

import pygame
import math

pygame.init()

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

RELOGIO = pygame.time.Clock()

fundo_primeira_pessoa = pygame.image.load(
    "imagens/Fundo/Arena.png"
).convert()

fundo_terceira_pessoa = pygame.image.load(
    "imagens/Fundo/ParedeArena2D.jpeg"
).convert()

vida = pygame.image.load(
    "imagens/UI/vida.png"
).convert_alpha()

vida = pygame.transform.scale(vida, (45, 30))

fundo_primeira_pessoa = pygame.transform.scale(
    fundo_primeira_pessoa,
    (LARGURA, ALTURA)
)

fundo_terceira_pessoa = pygame.transform.scale(
    fundo_terceira_pessoa,
    (LARGURA, ALTURA - 120)
)


def desenhar_chao(tela):
    altura_chao = 120

    pygame.draw.rect(
        tela,
        (255, 231, 176),
        (0, ALTURA - altura_chao, LARGURA, altura_chao)
    )

    tamanho_pedra = 60

    for x in range(0, LARGURA, tamanho_pedra):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (x, ALTURA - altura_chao),
            (x, ALTURA),
            2
        )

    for y in range(ALTURA - altura_chao, ALTURA, 40):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (0, y),
            (LARGURA, y),
            2
        )


def reconhecer_circulo(pontos):
    if len(pontos) < 20:
        return False

    inicio = pontos[0]
    fim = pontos[-1]

    distancia_fechamento = math.hypot(
        fim[0] - inicio[0],
        fim[1] - inicio[1]
    )

    xs = [ponto[0] for ponto in pontos]
    ys = [ponto[1] for ponto in pontos]

    largura = max(xs) - min(xs)
    altura = max(ys) - min(ys)

    if largura < 60 or altura < 60:
        return False

    proporcao = largura / altura

    if not 0.65 <= proporcao <= 1.35:
        return False

    if distancia_fechamento > max(largura, altura) * 0.25:
        return False

    return True


def desenhar_vidas_maga(tela, maga):
    texto = fonte_menor.render(
        "MAGA",
        True,
        BRANCO
    )

    tela.blit(texto, (20, 15))

    for i in range(max(0, maga.vida)):
        tela.blit(vida, (20 + i * 50, 45))


def desenhar_barra_vida_clone(tela, feiticeira):
    largura_barra = 350
    altura_barra = 26

    posicao_x = LARGURA - largura_barra - 30
    posicao_y = 35

    vidas_atuais = max(
        0,
        min(feiticeira.vida, feiticeira.vida_maxima)
    )

    proporcao_vida = (
        vidas_atuais / feiticeira.vida_maxima
        if feiticeira.vida_maxima > 0
        else 0
    )

    largura_preenchimento = int(
        largura_barra * proporcao_vida
    )

    texto = fonte_menor.render(
        f"FEITICEIRA CLONE: {vidas_atuais}/{feiticeira.vida_maxima}",
        True,
        BRANCO
    )

    tela.blit(texto, (posicao_x, 5))

    pygame.draw.rect(
        tela,
        (45, 35, 55),
        (posicao_x, posicao_y, largura_barra, altura_barra),
        border_radius=8
    )

    if largura_preenchimento > 0:
        pygame.draw.rect(
            tela,
            (180, 50, 220),
            (
                posicao_x,
                posicao_y,
                largura_preenchimento,
                altura_barra
            ),
            border_radius=8
        )

    pygame.draw.rect(
        tela,
        (230, 210, 240),
        (posicao_x, posicao_y, largura_barra, altura_barra),
        width=2,
        border_radius=8
    )


maga = Maga(150, ALTURA - 200)
feiticeira = Feiticeira(950, 180)
cajado = Cajado()

todos_sprites = pygame.sprite.Group()
todos_sprites.add(maga, feiticeira)

modo_feitico = False
desenhando = False

pontos_magicos = []
projeteis = []

fonte = pygame.font.SysFont(None, 36)
fonte_menor = pygame.font.SysFont(None, 28)

rodando = True

while rodando:
    RELOGIO.tick(60)

    if maga.rect.centerx < feiticeira.rect.centerx:
        maga.direcao = "direita"
        feiticeira.direcao = "esquerda"
    else:
        maga.direcao = "esquerda"
        feiticeira.direcao = "direita"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f and not modo_feitico:
                modo_feitico = True
                pontos_magicos = []

            if event.key in (pygame.K_w, pygame.K_UP):
                if maga.no_chao and not maga.voando:
                    maga.velocidade_y = maga.forca_pulo
                    maga.no_chao = False
                    maga.pulando = True

                elif maga.pulando and not maga.voando:
                    maga.voando = True
                    maga.pulando = False
                    maga.velocidade_y = 0
                    maga.tempo_voo = 0

                    print("A maga começou a voar!")

            if not modo_feitico and event.key in (
                pygame.K_w,
                pygame.K_UP
            ):
                maga.contagem_w += 1

                if maga.contagem_w >= 2 and not maga.voando:
                    maga.voando = True
                    print("A maga começou a voar!")

        if modo_feitico:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    desenhando = True
                    pontos_magicos = [event.pos]

            elif event.type == pygame.MOUSEMOTION:
                if desenhando:
                    pontos_magicos.append(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and desenhando:
                    desenhando = False

                    if reconhecer_circulo(pontos_magicos):
                        print("Círculo mágico reconhecido!")

                        projeteis.append(
                            ProjetilMagico(maga.rect.center)
                        )
                    else:
                        print("Símbolo incorreto. Tente novamente.")

                    modo_feitico = False
                    pontos_magicos = []

    if not modo_feitico:
        maga.update(TELA)

        if feiticeira.vida > 0:
            feiticeira.update(maga)

    for projetil in projeteis[:]:

        for tiro_clone in feiticeira.projeteis[:]:
            tiro_clone.update()

            if not TELA.get_rect().colliderect(tiro_clone.rect):
                feiticeira.projeteis.remove(tiro_clone)
                continue

            if maga.vida > 0 and tiro_clone.rect.colliderect(maga.rect):
                maga.vida -= tiro_clone.dano
                feiticeira.projeteis.remove(tiro_clone)

                print("A Maga recebeu dano!")
                print("Vida restante:", max(0, maga.vida))

                if maga.vida <= 0:
                    maga.vida = 0
                    print("A Maga foi derrotada!")

        if feiticeira.vida <= 0:
            projeteis.remove(projetil)
            continue

        projetil.update(feiticeira)

        if not projetil.ativo:
            feiticeira.vida -= 1

            feiticeira.ultimo_dano = pygame.time.get_ticks()
            projeteis.remove(projetil)

            print("O ataque acertou a inimiga!")
            print("Vidas restantes:", max(0, feiticeira.vida))

            if feiticeira.vida <= 0:
                feiticeira.vida = 0
                feiticeira.kill()
                print("Inimiga derrotada!")

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

    else:
        TELA.blit(fundo_terceira_pessoa, (0, 0))
        desenhar_chao(TELA)

        todos_sprites.draw(TELA)

        for projetil in projeteis:
            projetil.desenhar(TELA)

        for tiro_clone in feiticeira.projeteis:
            tiro_clone.desenhar(TELA)

        desenhar_vidas_maga(TELA, maga)
        desenhar_barra_vida_clone(TELA, feiticeira)

        estado_voo = "Voando" if maga.voando else "No chão"

        texto_estado = fonte_menor.render(
            f"Estado da maga: {estado_voo}",
            True,
            BRANCO
        )

        TELA.blit(texto_estado, (20, 90))

    pygame.display.flip()

pygame.quit()
