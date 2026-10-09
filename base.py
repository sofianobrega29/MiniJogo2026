
import pygame
import math

pygame.init()

LARGURA = 1300
ALTURA = 900

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Confronto Mágico")

RELOGIO = pygame.time.Clock()

fundo_primeira_pessoa = pygame.image.load(
    "imagens/frieren-clone.webp"
).convert()
fundo_primeira_pessoa = pygame.transform.scale(
    fundo_primeira_pessoa, (LARGURA, ALTURA)
)

# Cores
BRANCO = (255, 255, 255)
AZUL_MAGICO = (100, 220, 255)
AZUL_CLARO = (220, 250, 255)


class Entidade(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 80), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))




class Maga(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vida = 3
        self.image.fill((80, 150, 255))

        self.no_chao = True
        self.pulando = False
        self.voando = False

        self.velocidade_y = 0
        self.gravidade = 0.7
        self.forca_pulo = -14

        self.tempo_voo = 0
        self.altura_base = y

    def update(self):
        teclas = pygame.key.get_pressed()

        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.rect.x -= 5

        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.rect.x += 5

        if self.voando:
            self.tempo_voo += 0.08

            if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                self.rect.y -= 4

            if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                self.rect.y += 4

            # Animação suave de flutuação.
            oscilacao = math.sin(self.tempo_voo) * 5
            self.rect.y += int(oscilacao)

        else:
            self.velocidade_y += self.gravidade
            self.rect.y += int(self.velocidade_y)

            limite_chao = ALTURA - 120 - self.rect.height

            if self.rect.bottom >= ALTURA - 120:
                self.rect.bottom = ALTURA - 120
                self.velocidade_y = 0
                self.no_chao = True
                self.pulando = False

            else:
                self.no_chao = False

        self.rect.clamp_ip(TELA.get_rect())






class Feiticeira(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vida = 3
        self.image.fill((220, 70, 100))

        self.velocidade = 3
        self.tempo_voo = 0
        self.canto_atual = 0
        self.ultimo_canto = pygame.time.get_ticks()

        self.limite_esquerdo = 80
        self.limite_direito = LARGURA - 140
        self.limite_superior = 100
        self.limite_inferior = ALTURA - 220

    def update(self):
        agora = pygame.time.get_ticks()
        self.tempo_voo += 0.06

        if maga.voando:
            # Fica no lado oposto ao jogador.
            if maga.rect.centerx > LARGURA // 2:
                alvo_x = self.limite_esquerdo
            else:
                alvo_x = self.limite_direito

            if self.rect.x < alvo_x:
                self.rect.x += self.velocidade
            elif self.rect.x > alvo_x:
                self.rect.x -= self.velocidade

            # Alterna entre o canto superior e o inferior.
            if agora - self.ultimo_canto >= 1500:
                self.canto_atual = 1 - self.canto_atual
                self.ultimo_canto = agora

            if self.canto_atual == 0:
                alvo_y = self.limite_superior
            else:
                alvo_y = self.limite_inferior

            if self.rect.y < alvo_y:
                self.rect.y += self.velocidade
            elif self.rect.y > alvo_y:
                self.rect.y -= self.velocidade

        else:
            # No chão, a inimiga flutua de um lado para o outro.
            if maga.rect.centerx < LARGURA // 2:
                alvo_x = self.limite_direito
            else:
                alvo_x = self.limite_esquerdo

            if self.rect.x < alvo_x:
                self.rect.x += self.velocidade
            elif self.rect.x > alvo_x:
                self.rect.x -= self.velocidade

            self.rect.y = int(
                180 + math.sin(self.tempo_voo) * 25
            )




class Cajado:
    def __init__(self):
        imagem = pygame.image.load(
            "imagens/Cajado.png"
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


def desenhar_chao(tela):
    altura_chao = 120

    pygame.draw.rect(
        tela,
        (70, 65, 75),
        (0, ALTURA - altura_chao, LARGURA, altura_chao)
    )

    tamanho_pedra = 60

    for x in range(0, LARGURA, tamanho_pedra):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (x, ALTURA - altura_chao),
            (x, ALTURA),
            2
        )

    for y in range(ALTURA - altura_chao, ALTURA, 40):
        pygame.draw.line(
            tela,
            (45, 42, 50),
            (0, y),
            (LARGURA, y),
            2
        )


def reconhecer_circulo(pontos):
    if len(pontos) < 20:
        return False

    inicio = pontos[0]
    fim = pontos[-1]

    distancia_fechamento = math.hypot(
        fim[0] - inicio[0],
        fim[1] - inicio[1]
    )

    xs = [ponto[0] for ponto in pontos]
    ys = [ponto[1] for ponto in pontos]

    largura = max(xs) - min(xs)
    altura = max(ys) - min(ys)

    if largura < 60 or altura < 60:
        return False

    proporcao = largura / altura

    if not 0.65 <= proporcao <= 1.35:
        return False

    if distancia_fechamento > max(largura, altura) * 0.25:
        return False

    return True


maga = Maga(150, ALTURA - 200)
feiticeira = Feiticeira(950, 180)
cajado = Cajado()

todos_sprites = pygame.sprite.Group()
todos_sprites.add(maga, feiticeira)

modo_feitico = False
pontos_magicos = []
desenhando = False
projeteis = []

fonte = pygame.font.SysFont(None, 36)
fonte_menor = pygame.font.SysFont(None, 28)

rodando = True

while rodando:
    RELOGIO.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

        
        if event.key == pygame.K_w or event.key == pygame.K_UP:
            if maga.no_chao and not maga.voando:
                # Primeiro W: pula.
                maga.velocidade_y = maga.forca_pulo
                maga.no_chao = False
                maga.pulando = True

            elif maga.pulando and not maga.voando:
                # Segundo W durante o pulo: começa a voar.
                maga.voando = True
                maga.pulando = False
                maga.velocidade_y = 0
                maga.tempo_voo = 0

                print("A maga começou a voar!")


            # O jogador começa andando.
            # Ao apertar W duas vezes, começa a voar.
            if not modo_feitico and event.key == pygame.K_w:
                maga.contagem_w += 1

                if maga.contagem_w >= 2 and not maga.voando:
                    maga.voando = True
                    print("A maga começou a voar!")

            if not modo_feitico and event.key == pygame.K_UP:
                maga.contagem_w += 1

                if maga.contagem_w >= 2 and not maga.voando:
                    maga.voando = True
                    print("A maga começou a voar!")

        if modo_feitico:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    desenhando = True
                    pontos_magicos = [event.pos]

            elif event.type == pygame.MOUSEMOTION:
                if desenhando:
                    pontos_magicos.append(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and desenhando:
                    desenhando = False

                    if reconhecer_circulo(pontos_magicos):
                        print("Círculo mágico reconhecido!")

                        # O ataque começa na posição da maga.
                        projeteis.append(
                            ProjetilMagico(maga.rect.center)
                        )
                    else:
                        print("Símbolo incorreto. Tente novamente.")

                    # Volta imediatamente ao modo normal.
                    modo_feitico = False
                    pontos_magicos = []

    # Atualiza personagens somente no modo normal.
    if not modo_feitico:
        maga.update()

        if feiticeira.vida > 0:
            feiticeira.update()

    # Atualiza os projéteis e verifica os acertos.
    for projetil in projeteis[:]:
        if feiticeira.vida <= 0:
            projeteis.remove(projetil)
            continue

        projetil.update(feiticeira)

        if not projetil.ativo:
            feiticeira.vida -= 1
            projeteis.remove(projetil)

            print("O ataque acertou a inimiga!")
            print("Vidas restantes:", max(0, feiticeira.vida))

            if feiticeira.vida <= 0:
                feiticeira.vida = 0
                feiticeira.kill()
                print("Inimiga derrotada!")

    # DESENHO DA TELA
    if modo_feitico:
        # A imagem de primeira pessoa aparece apenas ao desenhar.
        TELA.blit(fundo_primeira_pessoa, (0, 0))

        if len(pontos_magicos) > 1:
            pygame.draw.lines(
                TELA,
                AZUL_MAGICO,
                False,
                pontos_magicos,
                5
            )

        cajado.desenhar(TELA)

    else:
        # O modo normal não usa a imagem de primeira pessoa.
        TELA.fill((20, 10, 30))
        desenhar_chao(TELA)

        todos_sprites.draw(TELA)

        for projetil in projeteis:
            projetil.desenhar(TELA)

        texto_vida = fonte.render(
            f"Vidas da inimiga: {feiticeira.vida}",
            True,
            BRANCO
        )
        TELA.blit(texto_vida, (20, 20))

        estado_voo = "Voando" if maga.voando else "No chão"
        texto_estado = fonte_menor.render(
            f"Estado da maga: {estado_voo}",
            True,
            BRANCO
        )
        TELA.blit(texto_estado, (20, 60))

    pygame.display.flip()

pygame.quit()
