"""Sistema sonoro do jogo (música + efeitos).

Uso, de qualquer arquivo:
    from sons import SONS
    SONS.tocar_musica("batalha")
    SONS.tocar_efeito("cura")

Os arquivos ficam na pasta `musica/`. Se a placa de som não puder ser aberta ou
um arquivo estiver faltando, o jogo continua normalmente, só que sem aquele som.

COMO AJUSTAR O VOLUME
    * VOLUME_MUSICA e VOLUME_EFEITOS são os "botões mestres" (0.0 a 1.0).
    * O número ao lado de cada arquivo (em MUSICAS / EFEITOS) já está equilibrado
      para que todos soem no mesmo nível; mexa nele só para ajustar um som específico.
"""

from pathlib import Path

import pygame

PASTA_MUSICA = Path(__file__).resolve().parent / "musica"

# Botões mestres: multiplicam o volume de cada som.
VOLUME_MUSICA = 1.0
VOLUME_EFEITOS = 1.0

# nome: (arquivo, volume)
# A música da batalha toca o tempo todo, então fica baixa, por baixo dos efeitos.
MUSICAS = {
    "menu": ("tela_inicial.mp3", 0.30),
    "batalha": ("batalha_zoltraak.mp3", 0.20),
}

# Os efeitos tinham volumes bem diferentes entre si; os valores abaixo os igualam
# (os mais fortes, como as explosões, ficam bem baixos; a cura, que é suave, mais alta).
EFEITOS = {
    "cura": ("cura.mp3", 0.60),
    "gelo": ("gelo.mp3", 0.25),
    "raio": ("raio.mp3", 0.25),
    "explosao": ("explosao_orbe.mp3", 0.10),
    "estrela": ("estrela.mp3", 0.20),
}

# Evita o "metralhar" do mesmo som (ms mínimos entre duas execuções do mesmo efeito).
INTERVALO_MINIMO_EFEITO = 150


class SistemaSonoro:
    def __init__(self):
        self.efeitos = {}
        self.musica_atual = None
        self.pronto = False
        self._tentou_iniciar = False
        self._ultimo_toque = {}
        self._fade = None  # (inicio, duracao, volume_inicial, volume_final, parar_no_fim)

    # ------------------------------------------------------------------
    # Preparação
    # ------------------------------------------------------------------
    def iniciar(self):
        """Abre o mixer e carrega os efeitos. Pode ser chamado várias vezes."""
        if self._tentou_iniciar:
            return

        self._tentou_iniciar = True

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)

            pygame.mixer.set_num_channels(16)
        except pygame.error as erro:
            print(f"Som desativado (não foi possível abrir o áudio): {erro}")
            return

        for nome, (arquivo, volume) in EFEITOS.items():
            caminho = PASTA_MUSICA / arquivo

            if not caminho.exists():
                print(f"Efeito sonoro não encontrado: {caminho}")
                continue

            try:
                efeito = pygame.mixer.Sound(str(caminho))
                efeito.set_volume(min(1.0, volume * VOLUME_EFEITOS))
                self.efeitos[nome] = efeito
            except pygame.error as erro:
                print(f"Erro ao carregar o efeito {nome}: {erro}")

        self.pronto = True

    # ------------------------------------------------------------------
    # Música
    # ------------------------------------------------------------------
    def tocar_musica(self, nome, fade_in=1500):
        """Toca a música `nome` em loop. Se ela já está tocando, não faz nada."""
        self.iniciar()

        if not self.pronto or nome not in MUSICAS:
            return

        if self.musica_atual == nome and pygame.mixer.music.get_busy():
            if self._fade is not None and self._fade[3] == 0:  # estava sumindo: volta ao normal
                self._fade = None
                pygame.mixer.music.set_volume(self._volume_da_musica(nome))

            return

        arquivo, _ = MUSICAS[nome]
        caminho = PASTA_MUSICA / arquivo

        if not caminho.exists():
            print(f"Música não encontrada: {caminho}")
            return

        volume = self._volume_da_musica(nome)

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(caminho))
            pygame.mixer.music.set_volume(0.0 if fade_in > 0 else volume)
            pygame.mixer.music.play(-1)
        except pygame.error as erro:
            print(f"Erro ao tocar a música {nome}: {erro}")
            self.musica_atual = None
            return

        self.musica_atual = nome
        self._fade = None

        if fade_in > 0:
            self._iniciar_fade(0.0, volume, fade_in, parar_no_fim=False)

    def parar_musica(self, fade_out=1500):
        """Some aos poucos (sem travar o jogo) e para."""
        if not self.pronto or not pygame.mixer.music.get_busy():
            return

        if fade_out <= 0:
            pygame.mixer.music.stop()
            self.musica_atual = None
            self._fade = None
            return

        self._iniciar_fade(pygame.mixer.music.get_volume(), 0.0, fade_out, parar_no_fim=True)

    def atualizar(self):
        """Chame uma vez por quadro nos laços das telas: faz os fades andarem."""
        if self._fade is None or not self.pronto:
            return

        inicio, duracao, v_inicial, v_final, parar = self._fade
        progresso = min(1.0, (pygame.time.get_ticks() - inicio) / max(1, duracao))
        pygame.mixer.music.set_volume(v_inicial + (v_final - v_inicial) * progresso)

        if progresso >= 1.0:
            self._fade = None

            if parar:
                pygame.mixer.music.stop()
                self.musica_atual = None

    def _iniciar_fade(self, v_inicial, v_final, duracao, parar_no_fim):
        self._fade = (pygame.time.get_ticks(), duracao, v_inicial, v_final, parar_no_fim)

    @staticmethod
    def _volume_da_musica(nome):
        return min(1.0, MUSICAS[nome][1] * VOLUME_MUSICA)

    # ------------------------------------------------------------------
    # Efeitos
    # ------------------------------------------------------------------
    def tocar_efeito(self, nome):
        self.iniciar()

        efeito = self.efeitos.get(nome)

        if not self.pronto or efeito is None:
            return

        agora = pygame.time.get_ticks()

        if agora - self._ultimo_toque.get(nome, -10000) < INTERVALO_MINIMO_EFEITO:
            return

        self._ultimo_toque[nome] = agora
        efeito.play()


SONS = SistemaSonoro()
