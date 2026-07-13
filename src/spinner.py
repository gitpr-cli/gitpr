"""
Animated spinner with braille characters and thinking words.
Visual effect: rotating braille character (magenta) + word being "discovered"
letter by letter with random colors.
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
from src.i18n import __, CURRENT_LANG

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

# URL do template remoto com a lista de palavras (language-aware).
# English (en) = original file without suffix; other languages get a suffix
# (e.g.: gitpr.thinking-words.pt_br.md), mirroring generate_skill_template().
_LANG_SUFFIX = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
THINKING_WORDS_URL = (
    "https://raw.githubusercontent.com/natanfiuza/gitpr/"
    f"refs/heads/main/templates/gitpr.thinking-words{_LANG_SUFFIX}.md"
)

# Fallback interno caso o download falhe
_FALLBACK_WORDS = [
    __("Fabulous"), __("Thinking"), __("Analyzing"), __("Reasoning"),
    __("Elaborating"), __("Processing"), __("Deciphering"), 
    __("Calculating"),__("Reflecting"), __("Computing"),    
]

def _load_thinking_words():
    """Loads the word list from .env or downloads from the remote template."""
    env_file = str(Path.home() / ".gitpr" / ".env")

    # Ensure .env has been loaded
    load_dotenv(env_file)

    raw = os.getenv("SPINNER_THINKING_WORDS", "").strip()

    if raw:
        # .env already has words: supports | or , separator
        sep = "|" if "|" in raw else ","
        return [w.strip() for w in raw.split(sep) if w.strip()]

    # .env has no words: download from GitHub
    try:
        with urllib.request.urlopen(THINKING_WORDS_URL, timeout=10) as resp:
            content = resp.read().decode("utf-8")

        # Parse: supports comma-separated OR one-per-line words
        words = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Each line can have multiple words separated by commas
            for word in line.split(","):
                word = word.strip()
                if word:
                    words.append(word)

        if words:
            # Save to .env as pipe-separated
            set_key(env_file, "SPINNER_THINKING_WORDS", "|".join(words))
            return words
    except Exception:
        pass

    # Fallback: use internal list
    return list(_FALLBACK_WORDS)


# Words representing AI "thinking" (loaded from .env or remote template)
THINKING_WORDS = _load_thinking_words()

class Spinner:
    """Animated spinner that runs in the background while the AI processes."""

    def __init__(self, quiet=False):
        self._thread = None
        self._running = False
        self._quiet = quiet

    def _spin(self):
        """Main animation loop, runs in a separate thread."""
        braille_idx = 0
        word_idx = random.randrange(len(THINKING_WORDS))
        word = THINKING_WORDS[word_idx]
        word_color = random.choice(WORD_COLORS)
        discovered = ""          # Letters already "discovered" of the word
        dots_cycle = 0           # 0 = ".", 1 = "..", 2 = "..."
        char_step = 0            # Frame counter for revealing letters
        chars_per_letter = 4     # Frames with random chars before revealing a letter

        while self._running:
            braille_char = BRAILLE_FRAMES[braille_idx]
            braille_idx = (braille_idx + 1) % len(BRAILLE_FRAMES)

            # Word "discovery" animation
            if len(discovered) < len(word):
                char_step += 1
                if char_step >= chars_per_letter:
                    # Reveal one more letter of the word
                    discovered = word[:len(discovered) + 1]
                    char_step = 0
                else:
                    # Show a random character in place of the next letter
                    fake_char = random.choice(string.ascii_uppercase + "0123456789!@#$")
                    discovered = word[:len(discovered)] + fake_char

                display_word = discovered
            else:
                # Complete word: dot cycle
                dots_cycle = (dots_cycle + 1) % 12
                if dots_cycle < 4:
                    dots = "."
                elif dots_cycle < 8:
                    dots = ".."
                else:
                    dots = "..."

                display_word = word + dots

                # Change word and color after a few dot cycles
                if dots_cycle == 0 and braille_idx == 0:
                    word_idx = (word_idx + 1) % len(THINKING_WORDS)
                    word = THINKING_WORDS[word_idx]
                    word_color = random.choice(WORD_COLORS)
                    discovered = ""
                    char_step = 0

            # Build and display the line: magenta braille + colored word
            line = f"\r  {MAGENTA}{braille_char}{RESET} {word_color}{display_word}{RESET}"
            # Pad the rest of the line with spaces
            line = line.ljust(70 + len(MAGENTA) + len(RESET) * 2 + len(word_color))

            if not self._quiet:
                sys.stdout.write(line)
                sys.stdout.flush()

            time.sleep(0.08)  # ~12 fps, suave

    def start(self):
        """Starts the animation in the background."""
        if self._quiet:
            return
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the animation and clears the line."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        if not self._quiet:
            sys.stdout.write("\r" + " " * 70 + "\r")
            sys.stdout.flush()
