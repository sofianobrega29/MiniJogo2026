# Tela
LARGURA = 1300
ALTURA = 900
FPS = 60

# Chão
# Y_PES_CHAO é onde ficam os pés dos personagens; Y_EXPLOSAO_CHAO é onde os
# feitiços "tocam o chão" e explodem.
ALTURA_CHAO = 120
Y_PES_CHAO = ALTURA - 20
Y_EXPLOSAO_CHAO = ALTURA - 60

# Cores
BRANCO = (255, 255, 255)
AZUL_MAGICO = (100, 220, 255)
AZUL_CLARO = (220, 250, 255)
ROXO_RAIO = (150, 70, 255)
ROXO_CLARO_RAIO = (215, 175, 255)

# Mostra as caixas de colisão (útil para ajustar o jogo)
DEBUG_HITBOX = False

# Buraco negro e gelo
VIDA_BURACO_NEGRO = 3   # a clone abre o buraco negro quando chega a esta vida
DURACAO_GELO = 6000     # ms que a clone fica congelada
FATOR_GELO = 1.6        # congelada: movimento, ataques, recargas e regeneração ficam 60% mais lentos

# Ataques da Maga
TEMPO_ENTRE_ATAQUES = 1500   # ms de espera depois de lançar um ataque, antes de poder lançar outro
FEITICOS_DE_ATAQUE = ("orbe", "zoltraak", "raio", "gelo")   # parede (defesa) e cura não entram na espera
