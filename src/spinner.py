"""
Spinner animado com caracteres braille e palavras de pensamento.
Efeito visual: caracter braille girando (magenta) + palavra sendo "descoberta"
letra a letra com cores aleatorias.
"""
import os
import sys
import time
import random
import string
import threading
import urllib.request
from pathlib import Path
from dotenv import load_dotenv, set_key

# ANSI color codes
MAGENTA = '\033[35m'
RESET = '\033[0m'

# Paleta de cores para as palavras
WORD_COLORS = [
    '\033[36m',  # cyan
    '\033[33m',  # yellow
    '\033[32m',  # green
    '\033[34m',  # blue
    '\033[95m',  # bright magenta
    '\033[96m',  # bright cyan
    '\033[93m',  # bright yellow
    '\033[92m',  # bright green
    '\033[94m',  # bright blue
    '\033[91m',  # red
]

# Caracteres braille unicode que simulam um giro
BRAILLE_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# URL do template remoto com a lista de palavras
THINKING_WORDS_URL = (
    "https://raw.githubusercontent.com/natanfiuza/gitpr/"
    "refs/heads/main/templates/gitpr.thinking-words.md"
)

# Fallback interno caso o download falhe
_FALLBACK_WORDS = [
    "Fabuloso", "Pensando", "Analisando", "Raciocinando",
    "Elaborando", "Processando", "Decifrando", "Calculando",
    "Refletindo", "Maquinando",
]

def _load_thinking_words():
    """Carrega a lista de palavras do .env ou faz download do template remoto."""
    env_file = str(Path.home() / ".gitpr" / ".env")

    # Garante que o .env foi carregado
    load_dotenv(env_file)

    raw = os.getenv("SPINNER_THINKING_WORDS", "").strip()

    if raw:
        # .env ja tem palavras: suporta separador | ou ,
        sep = "|" if "|" in raw else ","
        return [w.strip() for w in raw.split(sep) if w.strip()]

    # .env nao tem palavras: baixa do GitHub
    try:
        with urllib.request.urlopen(THINKING_WORDS_URL, timeout=10) as resp:
            content = resp.read().decode("utf-8")

        # Parse: suporta palavras separadas por virgula OU uma por linha
        words = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Cada linha pode ter varias palavras separadas por virgula
            for word in line.split(","):
                word = word.strip()
                if word:
                    words.append(word)

        if words:
            # Salva no .env como pipe-separated
            set_key(env_file, "SPINNER_THINKING_WORDS", "|".join(words))
            return words
    except Exception:
        pass

    # Fallback: usa lista interna
    return list(_FALLBACK_WORDS)


# Palavras que representam "pensamento" da IA (carregadas do .env ou template remoto)
THINKING_WORDS = _load_thinking_words()

class Spinner:
    """Spinner animado que roda em background enquanto a IA processa."""

    def __init__(self, quiet=False):
        self._thread = None
        self._running = False
        self._quiet = quiet

    def _spin(self):
        """Loop principal da animacao, executado em thread separada."""
        braille_idx = 0
        word_idx = random.randrange(len(THINKING_WORDS))
        word = THINKING_WORDS[word_idx]
        word_color = random.choice(WORD_COLORS)
        discovered = ""          # Letras ja "descobertas" da palavra
        dots_cycle = 0           # 0 = ".", 1 = "..", 2 = "..."
        char_step = 0            # Contador de frames para revelar letras
        chars_per_letter = 4     # Frames com caracteres aleatorios antes de revelar uma letra

        while self._running:
            braille_char = BRAILLE_FRAMES[braille_idx]
            braille_idx = (braille_idx + 1) % len(BRAILLE_FRAMES)

            # Animacao da palavra sendo "descoberta"
            if len(discovered) < len(word):
                char_step += 1
                if char_step >= chars_per_letter:
                    # Revela mais uma letra da palavra
                    discovered = word[:len(discovered) + 1]
                    char_step = 0
                else:
                    # Mostra um caractere aleatorio no lugar da proxima letra
                    fake_char = random.choice(string.ascii_uppercase + "0123456789!@#$")
                    discovered = word[:len(discovered)] + fake_char

                display_word = discovered
            else:
                # Palavra completa: ciclo dos pontinhos
                dots_cycle = (dots_cycle + 1) % 12
                if dots_cycle < 4:
                    dots = "."
                elif dots_cycle < 8:
                    dots = ".."
                else:
                    dots = "..."

                display_word = word + dots

                # Troca de palavra e cor apos alguns ciclos de pontinhos
                if dots_cycle == 0 and braille_idx == 0:
                    word_idx = (word_idx + 1) % len(THINKING_WORDS)
                    word = THINKING_WORDS[word_idx]
                    word_color = random.choice(WORD_COLORS)
                    discovered = ""
                    char_step = 0

            # Monta e exibe a linha: braille magenta + palavra colorida
            line = f"\r  {MAGENTA}{braille_char}{RESET} {word_color}{display_word}{RESET}"
            # Limpa o resto da linha com espacos
            line = line.ljust(70 + len(MAGENTA) + len(RESET) * 2 + len(word_color))

            if not self._quiet:
                sys.stdout.write(line)
                sys.stdout.flush()

            time.sleep(0.08)  # ~12 fps, suave

    def start(self):
        """Inicia a animacao em background."""
        if self._quiet:
            return
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        """Para a animacao e limpa a linha."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        if not self._quiet:
            sys.stdout.write("\r" + " " * 70 + "\r")
            sys.stdout.flush()
