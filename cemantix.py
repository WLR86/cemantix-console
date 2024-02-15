#!/usr/bin/env python

import os
from pathlib import Path
import datetime
import cmd
import csv
import requests

cemantix_URL = "https://cemantix.certitudes.org"
headers = {'Origin': cemantix_URL, 'Referer': cemantix_URL}
cachePath = os.path.expanduser('~/.cemantix/')


class Cemantix(cmd.Cmd):
    prompt = "Cémantix > "
    intro = "Welcome to Cémantix"
    limit = 20
    lastRow = {}

    def preloop(self):
        self.cls()
        self.init()

    def do_test(self, line):
        self.postWord("score", line)

    def do_print(self, line):
        self.print_row(self, self.lastRow, bold=True)

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
        print()
        style = 0
        color = 0
        try:
            temperature = row['percentile']
        except KeyError:
            temperature = 0
        if temperature == 1000 : icon = "🥳"
        if temperature < 1000:   icon = "😱"
        if temperature < 999:    icon = "🔥"
        if temperature < 990:    icon = "🥵"
        if temperature < 900:    icon = "😎"
        if temperature < 1:      icon = "🥶"
        if temperature < -100:   icon = "🧊"
        if bold: style='1'
        if row['percentile'] > 990: color='31'
        elif row['percentile'] > 900: color='33'
        elif row['percentile']=="": color='93'
        print("\033[{};{}m{} {}\033[0m".format(style, color, icon, row['word']))

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
        action = "score"
        # POST line as word variable via POST to cemantix_URL
        data = {"word": word}
        r = requests.Session()
        out = r.post(cemantix_URL + "/" + action, headers=headers, data=data)
        if out.status_code == 200:
            return out.json()
        else:
            return out.status_code

    def xloadCache(self):
        """ Load the cache file into a dictionary """
        self.filename = "cem" + str(self.num) + ".csv"
        self.cache = {}
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

    def loadCache(self):
        num = self.num
        if not Path(cachePath).is_dir():
            os.makedirs(cachePath, mode=0o755, exist_ok=True)
        self.filename = f"{cachePath}cem{num}.csv"
        try:
            with open(self.filename, "r") as handle:
                self.cache = {}
                for idx, data in enumerate(csv.reader(handle)):
                    word = data[0]
                    self.cache[word] = {
                            'word': word,
                            'score': float(data[1]),
                            'percentile': int(data[2]) if len(data) > 2 else None,
                            'idx': idx
                            }
                # How sort entries by percentile and score
            self.s_cache = sorted(self.cache.values(), key=lambda x: (x['percentile'], x['score']), reverse=True)
            #  print(self.s_cache)

        except FileNotFoundError:
            print(f"File {self.filename} not found", file=sys.stderr)

    def sorter(self, a, b):
        """ Sort the cache by value """
        if a['percentile'] != b['percentile']:
            return b['percentile'] > a['percentile']
        return b['score'] > a['score']

    def writeCacheLine(self, row):
        """ Write a line to the cache file """
        with open(self.filename, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def do_loadFile(self, num):
        """ Load the file into a dictionary """
        self.filename = "cem" + str(num) + ".csv"
        self.cache = {}
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

    def default(self, word):
        """ Send word via POST request to cemantix_URL and return its score """
        self.cls()
        self.num = self.get('stats')['num']
        self.loadCache()
        response = self.postWord("score", word)

        try:
            if int(response['percentile']) == 1000:
                print("Gagné !")
        except KeyError:
            response['percentile'] = 0

        try:
            # round the score to 2 decimal places
            response['score'] = round(response['score'], 2)
        except KeyError:
            response['score'] = 0

        try:
            # strip tags from the error message
            response['error'] = response['error'].replace('<i>', '').replace('</i>', '')
            print(response['error'])
        except KeyError:
            self.lastRow = response
            print(self.writeCacheLine([word, response['score'], response['percentile']]))
            print(str(response['score'] * 100) + " " + word.rjust(30) + " : " + str(response['percentile']))


if __name__ == '__main__':
    Cemantix().cmdloop()
