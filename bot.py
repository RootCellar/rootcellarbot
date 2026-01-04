import os
import re
import json
import requests
import random
import datetime

import asyncio
from asyncio import Lock

import discord
from discord.ext import commands

from dotenv import load_dotenv
from requests import JSONDecodeError

load_dotenv()

COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', default = '!')
DEFAULT_STATUS = os.getenv('DEFAULT_STATUS', default = '')
DEFAULT_STATUS_MESSAGE = os.getenv('DEFAULT_STATUS_MESSAGE', default = '')
ADMIN_USERNAMES = os.getenv('ADMIN_USERNAMES', default = '')

DEBUG_CHANNEL_DICT_PATH = "debug.type"

FORTUNES= [
"It is certain",
"It is decidedly so",
"Without a doubt",
"Yes definitely",
"You may rely on it",
"As I see it, yes",
"Most likely",
"Outlook good",
"Yes",
"Signs points to yes",
"Reply hazy, try again",
"Ask again later",
"Better not tell you now",
"Cannot predict now",
"Concentrate and ask again",
"Don't count on it",
"My reply is no",
"My sources say no",
"Outlook not so good",
"Very doubtful"
]

ERROR_MESSAGES = [ "huh?", "what?", "*implodes*", "no u", "AAAAAAAAAAAAAA", "I need....a penguin plushie", "whar?", "~~sanity~~", "explode", "you wish", "bruh", "|| no ||",
                   "I'm gonna", "Ask ChatGPT", "imagine", "yesn't", "Segmentation fault (core dumped)" ]
NO_PERMISSION_ERROR_MESSAGE = f"Sorry, you don't have permission to do that."

#
# Emoji's
#

EMOJI_GREEN_SQUARE = '\U0001F7E9'
EMOJI_YELLOW_SQUARE = '\U0001F7E8'
EMOJI_BLACK_SQUARE = '\U00002B1B'

MAIN_DATA_FILE = "main_bot_data.json"

data_lock = Lock()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
intents.emojis = True
intents.reactions = True
intents.expressions = True
intents.typing = True

#
# DATA
#

def load_json_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    return {}

async def save_json_data(data, file_name):
    async with data_lock:
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=4)

class JsonDictionary(object):
    def __init__(self, name: str = "unnamed", dictionary = None):
        if dictionary is None:
            dictionary = dict()

        self.name = name
        self.dictionary = dictionary

    def get_string_prefix(self):
        return f"<JsonDictionary {self.name}>"

    def print_debug(self, message: str):
        debug("dictionary", f"{self.get_string_prefix()} {message}")

    def get_dictionary(self):
        return self.dictionary

    def ensure_path_exists_and_get_dictionary(self, sub_keys: list[str]):
        curr_dict = self.dictionary

        for i in range(0, len(sub_keys)):
            sub_key = sub_keys[i]
            sub_dict = curr_dict.get(sub_key)

            if sub_dict is None:
                curr_dict[sub_key] = { }
            elif isinstance(sub_dict, dict) is False:
                formatted_key = ".".join(sub_keys[:i + 1])
                raise TypeError(f"Expected a dictionary, but found a non-dictionary at {formatted_key}")

            curr_dict = curr_dict.get(sub_key)

        return curr_dict

    def get_sub_dict_and_leaf_node_key(self, key):
        split_key = key.split('.')
        dict_path = split_key[0:-1]
        leaf_key = split_key[-1]
        self.print_debug(f"dict_path: {dict_path}, leaf_key: {leaf_key}")
        sub_dict = self.ensure_path_exists_and_get_dictionary(dict_path)
        return sub_dict, leaf_key

    def dictionary_get(self, key: str):
        # Type Hint
        if isinstance(self.dictionary, dict) is False:
            raise TypeError("Expected a dictionary")

        sub_dict, leaf_key = self.get_sub_dict_and_leaf_node_key(key)
        value = sub_dict.get(leaf_key)
        self.print_debug(f"dictionary_get: '{key}': '{value}'")
        return value

    def dictionary_set(self, key: str, value):
        # Type Hint
        if isinstance(self.dictionary, dict) is False:
            raise TypeError("Expected a dictionary")

        sub_dict, leaf_key = self.get_sub_dict_and_leaf_node_key(key)
        if isinstance(sub_dict.get(leaf_key), dict) is True:
            raise TypeError(f"Expected a non-dictionary, but found a dictionary at {key}")
        else:
            sub_dict[leaf_key] = value
            self.print_debug(f"dictionary_set: '{key}' to '{value}'")

main_bot_data_json = load_json_data(MAIN_DATA_FILE)
main_bot_data = JsonDictionary(name = "main_data", dictionary = main_bot_data_json)

debug_channel_dict = {}

class CustomBot(commands.Bot):
    async def close(self):
        print("Saving data...")
        await save_json_data(main_bot_data.get_dictionary(), MAIN_DATA_FILE)

        await super().close()

bot = CustomBot(command_prefix=COMMAND_PREFIX, intents=intents)

#
# UTIL
#

def roll_dice(num_dice: int, sides: int):
    total = 0
    for x in range(1, num_dice + 1):
        total += random.choice( range(1, sides + 1) )
    return total

def random_error_message():
    return random.choice(ERROR_MESSAGES)

def mock_string(message):
    to_ret = ""
    for i in range(0, len(message)):
        rand = random.randint(0, 2)
        if rand == 0:
            to_ret += message[i].upper()
        else:
            to_ret += message[i].lower()
    return to_ret

def strip_non_ascii(text: str):
    return re.sub(r'[^\x00-\x7f]', r'?', text)

#
# Performs a GET fetch and returns the JSON response
# when the GET was successful. Otherwise, returns `None`
#
def http_get_json_generic(url):
    debug("http", f"JSON GET {url}")
    request = requests.get(url)

    if request.status_code != 200 and request.status_code != 201:
        log(f"Request to '{url}' returned status code {request.status_code}")
        return None

    try:
        response_json = request.json()
    except JSONDecodeError:
        log(f"Request to '{url}' returned bad JSON")
        return None

    return response_json

async def get_random_no():
    response_json = http_get_json_generic("https://naas.isalman.dev/no")
    if response_json is None:
        return None

    reason = response_json["reason"]
    if reason is None:
        raise ValueError("'reason' is not set")

    return reason

def status_str_to_discord_status(status):
    if status == "online":
        discord_status = discord.Status.online
    elif status == "idle":
        discord_status = discord.Status.idle
    elif status == "dnd":
        discord_status = discord.Status.do_not_disturb
    elif status == "invisible":
        discord_status = discord.Status.invisible
    else:
        discord_status = None
    return discord_status

async def update_presence(status: discord.Status | None, message: str | None):
    if status is None:
        status = discord.Status.online

    if message is None:
        await bot.change_presence(status=status)
    else:
        game = discord.Game(message)
        await bot.change_presence(status=status, activity=game)

def is_admin_user(user):
    users = ADMIN_USERNAMES.split(",")
    for name in users:
        if user.name == name:
            return True
    return False


def get_debug_channel_value_path(name: str):
    return f"{DEBUG_CHANNEL_DICT_PATH}.{name}"

def get_debug_channel_value(channel: str):
    value = debug_channel_dict.get(channel)
    return value

def set_debug_channel_value(channel: str, value: bool):
    debug_channel_dict[channel] = value
    key = get_debug_channel_value_path(channel)
    main_bot_data.dictionary_set(key, value)

def should_log_debug_channel(channel: str):
    value = get_debug_channel_value(channel)

    if value is True:
        return True
    if value is None:
        # This serves as an "automatic registration", so that
        # commands such as "prefix!debugged" will show all channels
        # that the program has attempted to use
        set_debug_channel_value(channel, False)

    return False

def debug(channel: str, message: str):
    if should_log_debug_channel(channel) is True:
        log(f"[DEBUG] {channel}: {message}")

def log(message):
    message_to_write = generate_log_message(message)
    print(message_to_write)
    with open('info.log', 'a') as file:
        file.write(f"{message_to_write} \n")

def generate_log_message(message):
    now = datetime.datetime.now()
    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = strip_non_ascii(message)
    message_to_write = f"{formatted_datetime} - {formatted_message}"
    return message_to_write

#
# On Connect
#

@bot.event
async def on_ready():
    log("Populating data...")

    debug_dict = main_bot_data.dictionary_get(DEBUG_CHANNEL_DICT_PATH)
    for key in debug_dict.keys():
        value = debug_dict[key]
        debug_channel_dict[key] = value

    log(f"Logged in as {bot.user}!")
    debug("startup", f"Logged in as {bot.user}")

    status = status_str_to_discord_status(DEFAULT_STATUS)
    await update_presence(status, DEFAULT_STATUS_MESSAGE)

@bot.event
async def on_disconnect():
    pass

#
# Commands
#

@bot.event
async def on_command_error(ctx, error):
    log(f"Command invocation threw an error: {error}")

    if not isinstance(ctx, commands.Context):
        raise ValueError("ctx is not a Context")
    if not isinstance(error, commands.CommandError):
        raise ValueError("error is not a CommandError")

    await ctx.reply(f"Command Invocation Failed: {error}")

    # await ctx.send("well that threw an error")
    # await ctx.send(random_error_message())

@bot.command(name="hello", help="Says hello")
async def hello_command(ctx):
    await ctx.send("Hello! I'm a bot.")

@bot.command(name="debug", help="(Admin-only) Enable/Disable specific debug channels)")
async def debug_command(ctx, name: str, value: bool):
    if is_admin_user(ctx.author) is False:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)
        return

    # Type hint
    assert isinstance(ctx, commands.Context)

    if '.' in name:
        await ctx.reply("Channel name cannot contain dots")
        return

    set_debug_channel_value(name, value)

    key = get_debug_channel_value_path(name)
    await ctx.reply(f"Set `{key}` to `{value}`")

@bot.command(name="debugged", help="(Admin-only) Show debug channel values)")
async def debugged_command(ctx):
    if is_admin_user(ctx.author) is False:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)
        return

    # Type hint
    assert isinstance(ctx, commands.Context)

    if isinstance(debug_channel_dict, dict) is False:
        await ctx.reply("Debug dictionary is not a dictionary!")
        raise TypeError("Debug dictionary is not a dictionary!")

    keys = debug_channel_dict.keys()
    lines = []

    for key in keys:
        lines.append(f"{key} = {debug_channel_dict[key]}")

    string_to_send = ", ".join(lines)

    await ctx.reply(f"```{string_to_send}```")

@bot.command(name="say", help="(Admin-only) Forces the bot to send the given message")
async def say_command(ctx, message: str):
    if is_admin_user(ctx.author):
        await ctx.send(message)
    else:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)

@bot.command(name="say_to", help="(Admin-only) Forces the bot to send the given message to the given channel")
async def say_to_command(ctx, channel_id: int, message: str):
    if is_admin_user(ctx.author):
        channel = await bot.fetch_channel(channel_id)
        await channel.send(message)
    else:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)

@bot.command(name="status", help="(Admin-only) Changes the bot's status")
async def status_command(ctx, status: str, message: str):
    if is_admin_user(ctx.author) is False:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)
        return

    discord_status = status_str_to_discord_status(status)

    await update_presence(discord_status, message)

@bot.command(name="joke", help="Drop a joke into the chat")
async def joke_command(ctx):
    async with ctx.typing():
        joke = http_get_json_generic("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit")

    if joke["error"]:
        raise ValueError("'error' is set")

    if joke["type"] == "twopart":
        setup = joke["setup"]
        delivery = joke["delivery"]
        await ctx.send(f"{setup} \n|| {delivery} ||")
    else:
        delivery = joke["joke"]
        await ctx.send(f"{delivery}")

@bot.command(name="quote", help="Drop a wise quote into the chat")
async def quote_command(ctx):
    async with ctx.typing():
        quotes = http_get_json_generic("https://zenquotes.io/api/random")

    quote = quotes[0]
    if quote is None:
        raise ValueError("'quote' is not set")

    line = quote["q"]
    author = quote["a"]

    await ctx.send(f"> {line} \n - {author}")

@bot.command(name="kitty", help="Drop a cute kitty photo into the chat")
async def kitty_command(ctx):
    async with ctx.typing():
        json = http_get_json_generic("https://api.thecatapi.com/v1/images/search")

    item = json[0]
    if item is None:
        raise ValueError("'item' is not set")
    url = item["url"]
    if url is None:
        raise ValueError("'url' is not set")

    await ctx.send(f"{url}")

@bot.command(name="doggo", help="Drop a cute dog photo into the chat")
async def doggo_command(ctx):
    async with ctx.typing():
        json = http_get_json_generic("https://api.thedogapi.com/v1/images/search")

    item = json[0]
    if item is None:
        raise ValueError("'item' is not set")
    url = item["url"]
    if url is None:
        raise ValueError("'url' is not set")

    await ctx.send(f"{url}")

@bot.command(name="penguin", help="Drop a penguin photo into the chat")
async def penguin_command(ctx):
    async with ctx.typing():
        # From https://github.com/samSharivker/PenguinImageAPI
        item = http_get_json_generic("https://penguin.sjsharivker.workers.dev/api")

    if item is None:
        raise ValueError("'item' is not set")
    url = item["img"]
    if url is None:
        raise ValueError("'url' is not set")

    await ctx.send(f"{url}")

@bot.command(name="no", help="Send a creative way of just saying `no`")
async def random_no_command(ctx):
    async with ctx.typing():
        random_no = await get_random_no()

    if random_no is None:
        raise ValueError("'random_no' is not set")

    await ctx.send(f"{random_no}")

@bot.command(name="error", help="Send a random error message")
async def random_error_command(ctx):
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.reply(random_error_message())

@bot.command(name="mock", help="Generate and send a string mocking the given string")
async def mock_command(ctx, *args):
    message = ' '.join(args)
    mocked_message = mock_string(message)
    await ctx.send(mocked_message)

@bot.command(name="roll_dice", help="Rolls dice and sends the total")
async def roll_dice_command(ctx, num_dice: int, sides: int):
    if num_dice < 1 or sides < 1:
        await ctx.send(random_error_message())
        return
    if num_dice > 1000000 or sides > 1000000:
        await ctx.send(random_error_message())
        return

    total = roll_dice(num_dice, sides)

    await ctx.send(f"`{total}`")

@bot.command(name="choose_random", help="Choose a random item out of the given items")
async def choose_random_command(ctx, *args):
    choice = random.choice(args)
    await ctx.send(f"Random Choice: || `{choice}` ||")

@bot.command(name="fortune", help="Ask a question and learn your fortune")
async def fortune_command(ctx, *args):
    fortune = random.choice(FORTUNES)
    await ctx.send(fortune)

@bot.command(name="hangman", help="Start a game of hangman")
async def hangman_command(ctx, word: str):
    async with ctx.typing():
        base_key = f"hangman.{ctx.channel.id}"
        main_bot_data.dictionary_set(f"{base_key}.word", word)
        main_bot_data.dictionary_set(f"{base_key}.guesses", 4)
        main_bot_data.dictionary_set(f"{base_key}.guessed", [])
        await asyncio.sleep(1)

    await ctx.reply("Starting a game of hangman!")

@bot.command(name="hangman_channel", help="Start a game of hangman in another channel")
async def hangman_command(ctx, channel: int, word: str):
    async with ctx.typing():
        word = word.lower()
        guesses = 4
        channel = await bot.fetch_channel(channel)
        if channel is None:
            ctx.reply("Could not find that channel.")
            return
        base_key = f"hangman.{channel.id}"
        main_bot_data.dictionary_set(f"{base_key}.word", word)
        main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
        main_bot_data.dictionary_set(f"{base_key}.guessed", [])
        await asyncio.sleep(1)

    await channel.send("Starting a game of hangman!")
    word_to_show = generate_hangman_current_word(word, [])
    await channel.send(f"`{word_to_show}` \nIncorrect Guesses Remaining: {guesses} \nUse `{COMMAND_PREFIX}letter <letter>` to guess a letter!")
    await ctx.reply("Done!")

@bot.command(name="letter", help="Guess a letter for hangman")
async def letter_command(ctx, letter: str):
    if len(letter) != 1 or letter.isalnum() is False:
        await ctx.send(random_error_message())
        await ctx.reply("That's not a letter!")
        return

    async with ctx.typing():
        base_key = f"hangman.{ctx.channel.id}"
        hangman_dict = main_bot_data.dictionary_get(f"{base_key}")
        guesses = hangman_dict.get("guesses")

        if guesses is None or guesses < 1:
            await ctx.reply(f"The game is over! Please start a new one.")
            return

        guessed = hangman_dict["guessed"]

        letter = letter.lower()

        if letter in guessed:
            await ctx.reply(f"'**{letter}**' has already been guessed!")
            return

        word = hangman_dict["word"]

        if letter not in word:
            guesses -= 1
        guessed.append(letter)

        word_to_show = generate_hangman_current_word(word.lower(), guessed)

        await ctx.reply(f"`{word_to_show}` \nIncorrect Guesses Remaining: {guesses}")

        if word_to_show == word:
            await ctx.reply("You win! Great Job!")
            guesses = 0
        elif guesses < 1:
            await ctx.reply(f"You Lose! Better luck next time! \nThe word was: || {word} ||")
            guesses = 0

        main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
        main_bot_data.dictionary_set(f"{base_key}.guessed", guessed)


def generate_hangman_current_word(word, guessed):
    word_to_show = word
    for character in word:
        if character not in guessed:
            word_to_show = word_to_show.replace(character, "_")
    return word_to_show

@bot.command(name="wordle_channel", help="Start a game of wordle in another channel")
async def wordle_channel_command(ctx, channel: int, word: str):
    async with ctx.typing():
        word = word.lower()
        length = len(word)
        guesses = length + 1
        channel = await bot.fetch_channel(channel)
        if channel is None:
            ctx.reply("Could not find that channel.")
            return
        base_key = f"wordle.{channel.id}"
        main_bot_data.dictionary_set(f"{base_key}.word", word)
        main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
        await asyncio.sleep(1)

    await channel.send("Starting a game of wordle!")
    await channel.send(f"`{length}` letters... \nWhat is it? \nUse `{COMMAND_PREFIX}guess_word <word>` to guess!")
    await ctx.reply("Done!")

@bot.command(name="guess_word", help="Guess the word for Wordle")
async def wordle_guess_command(ctx, word_guess: str):
    if word_guess.isalnum() is False:
        await ctx.send(random_error_message())
        await ctx.reply("That's not a valid guess!")
        return

    async with ctx.typing():
        base_key = f"wordle.{ctx.channel.id}"
        hangman_dict = main_bot_data.dictionary_get(f"{base_key}")
        guesses = hangman_dict.get("guesses")

        if guesses is None or guesses < 1:
            await ctx.reply(f"The game is over! Please start a new one.")
            return

        word = hangman_dict["word"]

        word_length = len(word)
        guess_len = len(word_guess)
        if guess_len != word_length:
            await ctx.reply(f"The word is {word_length} characters long, try again!")
            return

        guesses -= 1

        result_to_show = generate_wordle_guess_response(word.lower(), word_guess)

        await ctx.reply(f"`{result_to_show}` \nGuesses Remaining: {guesses}")

        if word_guess == word:
            await ctx.reply("You win! Great Job!")
            guesses = 0
        elif guesses < 1:
            await ctx.reply(f"You Lose! Better luck next time! \nThe word was: || {word} ||")
            guesses = 0

        main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)

def generate_wordle_guess_response(word: str, guess: str):
    response = ""
    for i in range(0, len(guess)):
        if guess[i] == word[i]:
            response += EMOJI_GREEN_SQUARE
        elif guess[i] in word:
            response += EMOJI_YELLOW_SQUARE
        else:
            response += EMOJI_BLACK_SQUARE
    return response

@bot.command(name="game", help="EXPERIMENT!! DOES NOT DO ANYTHING OF VALUE")
async def game_command(ctx):

    # Just to give Pycharm a hint for the type
    # so it helps me write code :)
    assert isinstance(ctx, commands.Context)

    key = f"{ctx.channel.id}.{ctx.author.id}"
    value = random.choice(range(0, 100))
    main_bot_data.dictionary_set(key, value)

    await ctx.send(f"{main_bot_data.dictionary_get(key)}")

#
# Activity
#

@bot.event
async def on_presence_update(before, after):
    handle_online_status_change(before, after)
    handle_activity_change(before, after)

def handle_online_status_change(before, after):
    if before.status == after.status:
        return

    username = compute_printed_user(after)

    if after.status == discord.Status.online:
        log(f"Status: {username} is now online")
    elif after.status == discord.Status.idle:
        log(f"Status: {username} is now idle")
    elif after.status == discord.Status.do_not_disturb:
        log(f"Status: {username} is now in Do Not Disturb")
    elif after.status == discord.Status.offline:
        log(f"Status: {username} is now offline")

def handle_activity_change(before, after):
    username = compute_printed_user(after)
    before_spotify = get_spotify_activity(before.activities)
    after_spotify = get_spotify_activity(after.activities)

    before_playing = get_playing_activity(before.activities)
    after_playing = get_playing_activity(after.activities)

    if should_display_updated_spotify_activity(before_spotify, after_spotify):
        log(f"Status: {username} is now listening to {after_spotify.artist} - {after_spotify.title}")
    if should_display_updated_playing_activity(before_playing, after_playing):
        log(f"Status: {username} is now playing {after_playing.name} ({after_playing.state}, {after_playing.details})")

def should_display_updated_playing_activity(before, after):
    if isinstance(after, discord.Activity) is False:
        return False
    if before is not None:
        if after.name != before.name:
            return True
    return True

def should_display_updated_spotify_activity(before, after):
    if isinstance(after, discord.Spotify) is False:
        return False
    if before is not None:
        if after.title != before.title:
            return True
    return True

def get_spotify_activity(activities):
    for activity in activities:
        if isinstance(activity, discord.Spotify):
            return activity
    return None

def get_playing_activity(activities):
    for activity in activities:
        if activity.type == discord.ActivityType.playing:
            return activity
    return None

#
# Message
#

@bot.event
async def on_message(message):
    # Log all messages
    username = compute_printed_user(message.author)
    log(f"Message: [{compute_printed_channel_for_message(message)}] {username} {message.content}")

    # Only handle messages from *other* users
    if message.author == bot.user:
        return

    # Stop if the message was from a bot
    if message.author.bot is True:
        return

    # Process user messages

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # Handle commands
    # Explicit call required in order to use discord.py builtin command processing
    await bot.process_commands(message)

def compute_printed_channel_for_message(message):
    channel = message.channel
    return compute_printed_channel(channel)

def compute_printed_channel(channel):
    if isinstance(channel, discord.TextChannel):
        return f"Channel {channel.guild.name}/#{channel.name}"
    elif isinstance(channel, discord.Thread):
        return f"Thread {channel.guild.name}/<{channel.name}>"
    elif isinstance(channel, discord.DMChannel):
        return f"DM"

    return "<UNKNOWN>"

def compute_printed_user(user):
    return f"<{user.name}>"

#
# RUN
#

if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        raise ValueError('DISCORD_TOKEN environment variable not set')

    bot.run(token)
