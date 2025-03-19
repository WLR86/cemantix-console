#!/usr/bin/env python

import cmd
import csv
from datetime import datetime, date
import os
import re
import signal
import sys
import configparser
import shutil
from pathlib import Path

import requests
from termcolor import colored

# Set language from command line argument
try:
    lang = sys.argv[1]

except IndexError:
    lang = "fr"
#
# Load settings from ini file config.ini where sections are selected by var lang :
config = configparser.ConfigParser()
config.read("config.ini")
if lang in config:
    settings = {key: value for key, value in config[lang].items()}
    # globals().update(settings)
    game_name = settings["game_name"]
    cemantix_url = settings["cemantix_url"]
    prefix = settings["prefix"]
    # convert string to actual date object
    origin = date.fromisoformat(settings["origin"])
else:
    raise ValueError(f"La langue {lang} n'a pas été trouvée dans le fichier config.ini")

headers = {"Origin": cemantix_url, "Referer": cemantix_url}
cachePath = os.path.expanduser("~/.cemantix/")


def handle_sigchld(signum, frame):
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break


signal.signal(signal.SIGCHLD, handle_sigchld)


class Cemantix(cmd.Cmd):
    prompt = f"{game_name}> "
    intro = f"Welcome to {game_name}"
    limit = 20
    lastRow = {}
    cache = {}
    cache_idx = []
    s_cache = []
    elapsedTime = 0

    def preloop(self):
        self.cls()
        self.init()

    def precmd(self, line):
        try:
            if line[0] == "/":
                line = line[1:]
            else:
                line = "try " + line
        except IndexError:
            line = "help"
        return line

    def cls(self):
        out = os.system("cls" if os.name == "nt" else "clear")
        return out

    def init(self):
        # get today's date in Ymd format
        self.startDate = date.today()
        # no longer served
        # self.num = self.get('stats')['n']
        self.num = (self.startDate - origin).days + 1

        #  self.loadCache(self)
        self.loadCache()
        try:
            self.limit = self.getScreenSize()[0] - 3
        except ValueError:
            self.limit = 10
        self.do_printCache("")
        #  self.print()

    def print(self, word):
        """Print the word and its score"""
        self.limit = self.getScreenSize()[0] - 3
        self.cls()
        print(word)
        if word != "":
            if word in self.cache:
                self.print_row(self, self.cache[word])

        self.print_row(self, self.postWord("score", word), bold=True)

    def print_row(self, row, s_idx=0, bold=False, solvers=False):
        """Print a row of the cache"""
        # test if row is a valid dictionary
        if not isinstance(row, dict):
            row = self.lastRow

        style = ""
        color = "white"
        icon = "?"
        try:
            temperature = round(row["score"] * 1e2, 3)
        except KeyError:
            temperature = 0
        try:
            percent = row["percentile"]
        except KeyError:
            percent = 0

        icon = self.icon(percent, temperature)

        if bold:
            style = ["bold"]
        else:
            style = []
        try:
            row["percentile"] = row["percentile"] if "percentile" in row else 0
        except KeyError:
            row["percentile"] = 0
        if row["percentile"] > 990:
            color = "red"
        elif row["percentile"] > 900:
            color = "yellow"
        elif row["percentile"] > 800:
            color = "green"
        elif str(row["percentile"]) == "":
            color = "white"

        # round the score to 2 decimal after the decimal point
        try:
            row["score"] = round(row["score"] * 1e2, 4)
        except KeyError:
            row["score"] = 0

        try:
            row["word"] = row["word"]
        except KeyError:
            print(row)
            row["word"] = "Error"

        #  bargraph = "◼" * int(row['percentile'] / 50) + "◻" * (20 - int(row['percentile'] / 50))
        bargraph = "◼" * int(row["percentile"] / 50) + " " * (
            20 - int(row["percentile"] / 50)
        )
        try:
            cnt = f"{row['idx']}/{len(self.cache_idx)}"
        except KeyError:
            cnt = "0/0"
        # if solvers exists this is the current word
        if solvers:
            print(
                colored(
                    "* {:>4}{:>20} {:>6}°C{:>3}{:>5}  {:<20} {:>7} {:5.1f}ms".format(
                        " ",
                        row["word"],
                        temperature,
                        icon,
                        row["percentile"],
                        "Solvers:",
                        row["v"],
                        self.elapsedTime * 1000,
                    ),
                    color,
                    attrs=style,
                )
            )
            print("")
        else:
            try:
                idx = self.cache_idx.index(row["word"])
                thisline = "* {:>4}{:>20} {:>6}°C{:>3}{:>5} {:<20} {:>7}".format(
                    idx + 1,
                    row["word"],
                    temperature,
                    icon,
                    row["percentile"],
                    bargraph,
                    cnt,
                )
                print(colored(thisline, color, attrs=style))
            except ValueError:
                pass

    def get(self, verb):
        """Send a GET request to cemantix_url and return the response"""
        r = requests.Session()
        response = r.get(f"{cemantix_url}/{verb}?n={self.num}", headers=headers)
        return response.json()

    def post(self, verb, data):
        """Send a POST request to cemantix_url and return the response"""
        r = requests.Session()
        response = r.post(
            f"{cemantix_url}/{verb}?n={self.num}", headers=headers, data=data
        )
        self.elapsedTime = response.elapsed.total_seconds()
        return response.json()

    def getScreenSize(self):
        """return the stty rows and columns"""
        # return the stty rows and columns
        rows, columns = os.popen("stty size", "r").read().split()
        return int(rows), int(columns)

    def postWord(self, action, word):
        """
        Returns the score of the word, or an error message
        if the word is not found, or a status_code if the request
        fails
        """
        action = "score"
        data = {"word": word}
        r = requests.Session()
        out = r.post(
            f"{cemantix_url}/{action}?n={self.num}", headers=headers, data=data
        )
        self.elapsedTime = out.elapsed.total_seconds()
        if out.status_code == 200:
            return out.json()
        else:
            return out.status_code

    def icon(self, p, t):
        """
        output icon for temperature based on a value from -100 to 100
        linearized on a scale from 0 to 1000
        t : -100 to 100
        p : percentile ranging from 0 to 1000 (0: out of the top 1000 words)
            P        S
            1000 🥳 100.00
             999 😱 63.66
             990 🔥 39.41
             900 🥵 27.71
               1 😎 17.33
               0 🥶 0.00
               0  🧊 -100.00
        S scale is changing from game to game, so we can't set reliable steps
        """
        value = p
        icon = "🥶"

        if t < 0:
            p = -1
            icon = "🧊"
        if value == 1000:
            icon = "🥳"
        elif value > 998:
            icon = "😱"
        elif value > 990:
            icon = "🔥"
        elif value > 900:
            icon = "🥵"
        elif value > 1:
            icon = "😎"
        return icon

    def loadCache(self):
        num = self.num
        if not Path(cachePath).is_dir():
            os.makedirs(cachePath, mode=0o755, exist_ok=True)
        self.filename = f"{cachePath}{prefix}{num}.csv"
        #  print(self.filename)
        try:
            dataset = list()
            self.cache_idx = list()
            with open(self.filename, "r+") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if not row:
                        continue
                    dataset.append(
                        {
                            "word": row[0],
                            "score": float(row[1]),
                            "percentile": int(row[2]),
                        }
                    )
                    self.cache_idx.append(row[0])
            self.cache = dataset
            self.s_cache = sorted(
                dataset, key=lambda x: (x["score"], x["percentile"]), reverse=True
            )

        except FileNotFoundError:
            # actually no nothing
            # print(f"File {self.filename} not found", file=sys.stderr)
            pass

    def writeCacheLine(self, row):
        """Add a line to the cache file"""
        word = row[0]
        alreadyThere = any(word in d.values() for d in self.cache)
        if not alreadyThere:
            with open(self.filename, "a+", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def completedefault(self, *args):
        """Default completion function"""
        commands = set(self.completenames(*args))
        topics = set(a[5:] for a in self.get_names() if a.startswith("help_" + args[0]))
        return list(commands | topics)

    def do_init(self, line):
        self.init()

    def do_say(self, arg):
        print("You said", '"' + arg + '"')

    def do_test(self, line):
        print(self.cache)

    def do_print(self, line):
        row = self.lastRow
        row["word"] = line
        self.print_row(self, row, bold=True)

    def do_debug(self, line):
        print(f"Game #{self.num}")
        print("This is the unsorted cache:")
        print(self.cache)
        print("This is the unsorted cache index table:")
        print(self.cache_idx)
        print("This is the sorted cache:")
        print(self.s_cache)

    def do_loadFile(self, num):
        """Load the file into a dictionary"""
        self.filename = prefix + str(num) + ".csv"
        self.num = num
        # if cachePath doesn't exist, create it
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        try:
            with open(cachePath + self.filename, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    self.cache.append(row)
        except FileNotFoundError:
            print("No cache file found")
            pass

    def do_printScreenSize(self, line):
        """Print the screen size"""
        print(self.limit)

    # define a function that prints N lines of the cache depending
    # on the number of lines the display permits
    def do_printCache(self, word):
        """Print the cache"""
        self.loadCache()
        i = 1

        for row in self.s_cache:
            try:
                row["percentile"] = row["percentile"] if "percentile" in row else 0
                row["idx"] = i
                if row["word"] == word:
                    self.print_row(row, i, solvers=False, bold=True)
                else:
                    self.print_row(row, i)
                # s_cache is the sorted cache, cache is the unsorted cache
                # so look for the current line in the unsorted cache and return
                # its index
                i += 1
            except KeyError:
                pass
            if i >= self.limit:
                break

    def do_greet(self, line):
        print("hello")

    def do_cls(self, line):
        return self.cls()

    def do_quit(self, line):
        return True

    def do_nearby(self, line):
        """
        Get nearby words
        """
        if self.s_cache[0]["percentile"] == 1000:
            word = self.s_cache[0]["word"]
            ret = self.post("nearby", {"word": word})
            sorted_data = dict(
                sorted(ret.items(), key=lambda item: item[1][0], reverse=True)
            )
            i, t = 0, {}
            self.cls()
            for key, values in sorted_data.items():
                t["idx"] = i
                t["word"] = key
                t["percentile"] = values[0]
                t["score"] = round(float(values[1]), 4)
                i += 1
                if i < (self.limit + 3):
                    # self.print_row(t, i)
                    print(
                        "* {:3} {:20} {:3} {:6.2f}°C {:4} ".format(
                            i,
                            t["word"],
                            self.icon(t["percentile"]),
                            t["score"],
                            t["percentile"],
                        )
                    )
        else:
            print("Cheater !")

    def do_reset(self, line):
        """Resets the current game"""
        # This command resets the game so the cache is flushed
        self.cache = []
        # Make a backup just in case
        shutil.move(self.filename, self.filename.replace("csv", "bak.csv"))
        self.init()

    def do_history(self, line):
        """Print the history of words and their scores"""
        self.limit = self.getScreenSize()[0] - 3
        ret = self.get("history")
        self.cls()
        print("History:")
        for i in range(0, self.limit + 2):
            Num = ret[i][0]
            Solvers = ret[i][1]
            Word = ret[i][2]
            # run grep on the cache file to get entries from 1 to 1000
            # search in given csv file for 1000
            filename = cachePath + prefix + str(Num) + ".csv"
            try:
                with open(filename, "r") as f:
                    reader = csv.reader(f)
                    foundMark = "❌"
                    idx = 0
                    NTries = ""
                    for row in reader:
                        idx = idx + 1
                        if row[0] == Word:
                            foundMark = "✅"
                            NTries = idx
                    print(
                        "* {:4} {:4} {:20} {:8} {:1}".format(
                            Num, NTries, Word, Solvers, foundMark
                        )
                    )
            except FileNotFoundError:
                pass

    def do_try(self, word):
        """
        Send word via POST request to cemantix_url and return its score
        """
        # If the date is different from the one in the cache, we have to re-initialiaze the game
        if self.startDate != date.today():
            self.init()
        self.limit = self.getScreenSize()[0] - 3
        #   self.cls()
        self.loadCache()
        response = self.postWord("score", word)

        self.cls()
        try:
            response["percentile"] = response["p"]
        except KeyError:
            response["percentile"] = 0

        try:
            response["score"] = round(response["s"], 4)
        except KeyError:
            response["score"] = 0

        rcode = "Ok"

        try:
            response["error"] = response["e"]
            rcode = "Error"
            print(re.sub("<[^<]+?>", "", response["error"]))
            print()
        except KeyError:
            pass

        self.lastRow = response
        self.lastRow["word"] = word
        if rcode == "Ok":
            try:
                if int(response["percentile"]) == 1000:
                    print("Gagné !")

                rcode = "Ok"
            except KeyError:
                response["percentile"] = 0
                rcode = "Error"
            row = [word, response["score"], response["percentile"]]
            self.writeCacheLine(row)

        #  s_idx = 1
        self.print_row(self, self.lastRow, 0, response["score"])
        self.do_printCache(word)


if __name__ == "__main__":
    Cemantix().cmdloop()
