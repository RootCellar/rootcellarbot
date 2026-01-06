# rootcellarbot

A Discord Bot that is meant to bring some extra fun into the chat.

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