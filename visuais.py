"""Desenhos dos feitiços: feixes, relâmpago, floco de gelo e buracos de vidro.

Os efeitos mais "grossos" (feixe do Zoltraak e coluna da cura) são desenhados numa
imagem pequena e ampliada sem suavização (PIXEL vezes), para parecer pixel art como
os sprites do jogo.
"""

import math
import random

import pygame

PIXEL = 3

# Cores dos feixes: (brilho externo, brilho médio, corpo, núcleo, centro, cabeça)
PALETA_AZUL = ((50, 120, 255, 70), (80, 160, 255, 120), (130, 205, 255, 255), (215, 242, 255, 255), (255, 255, 255, 255), (120, 200, 255, 255))
PALETA_VERDE = ((40, 200, 110, 70), (70, 230, 140, 120), (140, 255, 175, 255), (220, 255, 232, 255), (255, 255, 255, 255), (120, 255, 170, 255))


# --------------------------------------------------------------------------
# Feixe de luz (Zoltraak, cura)
# --------------------------------------------------------------------------
def gerar_feixe(comprimento, altura, afunilar, tempo_ms, paleta=PALETA_AZUL, cabeca=True):
    """Imagem de um feixe horizontal: cauda à esquerda, cabeça à direita.

    Devolve (imagem, recuo): `recuo` é quantos pixels a imagem sobra à esquerda da cauda.
    """
    h = max(6, int(altura))
    margem = int(h * 0.55) + 12
    largura = comprimento // PIXEL + 2 * (margem // PIXEL) + 2
    alto = (h + 2 * margem) // PIXEL + 2
    camada = pygame.Surface((largura, alto), pygame.SRCALPHA)

    x0 = margem // PIXEL
    x1 = x0 + comprimento // PIXEL
    cy = alto / 2
    meia = h / PIXEL / 2
    rampa = max(1.0, min(comprimento / PIXEL * 0.7, afunilar / PIXEL))

    def corpo(escala, cor):
        m = meia * escala
        pygame.draw.polygon(camada, cor, [
            (x0, cy), (x0 + rampa, cy - m), (x1 - 2, cy - m), (x1, cy - m * 0.55),
            (x1, cy + m * 0.55), (x1 - 2, cy + m), (x0 + rampa, cy + m),
        ])

    corpo(1.75, paleta[0])
    corpo(1.40, paleta[1])
    corpo(1.05, paleta[2])
    corpo(0.66, paleta[3])
    corpo(0.30, paleta[4])

    # Riscos de energia correndo pelo feixe (dão a sensação de velocidade).
    desloc = (tempo_ms / 5.0) % 24

    for k, posicao in enumerate((-0.50, 0.0, 0.50)):
        y = cy + posicao * meia
        x = x0 + rampa * 0.4 - ((desloc * (1 + 0.35 * k)) % 24)
        cor = (255, 255, 255, 235) if k == 1 else (205, 235, 255, 210)

        while x < x1 - 4:
            xa, xb = max(x, x0 + rampa * 0.3), min(x + 9, x1 - 3)

            if xb > xa:
                pygame.draw.line(camada, cor, (xa, y), (xb, y), 1)

            x += 24

    if cabeca:
        bola = pygame.Rect(0, 0, max(5, int(meia * 0.8)), max(4, int(meia * 2.6)))
        bola.center = (int(x1 - 2), int(cy))
        pygame.draw.ellipse(camada, paleta[5], bola.inflate(5, 5))
        pygame.draw.ellipse(camada, (255, 255, 255, 255), bola)

    return pygame.transform.scale(camada, (largura * PIXEL, alto * PIXEL)), x0 * PIXEL


def desenhar_feixe(tela, retangulo, espessura, sentido, afunilar, tempo_ms, paleta=PALETA_AZUL):
    """Feixe horizontal ocupando `retangulo`. sentido>0: sai da esquerda para a direita."""
    imagem, recuo = gerar_feixe(retangulo.width, retangulo.height * espessura, afunilar, tempo_ms, paleta)

    if sentido > 0:
        tela.blit(imagem, (retangulo.left - recuo, retangulo.centery - imagem.get_height() // 2))
    else:
        imagem = pygame.transform.flip(imagem, True, False)
        tela.blit(imagem, (retangulo.right + recuo - imagem.get_width(), retangulo.centery - imagem.get_height() // 2))


def desenhar_coluna(tela, x, y_base, altura, largura, espessura, afunilar, tempo_ms, paleta=PALETA_VERDE):
    """Feixe vertical subindo a partir de (x, y_base): usado pela cura."""
    imagem, recuo = gerar_feixe(altura, largura * espessura, afunilar, tempo_ms, paleta)
    imagem = pygame.transform.rotate(imagem, 90)  # cauda embaixo, cabeça em cima
    tela.blit(imagem, (x - imagem.get_width() // 2, y_base + recuo - imagem.get_height()))


def brilho_elipse(tela, centro, largura, altura, cor, camadas=9, alfa=70):
    """Halo suave (elipses concentrais translúcidas)."""
    folha = pygame.Surface((int(largura * 1.6) + 4, int(altura * 1.6) + 4), pygame.SRCALPHA)
    cx, cy = folha.get_width() // 2, folha.get_height() // 2

    for i in range(camadas, 0, -1):
        t = i / camadas
        elipse = pygame.Rect(0, 0, int(largura * (0.4 + 1.2 * t)), int(altura * (0.4 + 1.2 * t)))
        elipse.center = (cx, cy)
        pygame.draw.ellipse(folha, (*cor, int(alfa * (1 - t) ** 1.3 + 6)), elipse)

    tela.blit(folha, folha.get_rect(center=centro))


# --------------------------------------------------------------------------
# Relâmpago (raio roxo)
# --------------------------------------------------------------------------
def desenhar_relampago(tela, pontos, ramos, fino, fase_fim, sorteio, cor_forte, cor_clara, y_chao, x_centro, flash):
    """Raio com brilho, ramos e (no fim) pedaços que piscam e somem, como uma descarga elétrica."""
    if len(pontos) < 2:
        return

    largura_folha = 320
    folha = pygame.Surface((largura_folha, y_chao + 40), pygame.SRCALPHA)
    deslocar = (largura_folha // 2 - x_centro, 0)

    def mover(lista):
        return [(x + deslocar[0], y + deslocar[1]) for x, y in lista]

    corpo = mover(pontos)
    ramos_m = [mover(r) for r in ramos]

    def traco(pts, largura, cor):
        if fase_fim:  # no fim o raio se parte em pedaços que piscam e somem
            for i in range(len(pts) - 1):
                if sorteio.random() < 0.72 - 0.5 * fase_fim:
                    pygame.draw.line(folha, cor, pts[i], pts[i + 1], max(1, largura))
        else:
            pygame.draw.lines(folha, cor, False, pts, max(1, largura))

    for largura, cor in ((int(38 * fino), (*cor_forte, 38)), (int(22 * fino), (*cor_forte, 85)), (int(11 * fino), (*cor_clara, 190))):
        traco(corpo, largura, cor)

    for ramo in ramos_m:
        traco(ramo, max(1, int(8 * fino)), (*cor_forte, 120))
        traco(ramo, max(1, int(3 * fino)), (255, 245, 255, 255))

    traco(corpo, max(2, int(5 * fino)), (255, 250, 255, 255))
    tela.blit(folha, (x_centro - largura_folha // 2, 0))

    # Luz no ponto de impacto.
    brilho_elipse(tela, (x_centro, y_chao), 210 * fino + 40, 56 * fino + 12, cor_forte, camadas=8, alfa=95)
    brilho_elipse(tela, (x_centro, y_chao), 90 * fino + 16, 24 * fino + 6, (255, 245, 255), camadas=6, alfa=140)

    if flash > 0:  # clarão rápido na tela toda (o raio ilumina o ambiente)
        clarao = pygame.Surface(tela.get_size(), pygame.SRCALPHA)
        clarao.fill((225, 205, 255, int(70 * flash)))
        tela.blit(clarao, (0, 0))


# --------------------------------------------------------------------------
# Floco de gelo
# --------------------------------------------------------------------------
def desenhar_floco(tela, centro, raio, angulo):
    """Floco de neve de 6 pontas com brilho, no estilo pixel (linhas grossas)."""
    cx, cy = centro
    brilho_elipse(tela, centro, raio * 2.2, raio * 2.2, (110, 190, 255), camadas=7, alfa=85)

    for passo, (largura, cor) in enumerate(((7, (90, 170, 255)), (3, (240, 252, 255)))):
        for i in range(6):
            a = angulo + i * math.pi / 3
            ponta = (cx + math.cos(a) * raio, cy + math.sin(a) * raio)
            pygame.draw.line(tela, cor, (cx, cy), ponta, largura)

            # galhos laterais e "V" na ponta
            for fracao, comp in ((0.55, 0.38), (0.82, 0.22)):
                bx, by = cx + math.cos(a) * raio * fracao, cy + math.sin(a) * raio * fracao

                for lado in (-1, 1):
                    b = a + lado * math.radians(58)
                    pygame.draw.line(tela, cor, (bx, by), (bx + math.cos(b) * raio * comp, by + math.sin(b) * raio * comp), max(2, largura - 1))

    pygame.draw.circle(tela, (255, 255, 255), (int(cx), int(cy)), max(3, int(raio * 0.16)))


# --------------------------------------------------------------------------
# Hexágono de vidro (escudo)
# --------------------------------------------------------------------------
def furar_hexagono(superficie, centro, raio):
    """Apaga um hexágono do sprite do escudo (fica transparente), como uma peça de vidro que se soltou."""
    cx, cy = centro
    pontos = [(cx + math.cos(math.radians(60 * i + 30)) * raio, cy + math.sin(math.radians(60 * i + 30)) * raio) for i in range(6)]
    pygame.draw.polygon(superficie, (0, 0, 0, 0), pontos)
    return pontos
