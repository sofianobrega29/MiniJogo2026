"""Estilo visual do jogo: "mana azul" como nos feitiços do anime.

Aqui ficam as fontes e os desenhos reutilizáveis da interface: texto com brilho,
botões mágicos e as caixas dos feitiços. Para trocar uma fonte, é só colocar o
arquivo .ttf na pasta `fontes/` e mudar o nome nas constantes abaixo; se o arquivo
não existir, o jogo usa uma fonte do sistema no lugar.
"""

import math
import random
from pathlib import Path

import pygame

from particulas import misturar

PASTA_FONTES = Path(__file__).resolve().parent / "fontes"

# Qual arquivo de fonte cada parte do jogo usa.
FONTE_BOTAO = "Italiana-Regular.ttf"             # botões, caixas de feitiço (maiúsculas elegantes)
FONTE_GRIMORIO_TITULO = "Gloock-Regular.ttf"     # títulos do grimório
FONTE_GRIMORIO_TEXTO = "CrimsonPro-Italic.ttf"   # texto do grimório
FONTE_NOTAS = "NothingYouCouldDo-Regular.ttf"    # anotações à mão

# Paleta de mana
MANA_FUNDO = (8, 14, 40)
MANA_ESCURO = (16, 30, 78)
MANA_AZUL = (70, 150, 255)
MANA_CIANO = (120, 215, 255)
MANA_CLARO = (190, 235, 255)
MANA_BRANCO = (240, 250, 255)

_fontes = {}
_texto_cache = {}
_painel_cache = {}


# --------------------------------------------------------------------------
# Fontes
# --------------------------------------------------------------------------
def fonte(arquivo, tamanho, negrito_reserva=False):
    """Carrega uma fonte da pasta fontes/ (com cache). Sem o arquivo, usa uma do sistema."""
    chave = (arquivo, tamanho)

    if chave not in _fontes:
        try:
            _fontes[chave] = pygame.font.Font(str(PASTA_FONTES / arquivo), tamanho)
        except (FileNotFoundError, OSError, pygame.error):
            _fontes[chave] = pygame.font.SysFont("georgia", tamanho, bold=negrito_reserva)

    return _fontes[chave]


def fonte_botao(tamanho):
    return fonte(FONTE_BOTAO, tamanho)


# --------------------------------------------------------------------------
# Texto com brilho
# --------------------------------------------------------------------------
def texto_brilhante(texto, fonte_texto, cor=MANA_BRANCO, brilho=MANA_AZUL, raio=10, forca=2):
    """Imagem do texto com um halo de mana em volta (guardada em cache)."""
    chave = (texto, id(fonte_texto), cor, brilho, raio, forca)

    if chave in _texto_cache:
        return _texto_cache[chave]

    miolo = fonte_texto.render(texto, True, brilho)
    margem = raio * 2
    largura, altura = miolo.get_width() + margem * 2, miolo.get_height() + margem * 2

    base = pygame.Surface((largura, altura), pygame.SRCALPHA)
    base.blit(miolo, (margem, margem))

    # Desfoque barato: reduz e amplia suavizando.
    fator = max(2, raio // 2)
    pequena = pygame.transform.smoothscale(base, (max(1, largura // fator), max(1, altura // fator)))
    halo = pygame.transform.smoothscale(pequena, (largura, altura))

    resultado = pygame.Surface((largura, altura), pygame.SRCALPHA)

    for _ in range(forca):
        resultado.blit(halo, (0, 0))

    resultado.blit(fonte_texto.render(texto, True, cor), (margem, margem))
    _texto_cache[chave] = resultado
    return resultado


def desenhar_texto_magico(tela, texto, fonte_texto, centro, cor=MANA_BRANCO, brilho=MANA_AZUL, raio=10, forca=2):
    imagem = texto_brilhante(texto, fonte_texto, cor, brilho, raio, forca)
    tela.blit(imagem, imagem.get_rect(center=centro))


# --------------------------------------------------------------------------
# Painel de mana (base dos botões e das caixas)
# --------------------------------------------------------------------------
MARGEM_BRILHO = 24


def _estrela4(superficie, centro, raio, cor):
    cx, cy = centro
    fino = raio * 0.26
    pontos = [
        (cx, cy - raio), (cx + fino, cy - fino), (cx + raio, cy), (cx + fino, cy + fino),
        (cx, cy + raio), (cx - fino, cy + fino), (cx - raio, cy), (cx - fino, cy - fino),
    ]
    pygame.draw.polygon(superficie, cor, pontos)


def _painel(largura, altura, intensidade, raio, ornamentos):
    """Moldura de mana: brilho azul por fora, vidro escuro com luz na borda por dentro."""
    chave = (largura, altura, round(intensidade * 10), raio, ornamentos)

    if chave in _painel_cache:
        return _painel_cache[chave]

    m = MARGEM_BRILHO
    superficie = pygame.Surface((largura + m * 2, altura + m * 2), pygame.SRCALPHA)

    # 1) brilho externo: faixas de fora para dentro, cada vez mais fortes
    for i in range(m, 0, -2):
        alfa = int(95 * intensidade * (1 - i / m) ** 2.0)
        pygame.draw.rect(
            superficie, (*MANA_AZUL, alfa),
            (m - i, m - i, largura + i * 2, altura + i * 2), border_radius=raio + i,
        )

    # 2) corpo de vidro escuro com a luz da mana acesa nas bordas
    profundidade = max(6, min(16, altura // 3))

    for i in range(profundidade):
        t = (i / profundidade) ** 0.65
        cor = misturar((52, 120, 235), MANA_FUNDO, t)
        pygame.draw.rect(
            superficie, (*cor, 244),
            (m + i, m + i, largura - i * 2, altura - i * 2), border_radius=max(2, raio - i),
        )

    # 3) reflexo suave no alto
    reflexo = pygame.Rect(m + raio, m + 4, largura - raio * 2, max(2, altura // 7))
    pygame.draw.rect(superficie, (190, 230, 255, 46), reflexo, border_radius=4)

    # 4) borda dupla: linha ciano e fio branco por dentro
    pygame.draw.rect(superficie, (*MANA_CIANO, 255), (m, m, largura, altura), 2, border_radius=raio)
    pygame.draw.rect(
        superficie, (*MANA_BRANCO, int(120 + 100 * intensidade)),
        (m + 4, m + 4, largura - 8, altura - 8), 1, border_radius=max(2, raio - 3),
    )

    if ornamentos:
        # estrelinhas nos cantos
        for cx, cy in ((m, m), (m + largura, m), (m, m + altura), (m + largura, m + altura)):
            _estrela4(superficie, (cx, cy), 9, (*MANA_BRANCO, 255))
            pygame.draw.circle(superficie, (*MANA_AZUL, 90), (cx, cy), 13, 2)

        # losangos e traços rúnicos no meio das bordas de cima e de baixo
        meio = m + largura // 2

        for y in (m, m + altura):
            _estrela4(superficie, (meio, y), 6, (*MANA_BRANCO, 255))

            for lado in (-1, 1):
                for ini, fim, alfa in ((16, 44, 190), (54, 66, 120), (74, 80, 80)):
                    pygame.draw.line(
                        superficie, (*MANA_CLARO, alfa),
                        (meio + lado * ini, y), (meio + lado * fim, y), 2,
                    )

    _painel_cache[chave] = superficie
    return superficie


def _ponto_no_perimetro(retangulo, distancia):
    """Ponto a `distancia` pixels andando pela borda do retângulo (sentido horário)."""
    w, h = retangulo.width, retangulo.height
    perimetro = 2 * (w + h)
    d = distancia % perimetro

    if d < w:
        return retangulo.left + d, retangulo.top
    d -= w

    if d < h:
        return retangulo.right, retangulo.top + d
    d -= h

    if d < w:
        return retangulo.right - d, retangulo.bottom
    d -= w

    return retangulo.left, retangulo.bottom - d


def _cometa(tela, retangulo, distancia, comprimento=12, passo=5):
    """Ponto de luz correndo pela borda, com um rastro contínuo que vai de branco a azul-mana."""
    anterior = _ponto_no_perimetro(retangulo, distancia)

    for k in range(1, comprimento + 1):
        atual = _ponto_no_perimetro(retangulo, distancia - k * passo)
        t = k / comprimento
        cor = misturar(MANA_BRANCO, (40, 110, 235), t ** 0.6)
        espessura = max(1, round(5.0 * (1 - t) + 1))
        pygame.draw.line(tela, cor, anterior, atual, espessura)
        anterior = atual

    x, y = _ponto_no_perimetro(retangulo, distancia)
    pygame.draw.circle(tela, MANA_BRANCO, (int(x), int(y)), 4)


def _faiscas(tela, retangulo, tempo, quantidade=7):
    """Estrelinhas que nascem na borda, sobem e somem (só com o mouse em cima)."""
    for k in range(quantidade):
        ciclo = tempo / 900 + k / quantidade
        fase = ciclo % 1.0
        sorteio = random.Random(int(ciclo) * 31 + k * 7)
        x = retangulo.left + 10 + sorteio.random() * (retangulo.width - 20)
        y = (retangulo.top - 2 - fase * 26) if k % 2 == 0 else (retangulo.bottom + 2 + fase * 26)
        brilho = math.sin(fase * math.pi)

        if brilho <= 0.08:
            continue

        cor = misturar(MANA_FUNDO, MANA_BRANCO, brilho)
        tam = 1 + int(2 * brilho)
        pygame.draw.rect(tela, cor, (x - tam * 2, y - tam // 2, tam * 4 + 1, tam))
        pygame.draw.rect(tela, cor, (x - tam // 2, y - tam * 2, tam, tam * 4 + 1))


# --------------------------------------------------------------------------
# Botão mágico
# --------------------------------------------------------------------------
def desenhar_botao(tela, retangulo, texto, mouse, tempo, fonte_texto=None, indice=0):
    """Botão de mana azul. `tempo` em ms (ex.: pygame.time.get_ticks())."""
    fonte_texto = fonte_texto or fonte_botao(38)
    sobre = retangulo.collidepoint(mouse)
    intensidade = 1.0 if sobre else 0.55

    painel = _painel(retangulo.width, retangulo.height, intensidade, 14, True)
    tela.blit(painel, (retangulo.x - MARGEM_BRILHO, retangulo.y - MARGEM_BRILHO))

    cor_texto = MANA_BRANCO if sobre else MANA_CLARO
    desenhar_texto_magico(
        tela, texto, fonte_texto, retangulo.center, cor_texto, MANA_AZUL,
        raio=10 if sobre else 8, forca=3 if sobre else 2,
    )

    velocidade = 0.34 if sobre else 0.12
    _cometa(tela, retangulo.inflate(-2, -2), tempo * velocidade + indice * 190)

    if sobre:
        _cometa(tela, retangulo.inflate(-2, -2), tempo * velocidade + retangulo.width + retangulo.height)
        _faiscas(tela, retangulo, tempo + indice * 130)


# --------------------------------------------------------------------------
# Caixa de feitiço (mostra a recarga como mana enchendo)
# --------------------------------------------------------------------------
def desenhar_caixa_feitico(tela, retangulo, carga, tempo):
    """Moldura de mana de um feitiço. `carga` vai de 0 (acabou de usar) a 1 (pronto)."""
    pronto = carga >= 1.0

    if pronto:
        pulso = 0.75 + 0.25 * math.sin(tempo / 260)
        intensidade = pulso
    else:
        intensidade = 0.2

    painel = _painel(retangulo.width, retangulo.height, intensidade, 10, False)
    tela.blit(painel, (retangulo.x - MARGEM_BRILHO, retangulo.y - MARGEM_BRILHO))

    if not pronto and carga > 0:
        largura = max(2, int((retangulo.width - 10) * carga))
        enchimento = pygame.Rect(retangulo.x + 5, retangulo.y + 5, largura, retangulo.height - 10)
        pygame.draw.rect(tela, (28, 66, 150), enchimento, border_radius=6)
        pygame.draw.line(tela, MANA_CIANO, (enchimento.right, enchimento.top + 2), (enchimento.right, enchimento.bottom - 2), 2)
        pygame.draw.rect(tela, (70, 120, 205), enchimento, 1, border_radius=6)

    if pronto:
        _cometa(tela, retangulo.inflate(-2, -2), tempo * 0.16 + retangulo.x * 3, comprimento=8, passo=5)
