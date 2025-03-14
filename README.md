# cemantix-console

My 2 cents on cemantix-console, largely based on [farfabet](https://github.com/farfabet)'s work

Play Cémantix in your shell !

Now you can choose between php-cli or python3 version
Both versions are not quite on par, python version offers basic functionnality while php-cli is a bit more advanced
Python version supports game in english language (use "en" as an argument, "fr" is used by default)

![Screenshot](doc/screenshot.png)

## Supported commands

*(use prefix "/" to indicate you want to enter a command)*

- exit / quit : Self explanatory
- help : Self explanatory
- reset / restart : Erase data file and restart the game from start. A backup is created, just in case.
- nearby : Once you found today's word, you can have a look at all the nearby words
- history : Displays a list of the latest words

## Game data

Since v1.1, game data is now stored in ~/.cemantix as CSV files (one file per game). This was previously stored in /tmp so if you have existing game data from versions prior to v1.1, you may want to move it to the new location :

```bash
mkdir ~/.cemantix
cp /tmp/cem*.csv ~/.cemantix/
```

## To-Do

- [X] History (previous words and their status "found"/"not found")
- [X] New commands (/history, /exit, /quit, /reset, /restart)
- [X] Command completion
- [X] Inline help (/help)
