from pathlib import Path
import math
import random
import pygame
from constantes import *
from frieren import Entidade
from elementos import RajadaZoltraak, ParedeMagica


class Cloneataque:
    def __init__(self, origem, alvo, velocidade=6):
        self.posicao = pygame.Vector2(origem)
        direcao = pygame.Vector2(alvo) - self.posicao
        self.direcao = direcao.normalize() if direcao.length_squared() else pygame.Vector2(1, 0)
        self.velocidade = velocidade
        self.dano = 1
        self.raio = 9
        self.rect = pygame.Rect(0, 0, self.raio*2, self.raio*2)
        self._atualizar_rect()

    def _atualizar_rect(self):
        self.rect.center = (int(self.posicao.x), int(self.posicao.y))

    def update(self):
        self.posicao += self.direcao * self.velocidade
        self._atualizar_rect()

    def desenhar(self, tela):
        pygame.draw.circle(tela, (190, 50, 255), self.rect.center, self.raio)
        pygame.draw.circle(tela, (240, 200, 255), self.rect.center, 4)

class Feiticeira(Entidade):
    def __init__(self, x, y, audio=None):
        super().__init__(x, y)
        self.audio = audio
        base_dir = Path(__file__).resolve().parent
        pasta_imagens = base_dir / "imagens" / "Personagens"
        self.vida = 11
        self.vida_maxima = 11
        self.projeteis = []
        self.rajadas = []
        self.paredes = []
        self.ultimo_zoltraak = 0
        self.ultima_defesa = 0
        self.nivel_dificuldade = 0
        self.ultimo_ataque = pygame.time.get_ticks()
        self.ultimo_esquiva = 0
        self.escudo_ate = 0
        self.spritesheet_voando = pygame.image.load(str(pasta_imagens / "CloneFly.png")).convert_alpha()
        self.frames_voando = []
        for i in range(3):
            quadro = self.spritesheet_voando.subsurface((i * 48, 0, 44, 64)).copy()
            self.frames_voando.append(pygame.transform.scale_by(quadro, 3))
        self.tempo_animacao = 0
        self.quadro_atual = 0
        self.direcao = "esquerda"
        self.velocidade = 2.5
        self.tempo_voo = 0
        self.canto_atual = 0
        self.ultimo_canto = pygame.time.get_ticks()
        self.limite_esquerdo = 80
        self.limite_direito = LARGURA - 140
        self.limite_superior = 100
        self.limite_inferior = ALTURA - 220
        self.imagem_original = self.frames_voando[0]
        self.image = self.imagem_original
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mudar_direcao()

    @property
    def vidas_perdidas(self):
        return self.vida_maxima - self.vida

    @property
    def dificuldade(self):
        # Progresso em etapas: cada vida perdida desbloqueia ou melhora habilidades.
        return self.vidas_perdidas

    def atributos_dificuldade(self):
        perdidas = self.vidas_perdidas
        return {
            "velocidade": 2.0 + min(perdidas, 10) * 0.35,
            "intervalo_ataque": max(480, 1700 - perdidas * 105),
            "velocidade_projetil": 4.0 + perdidas * 0.45,
            "chance_esquiva": min(0.08 + max(0, perdidas - 1) * 0.075, 0.72),
            "chance_defesa": min(max(0, perdidas - 2) * 0.09, 0.55),
            "chance_zoltraak": min(max(0, perdidas - 1) * 0.10, 0.65),
            "intervalo_zoltraak": max(1600, 4200 - perdidas * 220),
        }

    def mudar_direcao(self):
        self.image = pygame.transform.flip(self.imagem_original, True, False) if self.direcao == "direita" else self.imagem_original

    def defender(self, agora, maga, atributos):
        # Defesa desbloqueada depois de perder 3 vidas; chance aumenta por etapa.
        if (self.vidas_perdidas >= 3 and agora - self.ultima_defesa >= 1800
                and random.random() < atributos["chance_defesa"]):
            self.escudo_ate = agora + 900
            self.ultima_defesa = agora

    def update(self, maga, ataques_jogador=None):
        agora = pygame.time.get_ticks()
        atributos = self.atributos_dificuldade()
        dificuldade = self.vidas_perdidas
        self.tempo_voo += 0.06 + dificuldade * 0.012
        self.tempo_animacao += 1
        self.velocidade = atributos["velocidade"]
        self.cooldown_ataque = atributos["intervalo_ataque"]

        # Esquiva só começa a ser relevante após a primeira vida perdida.
        if ataques_jogador and agora - self.ultimo_esquiva > max(350, 900 - dificuldade * 45):
            for ataque in ataques_jogador:
                if not getattr(ataque, "explodindo", False) and self.rect.inflate(100, 90).colliderect(ataque.rect):
                    if random.random() < atributos["chance_esquiva"]:
                        self.rect.x += -95 if maga.rect.centerx > self.rect.centerx else 95
                        self.rect.y += random.choice((-65, 65))
                        self.rect.clamp_ip(pygame.Rect(20, 40, LARGURA-40, ALTURA-180))
                        self.ultimo_esquiva = agora
                    break

        if agora >= self.escudo_ate:
            self.defender(agora, maga, atributos)

        # Ataque básico: disponível desde o início, ficando gradualmente mais rápido.
        if agora - self.ultimo_ataque >= self.cooldown_ataque:
            self.projeteis.append(
                Cloneataque(
                    self.rect.center,
                    maga.rect.center,
                    atributos["velocidade_projetil"]
                )
            )
            if self.audio:
                self.audio.tocar_efeito("disparo_inimiga")
            self.ultimo_ataque = agora

        # Zoltraak desbloqueia após perder 2 vidas. A probabilidade é independente
        # do ataque básico: ela pode conjurar, mas não é obrigada a fazê-lo.
        if (dificuldade >= 2 and agora - self.ultimo_zoltraak >= atributos["intervalo_zoltraak"]
                and random.random() < atributos["chance_zoltraak"]):
            self.rajadas.append(RajadaZoltraak(self.rect.center, maga.rect.center,
                                               velocidade=9 + max(0, dificuldade - 2) * 0.9))
            self.ultimo_zoltraak = agora

        if self.tempo_animacao >= max(5, int(30 - dificuldade * 18)):
            self.quadro_atual = (self.quadro_atual + 1) % len(self.frames_voando)
            self.tempo_animacao = 0
        self.imagem_original = self.frames_voando[self.quadro_atual]

        if maga.voando:
            alvo_x = self.limite_esquerdo if maga.rect.centerx > LARGURA // 2 else self.limite_direito
            alvo_y = self.limite_superior if self.canto_atual == 0 else self.limite_inferior
            if agora - self.ultimo_canto >= max(500, 1500 - int(dificuldade * 700)):
                self.canto_atual = 1 - self.canto_atual
                self.ultimo_canto = agora
        else:
            alvo_x = self.limite_direito if maga.rect.centerx < LARGURA // 2 else self.limite_esquerdo
            alvo_y = int(180 + math.sin(self.tempo_voo) * 25)

        if self.rect.x < alvo_x: self.rect.x = min(alvo_x, self.rect.x + int(self.velocidade + 1))
        elif self.rect.x > alvo_x: self.rect.x = max(alvo_x, self.rect.x - int(self.velocidade + 1))
        if self.rect.y < alvo_y: self.rect.y = min(alvo_y, self.rect.y + int(self.velocidade + 1))
        elif self.rect.y > alvo_y: self.rect.y = max(alvo_y, self.rect.y - int(self.velocidade + 1))
        self.rect.clamp_ip(pygame.Rect(20, 40, LARGURA-40, ALTURA-180))
        self.mudar_direcao()

    def desenhar_escudo(self, tela):
        if pygame.time.get_ticks() < self.escudo_ate:
            pygame.draw.ellipse(tela, (190, 80, 255), self.rect.inflate(32, 30), 4)

    def atualizar_magias(self, maga):
        for rajada in self.rajadas[:]:
            rajada.update(maga)
            if not rajada.ativo:
                self.rajadas.remove(rajada)

    def desenhar_magias(self, tela):
        for rajada in self.rajadas:
            rajada.desenhar(tela)
        self.desenhar_escudo(tela)
