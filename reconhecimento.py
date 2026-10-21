"""Reconhecimento dos símbolos desenhados com o mouse no modo cajado.

Este módulo não depende do pygame: recebe uma lista de pontos (x, y) e devolve o
nome do símbolo reconhecido. Isso permite testar tudo sem abrir janela.

Símbolos aceitos:
    "circulo"  -> ataque com orbe explosivo
    "quadrado" -> defesa (parede mágica)
    "estrela"  -> zoltraak (estrela de cinco pontas, de preferência num traço só)
    "raio"     -> raio roxo (letra Z, ou o Z espelhado)

Como funciona: o traço é reamostrado em N pontos, centralizado e escalado para
uma caixa 1x1. Depois medimos a distância entre o desenho e cada modelo, nos dois
sentidos (desenho -> modelo e modelo -> desenho). Como a comparação não depende
da ordem dos pontos, tanto faz onde o jogador começou a desenhar ou para que lado.
Os 10% de pontos mais distantes são ignorados, o que perdoa pequenas sobras e
falhas no fechamento da forma.
"""

import math

N_PONTOS = 96
TAMANHO_MINIMO = 60      # largura e altura mínimas do desenho, em pixels
PROPORCAO_MINIMA = 0.4   # largura/altura aceitas (e o inverso)
PERCENTIL = 0.90         # ignora os 10% de pontos mais distantes

# Distância máxima aceita entre o desenho e o modelo (caixa normalizada 1x1).
# Quanto maior, mais tolerante. Ajuste aqui se estiver difícil ou fácil demais.
TOLERANCIA = {
    "circulo": 0.11,
    "quadrado": 0.11,
    "estrela": 0.11,
    "raio": 0.14,
}


# --------------------------------------------------------------------------
# Funções geométricas básicas
# --------------------------------------------------------------------------
def _distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def comprimento_total(pontos):
    return sum(_distancia(pontos[i - 1], pontos[i]) for i in range(1, len(pontos)))


def reamostrar(pontos, n=N_PONTOS):
    """Devolve n pontos igualmente espaçados ao longo do traço."""
    pts = [tuple(p) for p in pontos]
    comprimento = comprimento_total(pts)

    if comprimento == 0:
        return [pts[0]] * n

    intervalo = comprimento / (n - 1)
    novos = [pts[0]]
    acumulado = 0.0
    i = 1

    while i < len(pts):
        d = _distancia(pts[i - 1], pts[i])

        if d > 0 and acumulado + d >= intervalo:
            t = (intervalo - acumulado) / d
            q = (
                pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0]),
                pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1]),
            )
            novos.append(q)
            pts.insert(i, q)
            acumulado = 0.0
        else:
            acumulado += d

        i += 1

    while len(novos) < n:
        novos.append(pts[-1])

    return novos[:n]


def normalizar(pontos):
    """Centraliza no zero e escala para uma caixa de 1x1 (cada eixo separado)."""
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]

    largura = (max(xs) - min(xs)) or 1.0
    altura = (max(ys) - min(ys)) or 1.0
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2

    return [((x - cx) / largura, (y - cy) / altura) for x, y in pontos]


def _rotacionar(pontos, graus):
    rad = math.radians(graus)
    c, s = math.cos(rad), math.sin(rad)
    return [(x * c - y * s, x * s + y * c) for x, y in pontos]


def _distancias_ate(origem, destino):
    """Para cada ponto de origem, a distância até o ponto mais próximo de destino."""
    resultado = []

    for ox, oy in origem:
        melhor = float("inf")

        for dx, dy in destino:
            d = (ox - dx) * (ox - dx) + (oy - dy) * (oy - dy)

            if d < melhor:
                melhor = d

        resultado.append(math.sqrt(melhor))

    return resultado


def _percentil(valores, p=PERCENTIL):
    ordenados = sorted(valores)
    indice = min(len(ordenados) - 1, int(p * len(ordenados)))
    return ordenados[indice]


def distancia_ao_modelo(candidato, modelo):
    """Distância (0 = idêntico) entre dois caminhos normalizados."""
    return max(
        _percentil(_distancias_ate(candidato, modelo)),
        _percentil(_distancias_ate(modelo, candidato)),
    )


# --------------------------------------------------------------------------
# Modelos
# --------------------------------------------------------------------------
def _modelo(vertices, fechado, graus=0):
    caminho = list(vertices) + ([vertices[0]] if fechado else [])

    if graus:
        caminho = _rotacionar(caminho, graus)

    return normalizar(reamostrar(caminho))


def _construir_modelos():
    modelos = {}

    # Círculo (como a ordem não importa, basta uma volta completa).
    circulo = [
        (0.5 * math.cos(math.radians(360 * i / 72)), 0.5 * math.sin(math.radians(360 * i / 72)))
        for i in range(72)
    ]
    modelos["circulo"] = [_modelo(circulo, True)]

    quadrado = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    modelos["quadrado"] = [_modelo(quadrado, True, g) for g in (0, -8, 8)]

    # Estrela de cinco pontas num traço só (pentagrama): pula de ponta em ponta.
    pontas = [
        (0.5 * math.cos(math.radians(-90 + 72 * k)), 0.5 * math.sin(math.radians(-90 + 72 * k)))
        for k in range(5)
    ]
    pentagrama = [pontas[i] for i in (0, 2, 4, 1, 3)]
    # A estrela se repete a cada 72 graus, então 0..60 cobre todas as inclinações.
    modelos["estrela"] = [_modelo(pentagrama, True, g) for g in (0, 12, 24, 36, 48, 60)]

    # Z (e o Z espelhado): traço de cima, diagonal para baixo e traço de baixo.
    # Cada Z é guardado também levemente inclinado, porque ninguém desenha um Z
    # perfeitamente reto com o mouse.
    z = [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)]
    z_espelhado = [(0.5, -0.5), (-0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    modelos["raio"] = [
        _modelo(v, False, g)
        for v in (z, z_espelhado)
        for g in (-10, 0, 10)
    ]

    return modelos


MODELOS = _construir_modelos()


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------
def medir(pontos):
    """Devolve {simbolo: distancia} ou {} se o desenho for pequeno demais."""
    if len(pontos) < 12:
        return {}

    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]
    largura = max(xs) - min(xs)
    altura = max(ys) - min(ys)

    if largura < TAMANHO_MINIMO or altura < TAMANHO_MINIMO:
        return {}

    if not PROPORCAO_MINIMA <= largura / altura <= 1 / PROPORCAO_MINIMA:
        return {}

    candidato = normalizar(reamostrar(pontos))

    return {
        nome: min(distancia_ao_modelo(candidato, m) for m in variantes)
        for nome, variantes in MODELOS.items()
    }


def reconhecer(pontos):
    """Devolve o nome do símbolo desenhado ou None se nenhum for reconhecido."""
    distancias = medir(pontos)

    # Fica só com os símbolos dentro da tolerância e escolhe o mais parecido.
    aceitos = {
        nome: d / TOLERANCIA[nome]
        for nome, d in distancias.items()
        if d <= TOLERANCIA[nome]
    }

    if not aceitos:
        return None

    return min(aceitos, key=aceitos.get)


# --------------------------------------------------------------------------
# Feitiços de 2 traços: cruz (+) = cura, X = gelo
# --------------------------------------------------------------------------
def e_linha(pontos):
    """True se o traço é (quase) uma reta de tamanho razoável."""
    if len(pontos) < 6:
        return False

    a, b = pontos[0], pontos[-1]
    corda = _distancia(a, b)

    if corda < 60:
        return False

    dx, dy = (b[0] - a[0]) / corda, (b[1] - a[1]) / corda
    desvio = max(abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) for p in pontos)

    return desvio <= 0.14 * corda and comprimento_total(pontos) <= 1.35 * corda


def classificar_cruz(traco_a, traco_b):
    """Dois traços retos formam uma "cruz" (+), um "x" ou nada (None)?

    Os traços precisam ter tamanhos parecidos, ser quase perpendiculares e se
    cruzar perto do meio de cada um.
    """
    if not (e_linha(traco_a) and e_linha(traco_b)):
        return None

    a0, a1, b0, b1 = traco_a[0], traco_a[-1], traco_b[0], traco_b[-1]
    da = (a1[0] - a0[0], a1[1] - a0[1])
    db = (b1[0] - b0[0], b1[1] - b0[1])
    la, lb = math.hypot(*da), math.hypot(*db)

    if not 0.4 <= la / lb <= 2.5:
        return None

    # quase perpendiculares (ângulo entre eles de pelo menos 55 graus)
    if abs(da[0] * db[0] + da[1] * db[1]) / (la * lb) > math.cos(math.radians(55)):
        return None

    # onde as retas se cruzam, como fração de cada traço
    det = db[0] * da[1] - da[0] * db[1]

    if abs(det) < 1e-6:
        return None

    w = (b0[0] - a0[0], b0[1] - a0[1])
    ta = (db[0] * w[1] - w[0] * db[1]) / det
    tb = (da[0] * w[1] - w[0] * da[1]) / det

    if not (0.15 <= ta <= 0.85 and 0.15 <= tb <= 0.85):
        return None

    angulo = math.degrees(math.atan2(da[1], da[0])) % 90
    desvio_eixo = min(angulo, 90 - angulo)  # 0 = em pé/deitado (+); 45 = diagonal (X)

    return "cruz" if desvio_eixo <= 22.5 else "x"
