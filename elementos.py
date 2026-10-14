from pathlib import Path
import math
import pygame
from constantes import *

BASE_DIR = Path(__file__).resolve().parent

class Cajado:
    def __init__(self):
        imagem = pygame.image.load(str(BASE_DIR / "imagens" / "UI" / "Cajado.png")).convert_alpha()
        self.image = pygame.transform.scale(imagem, (240, 400))
        self.rect = self.image.get_rect()

    def desenhar(self, tela):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.rect.topleft = (mouse_x - 120, mouse_y - 55)
        tela.blit(self.image, self.rect)

class ProjetilMagico:
    def __init__(self, inicio, alvo, velocidade=12, dano=1, tipo="explosao"):
        self.posicao = pygame.Vector2(inicio)
        self.alvo = pygame.Vector2(alvo)
        self.velocidade = velocidade
        self.dano = dano
        self.tipo = tipo
        self.raio = 12
        self.ativo = True
        self.explodindo = False
        self.tempo_explosao = 0
        self.raio_explosao = 0
        self.dano_aplicado = False
        direcao = self.alvo - self.posicao
        self.direcao = direcao.normalize() if direcao.length_squared() else pygame.Vector2(1, 0)

    def update(self, alvo=None):
        if self.explodindo:
            self.tempo_explosao += 1
            self.raio_explosao = min(55, self.raio_explosao + 5)
            if alvo is not None and not self.dano_aplicado:
                if pygame.Vector2(alvo.rect.center).distance_to(self.posicao) <= self.raio_explosao + max(alvo.rect.width, alvo.rect.height) * 0.35:
                    alvo.vida = max(0, alvo.vida - self.dano)
                    self.dano_aplicado = True
                    if hasattr(alvo, "ultimo_dano"):
                        alvo.ultimo_dano = pygame.time.get_ticks()
            if self.tempo_explosao >= 12:
                self.ativo = False
            return
        proxima = self.posicao + self.direcao * self.velocidade
        limite_chao = ALTURA - 120
        bateu_borda = proxima.x <= 0 or proxima.x >= LARGURA or proxima.y <= 0 or proxima.y >= limite_chao
        bateu_alvo = alvo is not None and pygame.Rect(0, 0, 1, 1).colliderect(pygame.Rect(0,0,0,0))
        if bateu_borda:
            self.posicao = pygame.Vector2(max(0, min(LARGURA, proxima.x)), max(0, min(limite_chao, proxima.y)))
            if self.tipo == "explosao":
                self.explodindo = True
                self.tempo_explosao = 0
                self.raio_explosao = 8
            else:
                self.ativo = False
            return
        self.posicao = proxima
        if alvo and self.rect.colliderect(alvo.rect):
            self.ativo = False
            alvo.vida = max(0, alvo.vida - self.dano)
            if hasattr(alvo, "ultimo_dano"):
                alvo.ultimo_dano = pygame.time.get_ticks()

    @property
    def rect(self):
        if self.explodindo:
            r = self.raio_explosao
            return pygame.Rect(int(self.posicao.x-r), int(self.posicao.y-r), r*2, r*2)
        return pygame.Rect(int(self.posicao.x-self.raio), int(self.posicao.y-self.raio), self.raio*2, self.raio*2)

    def desenhar(self, tela):
        if self.explodindo:
            pygame.draw.circle(tela, (255, 80, 80), (int(self.posicao.x), int(self.posicao.y)), self.raio_explosao)
            pygame.draw.circle(tela, (255, 190, 90), (int(self.posicao.x), int(self.posicao.y)), max(2, self.raio_explosao-10), 3)
            return
        centro = (int(self.posicao.x), int(self.posicao.y))
        pygame.draw.circle(tela, (255, 65, 75), centro, self.raio + 5)
        pygame.draw.circle(tela, (255, 180, 180), centro, self.raio)
        pygame.draw.circle(tela, BRANCO, centro, 4)

class RajadaZoltraak:
    def __init__(self, origem, alvo, velocidade=17):
        base_dir = Path(__file__).resolve().parent
        pasta_ui = base_dir / "imagens" / "UI"
        self.portal = pygame.image.load(str(pasta_ui / "zoltrak-pixilart.png")).convert_alpha()
        self.portal = pygame.transform.scale_by(self.portal, 5)
        self.raio_img = pygame.image.load(str(pasta_ui / "zoltrak-pixilart (1).png")).convert_alpha()
        self.raio_img = pygame.transform.scale_by(self.raio_img, 5)
        self.quadro_portal = 0
        self.posicao = pygame.Vector2(origem)
        direcao = pygame.Vector2(alvo) - self.posicao
        self.direcao = direcao.normalize() if direcao.length_squared() else pygame.Vector2(1, 0)
        self.velocidade = velocidade
        self.ativo = True
        self.rect = pygame.Rect(0, 0, 52, 18)
        self._atualizar_rect()

    def _atualizar_rect(self):
        self.rect.center = (int(self.posicao.x), int(self.posicao.y))

    def update(self, alvo=None):
        self.quadro_portal += 1
        if self.quadro_portal > 18:
            self.posicao += self.direcao * self.velocidade
        self._atualizar_rect()
        if not pygame.Rect(0, 0, LARGURA, ALTURA-120).colliderect(self.rect):
            self.ativo = False
        elif alvo and self.rect.colliderect(alvo.rect):
            alvo.vida = max(0, alvo.vida - 1)
            self.ativo = False

    def desenhar(self, tela):
        if self.quadro_portal <= 18:
            portal = pygame.transform.rotate(self.portal, -math.degrees(math.atan2(self.direcao.y, self.direcao.x)) + 90)
            tela.blit(portal, portal.get_rect(center=(int(self.posicao.x), int(self.posicao.y))))
        else:
            angulo = -math.degrees(math.atan2(self.direcao.y, self.direcao.x))
            raio = pygame.transform.rotate(self.raio_img, angulo)
            tela.blit(raio, raio.get_rect(center=(int(self.posicao.x), int(self.posicao.y))))

class ParedeMagica:
    def __init__(self, maga, duracao=2400):
        self.duracao = duracao
        self.criado = pygame.time.get_ticks()
        largura, altura = 28, 145
        x = maga.rect.right + 18 if maga.direcao == "direita" else maga.rect.left - largura - 18
        self.rect = pygame.Rect(x, maga.rect.centery - altura//2, largura, altura)

    def ativa(self):
        return pygame.time.get_ticks() - self.criado < self.duracao

    def desenhar(self, tela):
        pygame.draw.rect(tela, (80, 220, 255), self.rect, border_radius=8)
        pygame.draw.rect(tela, (225, 255, 255), self.rect, 3, border_radius=8)
        pygame.draw.line(tela, (180, 250, 255), self.rect.midtop, self.rect.midbottom, 2)
