import os
import runpy
from pathlib import Path

import pygame
from constantes import LARGURA, ALTURA
from sons import SistemaSonoro

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

pygame.init()

audio = SistemaSonoro()
audio.iniciar_musica()
audio.aumentar_volume()

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

RELOGIO = pygame.time.Clock()

PRETO = (15, 10, 28)
ROXO_ESCURO = (35, 18, 58)
ROXO = (125, 55, 210)
ROXO_CLARO = (190, 130, 255)
BRANCO = (245, 240, 255)
CINZA = (190, 180, 205)

fonte_titulo = pygame.font.SysFont("arial", 88, bold=True)
fonte_subtitulo = pygame.font.SysFont("arial", 28)
fonte_botao = pygame.font.SysFont("arial", 34, bold=True)
fonte_texto = pygame.font.SysFont("arial", 27)
fonte_pequena = pygame.font.SysFont("arial", 22)


def desenhar_fundo():
    TELA.fill(PRETO)

    pygame.draw.rect(
        TELA,
        ROXO_ESCURO,
        (0, 0, LARGURA, ALTURA // 2)
    )

    pygame.draw.circle(TELA, ROXO, (100, 120), 5)
    pygame.draw.circle(TELA, ROXO_CLARO, (1180, 180), 4)
    pygame.draw.circle(TELA, ROXO, (1080, 720), 6)
    pygame.draw.circle(TELA, ROXO_CLARO, (180, 760), 4)

    pygame.draw.circle(
        TELA,
        ROXO,
        (LARGURA // 2, 300),
        150,
        2
    )

    pygame.draw.circle(
        TELA,
        ROXO_CLARO,
        (LARGURA // 2, 300),
        125,
        2
    )

    pygame.draw.polygon(
        TELA,
        ROXO,
        [
            (LARGURA // 2, 120),
            (LARGURA // 2 + 20, 280),
            (LARGURA // 2, 300),
            (LARGURA // 2 - 20, 280)
        ],
        2
    )


def desenhar_texto(texto, fonte, cor, centro):
    imagem = fonte.render(texto, True, cor)
    retangulo = imagem.get_rect(center=centro)
    TELA.blit(imagem, retangulo)


def desenhar_botao(texto, retangulo, mouse):
    cor = ROXO_CLARO if retangulo.collidepoint(mouse) else ROXO

    pygame.draw.rect(
        TELA,
        cor,
        retangulo,
        border_radius=14
    )

    pygame.draw.rect(
        TELA,
        BRANCO,
        retangulo,
        width=2,
        border_radius=14
    )

    desenhar_texto(
        texto,
        fonte_botao,
        BRANCO,
        retangulo.center
    )


def tela_inicial():
    botoes = {
        "jogar": pygame.Rect(LARGURA // 2 - 170, 510, 340, 70),
        "instrucoes": pygame.Rect(LARGURA // 2 - 170, 600, 340, 70),
        "sair": pygame.Rect(LARGURA // 2 - 170, 690, 340, 70)
    }

    while True:
        RELOGIO.tick(60)
        mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if botoes["jogar"].collidepoint(evento.pos):
                    return "jogar"

                if botoes["instrucoes"].collidepoint(evento.pos):
                    return "instrucoes"

                if botoes["sair"].collidepoint(evento.pos):
                    return "sair"

        desenhar_fundo()

        desenhar_texto(
            "CONFRONTO",
            fonte_titulo,
            BRANCO,
            (LARGURA // 2, 180)
        )

        desenhar_texto(
            "MÁGICO",
            fonte_titulo,
            ROXO_CLARO,
            (LARGURA // 2, 275)
        )

        desenhar_texto(
            "Prepare sua magia e enfrente seu clone!",
            fonte_subtitulo,
            CINZA,
            (LARGURA // 2, 405)
        )

        desenhar_botao("JOGAR", botoes["jogar"], mouse)
        desenhar_botao("COMO JOGAR", botoes["instrucoes"], mouse)
        desenhar_botao("SAIR", botoes["sair"], mouse)

        pygame.display.flip()


def tela_instrucoes():
    while True:
        RELOGIO.tick(60)
        mouse = pygame.mouse.get_pos()

        botao_voltar = pygame.Rect(
            LARGURA // 2 - 150,
            750,
            300,
            65
        )

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return "sair"

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return "voltar"

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if botao_voltar.collidepoint(evento.pos):
                    return "voltar"

        desenhar_fundo()

        desenhar_texto(
            "COMO JOGAR",
            fonte_titulo,
            ROXO_CLARO,
            (LARGURA // 2, 130)
        )

        instrucoes = [
            ("A / D ou setas laterais", "Mover a maga"),
            ("W ou seta para cima", "Pular e iniciar o voo"),
            ("S ou seta para baixo", "Descer durante o voo"),
            ("F", "Entrar no modo de feitiço"),
            ("Mouse esquerdo", "Desenhar o círculo mágico"),
            ("Objetivo", "Acerte a clone para reduzir suas vidas")
        ]

        y = 280

        for titulo, descricao in instrucoes:
            desenhar_texto(
                titulo,
                fonte_texto,
                ROXO_CLARO,
                (LARGURA // 2 - 220, y)
            )

            desenhar_texto(
                descricao,
                fonte_pequena,
                BRANCO,
                (LARGURA // 2 + 190, y)
            )

            y += 65

        desenhar_botao("VOLTAR", botao_voltar, mouse)

        pygame.display.flip()


rodando = True

while rodando:
    escolha = tela_inicial()

    if escolha == "jogar":
        audio.definir_volume(0.2)

        pygame.display.quit()

        try:
            runpy.run_path(str(BASE_DIR / "jogo.py"))
        finally:
            if not pygame.get_init():
                pygame.init()

            if not pygame.display.get_init():
                pygame.display.init()

            TELA = pygame.display.set_mode((LARGURA, ALTURA))
            pygame.display.set_caption("Confronto Mágico")
            RELOGIO = pygame.time.Clock()

            audio.definir_volume(0.7)

    elif escolha == "instrucoes":
        resultado = tela_instrucoes()

        if resultado == "sair":
            rodando = False

    else:
        rodando = False

pygame.quit()