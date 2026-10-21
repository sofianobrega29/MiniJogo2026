import pygame


class Entidade(pygame.sprite.Sprite):
    """Qualquer coisa com sprite e posição na arena."""

    # Proporção do sprite que realmente conta para colisões.
    PROPORCAO_HITBOX = (0.5, 0.7)

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 80), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))

    @property
    def hitbox(self):
        """Caixa de colisão: menor que o sprite e centralizada nele."""
        largura = int(self.rect.width * self.PROPORCAO_HITBOX[0])
        altura = int(self.rect.height * self.PROPORCAO_HITBOX[1])
        caixa = pygame.Rect(0, 0, largura, altura)
        caixa.center = self.rect.center
        return caixa


class Combatente(Entidade):
    """Entidade que tem vida, olha para o oponente e lança feitiços.

    A Maga (controlada pelo jogador) e a Feiticeira clone (controlada pela IA)
    herdam desta classe, então as duas usam exatamente os mesmos feitiços.
    """

    # Os sprites originais olham para a esquerda; viram quando a direção é "direita".
    TEMPO_INVULNERAVEL = 700  # ms depois de levar dano

    def __init__(self, x, y, vida_maxima):
        super().__init__(x, y)
        self.vida_maxima = vida_maxima
        self.vida = vida_maxima
        self.direcao = "esquerda"
        self.oponente = None
        self.imagem_original = self.image
        self.dano_maximo = None  # limite de dano por feitiço (None = sem limite)

        self.invulneravel_ate = 0
        self.pronto_em = {}  # nome do feitiço -> instante em que pode ser usado de novo

    # ---- estado --------------------------------------------------------
    @property
    def vivo(self):
        return self.vida > 0

    def invulneravel(self, agora):
        return agora < self.invulneravel_ate

    def visivel(self, agora):
        """Pisca enquanto está invulnerável depois de levar dano."""
        if not self.invulneravel(agora):
            return True

        return (agora // 90) % 2 == 0

    def receber_dano(self, dano, agora):
        """Aplica o dano. Devolve True se o golpe valeu."""
        if dano <= 0 or not self.vivo or self.invulneravel(agora):
            return False

        self.vida = max(0, self.vida - dano)
        self.invulneravel_ate = agora + self.TEMPO_INVULNERAVEL
        self.ao_receber_dano(agora)
        return True

    def ao_receber_dano(self, agora):
        """Gancho para as subclasses reagirem ao dano."""

    def curar(self, quantidade=1):
        """Recupera vida (sem passar do máximo). Devolve True se curou."""
        if not self.vivo or self.vida >= self.vida_maxima:
            return False

        self.vida = min(self.vida_maxima, self.vida + quantidade)
        return True

    # ---- imagem --------------------------------------------------------
    def imagem_visual(self, agora):
        """Imagem que aparece na tela (as subclasses podem tingir, por exemplo)."""
        return self.image

    def desenhar_efeitos(self, tela, agora):
        """Gancho para efeitos desenhados por cima do sprite (gelo, aura...)."""

    def definir_imagem(self, imagem):
        """Troca o sprite mantendo os pés no mesmo lugar e vira conforme a direção.

        O retângulo acompanha o tamanho do sprite; assim a posição, o chão e a
        hitbox sempre correspondem ao que aparece na tela.
        """
        self.imagem_original = imagem
        self.mudar_direcao()

    def mudar_direcao(self):
        if self.direcao == "direita":
            imagem = pygame.transform.flip(self.imagem_original, True, False)
        else:
            imagem = self.imagem_original

        base = self.rect.midbottom
        self.image = imagem
        self.rect = self.image.get_rect(midbottom=base)

    # ---- feitiços ------------------------------------------------------
    def recarga_restante(self, nome, agora):
        return max(0, self.pronto_em.get(nome, 0) - agora)

    def pode_conjurar(self, nome, agora):
        return self.vivo and self.recarga_restante(nome, agora) == 0

    def conjurar(self, nome, ctx, fator_recarga=1.0, erro=0):
        """Cria o feitiço e o adiciona à arena. Devolve o feitiço ou None."""
        from feiticos import criar_feitico, CATALOGO

        if nome not in CATALOGO or not self.pode_conjurar(nome, ctx.tempo):
            return None

        feitico = criar_feitico(nome, self, self.oponente, ctx.tempo, erro)
        ctx.adicionar_feitico(feitico)
        self.pronto_em[nome] = ctx.tempo + int(CATALOGO[nome].RECARGA * fator_recarga)
        return feitico

    def update(self, ctx):
        raise NotImplementedError
