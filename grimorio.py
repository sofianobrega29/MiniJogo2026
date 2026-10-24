"""Tela "Como jogar" em forma de grimório: pergaminho, tinta escura e símbolos feitos à pena.

`obter()` monta a imagem uma única vez (é pesada) e devolve sempre a mesma.
"""

import math
import random

import pygame

import estilo
from constantes import LARGURA, ALTURA
from particulas import misturar

TINTA = (24, 16, 20)             # tinta bem escura
TINTA_VERMELHA = (104, 24, 26)   # destaques (teclas)
TINTA_AZUL = (30, 34, 82)        # anotação à mão na margem
PAPEL = (222, 199, 155)

PAGINA_ESQUERDA = pygame.Rect(64, 46, 578, 730)
PAGINA_DIREITA = pygame.Rect(658, 46, 578, 730)

_cache = {}


# --------------------------------------------------------------------------
# Tinta e pena
# --------------------------------------------------------------------------
def _tinta(superficie, pontos, largura=3.0, cor=TINTA, sorteio=None, tremor=0.7, borrao=True):
    """Traço de pena: largura que varia (pressão), tremidinha e pingos de tinta."""
    sorteio = sorteio or random.Random(5)
    total = len(pontos) - 1
    fase = sorteio.uniform(0, math.tau)

    for i in range(total):
        (x0, y0), (x1, y1) = pontos[i], pontos[i + 1]
        comprimento = max(1.0, math.hypot(x1 - x0, y1 - y0))
        passos = max(1, int(comprimento / 1.6))

        for k in range(passos):
            t = k / passos
            x = x0 + (x1 - x0) * t + sorteio.uniform(-tremor, tremor) * 0.35
            y = y0 + (y1 - y0) * t + sorteio.uniform(-tremor, tremor) * 0.35
            avanco = (i + t) / max(1, total)
            pressao = 0.62 + 0.38 * math.sin(fase + avanco * 9.0) * max(0.0, math.sin(avanco * math.pi + 0.3)) ** 0.5
            raio = max(0.7, largura * pressao * 0.5)
            pygame.draw.circle(superficie, cor, (round(x), round(y)), max(1, round(raio)))

    if borrao and pontos:
        # Pinguinho de tinta onde a pena encostou.
        x, y = pontos[0]
        pygame.draw.circle(superficie, cor, (round(x), round(y)), max(2, round(largura * 0.95)))


def _escrever(superficie, texto, fonte, posicao, cor=TINTA, ancora="topleft", rotacao=0.0):
    """Texto "de tinta": desenhado duas vezes, com um fio mais claro por baixo (a tinta escorre um pouco)."""
    imagem = fonte.render(texto, True, cor)
    sombra = fonte.render(texto, True, misturar(cor, PAPEL, 0.45))
    folha = pygame.Surface((imagem.get_width() + 3, imagem.get_height() + 3), pygame.SRCALPHA)
    folha.blit(sombra, (1, 1))
    folha.blit(imagem, (0, 0))

    if rotacao:
        folha = pygame.transform.rotate(folha, rotacao)

    retangulo = folha.get_rect(**{ancora: posicao})
    superficie.blit(folha, retangulo)
    return retangulo


# --------------------------------------------------------------------------
# Pergaminho
# --------------------------------------------------------------------------
def _mesa():
    """Fundo escuro, com um halo de mana azul atrás do livro."""
    mesa = pygame.Surface((LARGURA, ALTURA))
    mesa.fill((14, 10, 18))

    for y in range(0, ALTURA, 46):
        pygame.draw.line(mesa, (21, 15, 24), (0, y), (LARGURA, y), 2)

    halo = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    for i in range(16, 0, -1):  # elipses de fora para dentro, cada vez mais fortes
        elipse = pygame.Rect(0, 0, 1240 + i * 36, 800 + i * 30)
        elipse.center = (LARGURA // 2, ALTURA // 2)
        pygame.draw.ellipse(halo, (50, 100, 220, int(7 + (16 - i) * 1.4)), elipse)

    mesa.blit(halo, (0, 0))
    return mesa


def _papel(retangulo, semente):
    """Página de pergaminho: manchas de papel, bordas queimadas e sombra na dobra do meio."""
    sorteio = random.Random(semente)
    largura, altura = retangulo.size
    pagina = pygame.Surface((largura, altura))

    # textura: ruído de baixa resolução ampliado com suavização
    colunas, linhas = largura // 7, altura // 7
    ruido = pygame.Surface((colunas, linhas))

    for y in range(linhas):
        for x in range(colunas):
            variacao = sorteio.randint(-12, 10)
            ruido.set_at((x, y), tuple(max(0, min(255, c + variacao)) for c in PAPEL))

    pagina.blit(pygame.transform.smoothscale(ruido, (largura, altura)), (0, 0))

    marcas = pygame.Surface((largura, altura), pygame.SRCALPHA)

    # manchas envelhecidas
    for _ in range(16):
        raio = sorteio.randint(22, 80)
        pygame.draw.circle(
            marcas, (150, 104, 54, sorteio.randint(10, 24)),
            (sorteio.randint(0, largura), sorteio.randint(0, altura)), raio,
        )

    # bordas queimadas
    for i in range(46):
        alfa = int(84 * (1 - i / 46) ** 2.2)
        pygame.draw.rect(marcas, (96, 56, 22, alfa), (i, i, largura - i * 2, altura - i * 2), 1)

    # sombra da dobra do livro (lado de dentro da página)
    esquerda = retangulo.x < LARGURA // 2

    pagina.blit(marcas, (0, 0))

    dobra = pygame.Surface((largura, altura), pygame.SRCALPHA)  # camada à parte: soma ao escurecimento das bordas

    for i in range(86):
        alfa = int(130 * (1 - i / 86) ** 2.0)
        x = largura - 1 - i if esquerda else i
        pygame.draw.line(dobra, (52, 28, 16, alfa), (x, 0), (x, altura))

    pagina.blit(dobra, (0, 0))
    return pagina


def _livro():
    """Capa de couro, as duas páginas e a lombada."""
    livro = _mesa()
    couro = pygame.Rect(36, 22, 1228, 780)

    pygame.draw.rect(livro, (24, 14, 10), couro.inflate(10, 10), border_radius=22)
    pygame.draw.rect(livro, (66, 38, 28), couro, border_radius=18)
    pygame.draw.rect(livro, (112, 80, 40), couro.inflate(-16, -16), 2, border_radius=14)

    # tachinhas douradas nos cantos
    for cx, cy in ((couro.left + 20, couro.top + 20), (couro.right - 20, couro.top + 20),
                   (couro.left + 20, couro.bottom - 20), (couro.right - 20, couro.bottom - 20)):
        pygame.draw.circle(livro, (170, 128, 52), (cx, cy), 7)
        pygame.draw.circle(livro, (236, 206, 120), (cx - 2, cy - 2), 2)

    livro.blit(_papel(PAGINA_ESQUERDA, 11), PAGINA_ESQUERDA.topleft)
    livro.blit(_papel(PAGINA_DIREITA, 12), PAGINA_DIREITA.topleft)
    pygame.draw.line(livro, (30, 16, 10), (LARGURA // 2, 46), (LARGURA // 2, 776), 6)
    return livro


# --------------------------------------------------------------------------
# Enfeites e símbolos à pena
# --------------------------------------------------------------------------
def _moldura(livro, pagina, sorteio):
    """Fio duplo em volta da página com losangos nos cantos."""
    caixa = pagina.inflate(-30, -30)
    _tinta(livro, [caixa.topleft, caixa.topright, caixa.bottomright, caixa.bottomleft, caixa.topleft], 2.0, sorteio=sorteio, tremor=0.5, borrao=False)
    caixa2 = pagina.inflate(-40, -40)
    _tinta(livro, [caixa2.topleft, caixa2.topright, caixa2.bottomright, caixa2.bottomleft, caixa2.topleft], 1.1, sorteio=sorteio, tremor=0.4, borrao=False)

    for canto in (caixa.topleft, caixa.topright, caixa.bottomleft, caixa.bottomright):
        x, y = canto
        pygame.draw.polygon(livro, TINTA, [(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)])


def _floreio(livro, centro, comprimento, sorteio):
    """Traço decorativo sob os títulos: linha ondulada com espirais nas pontas."""
    cx, cy = centro
    pontos = []

    for i in range(41):
        t = i / 40
        pontos.append((cx - comprimento / 2 + comprimento * t, cy + math.sin(t * math.pi * 4) * 3.2))

    _tinta(livro, pontos, 2.6, sorteio=sorteio, tremor=0.5)

    # espiral que sai da ponta direita e se enrola; a da esquerda é o espelho dela
    fim_x = cx + comprimento / 2
    espiral = []

    for i in range(30):
        t = i / 29
        angulo = math.pi + t * math.pi * 3.4
        raio = 12 * (1 - t) + 1
        espiral.append((fim_x + 12 + math.cos(angulo) * raio, cy + math.sin(angulo) * raio))

    _tinta(livro, espiral, 2.2, sorteio=sorteio, tremor=0.4, borrao=False)
    _tinta(livro, [(2 * cx - x, y) for x, y in espiral], 2.2, sorteio=sorteio, tremor=0.4, borrao=False)
    pygame.draw.polygon(livro, TINTA, [(cx, cy - 7), (cx + 6, cy), (cx, cy + 7), (cx - 6, cy)])


def _estrelinha_tinta(livro, centro, raio, cor=TINTA):
    cx, cy = centro
    fino = raio * 0.28
    pygame.draw.polygon(livro, cor, [
        (cx, cy - raio), (cx + fino, cy - fino), (cx + raio, cy), (cx + fino, cy + fino),
        (cx, cy + raio), (cx - fino, cy + fino), (cx - raio, cy), (cx - fino, cy - fino),
    ])


def _simbolo(livro, nome, centro, r, sorteio):
    """O desenho de cada feitiço, como o jogador deve traçar, com aguada de cor por baixo."""
    cx, cy = centro
    aguada = {
        "circulo": (178, 44, 44), "quadrado": (60, 120, 210), "estrela": (70, 170, 220),
        "raio": (130, 70, 200), "cruz": (70, 170, 100), "x": (120, 190, 230),
    }[nome]

    # aguada (mancha de tinta colorida e translúcida)
    mancha = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)

    for k in range(4):
        pygame.draw.circle(mancha, (*aguada, 26), (int(r * 1.5 + sorteio.uniform(-6, 6)), int(r * 1.5 + sorteio.uniform(-6, 6))), int(r * (1.15 - k * 0.12)))

    livro.blit(mancha, mancha.get_rect(center=centro))

    def v(x, y):
        return (cx + x * r, cy + y * r)

    if nome == "circulo":
        pontos = [v(math.cos(a) * (1 + 0.035 * math.sin(3 * a)), math.sin(a) * (1 + 0.035 * math.sin(3 * a)))
                  for a in [(-math.pi / 2) + i * (math.tau * 1.07) / 50 for i in range(51)]]
        _tinta(livro, pontos, 3.6, sorteio=sorteio)
    elif nome == "quadrado":
        _tinta(livro, [v(-0.95, -1.0), v(1.0, -0.95), v(0.95, 1.0), v(-1.0, 0.95), v(-0.93, -1.08)], 3.6, sorteio=sorteio)
    elif nome == "estrela":
        vert = [v(math.sin(math.radians(a)), -math.cos(math.radians(a))) for a in (0, 144, 288, 72, 216, 0)]
        _tinta(livro, vert, 3.4, sorteio=sorteio)
    elif nome == "raio":
        _tinta(livro, [v(-0.9, -0.95), v(0.95, -0.95), v(-0.95, 0.95), v(0.9, 0.95)], 3.6, sorteio=sorteio)
    elif nome == "cruz":
        _tinta(livro, [v(0, -1.05), v(0.02, 1.05)], 3.8, sorteio=sorteio)
        _tinta(livro, [v(-0.9, 0.02), v(0.95, 0.0)], 3.8, sorteio=sorteio)
    elif nome == "x":
        _tinta(livro, [v(-0.9, -0.9), v(0.95, 0.95)], 3.8, sorteio=sorteio)
        _tinta(livro, [v(0.9, -0.9), v(-0.95, 0.95)], 3.8, sorteio=sorteio)

    # pontinho de partida do traço
    inicio = {"circulo": v(0, -1), "quadrado": v(-0.95, -1.0), "estrela": v(0, -1), "raio": v(-0.9, -0.95),
              "cruz": v(0, -1.05), "x": v(-0.9, -0.9)}[nome]
    pygame.draw.circle(livro, TINTA_VERMELHA, (round(inicio[0]), round(inicio[1])), 5)


# --------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------
FEITICOS = [
    ("circulo", "Orbe", ("explode ao tocar o chão,", "a parede ou a clone")),
    ("quadrado", "Parede", ("escudo de hexágonos que", "aguenta 3 golpes")),
    ("estrela", "Zoltraak", ("portal que dispara", "um feixe de luz")),
    ("raio", "Raio", ("cai do céu depois", "de um aviso no chão")),
    ("cruz", "Cura", ("2 traços cruzados, em pé:", "recupera 1 vida")),
    ("x", "Gelo", ("2 traços em diagonal:", "congela a clone")),
]


def _montar():
    sorteio = random.Random(42)
    livro = _livro()

    titulo = estilo.fonte(estilo.FONTE_GRIMORIO_TITULO, 54, True)
    secao = estilo.fonte(estilo.FONTE_GRIMORIO_TITULO, 30, True)
    chave = estilo.fonte(estilo.FONTE_GRIMORIO_TITULO, 25, True)
    texto = estilo.fonte(estilo.FONTE_GRIMORIO_TEXTO, 25)
    texto_pequeno = estilo.fonte(estilo.FONTE_GRIMORIO_TEXTO, 22)
    nota = estilo.fonte(estilo.FONTE_NOTAS, 30)

    for pagina in (PAGINA_ESQUERDA, PAGINA_DIREITA):
        _moldura(livro, pagina, sorteio)

    # ------------------------ página da esquerda ------------------------
    e = PAGINA_ESQUERDA
    _escrever(livro, "Como Jogar", titulo, (e.centerx, e.top + 30), TINTA, "midtop")
    _floreio(livro, (e.centerx, e.top + 100), 300, sorteio)

    x = e.left + 58
    y = e.top + 130

    def bloco(titulo_secao, linhas, y):
        _escrever(livro, titulo_secao, secao, (x - 6, y), TINTA)
        _tinta(livro, [(x - 6, y + 40), (x + 250, y + 41)], 1.6, sorteio=sorteio, borrao=False)
        y += 52

        for tecla, descricao in linhas:
            _escrever(livro, tecla, chave, (x, y), TINTA_VERMELHA)
            _escrever(livro, descricao, texto, (x + 14, y + 28), TINTA)
            y += 58

        return y

    y = bloco("Movimento", [
        ("A / D   ou   setas", "andar para os lados"),
        ("W   ou   seta para cima", "saltar; de novo no ar, voar"),
        ("S   ou   seta para baixo", "descer; ao tocar o chão, pousa"),
    ], y)
    y = bloco("Feitiços", [
        ("F", "abrir o modo de feitiço (F ou ESC fecha)"),
        ("Mouse", "desenhe o símbolo e solte para lançar"),
    ], y + 4)

    _escrever(livro, "Objetivo", secao, (x - 6, y + 2), TINTA)
    _tinta(livro, [(x - 6, y + 42), (x + 190, y + 43)], 1.6, sorteio=sorteio, borrao=False)
    _escrever(livro, "Zere as 11 vidas da clone", texto, (x + 14, y + 52), TINTA)
    _escrever(livro, "sem perder as suas 3.", texto, (x + 14, y + 78), TINTA)

    # anotações à mão na margem, em outra tinta
    _escrever(livro, "o tempo para enquanto você desenha!", estilo.fonte(estilo.FONTE_NOTAS, 26), (e.centerx, e.bottom - 100), TINTA_AZUL, "midtop", rotacao=1.5)
    _escrever(livro, "(com 3 vidas, a clone abre um buraco negro...)", estilo.fonte(estilo.FONTE_NOTAS, 22), (e.centerx, e.bottom - 68), TINTA_AZUL, "midtop", rotacao=-1.0)
    _estrelinha_tinta(livro, (e.left + 46, e.bottom - 82), 8)

    # ------------------------- página da direita -------------------------
    d = PAGINA_DIREITA
    _escrever(livro, "Os Feitiços", titulo, (d.centerx, d.top + 30), TINTA, "midtop")
    _floreio(livro, (d.centerx, d.top + 100), 300, sorteio)

    colunas = (d.left + 150, d.right - 150)
    linhas_y = (d.top + 196, d.top + 374, d.top + 552)

    for indice, (simbolo, nome, descricao) in enumerate(FEITICOS):
        cx = colunas[indice % 2]
        cy = linhas_y[indice // 2]
        _simbolo(livro, simbolo, (cx, cy), 32, sorteio)
        _escrever(livro, nome, secao, (cx, cy + 46), TINTA, "midtop")

        for n, linha in enumerate(descricao):
            _escrever(livro, linha, texto_pequeno, (cx, cy + 86 + n * 22), TINTA, "midtop")

    _estrelinha_tinta(livro, (d.right - 46, d.bottom - 60), 8)
    return livro


def obter():
    if "livro" not in _cache:
        _cache["livro"] = _montar().convert()

    return _cache["livro"]
