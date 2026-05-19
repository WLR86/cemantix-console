#!/usr/bin/env python3
"""Cémantix CLI - Interface pour le jeu Cémantix"""

import csv
import configparser
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import requests
from termcolor import colored

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False


@dataclass
class GameResult:
    word: str
    score: float  # 0-1 (température en °C / 100)
    percentile: int  # 0-1000
    solvers: int = 0


@dataclass
class GameState:
    num: int
    cache_path: Path
    url: str = ""
    game_name: str = ""
    prefix: str = ""
    cache: list[GameResult] = field(default_factory=list)
    last_result: Optional[GameResult] = None
    last_response_time: float = 0.0


class CemantixGame:
    def __init__(self, lang: str = "fr", config_path: str = "config.ini"):
        self.session = requests.Session()
        self.state = self._load_config(lang, config_path)
        self.headers = {
            "Origin": self.state.url,
            "Referer": self.state.url,
        }

    def _load_config(self, lang: str, config_path: str) -> GameState:
        config = configparser.ConfigParser()
        config.read(config_path)

        if lang not in config:
            raise ValueError(f"Langue '{lang}' non trouvée dans {config_path}")

        settings = dict(config[lang])
        origin = date.fromisoformat(settings["origin"])
        game_num = (date.today() - origin).days + 1
        url = settings["cemantix_url"]

        cache_dir = Path.home() / ".cemantix"
        cache_dir.mkdir(mode=0o755, exist_ok=True)

        return GameState(
            num=game_num,
            cache_path=cache_dir / f"{settings['prefix']}{game_num}.csv",
            url=url,
            game_name=settings["game_name"],
            prefix=settings["prefix"],
        )

    def guess(self, word: str) -> GameResult | None:
        """Propose un mot et retourne le résultat, ou None si le mot n'existe pas"""
        response = self.session.post(
            f"{self.state.url}/score?n={self.state.num}",
            headers=self.headers,
            data={"word": word},
        )
        response.raise_for_status()
        self.state.last_response_time = response.elapsed.total_seconds()
        data = response.json()

        if "e" in data:
            error_msg = data["e"]
            raise ValueError(error_msg)

        result = GameResult(
            word=word,
            score=data.get("s", 0),
            percentile=data.get("p", 0),
            solvers=data.get("v", 0),
        )

        self._save_result(result)
        self.state.last_result = result
        return result

    def get_nearby(self, word: str) -> dict[str, tuple[int, float]]:
        """Récupère les mots proches (après avoir trouvé le mot)"""
        response = self.session.post(
            f"{self.state.url}/nearby?n={self.state.num}",
            headers=self.headers,
            data={"word": word},
        )
        response.raise_for_status()
        return response.json()  # {word: (percentile, score)}

    def get_history(self) -> list[tuple[int, int, str]]:
        """Récupère l'historique des parties"""
        response = self.session.get(
            f"{self.state.url}/history?n={self.state.num}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()  # [[num, solvers, word], ...]

    def check_game_solved(self, game_num: int, prefix: str) -> bool:
        """Vérifie si une partie a été résolue en analysant le CSV local"""
        cache_file = Path.home() / ".cemantix" / f"{prefix}{game_num}.csv"
        if not cache_file.exists():
            return False
        try:
            with open(cache_file, "r") as f:
                for row in csv.reader(f):
                    if len(row) >= 3 and row[2] == "1000":
                        return True
        except Exception:
            pass
        return False

    def _save_result(self, result: GameResult) -> None:
        """Sauvegarde le résultat dans le cache"""
        if any(r.word == result.word for r in self.state.cache):
            return

        self.state.cache.append(result)
        with open(self.state.cache_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([result.word, result.score, result.percentile])

    def load_cache(self) -> None:
        """Charge le cache depuis le fichier"""
        if not self.state.cache_path.exists():
            return

        self.state.cache = []
        with open(self.state.cache_path, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    self.state.cache.append(
                        GameResult(
                            word=row[0],
                            score=float(row[1]),
                            percentile=int(row[2]),
                        )
                    )

    def get_sorted_cache(self) -> list[GameResult]:
        """Retourne le cache trié par score décroissant"""
        return sorted(
            self.state.cache, key=lambda r: (r.score, r.percentile), reverse=True
        )


class TerminalUI:
    ICONS = {
        (999, 1001): "🥳",
        (990, 999): "🔥",
        (900, 990): "🥵",
        (1, 900): "😎",
        (-1, 0): "🥶",
        (-2, -1): "🧊",
    }

    @staticmethod
    def temp_to_degrees(score: float) -> float:
        return round(score * 100, 2)

    @staticmethod
    def get_icon(percentile: int, score: float) -> str:
        if score < 0:
            return "🧊"
        for (low, high), icon in TerminalUI.ICONS.items():
            if low < percentile <= high:
                return icon
        return "🥶"

    @staticmethod
    def get_color(percentile: int) -> str:
        if percentile > 990:
            return "red"
        elif percentile > 900:
            return "yellow"
        elif percentile > 800:
            return "green"
        return "white"

    @staticmethod
    def get_terminal_size() -> tuple[int, int]:
        try:
            size = os.get_terminal_size()
            return size.lines, size.columns
        except OSError:
            return 24, 80

    @staticmethod
    def format_row(result: GameResult, idx: int, total: int, bold: bool = False) -> str:
        temp = TerminalUI.temp_to_degrees(result.score)
        icon = TerminalUI.get_icon(result.percentile, result.score)
        color = TerminalUI.get_color(result.percentile)
        bar = "◼" * (result.percentile // 50) + " " * (20 - result.percentile // 50)

        fmt_args = {
            "idx": idx,
            "word": result.word,
            "temp": temp,
            "icon": icon,
            "percent": result.percentile,
            "bar": bar,
            "total": f"{idx}/{total}",
        }

        template = "| {idx:>4}{word:>20} {temp:>6}°C {icon:>3}{percent:>5} {bar:<20} {total:>7} |"

        text = template.format(**fmt_args, solvers=result.solvers)
        attrs: list[Any] = ["bold"] if bold else []
        return colored(text, color, attrs=attrs)  # type: ignore[arg-type]

    @staticmethod
    def format_header(result: GameResult, response_time: float) -> str:
        temp = TerminalUI.temp_to_degrees(result.score)
        icon = TerminalUI.get_icon(result.percentile, result.score)
        time_ms = f"{response_time * 1000:.1f}ms"

        text = f"| {'':<4}{result.word:>20} {temp:>6}°C {icon:>3}{result.percentile:>5} Solvers:{result.solvers:>6} {time_ms:>13} |"

        return colored(text, "white", attrs=["bold"])

        return colored(text, "white", attrs=["bold"])


class CemantixCLI:
    def __init__(self, lang: str = "fr"):
        self.game = CemantixGame(lang)
        self.ui = TerminalUI()
        self.prompt = f"{self.game.state.game_name}> "
        self._histfile: Path | None = None
        self._message: str = ""
        self._welcome_shown: bool = False
        self._init_readline()

    def _init_readline(self) -> None:
        if not READLINE_AVAILABLE:
            return
        histfile = Path.home() / ".cemantix_history"
        try:
            import readline
            from functools import partial

            readline.read_history_file(histfile)

            def completer(text, state):
                commands = [
                    "help",
                    "nearby",
                    "history",
                    "printCache",
                    "cls",
                    "quit",
                    "exit",
                ]
                text = text.lstrip("/")
                matches = [c for c in commands if c.startswith(text)]
                if state < len(matches):
                    return matches[state]
                return None

            readline.set_completer(completer)
            readline.parse_and_bind("tab: complete")
        except Exception:
            pass
        self._histfile = histfile

    def _save_history(self) -> None:
        if not READLINE_AVAILABLE or self._histfile is None:
            return
        try:
            import readline

            readline.write_history_file(self._histfile)
        except Exception:
            pass

    def run(self) -> None:
        self.game.load_cache()

        while True:
            try:
                self._display_cache()
                cmd = input(self.prompt).strip()

                if not cmd:
                    continue
                elif cmd.startswith("/"):
                    self._handle_command(cmd[1:])
                else:
                    self._handle_guess(cmd)

                self._save_history()

            except KeyboardInterrupt:
                print("\nAu revoir!")
                self._save_history()
                break
            except EOFError:
                self._save_history()
                break

    def _display_cache(self) -> None:
        import sys

        os.system("cls" if os.name == "nt" else "clear")
        sys.stderr.flush()
        sys.stdout.flush()

        if not self._welcome_shown:
            print(
                f"Welcome to {self.game.state.game_name} (Game #{self.game.state.num})\n"
            )
            self._welcome_shown = True

        rows, _ = self.ui.get_terminal_size()
        max_lines = rows - 3

        if self.game.state.last_result:
            print(
                self.ui.format_header(
                    self.game.state.last_result, self.game.state.last_response_time
                )
            )

        sorted_cache = self.game.get_sorted_cache()
        last_word = (
            self.game.state.last_result.word if self.game.state.last_result else ""
        )

        for i, result in enumerate(sorted_cache, 1):
            if i > max_lines:
                break
            bold = result.word == last_word
            print(self.ui.format_row(result, i, len(sorted_cache), bold=bold))

        if self._message:
            print(f"\n  >> {self._message} <<")
            self._message = ""

    def _handle_command(self, cmd: str) -> None:
        parts = cmd.split()
        command = parts[0]
        args = parts[1:]

        match command:
            case "help":
                print("""Commandes disponibles:
  /help       - Afficher cette aide
  /nearby     - Voir les mots proches (après avoir gagné)
  /history    - Voir l'historique des parties
  /printCache - Afficher les mots essayés
  /cls        - Effacer l'écran
  /quit       - Quitter""")

            case "printCache":
                pass

            case "nearby":
                if not self.game.state.cache:
                    self._message = "Aucun mot trouvé"
                    return
                top = max(self.game.state.cache, key=lambda r: r.percentile)
                if top.percentile < 1000:
                    self._message = "Il faut d'abord trouver le mot !"
                    return

                nearby = self.game.get_nearby(top.word)
                self._message = f"Mots proches de '{top.word}':"
                self._display_cache()
                for word, (p, s) in sorted(
                    nearby.items(), key=lambda x: x[1][0], reverse=True
                ):
                    result = GameResult(word=word, score=s, percentile=p)
                    print(self.ui.format_row(result, 0, 0))
                self._display_cache()

            case "history":
                history = self.game.get_history()
                prefix = self.game.state.prefix
                print("")
                for entry in history[:20]:
                    num, solvers, word = entry
                    # Use local CSV to check if WE solved it
                    solved = self.game.check_game_solved(num, prefix)
                    status = "✅" if solved else "❌"
                    color = "green" if solved else "red"
                    display_word = word if word else "(non trouvé)"
                    print(
                        colored(
                            f"| {num:>4} {status} {solvers:>6} {display_word:<20}",
                            color,
                        )
                    )
                input("Appuyez sur Entrée pour continuer...")

            case "cls":
                pass  # _display_cache will be called next loop

            case "quit" | "exit":
                raise EOFError

            case _:
                self._message = f"Commande inconnue: /{command}"

    def _handle_guess(self, word: str) -> None:
        try:
            result = self.game.guess(word)
            if result and result.percentile == 1000:
                self._message = f"🎉 Gagné! Mot trouvé: {word}"
        except ValueError as e:
            self._message = f"Erreur: {e}"
        except requests.RequestException as e:
            self._message = f"Erreur: {e}"


if __name__ == "__main__":
    import os
    import sys

    lang = sys.argv[1] if len(sys.argv) > 1 else "fr"
    CemantixCLI(lang).run()
