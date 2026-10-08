import pygame

pygame.init()

LARGURA = 1300
ALTURA = 900
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

FPS = 60
clock = pygame.time.Clock()


class Entidade(pygame.sprite.Sprite):
    def __init__(self, x, y, velocidade):
        super().__init__()
        self.velocidade = velocidade
        self.image = pygame.Surface((60, 80))
        self.rect = self.image.get_rect(center=(x, y))

    def mover(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy


class Maga(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, 5)
        self.image.fill((100, 0, 200))
        self.vida = 3

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            self.mover(0, -self.velocidade)

        if keys[pygame.K_s]:
            self.mover(0, self.velocidade)

        if keys[pygame.K_a]:
            self.mover(-self.velocidade, 0)

        if keys[pygame.K_d]:
            self.mover(self.velocidade, 0)

        self.rect.x = max(
            0,
            min(self.rect.x, LARGURA - self.rect.width)
        )

        self.rect.y = max(
            0,
            min(self.rect.y, ALTURA - self.rect.height)
        )


class Feiticeira(Entidade):
    def __init__(self, x, y, maga):
        super().__init__(x, y, 3)
        self.image.fill((200, 0, 100))
        self.vida = 3
        self.maga = maga

    def update(self):
        distancia_x = (
            self.maga.rect.centerx
            - self.rect.centerx
        )

        distancia_y = (
            self.maga.rect.centery
            - self.rect.centery
        )

        if abs(distancia_x) > 400:

            if distancia_x > 0:
                self.mover(self.velocidade, 0)
            else:
                self.mover(-self.velocidade, 0)

        elif abs(distancia_x) < 250:

            if distancia_x > 0:
                self.mover(-self.velocidade, 0)
            else:
                self.mover(self.velocidade, 0)

        else:

            if distancia_y > 0:
                self.mover(0, self.velocidade)
            else:
                self.mover(0, -self.velocidade)

        self.rect.x = max(
            0,
            min(self.rect.x, LARGURA - self.rect.width)
        )

        self.rect.y = max(
            0,
            min(self.rect.y, ALTURA - self.rect.height)
        )


class Cajado:
    def __init__(self):
        self.imagem = pygame.image.load(
            "imagens/Cajado.png"
        ).convert_alpha()

        self.imagem = pygame.transform.scale(
            self.imagem,
            (240, 400)
        )

        self.rect = self.imagem.get_rect()

    def atualizar(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.rect.topleft = (
            mouse_x - 120,
            mouse_y - 55
        )

    def desenhar(self, tela):
        tela.blit(self.imagem, self.rect)


todos_sprites = pygame.sprite.Group()

maga = Maga(150, ALTURA // 2)

feiticeira = Feiticeira(
    650,
    ALTURA // 2,
    maga
)

cajado = Cajado()

todos_sprites.add(maga)
todos_sprites.add(feiticeira)


modo_feitico = False


rodando = True

while rodando:
    clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            rodando = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_f:
                modo_feitico = not modo_feitico

    todos_sprites.update()

    cajado.atualizar()

    TELA.fill((20, 10, 30))

    if modo_feitico:
        cajado.desenhar(TELA)
    else:
        todos_sprites.draw(TELA)

    pygame.display.flip()

pygame.quit()