# cemantix-console
My 2 cents on cemantix-console, largely based on [farfabet](https://github.com/farfabet)'s work

Play Cémantix in your shell !

![Screenshot](doc/screenshot.png)

## Supported commands
*(use prefix "/" to indicate you want to enter a command)*
- exit / quit : Self explanatory
- reset / restart : Erase data file and restart the game from start
- nearby : Once you found today's word, you can have a look at all the nearby words
- history : Displays a list of the latest words

## Game data
Since v1.1, data is now stored in ~/.cemantix as CSV files (one file per game). This was previously stored in /tmp so if you have existing game data from versions prior to v1.1, you may want to copy you data to the new location :
```bash
mkdir ~/.cemantix
cp /tmp/cem*.csv ~/.cemantix/
```

## To-Do
- [X] History (previous words and their status "found"/"not found")
- [X] New commands (/history, /exit, /quit, /reset, /restart)
- [X] Command completion
- [X] Inline help (/help)

