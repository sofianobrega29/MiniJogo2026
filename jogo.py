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

fundo_primeira_pessoa = pygame.transform.scale(
    fundo_primeira_pessoa, (LARGURA, ALTURA)
)

def desenhar_chao(tela):
    altura_chao = 120

    pygame.draw.rect(
        tela,
        (70, 65, 75),
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

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w or event.key == pygame.K_UP:
                if maga.no_chao and not maga.voando:
                    # Primeiro W: pula.
                    maga.velocidade_y = maga.forca_pulo
                    maga.no_chao = False
                    maga.pulando = True

                elif maga.pulando and not maga.voando:
                    # Segundo W durante o pulo: começa a voar.
                    maga.voando = True
                    maga.pulando = False
                    maga.velocidade_y = 0
                    maga.tempo_voo = 0

                    print("A maga começou a voar!")

            # O jogador começa andando.
            # Ao apertar W duas vezes, começa a voar.
            if not modo_feitico and event.key == pygame.K_w:
                maga.contagem_w += 1

                if maga.contagem_w >= 2 and not maga.voando:
                    maga.voando = True
                    print("A maga começou a voar!")

            if not modo_feitico and event.key == pygame.K_UP:
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

                        # O ataque começa na posição da maga.
                        projeteis.append(
                            ProjetilMagico(maga.rect.center)
                        )
                    else:
                        print("Símbolo incorreto. Tente novamente.")

                    # Volta imediatamente ao modo normal.
                    modo_feitico = False
                    pontos_magicos = []

    # Atualiza personagens somente no modo normal.
    if not modo_feitico:
        maga.update(TELA)

        if feiticeira.vida > 0:
            feiticeira.update(TELA)

    # Atualiza os projéteis e verifica os acertos.
    for projetil in projeteis[:]:
        if feiticeira.vida <= 0:
            projeteis.remove(projetil)
            continue

        projetil.update(feiticeira)

        if not projetil.ativo:
            feiticeira.vida -= 1
            projeteis.remove(projetil)

            print("O ataque acertou a inimiga!")
            print("Vidas restantes:", max(0, feiticeira.vida))

            if feiticeira.vida <= 0:
                feiticeira.vida = 0
                feiticeira.kill()
                print("Inimiga derrotada!")

    # DESENHO DA TELA
    if modo_feitico:
        # A imagem de primeira pessoa aparece apenas ao desenhar.
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
        # O modo normal não usa a imagem de primeira pessoa.
        TELA.fill((20, 10, 30))
        desenhar_chao(TELA)

        todos_sprites.draw(TELA)

        for projetil in projeteis:
            projetil.desenhar(TELA)

        texto_vida = fonte.render(
            f"Vidas da inimiga: {feiticeira.vida}",
            True,
            BRANCO
        )
        TELA.blit(texto_vida, (20, 20))

        estado_voo = "Voando" if maga.voando else "No chão"
        texto_estado = fonte_menor.render(
            f"Estado da maga: {estado_voo}",
            True,
            BRANCO
        )
        TELA.blit(texto_estado, (20, 60))

    pygame.display.flip()

pygame.quit()
