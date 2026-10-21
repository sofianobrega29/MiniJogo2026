"""Confere a cruz (+) e o X, feitiços de 2 traços, e que um traço reto sozinho não vira outro feitiço."""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import reconhecimento as R

random.seed(9)


def reta(p0, p1, ruido=2.5):
    n = random.randint(8, 40)
    return [
        (int(p0[0] + (p1[0] - p0[0]) * k / (n - 1) + random.gauss(0, ruido)),
         int(p0[1] + (p1[1] - p0[1]) * k / (n - 1) + random.gauss(0, ruido)))
        for k in range(n)
    ]


def par_cruzado(tipo):
    """Dois traços retos cruzados (com ruído, inclinação, tamanhos e sentidos variados)."""
    t = random.uniform(70, 170)
    rot = random.uniform(-0.3, 0.3) + (math.pi / 4 if tipo == "x" else 0)

    def pt(x, y):
        return (650 + x * math.cos(rot) - y * math.sin(rot), 450 + x * math.sin(rot) + y * math.cos(rot))

    desvio = lambda: random.uniform(-0.15, 0.15) * t
    a = reta(pt(-t * random.uniform(.8, 1.2), desvio()), pt(t * random.uniform(.8, 1.2), desvio()))
    b = reta(pt(desvio(), -t * random.uniform(.8, 1.2)), pt(desvio(), t * random.uniform(.8, 1.2)))

    if random.random() < .5: a = a[::-1]
    if random.random() < .5: b = b[::-1]
    return (a, b) if random.random() < .5 else (b, a)


def main():
    N, ok = 1000, True

    for tipo in ("cruz", "x"):
        acertos = sum(R.classificar_cruz(*par_cruzado(tipo)) == tipo for _ in range(N))
        print(f"{tipo:5s} (2 traços) {acertos / N * 100:5.1f}%")
        ok &= acertos / N >= 0.9

    # Um traço reto sozinho (qualquer ângulo) não pode ser reconhecido como feitiço.
    confusoes = 0
    for _ in range(N):
        ang, t = random.uniform(0, math.pi), random.uniform(70, 260)
        cx, cy = random.uniform(300, 900), random.uniform(250, 650)
        traco = reta((cx - math.cos(ang) * t, cy - math.sin(ang) * t), (cx + math.cos(ang) * t, cy + math.sin(ang) * t))
        confusoes += R.reconhecer(traco) is not None
    print(f"traço reto sozinho virando feitiço: {confusoes}/{N}")
    ok &= confusoes == 0

    # Traços paralelos ou que não se cruzam não formam nada.
    falsos = 0
    for _ in range(300):
        falsos += R.classificar_cruz(reta((400, 400), (600, 400)), reta((400, 470), (600, 470))) is not None
        falsos += R.classificar_cruz(reta((400, 400), (600, 400)), reta((620, 300), (620, 500))) is not None
    print(f"paralelos / que não se cruzam aceitos: {falsos}/600")
    ok &= falsos == 0

    print("OK" if ok else "FALHOU")
    sys.exit(0 if ok else 1)


main()
