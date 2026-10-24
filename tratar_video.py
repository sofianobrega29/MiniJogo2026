"""Gera imagens/Video/vitoria_hd.mp4 a partir de vitoria.mp4, com mais qualidade.

O vídeo original é pequeno (848x478) e cheio de "blocos" de compressão. O jogo esticava
esse quadro para 1300x900 sem suavização, o que deixava tudo serrilhado. Aqui fazemos o
tratamento uma vez, antes de jogar:

  1. deblock  - suaviza os blocos de compressão
  2. hqdn3d   - tira o ruído (usando também os quadros vizinhos)
  3. scale    - amplia para a largura da tela com o filtro Lanczos (o melhor para ampliar)
  4. cas      - realça a nitidez sem criar halos

Isto melhora bastante o aspecto, mas não inventa detalhes que o vídeo original não tem.
Precisa do `ffmpeg` instalado. Uso:  python tratar_video.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

from constantes import LARGURA

PASTA = Path(__file__).resolve().parent / "imagens" / "Video"
ORIGEM = PASTA / "vitoria.mp4"
DESTINO = PASTA / "vitoria_hd.mp4"


def tratar(origem=ORIGEM, destino=DESTINO, largura=LARGURA):
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg não encontrado. Instale-o (https://ffmpeg.org) e rode de novo.")

    filtros = ",".join([
        "deblock=filter=weak:block=8",
        "hqdn3d=1.6:1.3:5:4",
        f"scale={largura}:-2:flags=lanczos+accurate_rnd+full_chroma_int",
        "cas=0.55",
        "format=yuv420p",
    ])

    comando = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(origem),
        "-vf", filtros,
        "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-profile:v", "high",
        "-c:a", "copy", "-movflags", "+faststart",
        str(destino),
    ]
    print("Tratando o vídeo (pode levar alguns segundos)...")
    subprocess.run(comando, check=True)
    print(f"Pronto: {destino}")


if __name__ == "__main__":
    tratar()
