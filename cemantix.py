#!/usr/bin/env python

import os
import sys
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
    prompt  = "Cémantix > "
    intro   = "Welcome to Cémantix"
    limit   = 20
    lastRow = {}

    def preloop(self):
        self.cls()
        self.init()

    def do_test(self, line):
        self.postWord("score", line)

    def do_print(self, line):
        row = self.lastRow
        row['word'] = line
        self.print_row(self, row, bold=True)

    def do_printScrenSize(self, line):
        """ Print the screen size """
        print(self.getScreenSize()[0])

    # define a function that prints N lines of the cache depending on the number of lines the display permits
    def do_printCache(self, line):
        """ Print the cache """
        self.cls()
        print("Cache:")
        # for each row in the cache, print the row items
        i = 1
        for row in self.cache:
            if i < self.limit:
                i += 1
                self.print(row)

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
        row = self.lastRow
        style = ''
        color = 'white'
        try:
            temperature = round(row['score'] * 1E2, 3)
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
        if row['percentile'] > 990:   color = 'red'
        elif row['percentile'] > 900: color = 'yellow'
        elif row['percentile'] > 800: color = 'green'
        elif str(row['percentile']) == "": color = 'white'

        # round the score to 2 decimal after the decimal point
        row['score'] = round(row['score']*1E2, 2)
        #  row['score'] = round(row['score'] * 1E2, 2)
        # *    9           théorique : 100.00°C 🥳 1000 ◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼◼   1/9
        # use color to represent the temperature
        bargraph = "◼" * int(row['percentile'] / 50) + "◻" * (20 - int(row['percentile'] / 50))
        cnt = f"1/{len(self.cache)}"
        print(colored("* {:>20} : {:>8}°C {:>3} {:>3} {:<20} {:>6}".format(row['word'], temperature, icon, row['percentile'],bargraph,cnt), color, attrs=style))


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
                            'idx': idx + 1
                            }
                # How sort entries by percentile and score
            self.s_cache = sorted(self.cache.values(), key=lambda x: (x['percentile'], x['score']), reverse=True)
            print(self.s_cache)

        except FileNotFoundError:
            print(f"File {self.filename} not found", file=sys.stderr)

    def sorter(self, a, b):
        """ Sort the cache by value """
        if a['percentile'] != b['percentile']:
            return b['percentile'] > a['percentile']
        return b['score'] > a['score']

    def writeCacheLine(self, row):
        """ Write a line to the cache file """
        with open(self.filename, 'a', newline='') as f:
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
        self.limit = self.getScreenSize()[0] - 2
        self.cls()
        self.num = self.get('stats')['num']
        self.loadCache()
        response = self.postWord("score", word)
        #  print(response)

        # test if response contains score and percentile it's ok else it's an error
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

        try:
            # round the score to 2 decimal places
            response['score'] = round(response['score'], 2)
        except KeyError:
            response['score'] = 0

        self.lastRow = response
        self.lastRow['word'] = word
        if rcode == "Ok":
            if word not in self.cache:
                self.cache[word] = self.lastRow
                self.cache[word]['idx'] = len(self.cache)
                self.writeCacheLine([word, response['score'], response['percentile']])
        s_idx = 1
        self.print_row(self, self.lastRow, s_idx)

        if result == "Error":
            print(response['error'].replace('<i>', '').replace('</i>', ''))


if __name__ == '__main__':
    Cemantix().cmdloop()
