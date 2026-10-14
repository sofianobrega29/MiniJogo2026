from pathlib import Path
import math
import runpy
import pygame
from constantes import *
from elementos import Cajado, ProjetilMagico, RajadaZoltraak, ParedeMagica
from frieren import Maga
from clone import Feiticeira

pygame.init()
BASE_DIR = Path(__file__).resolve().parent
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")
RELOGIO = pygame.time.Clock()

fundo_primeira_pessoa = pygame.image.load(str(BASE_DIR / "imagens/Fundo/Arena.png")).convert()
fundo_terceira_pessoa = pygame.image.load(str(BASE_DIR / "imagens/Fundo/ParedeArena2D.jpeg")).convert()
vida_img = pygame.image.load(str(BASE_DIR / "imagens/UI/vida.png")).convert_alpha()
vida_img = pygame.transform.scale(vida_img, (45, 30))
fundo_primeira_pessoa = pygame.transform.scale(fundo_primeira_pessoa, (LARGURA, ALTURA))
fundo_terceira_pessoa = pygame.transform.scale(fundo_terceira_pessoa, (LARGURA, ALTURA - 120))

fonte = pygame.font.SysFont("arial", 54, bold=True)
fonte_menor = pygame.font.SysFont("arial", 28)
fonte_pequena = pygame.font.SysFont("arial", 22)

CHAO_Y = ALTURA - 120
DURACAO_TELA_FINAL = 8000


def desenhar_chao(tela):
    pygame.draw.rect(tela, (255, 231, 176), (0, CHAO_Y, LARGURA, 120))
    for x in range(0, LARGURA, 60):
        pygame.draw.line(tela, (45, 42, 50), (x, CHAO_Y), (x, ALTURA), 2)
    for y in range(CHAO_Y, ALTURA, 40):
        pygame.draw.line(tela, (45, 42, 50), (0, y), (LARGURA, y), 2)


def distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def comprimento_traco(pontos):
    return sum(distancia(pontos[i-1], pontos[i]) for i in range(1, len(pontos)))


def reconhecer_simbolo(pontos):
    """Retorna circulo, quadrado, estrela, raio ou None."""
    if len(pontos) < 12:
        return None
    xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
    largura, altura = max(xs)-min(xs), max(ys)-min(ys)
    if largura < 45 or altura < 35:
        return None
    fechamento = distancia(pontos[0], pontos[-1])
    diagonal = math.hypot(largura, altura)
    percurso = comprimento_traco(pontos)
    proporcao = largura / max(altura, 1)

    # Raio/Z: traço aberto, largo, com deslocamento vertical considerável.
    if fechamento > diagonal * 0.20 and largura > altura * 1.15:
        segmentos = [pontos[0], pontos[len(pontos)//3], pontos[2*len(pontos)//3], pontos[-1]]
        if segmentos[0][1] < segmentos[1][1] and segmentos[1][1] > segmentos[2][1] and segmentos[2][1] < segmentos[3][1]:
            return "raio"
        if segmentos[0][1] > segmentos[1][1] and segmentos[1][1] < segmentos[2][1] and segmentos[2][1] > segmentos[3][1]:
            return "raio"
        # O gesto pode ser um Z simples: topo, diagonal e base.
        if abs(pontos[0][1] - pontos[-1][1]) < altura * 0.45:
            return "raio"

    if fechamento > diagonal * 0.25:
        return None
    razao_percurso = percurso / max(diagonal, 1)
    if razao_percurso > 3.45:
        return "estrela"
    if 0.65 <= proporcao <= 1.45:
        # Quadrado tem quatro cantos e percurso próximo de 2,8 diagonais;
        # círculo costuma aproximar-se de 2,2 diagonais.
        if razao_percurso >= 2.45:
            return "quadrado"
        return "circulo"
    return None


def desenhar_vidas_maga(tela, maga):
    tela.blit(fonte_pequena.render("MAGA", True, BRANCO), (20, 15))
    for i in range(max(0, maga.vida)):
        tela.blit(vida_img, (20 + i * 50, 45))


def desenhar_barra_vida_clone(tela, clone):
    largura, altura = 350, 26
    x, y = LARGURA - largura - 30, 35
    vidas = max(0, min(clone.vida, clone.vida_maxima))
    texto = fonte_pequena.render(f"FEITICEIRA CLONE: {vidas}/{clone.vida_maxima}", True, BRANCO)
    tela.blit(texto, (x, 5))
    pygame.draw.rect(tela, (45, 35, 55), (x, y, largura, altura), border_radius=8)
    if vidas:
        pygame.draw.rect(tela, (180, 50, 220), (x, y, int(largura * vidas / clone.vida_maxima), altura), border_radius=8)
    pygame.draw.rect(tela, (230, 210, 240), (x, y, largura, altura), 2, border_radius=8)


def novo_jogo():
    maga = Maga(150, ALTURA - 200)
    clone = Feiticeira(950, 180)
    return maga, clone, Cajado()

maga, feiticeira, cajado = novo_jogo()
modo_feitico = False
desenhando = False
pontos_magicos = []
projeteis = []
rajadas = []
parede_maga = None
estado_jogo = "jogando"
tempo_fim = 0
botao_menu = pygame.Rect(LARGURA//2 - 170, ALTURA//2 + 45, 340, 60)

rodando = True
while rodando:
    dt = RELOGIO.tick(60)
    agora = pygame.time.get_ticks()

    if maga.rect.centerx < feiticeira.rect.centerx:
        maga.direcao, feiticeira.direcao = "direita", "esquerda"
    else:
        maga.direcao, feiticeira.direcao = "esquerda", "direita"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
            break

        if estado_jogo in ("vitoria", "derrota"):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and botao_menu.collidepoint(event.pos):
                rodando = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                rodando = False
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f and not modo_feitico:
                modo_feitico = True
                pontos_magicos = []
            if not modo_feitico and event.key in (pygame.K_w, pygame.K_UP):
                if maga.no_chao and not maga.voando:
                    maga.velocidade_y = maga.forca_pulo
                    maga.no_chao = False
                    maga.pulando = True
                elif maga.pulando and not maga.voando:
                    maga.voando = True
                    maga.pulando = False
                    maga.velocidade_y = 0
                    maga.tempo_voo = 0
                elif not maga.voando:
                    maga.contagem_w += 1
                    if maga.contagem_w >= 2:
                        maga.voando = True
                        maga.tempo_voo = 0

        if modo_feitico:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                desenhando = True
                pontos_magicos = [event.pos]
            elif event.type == pygame.MOUSEMOTION and desenhando:
                pontos_magicos.append(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and desenhando:
                desenhando = False
                simbolo = reconhecer_simbolo(pontos_magicos)
                if simbolo == "circulo":
                    projeteis.append(ProjetilMagico(maga.rect.center, feiticeira.rect.center, tipo="explosao"))
                elif simbolo == "quadrado":
                    parede_maga = ParedeMagica(maga)
                elif simbolo == "estrela":
                    rajadas.append(RajadaZoltraak(maga.rect.center, feiticeira.rect.center))
                elif simbolo == "raio":
                    # Raio desenhado com Pygame: linha roxa em zigue-zague que atinge o clone.
                    rajadas.append(RajadaZoltraak(maga.rect.center, feiticeira.rect.center, velocidade=22))
                    rajadas[-1].tipo_raio = True
                modo_feitico = False
                pontos_magicos = []

    if not rodando:
        break

    if estado_jogo == "jogando":
        if parede_maga and not parede_maga.ativa():
            parede_maga = None
        if not modo_feitico and maga.vida > 0:
            maga.update(TELA)
        if feiticeira.vida > 0:
            feiticeira.update(maga, projeteis)
            feiticeira.atualizar_magias(maga)

        for p in projeteis[:]:
            if pygame.time.get_ticks() < feiticeira.escudo_ate and p.rect.colliderect(feiticeira.rect.inflate(32, 30)):
                p.ativo = False
            else:
                p.update(feiticeira)
            if not p.ativo:
                projeteis.remove(p)
        for r in rajadas[:]:
            if pygame.time.get_ticks() < feiticeira.escudo_ate and r.rect.colliderect(feiticeira.rect.inflate(32, 30)):
                r.ativo = False
            else:
                r.update(feiticeira)
            if not r.ativo:
                rajadas.remove(r)

        for tiro in feiticeira.projeteis[:]:
            tiro.update()
            if not TELA.get_rect().colliderect(tiro.rect):
                feiticeira.projeteis.remove(tiro)
                continue
            bloqueado = parede_maga is not None and parede_maga.ativa() and tiro.rect.colliderect(parede_maga.rect)
            if bloqueado:
                feiticeira.projeteis.remove(tiro)
            elif maga.vida > 0 and tiro.rect.colliderect(maga.rect):
                maga.vida = max(0, maga.vida - tiro.dano)
                feiticeira.projeteis.remove(tiro)

        if feiticeira.vida <= 0:
            feiticeira.vida = 0
            estado_jogo = "vitoria"
            tempo_fim = agora
        elif maga.vida <= 0:
            maga.vida = 0
            estado_jogo = "derrota"
            tempo_fim = agora

    if estado_jogo == "jogando":
        if modo_feitico:
            TELA.blit(fundo_primeira_pessoa, (0, 0))
            if len(pontos_magicos) > 1:
                pygame.draw.lines(TELA, AZUL_MAGICO, False, pontos_magicos, 5)
            cajado.desenhar(TELA)
            dica = fonte_pequena.render("Desenhe: círculo = explosão | quadrado = defesa | estrela = Zoltraak | Z = raio", True, BRANCO)
            TELA.blit(dica, (20, ALTURA-40))
        else:
            TELA.blit(fundo_terceira_pessoa, (0, 0))
            desenhar_chao(TELA)
            TELA.blit(maga.image, maga.rect)
            if feiticeira.vida > 0:
                TELA.blit(feiticeira.image, feiticeira.rect)
                feiticeira.desenhar_magias(TELA)
            for p in projeteis: p.desenhar(TELA)
            for r in rajadas:
                if getattr(r, "tipo_raio", False):
                    # O ataque relâmpago é desenhado proceduralmente, sem precisar de sprite.
                    inicio = pygame.Vector2(r.posicao)
                    pontos = [(int(inicio.x), int(inicio.y))]
                    for i in range(1, 5):
                        pontos.append((int(inicio.x - r.direcao.x * i * 14 + (18 if i % 2 else -18)), int(inicio.y - r.direcao.y * i * 14)))
                    pygame.draw.lines(TELA, (150, 45, 255), False, pontos, 9)
                    pygame.draw.lines(TELA, (235, 210, 255), False, pontos, 3)
                else:
                    r.desenhar(TELA)
            for tiro in feiticeira.projeteis: tiro.desenhar(TELA)
            if parede_maga and parede_maga.ativa(): parede_maga.desenhar(TELA)
            desenhar_vidas_maga(TELA, maga)
            desenhar_barra_vida_clone(TELA, feiticeira)
            estado_voo = "Voando" if maga.voando else "No chão"
            TELA.blit(fonte_pequena.render(f"Estado da maga: {estado_voo}", True, BRANCO), (20, 90))
    else:
        TELA.blit(fundo_terceira_pessoa, (0, 0))
        desenhar_chao(TELA)
        if maga.vida > 0: TELA.blit(maga.image, maga.rect)
        if feiticeira.vida > 0: TELA.blit(feiticeira.image, feiticeira.rect)
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((10, 8, 20, 205))
        TELA.blit(overlay, (0, 0))
        venceu = estado_jogo == "vitoria"
        titulo = fonte.render("VITÓRIA!" if venceu else "VOCÊ FOI DERROTADO", True, (100, 255, 150) if venceu else (255, 90, 100))
        TELA.blit(titulo, titulo.get_rect(center=(LARGURA//2, ALTURA//2 - 70)))
        subtitulo = fonte_menor.render("Você venceu o clone!" if venceu else "A clone foi mais forte desta vez.", True, BRANCO)
        TELA.blit(subtitulo, subtitulo.get_rect(center=(LARGURA//2, ALTURA//2 - 15)))
        cor_botao = (90, 50, 150) if botao_menu.collidepoint(pygame.mouse.get_pos()) else (65, 35, 115)
        pygame.draw.rect(TELA, cor_botao, botao_menu, border_radius=12)
        pygame.draw.rect(TELA, (220, 200, 255), botao_menu, 2, border_radius=12)
        texto = fonte_menor.render("Voltar ao menu", True, BRANCO)
        TELA.blit(texto, texto.get_rect(center=botao_menu.center))
        restante = max(0, DURACAO_TELA_FINAL - (agora - tempo_fim))
        TELA.blit(fonte_pequena.render(f"Retorno automático em {math.ceil(restante/1000)} s", True, BRANCO), (LARGURA//2 - 105, ALTURA//2 + 125))
        if agora - tempo_fim >= DURACAO_TELA_FINAL:
            rodando = False

    pygame.display.flip()

pygame.quit()
