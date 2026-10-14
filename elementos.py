from pathlib import Path

import pygame


class Cajado:
    """Cajado que acompanha o mouse no modo de feitiço."""

    def __init__(self):
        caminho = Path(__file__).resolve().parent / "imagens" / "UI" / "Cajado.png"
        imagem = pygame.image.load(str(caminho)).convert_alpha()

        self.image = pygame.transform.scale(imagem, (240, 400))
        self.rect = self.image.get_rect()

    def desenhar(self, tela):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.rect.topleft = (mouse_x - 120, mouse_y - 55)
        tela.blit(self.image, self.rect)
