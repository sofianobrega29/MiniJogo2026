
import os
import random
from pathlib import Path

import pygame
from constantes import LARGURA, ALTURA
from jogo import Jogo

os.chdir(Path(__file__).resolve().parent)

pygame.init()

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

RELOGIO = pygame.time.Clock()

import estilo
import grimorio
from particulas import Particulas

fonte_botao = estilo.fonte_botao(40)

# Mana flutuando pela tela, para dar vida aos menus.
AMBIENTE = Particulas(limite=160)


CAPA_INICIAL = pygame.image.load(
    str(Path(__file__).resolve().parent / "imagens" / "Fundo" / "capa_inicial.png")
).convert()
_escala = max(LARGURA / CAPA_INICIAL.get_width(), ALTURA / CAPA_INICIAL.get_height())
CAPA_INICIAL = pygame.transform.smoothscale(
    CAPA_INICIAL,
    (round(CAPA_INICIAL.get_width() * _escala), round(CAPA_INICIAL.get_height() * _escala)),
)
CAPA_INICIAL_CORTADA = pygame.Surface((LARGURA, ALTURA))
CAPA_INICIAL_CORTADA.blit(
    CAPA_INICIAL, CAPA_INICIAL.get_rect(center=(LARGURA // 2, ALTURA // 2))
)


def atualizar_ambiente():
    """Solta de vez em quando uma partícula de mana que sobe devagar e some."""
    if random.random() < 0.35:
        AMBIENTE.emitir(
            random.uniform(0, LARGURA),
            ALTURA + 6,
            vx=random.uniform(-0.25, 0.25),
            vy=random.uniform(-1.3, -0.5),
            vida=random.randint(260, 460),
            tamanho=random.choice((2, 2, 3)),
            cor=random.choice(((150, 215, 255), (220, 245, 255), (110, 170, 255))),
            cor_fim=(14, 24, 60),
            forma="estrela" if random.random() < 0.4 else "quadrado",
            atrito=1.0,
        )

    AMBIENTE.update()


def desenhar_botao(texto, retangulo, mouse, indice=0):
    estilo.desenhar_botao(
        TELA, retangulo, texto, mouse, pygame.time.get_ticks(), fonte_botao, indice
    )


def botoes_da_tela_inicial():
    # Os botões ficam à direita, abaixo do título que já faz parte da capa.
    x_botoes = int(LARGURA * 0.71) - 170
    return {
        "jogar": pygame.Rect(x_botoes, 405, 340, 70),
        "instrucoes": pygame.Rect(x_botoes, 513, 340, 70),
        "sair": pygame.Rect(x_botoes, 621, 340, 70)
    }


def desenhar_tela_inicial(botoes, mouse):
    TELA.blit(CAPA_INICIAL_CORTADA, (0, 0))
    AMBIENTE.desenhar(TELA)

    desenhar_botao("JOGAR", botoes["jogar"], mouse, 0)
    desenhar_botao("COMO JOGAR", botoes["instrucoes"], mouse, 1)
    desenhar_botao("SAIR", botoes["sair"], mouse, 2)


def tela_inicial():
    botoes = botoes_da_tela_inicial()

    while True:
        RELOGIO.tick(60)
        mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if botoes["jogar"].collidepoint(evento.pos):
                        return "jogar"

                    if botoes["instrucoes"].collidepoint(evento.pos):
                        return "instrucoes"

                    if botoes["sair"].collidepoint(evento.pos):
                        return "sair"

        atualizar_ambiente()
        desenhar_tela_inicial(botoes, mouse)
        pygame.display.flip()


BOTAO_VOLTAR = pygame.Rect(LARGURA // 2 - 150, 818, 300, 62)


def desenhar_tela_instrucoes(mouse):
    # A tela "Como jogar" é um grimório (veja grimorio.py).
    TELA.blit(grimorio.obter(), (0, 0))
    AMBIENTE.desenhar(TELA)
    desenhar_botao("VOLTAR", BOTAO_VOLTAR, mouse, 0)


def tela_instrucoes():
    while True:
        RELOGIO.tick(60)
        mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return "voltar"

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if BOTAO_VOLTAR.collidepoint(evento.pos):
                        return "voltar"

        atualizar_ambiente()
        desenhar_tela_instrucoes(mouse)
        pygame.display.flip()


def principal():
    rodando = True

    while rodando:
        escolha = tela_inicial()

        if escolha == "jogar":
            # Se a janela for fechada durante a partida, o programa inteiro encerra.
            if Jogo(TELA, RELOGIO).executar() == "sair":
                rodando = False

        elif escolha == "instrucoes":
            resultado = tela_instrucoes()

            if resultado == "sair":
                rodando = False

        else:
            rodando = False

    pygame.quit()


if __name__ == "__main__":
    principal()
