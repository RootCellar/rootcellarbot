# rootcellarbot

A Discord Bot that is meant to bring some extra fun into the chat.

As of right now, this bot is being developed just for fun, and so that I (RootCellar!)
can brush off my Python skills and discover what's possible with
the `discord.py` library and Discord's API.
This bot is intended to be somewhat well-made and very configurable,
and possibly even used as a starting point to develop other bots.

The bot has a variety of commands, including a couple of games.
The commands can be used from regular chat messages that look like so:

`cmd!help`

Where `cmd!` is replaced with the command prefix that the bot is configured with,
and `help` can be replaced with other commands.

The following commands are available:
```
choose_random   Choose a random item out of the given items
debug           (Admin-only) Enable/Disable specific debug channels
debugged        (Admin-only) Show debug channel values
doggo           Drop a cute dog photo into the chat
error           Send a random error message
fortune         Ask a question and learn your fortune
game            EXPERIMENT!! DOES NOT DO ANYTHING OF VALUE
guess_word      Guess the word for Wordle
hangman_channel Start a game of hangman in another channel
hello           Says hello
help            Shows this message
info            Send bot info
joke            Drop a joke into the chat
kitty           Drop a cute kitty photo into the chat
letter          Guess a letter for hangman
mock            Generate and send a string mocking the given string
no              Send a creative way of just saying `no`
penguin         Drop a penguin photo into the chat
quote           Drop a wise quote into the chat
random_hangman  Start a game of Hangman with a randomly chosen word
random_wordle   Start a game of Wordle with a randomly chosen word
roll_dice       Rolls dice and sends the total
say             (Admin-only) Forces the bot to send the given message
say_to          (Admin-only) Forces the bot to send the given message to th...
status          (Admin-only) Changes the bot's status
wordle_channel  Start a game of Wordle in another channel
```

## Setting up

The bot is configured using variables in the file `.env`, which should be
located in the directory where the program is executed from.

A `.env` configuration may look like this:
```dotenv
# An example `.env` configuration.
# The bot has defaults for many of these values,
# but you should set most of them.

# Name of your Bot
BOT_NAME="My RootCellarBot"

# URL to an icon for your bot
#BOT_ICON_URL="your_url"

# Your bot's color (hexadecimal)
BOT_COLOR=0x00ff00

# Uncomment and set if you have a file
#WORDLE_WORDS_FILE="five-letter-words.txt"

# The prefix that users must use in order to execute commands.
# For example, if your prefix is 'cmd!', then commands will look
# like this: 'cmd!help'
COMMAND_PREFIX="cmd!"

# Discord status to set after the bot is logged in
# Accepts "online", "idle", "dnd", and "invisible"
DEFAULT_STATUS="online"

# Status message to set after the bot is logged in
DEFAULT_STATUS_MESSAGE="Running :D"

# Your Discord Token (keep this secret!)
DISCORD_TOKEN=your-discord-token

# Account usernames of users that may run administrator commands
# that other users are not allowed to access
#ADMIN_USERNAMES=your_username

# Only use if you know what you are doing!
#ALWAYS_DEBUG=False
#DEFAULT_DEBUG_CHANNEL_STATUS=True
```