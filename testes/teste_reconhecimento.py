import math, random, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
import reconhecimento as R

def _laco_circulo():
    return [(0.5*math.cos(math.radians(-90+360*i/64)), 0.5*math.sin(math.radians(-90+360*i/64))) for i in range(64)]
def _laco_poligono(v):
    return R.reamostrar(list(v)+[v[0]], 65)[:-1]
R._laco_circulo = _laco_circulo
R._laco_poligono = _laco_poligono

random.seed(22)

def jitter_path(path, sigma):
    return [(x + random.gauss(0, sigma), y + random.gauss(0, sigma)) for x, y in path]

def irregular_sample(path, total=None):
    # simula velocidade de mouse irregular: pega pontos com espaçamento variável
    dense = R.reamostrar(path, 600)
    pts = [dense[0]]
    i = 0
    while i < len(dense) - 1:
        i += random.randint(3, 14)
        pts.append(dense[min(i, len(dense) - 1)])
    return pts

def transform(path, w, h, rot, cx=640, cy=450):
    rad = math.radians(rot)
    c, s = math.cos(rad), math.sin(rad)
    out = []
    for x, y in path:
        x, y = x * w, y * h
        out.append((cx + x * c - y * s, cy + x * s + y * c))
    return out

def laco_para_traco(laco, inicio, sentido, sobra):
    L = list(laco)
    if sentido < 0:
        L = list(reversed(L))
    L = L[inicio:] + L[:inicio]
    caminho = L + L[: max(1, int(len(L) * sobra))] if sobra >= 0 else L[: int(len(L) * (1 + sobra))]
    return caminho

def gerar(nome):
    if nome == "circulo":
        laco = R._laco_circulo()
    elif nome == "quadrado":
        laco = R._laco_poligono([(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)])
    elif nome == "estrela":
        pontas = [(0.5*math.cos(math.radians(-90+72*k)), 0.5*math.sin(math.radians(-90+72*k))) for k in range(5)]
        laco = R._laco_poligono([pontas[i] for i in [0,2,4,1,3]])
    if nome in ("circulo", "quadrado", "estrela"):
        n = len(laco)
        caminho = laco_para_traco(laco, random.randrange(n), random.choice([1,-1]), random.uniform(-0.08, 0.15))
        if nome == "circulo":
            # espiral leve: raio muda ao longo do traço
            caminho = [(x*(1+0.08*i/len(caminho)), y*(1+0.08*i/len(caminho))) for i,(x,y) in enumerate(caminho)]
        if nome == "quadrado":
            # cantos arredondados: suaviza
            caminho = [((caminho[i-1][0]+2*caminho[i][0]+caminho[(i+1)%len(caminho)][0])/4,
                        (caminho[i-1][1]+2*caminho[i][1]+caminho[(i+1)%len(caminho)][1])/4) for i in range(len(caminho))]
    else:
        z = [(-0.5,-0.5),(0.5,-0.5),(-0.5,0.5),(0.5,0.5)]
        if random.random() < 0.3:
            z = [(-x, y) for x, y in z]
        # cantos desalinhados
        z = [(x + random.gauss(0, .06), y + random.gauss(0, .06)) for x, y in z]
        caminho = R.reamostrar(z, 200)
        caminho = [((caminho[max(i-2,0)][0]+caminho[i][0]+caminho[min(i+2,len(caminho)-1)][0])/3,
                    (caminho[max(i-2,0)][1]+caminho[i][1]+caminho[min(i+2,len(caminho)-1)][1])/3) for i in range(len(caminho))]
    tam = random.uniform(110, 320)
    asp = random.uniform(0.75, 1.3)
    pts = transform(caminho, tam*asp, tam/asp, random.uniform(-12, 12), random.uniform(300, 900), random.uniform(250, 650))
    pts = jitter_path(pts, tam*random.uniform(0.01, 0.035))
    return irregular_sample(pts)

def negativos():
    out = []
    # triângulo
    for _ in range(40):
        tri = [(-0.5,0.5),(0.5,0.5),(0,-0.5),(-0.5,0.5)]
        out.append(("triangulo", irregular_sample(jitter_path(transform(R.reamostrar(tri,200), 220, 200, random.uniform(-20,20)), 5))))
    # V, N, S, M, 8, C, U, linha, arco, espiral, zigue-zague, rabisco
    formas = {
        "V": [(-0.5,-0.5),(0,0.5),(0.5,-0.5)],
        "N": [(-0.5,0.5),(-0.5,-0.5),(0.5,0.5),(0.5,-0.5)],
        "M": [(-0.5,0.5),(-0.5,-0.5),(0,0.1),(0.5,-0.5),(0.5,0.5)],
        "L": [(-0.5,-0.5),(-0.5,0.5),(0.5,0.5)],
        "linha": [(-0.5,-0.5),(0.5,0.5)],
        "zigzag": [(-0.5,-0.4),(-0.25,0.4),(0,-0.4),(0.25,0.4),(0.5,-0.4)],
        "seta": [(-0.5,0),(0.5,0),(0.2,-0.3),(0.5,0),(0.2,0.3)],
    }
    for nome, v in formas.items():
        for _ in range(15):
            out.append((nome, irregular_sample(jitter_path(transform(R.reamostrar(v,200), 230, 230, random.uniform(-15,15)), 4))))
    # C (arco aberto)
    for _ in range(20):
        arco = [(0.5*math.cos(math.radians(40+280*i/60)), 0.5*math.sin(math.radians(40+280*i/60))) for i in range(61)]
        out.append(("C", irregular_sample(jitter_path(transform(arco, 240, 240, 0), 4))))
    # 8
    for _ in range(15):
        oito = []
        for i in range(61):
            t = 2*math.pi*i/60
            oito.append((0.5*math.sin(t), 0.5*math.sin(2*t)))
        out.append(("oito", irregular_sample(jitter_path(transform(oito, 240, 240, 0), 4))))
    # rabisco aleatório
    for _ in range(40):
        p = [(random.uniform(300,900), random.uniform(200,700)) for _ in range(random.randint(6,14))]
        out.append(("rabisco", irregular_sample(p)))
    return out

def main():
    total_ok = 0; total = 0
    for nome in ("circulo","quadrado","estrela","raio"):
        ok = 0; n = 300
        erros = {}
        menor = 9
        for _ in range(n):
            pts = gerar(nome)
            r = R.reconhecer(pts)
            notas = R.medir(pts)
            if notas: menor = min(menor, -notas[nome])
            if r == nome: ok += 1
            else: erros[r] = erros.get(r, 0) + 1
        print(f"{nome:9s} {ok}/{n} ({100*ok/n:.0f}%) erros={erros} maior_dist={-menor:.3f}")
        total_ok += ok; total += n
    # negativos
    neg = negativos()
    falsos = {}
    for nome, pts in neg:
        r = R.reconhecer(pts)
        if r is not None:
            falsos.setdefault(nome, {}).setdefault(r, 0)
            falsos[nome][r] += 1
    print(f"negativos: {len(neg)} amostras, falsos positivos: {falsos}")
    # ruído pequeno demais
    print("curto:", R.reconhecer([(10,10),(12,12)]*10), "| pequeno:", R.reconhecer([(500+5*math.cos(t/3), 500+5*math.sin(t/3)) for t in range(40)]))
main()
