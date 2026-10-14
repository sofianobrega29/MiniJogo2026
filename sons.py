from pathlib import Path
import pygame


class SistemaSonoro:
    def __init__(self):
        self.pasta_base = Path(__file__).resolve().parent
        self.pasta_musica = self.pasta_base / "musica"

        self.volume_telas = 0.7
        self.volume_confronto = 0.2

        self.efeitos = {}
        self.musica_carregada = False

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.carregar_musica()
        self.carregar_sons_do_jogo()

    def carregar_musica(self):
        arquivo = self.pasta_musica / "musica_fundo.mp3"

        if not arquivo.exists():
            print(f"Música não encontrada: {arquivo}")
            return

        try:
            pygame.mixer.music.load(str(arquivo))
            pygame.mixer.music.set_volume(self.volume_telas)
            self.musica_carregada = True
        except pygame.error as erro:
            print(f"Erro ao carregar a música: {erro}")

    def iniciar_musica(self):
        if self.musica_carregada:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)

    def aumentar_volume(self):
        if self.musica_carregada:
            pygame.mixer.music.set_volume(self.volume_telas)

    def diminuir_volume(self):
        if self.musica_carregada:
            pygame.mixer.music.set_volume(self.volume_confronto)

    def definir_volume(self, volume):
        volume = max(0.0, min(1.0, volume))

        if self.musica_carregada:
            pygame.mixer.music.set_volume(volume)

    def pausar_musica(self):
        pygame.mixer.music.pause()

    def continuar_musica(self):
        pygame.mixer.music.unpause()

    def parar_musica(self):
        pygame.mixer.music.stop()

    def carregar_efeito(self, nome, arquivo):
        caminho = self.pasta_musica / arquivo

        if not caminho.exists():
            print(f"Efeito sonoro não encontrado: {caminho}")
            return

        try:
            self.efeitos[nome] = pygame.mixer.Sound(str(caminho))
        except pygame.error as erro:
            print(f"Erro ao carregar o efeito {nome}: {erro}")

    def carregar_sons_do_jogo(self):
        self.carregar_efeito("zoltrak", "zoltrak.mp3")
        self.carregar_efeito("disparo_inimiga", "som_inimiga.mp3")

    def tocar_efeito(self, nome):
        efeito = self.efeitos.get(nome)

        if efeito:
            efeito.play()

    def definir_volume_efeito(self, nome, volume):
        efeito = self.efeitos.get(nome)

        if efeito:
            volume = max(0.0, min(1.0, volume))
            efeito.set_volume(volume)