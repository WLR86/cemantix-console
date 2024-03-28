#!/usr/bin/env python

import os
import sys
import re
from pathlib import Path
import datetime
import cmd
import csv
import requests
from termcolor import colored

cemantix_URL = "https://cemantix.certitudes.org"
headers = {'Origin': cemantix_URL, 'Referer': cemantix_URL}
cachePath = os.path.expanduser('~/.cemantix/')


class Cemantix(cmd.Cmd):
    prompt = "Cémantix > "
    intro = "Welcome to Cémantix"
    limit = 20
    lastRow = {}
    cache = {}
    cache_idx = []
    s_cache = []

    def preloop(self):
        self.cls()
        self.init()

    def precmd(self, line):
        try:
            if line[0] == '/':
                line = line[1:]
            else:
                line = "try " + line
        except IndexError:
            line = "help"
        return line

    def emptyline(self):
        line = "help cmd"
        return line

    def do_say(self, arg):
        print("You said", '"' + arg + '"')

    def do_test(self, line):
        print(self.cache)

    def do_print(self, line):
        row = self.lastRow
        row['word'] = line
        self.print_row(self, row, bold=True)

    def do_debug(self, line):
        print("This is the unsorted cache:")
        print(self.cache)
        print("This is the unsorted cache index table:")
        print(self.cache_idx)
        print("This is the sorted cache:")
        print(self.s_cache)

    def do_printScreenSize(self, line):
        """ Print the screen size """
        print(self.limit)

    # define a function that prints N lines of the cache depending
    # on the number of lines the display permits
    def do_printCache(self, line):
        """ Print the cache """
        self.loadCache()
        i = 1

        for line in self.s_cache:
            try:
                line['percentile'] = line['percentile'] if 'percentile' \
                        in line else 0
                line['idx'] = i
                self.print_row(line, i)
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

    def do_quit(self, line):
        return True

    def cls(self):
        out = os.system('cls' if os.name == 'nt' else 'clear')

    def init(self):
        # get today's date in Ymd format
        self.startDate = datetime.date.today()
        self.num = self.get('stats')['num']
        #  self.loadCache(self)
        self.loadCache()
        #  self.print()

    def print(self, word):
        """ Print the word and its score """
        self.getScreenSize()
        self.cls()
        print(word)
        if word != "":
            if word in self.cache:
                self.print_row(self, self.cache[word])

        self.print_row(self, self.postWord("score", word), bold=True)

    def print_row(self, row, s_idx=0, bold=False, solvers=False):
        """ Print a row of the cache """
        # test if row is a valid dictionary
        if not isinstance(row, dict):
            row = self.lastRow

        style = ''
        color = 'white'
        icon  = "?"
        try:
            temperature = round(row['score'] * 1E2, 3)
            score = row['score']
        except KeyError:
            temperature = 0
        if temperature == 1000:  icon = "🥳"
        if temperature < 1000:   icon = "😱"
        if temperature < 999:    icon = "🔥"
        if temperature < 990:    icon = "🥵"
        if temperature < 900:    icon = "😎"
        if temperature < 1:      icon = "🥶"
        if temperature < -100:   icon = "🧊"
        if bold:
            style = ['bold']
        else:
            style = ['bold']
        try:
            row['percentile'] = row['percentile'] if 'percentile' in row else 0
        except KeyError:
            row['percentile'] = 0
        if row['percentile'] > 990:   color = 'red'
        elif row['percentile'] > 900: color = 'yellow'
        elif row['percentile'] > 800: color = 'green'
        elif str(row['percentile']) == "": color = 'white'

        # round the score to 2 decimal after the decimal point
        try:
            row['score'] = round(row['score']*1E2, 4)
        except KeyError:
            row['score'] = 0

        try:
            row['word'] = row['word']
        except KeyError:
            print(row)
            row['word'] = "Error"

        #  row['score'] = round(row['score'] * 1E2, 2)
        # *    9           théorique : 100.00°C 🥳 1000 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼   1/9
        # use color to represent the temperature
        #  bargraph = "◼" * int(row['percentile'] / 50) + "◻" * (20 - int(row['percentile'] / 50))
        bargraph = "◼" * int(row['percentile'] / 50) + " " * (20 - int(row['percentile'] / 50))
        try:
            cnt = f"{row['idx']}/{len(self.cache_idx)}"
        except KeyError:
            cnt = "0/0"
        # if solvers exists this is the current word
        if solvers:
            print(colored(
                "* {:>20} {:>8}°C{:>3}{:>5} Solvers: {:>6}".format(row['word'],
                temperature, icon, row['percentile'], row['solvers']),
                color, attrs=style
                )
            )
            print("\n")
        else:
            idx = self.cache_idx.index(row['word'])
            print(colored(
                "* {:>4} {:>20} {:>8}°C{:>3}{:>5} {:<20} {:>6}".format(idx, row['word'],
                temperature, icon, row['percentile'], bargraph, cnt),
                color, attrs=style
                )
            )

    def do_history(self, line):
        """ Print the history of words and their scores """
        ret = self.get('history')
        self.cls()
        print("History:")
        for i in range(0, self.limit + 2):
            N = ret[i][0]
            S = ret[i][1]
            W = ret[i][2]
            # run grep on the cache file to get entries from 1 to 1000

    def get(self, verb):
        """ Send a GET request to cemantix_URL and return the response"""
        r = requests.Session()
        response = r.get(cemantix_URL + "/" + verb, headers=headers)
        return response.json()

    def getScreenSize(self):
        """ return the stty rows and columns """
        # return the stty rows and columns
        rows, columns = os.popen('stty size', 'r').read().split()
        return int(rows), int(columns)

    def postWord(self, action, word):
        """
        Returns the score of the word, or an error message
        if the word is not found, or a status_code if the request
        fails
        """
        action = "score"
        # POST line as word variable via POST to cemantix_URL
        data = {"word": word}
        r = requests.Session()
        out = r.post(cemantix_URL + "/" + action, headers=headers, data=data)
        if out.status_code == 200:
            return out.json()
        else:
            return out.status_code

    def loadCache(self):
        num = self.num
        if not Path(cachePath).is_dir():
            os.makedirs(cachePath, mode=0o755, exist_ok=True)
        self.filename = f"{cachePath}cem{num}.csv"
        #  print(self.filename)
        try:
            dataset = list()
            self.cache_idx = list()
            with open(self.filename, 'r+') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if not row:
                        continue
                    dataset.append({
                            'word': row[0],
                            'score': float(row[1]),
                            'percentile': int(row[2])
                        })
                    self.cache_idx.append(row[0])
            self.cache = dataset
            self.s_cache = sorted(
                    dataset,
                    key=lambda x: (x['score'], x['percentile']),
                    reverse=True
                    )

        except FileNotFoundError:
            print(f"File {self.filename} not found", file=sys.stderr)

    def writeCacheLine(self, row):
        """ Add a line to the cache file """
        word = row[0]
        alreadyThere = any(word in d.values() for d in self.cache)
        if not alreadyThere:
            with open(self.filename, 'a+', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def do_loadFile(self, num):
        """ Load the file into a dictionary """
        self.filename = "cem" + str(num) + ".csv"
        # self.cache = {}
        # if cachePath doesn't exist, create it
        if not os.path.exists(cachePath):
            os.makedirs(cachePath)
        try:
            with open(cachePath + self.filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.cache[row[0]] = row[1]
        except FileNotFoundError:
            print("No cache file found")
            pass

    def completedefault(self, *args):
        """ Default completion function """
        commands = set(self.completenames(*args))
        topics = set(a[5:] for a in self.get_names()
            if a.startswith('help_' + args[0]))
        return list(commands | topics)

    def do_try(self, word):
        """
        Send word via POST request to cemantix_URL and return its score
        """
        self.limit = self.getScreenSize()[0] - 3
        self.cls()
        self.num = self.get('stats')['num']
        self.loadCache()
        response = self.postWord("score", word)
        #  print(response)
        rcode = "Ok"

        try:
            error = response['error']
        except KeyError:
            error = None

        try:
            # round the score to 2 decimal places
            response['score'] = round(response['score'], 4)
        except KeyError:
            response['score'] = 0

        self.lastRow = response
        self.lastRow['word'] = word
        if rcode == "Ok":
            #  if word not in self.cache:
                #  self.cache[word] = self.lastRow
                #  self.cache[word]['idx'] = len(self.cache)
                #  row = [word, response['score'], response['percentile']]
                #  print(row)
                #  print('Writing line to cache', self.filename)
                #  self.writeCacheLine(row)
            try:
                sc = response['score']
                result = "Ok"
            except KeyError:
                result = "Error"
            try:
                if int(response['percentile']) == 1000:
                    print("Gagné !")

                rcode = "Ok"
            except KeyError:
                response['percentile'] = 0
                rcode = "Error"
            row = [word, response['score'], response['percentile']]
            #  print(row)
            #  print('Writing line to cache', self.filename)
            if error:
                print(re.sub('<[^<]+?>', '', error))
            else:
                self.writeCacheLine(row)

        #  s_idx = 1
        self.print_row(self, self.lastRow, 0, response['solvers'])
        self.do_printCache(self)

        if result == "Error":
            print(re.sub('<[^<]+?>', '', response['error']))


if __name__ == '__main__':
    Cemantix().cmdloop()
