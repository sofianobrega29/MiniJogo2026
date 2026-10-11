import pygame
from constantes import *

class Cajado:
    def __init__(self):
        imagem = pygame.image.load(
            "imagens/UI/Cajado.png"
        ).convert_alpha()

        self.image = pygame.transform.scale(imagem, (240, 400))
        self.rect = self.image.get_rect()

    def desenhar(self, tela):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.rect.topleft = (mouse_x - 120, mouse_y - 55)
        tela.blit(self.image, self.rect)


class ProjetilMagico:
    def __init__(self, inicio):
        self.posicao = pygame.math.Vector2(inicio)
        self.velocidade = 12
        self.raio = 12
        self.ativo = True

    def update(self, alvo):
        if not self.ativo:
            return

        destino = pygame.math.Vector2(alvo.rect.center)
        direcao = destino - self.posicao

        if direcao.length() <= self.velocidade + self.raio:
            self.ativo = False
            return

        self.posicao += direcao.normalize() * self.velocidade

    def desenhar(self, tela):
        centro = (int(self.posicao.x), int(self.posicao.y))

        pygame.draw.circle(tela, AZUL_MAGICO, centro, self.raio + 5)
        pygame.draw.circle(tela, AZUL_CLARO, centro, self.raio)
        pygame.draw.circle(tela, BRANCO, centro, 5)
