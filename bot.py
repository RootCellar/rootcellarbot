
#
# Copyright (c) 2025 Darian Marvel. See LICENSE
#
# `rootcellar` on Discord.
#

import os
import shutil
import re
import json
import requests
import random
import datetime

import threading

import asyncio
from asyncio import Lock

import discord
from discord.ext import commands

from dotenv import load_dotenv
from requests import JSONDecodeError

load_dotenv()

#
# ENVIRONMENT VARIABLES
#

ALWAYS_DEBUG = bool(os.getenv('ALWAYS_DEBUG', default = 'False'))
DEFAULT_DEBUG_CHANNEL_STATUS = bool(os.getenv('DEFAULT_DEBUG_CHANNEL_STATUS', default = 'False'))

BOT_NAME = os.getenv('BOT_NAME', default = 'unnamed')
BOT_ICON_URL = os.getenv('BOT_ICON_URL', default = '')
BOT_COLOR = int(os.getenv('BOT_COLOR', default = '0xff0000'), 16)
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', default = '!')
DEFAULT_STATUS = os.getenv('DEFAULT_STATUS', default = '')
DEFAULT_STATUS_MESSAGE = os.getenv('DEFAULT_STATUS_MESSAGE', default = '')
ADMIN_USERNAMES = os.getenv('ADMIN_USERNAMES', default = '')

WORDLE_WORDS_FILE = os.getenv('WORDLE_WORDS_FILE', default = '')

#
# CONSTANTS
#

DEBUG_CHANNEL_DICT_PATH = "debug.type"

INFO_DESCRIPTION = "A Discord bot that's meant to bring some extra fun into the chat with a variety of available commands and a couple games"
INFO_USAGE = f"Use `{COMMAND_PREFIX}help` to get a list of available commands"
INFO_REPOSITORY_URL = "[Click Here](<https://github.com/RootCellar/RootCellarBot>)"

FORTUNES = [
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

ERROR_MESSAGES = [
    "huh?", "what?", "*implodes*", "no u", "AAAAAAAAAAAAAA", "I need....a penguin plushie", "whar?", "~~sanity~~",
    "explode", "you wish", "bruh", "|| no ||",
    "I'm gonna", "Ask ChatGPT", "imagine", "yesn't", "Segmentation fault (core dumped)"
]

NO_PERMISSION_ERROR_MESSAGE = "Sorry, you don't have permission to do that."

#
# Colors
#

COLOR_RED = 0xff0000
COLOR_GREEN = 0x00ff00
COLOR_BLUE = 0x0000ff

COLOR_YELLOW = 0xffff00
COLOR_GRAY = 0x777777

#
# Emoji's
#

EMOJI_GREEN_SQUARE = '\U0001F7E9'
EMOJI_YELLOW_SQUARE = '\U0001F7E8'
EMOJI_BLACK_SQUARE = '\U00002B1B'

EMOJI_DICE = '\U0001F3B2'
EMOJI_PARTY_POPPER = '\U0001F389'

MAIN_DATA_FILE = "main_bot_data.json"

#
# GLOBAL DATA
#

startup_time = datetime.datetime.now()
data_lock = Lock()
debug_channel_dict = {}
wordle_words = []

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
# LOGGING and DEBUGGING
#


def get_debug_channel_value_path(name: str):
    return f"{DEBUG_CHANNEL_DICT_PATH}.{name}"


def get_debug_channel_value(channel: str):
    value = debug_channel_dict.get(channel)
    return value


def set_debug_channel_value(channel: str, value: bool) -> None:
    debug_channel_dict[channel] = value


def should_log_debug_channel(channel: str):
    value = get_debug_channel_value(channel)

    if value is True:
        return True
    if value is None:
        # This serves as an "automatic registration", so that
        # commands such as "prefix!debugged" will show all channels
        # that the program has attempted to use
        set_debug_channel_value(channel, DEFAULT_DEBUG_CHANNEL_STATUS)

    return False


def debug(channel: str, message: str):
    if should_log_debug_channel(channel) is True or ALWAYS_DEBUG is True:
        log(f"[DEBUG] {channel}: {message}")


def match_all_regex(expr: str, text: str) -> list[str]:
    return re.findall(expr, text)


def strip_non_ascii(text: str):
    return re.sub(r'[^\x00-\x7f]', r'?', text)


def log(message: str) -> None:
    message_to_write = generate_log_message(message)
    print(message_to_write)
    with open('info.log', 'a') as file:
        file.write(f"{message_to_write} \n")


def generate_log_message(message: str) -> str:
    formatted_datetime = format_datetime(datetime.datetime.now())
    formatted_message = strip_non_ascii(message)
    message_to_write = f"{formatted_datetime} - {formatted_message}"
    return message_to_write


def format_datetime(datetime_to_format: datetime.datetime):
    formatted_datetime = datetime_to_format.strftime(f"%Y-%m-%d %H:%M:%S")
    return formatted_datetime


def format_datetime_all_dashes(datetime_to_format: datetime.datetime):
    formatted_datetime = datetime_to_format.strftime(f"%Y-%m-%d-%H-%M-%S")
    return formatted_datetime


#
# DATA
#


def mkdir_ignore_exists(dir_name: str) -> None:
    try:
        os.mkdir(dir_name)
    except FileExistsError:
        pass


def load_file_lines(file_name: str) -> list[str]:
    debug("load_file_lines", file_name)
    lines = []
    with open(file_name) as f:
        for line in f:
            lines.append(line)
    return lines


def load_json_data(file_name: str) -> dict:
    debug("json_data", f"Loading {file_name}...")
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    return {}


async def save_json_data(data: dict, file_name: str) -> None:
    debug("json_data", f"Saving {file_name}...")
    async with data_lock:
        with open(file_name, 'w') as file:
            json.dump(data, file, indent = 4)


async def backup_and_save_json_data(data: dict, file_name: str) -> None:
    if os.path.exists(file_name):
        try:
            dir_name = "discord_bot_data_backups"
            mkdir_ignore_exists(dir_name)
            time_formatted = format_datetime_all_dashes(datetime.datetime.now())
            dst_file_name = f"{file_name}-{time_formatted}"
            dst_name = "discord_bot_data_backups/" + dst_file_name
            debug("backup", f"Backing up '{file_name}' to '{dst_name}'...")
            shutil.copyfile(file_name, dst_name)
        except OSError as error:
            log(f"Failed to back up {file_name}: {error}")

    await save_json_data(data, file_name)


class JsonDictionary(object):
    def __init__(self, name: str = "unnamed", dictionary = None):
        if dictionary is None:
            dictionary = dict()

        self.data_structure_lock = threading.Lock()
        self.get_and_set_lock = threading.Lock()

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

    def get_sub_dict_and_leaf_node_key(self, key: str):
        with self.data_structure_lock:
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

        with self.get_and_set_lock:
            sub_dict, leaf_key = self.get_sub_dict_and_leaf_node_key(key)
            value = sub_dict.get(leaf_key)

        self.print_debug(f"dictionary_get: '{key}': '{value}'")
        return value

    def dictionary_set(self, key: str, value):
        # Type Hint
        if isinstance(self.dictionary, dict) is False:
            raise TypeError("Expected a dictionary")

        with self.get_and_set_lock:
            sub_dict, leaf_key = self.get_sub_dict_and_leaf_node_key(key)
            if isinstance(sub_dict.get(leaf_key), dict) is True:
                raise TypeError(f"Expected a non-dictionary, but found a dictionary at {key}")
            else:
                sub_dict[leaf_key] = value
                self.print_debug(f"dictionary_set: '{key}' to '{value}'")


main_bot_data_json = load_json_data(MAIN_DATA_FILE)
main_bot_data = JsonDictionary(name = "main_data", dictionary = main_bot_data_json)


class CustomBot(commands.Bot):
    async def close(self):
        log("Cleaning up...")

        for key in debug_channel_dict.keys():
            main_dict_key = get_debug_channel_value_path(key)
            main_bot_data.dictionary_set(main_dict_key, debug_channel_dict[key])

        log("Saving data...")
        await backup_and_save_json_data(main_bot_data.get_dictionary(), MAIN_DATA_FILE)

        log("Shutting down...")
        await super().close()


bot = CustomBot(command_prefix = COMMAND_PREFIX, intents = intents)


#
# UTIL
#


def get_server_data_path_prefix(server_id: int):
    return f"servers.{server_id}"


def get_server_user_data_path_prefix(server_id: int, user_id: int):
    return f"{get_server_data_path_prefix(server_id)}.users.{user_id}"


def get_server_user_permissions_data_path_prefix(server_id: int, user_id: int):
    return f"{get_server_user_data_path_prefix(server_id, user_id)}.permissions"


def get_server_user_permission_data_path(server_id: int, user_id: int, permission: str):
    return f"{get_server_user_permissions_data_path_prefix(server_id, user_id)}.{permission}"


def get_server_user_permission_value(server_id: int, user_id: int, permission: str):
    return main_bot_data.dictionary_get(get_server_user_permission_data_path(server_id, user_id, permission))


def get_quiz_data_path_prefix(server_id: int, quiz_name: str):
    return f"{get_server_data_path_prefix(server_id)}.quizzes.{quiz_name}"


def get_user_data_path_prefix(user_id: int):
    return f"users.{user_id}"


def roll_die(sides: int):
    return random.choice(range(1, sides + 1))


def roll_dice(num_dice: int, sides: int):
    total = 0
    for x in range(1, num_dice + 1):
        total += roll_die(sides)
    return total


def random_error_message():
    return random.choice(ERROR_MESSAGES)


def mock_word(word: str) -> str:
    if len(word) < 1:
        return word

    if len(word) == 1:
        return word.upper()

    lettercount = 0
    can_cap = []
    for i in range(0, len(word)):
        char = word[i]
        if char.isalpha():
            lettercount += 1
            can_cap.append(i)

    num_to_capitalize = int(float(lettercount) * (67/100))
    word = word.lower()

    which_to_capitalize = []
    for j in range(num_to_capitalize):
        i = random.choice(range(0, len(can_cap)))
        which_to_capitalize.append(can_cap[i])
        can_cap.remove(can_cap[i])

    to_ret = ""
    for i in range(0, len(word)):
        char = word[i]
        if i in which_to_capitalize:
            char = char.upper()
        to_ret += char
    return to_ret


def mock_string(message: str) -> str:
    words = message.split(" ")
    new_words = []
    for word in words:
        new_words.append(mock_word(word))
    return " ".join(new_words)


#
# Performs a GET fetch and returns the JSON response
# when the GET was successful. Otherwise, returns `None`
#
def http_get_json_generic(url: str):
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


def status_str_to_discord_status(status: str):
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
        await bot.change_presence(status = status)
    else:
        game = discord.Game(message)
        await bot.change_presence(status = status, activity = game)


def is_admin_user(user):
    users = ADMIN_USERNAMES.split(",")
    for name in users:
        if user.name == name:
            return True
    return False


def is_user_bot_admin_for_server(user_id: int, server_id: int):
    user_is_admin = get_server_user_permission_value(server_id, user_id, "is_admin")

    if user_is_admin is True:
        return True
    return False


def user_has_permission_in_server(user_id: int, server_id: int, permission: str):
    # If the user is an admin in the server, they automatically have permission to do *anything*
    if is_user_bot_admin_for_server(user_id, server_id) is True:
        return True

    permission_value = get_server_user_permission_value(server_id, user_id, permission)
    if permission_value is True:
        return True
    return False


async def send_dm_to_user(user: discord.User, message: str = None, embed: discord.Embed = None, silent: bool = False):
    details_list = []

    if message is not None:
        details_list.append(f"Message: `{message}`")

    if embed is not None:
        details_list.append("Has Embed")

    if silent is True:
        details_list.append("Is Silent")
    else:
        details_list.append("Is Not Silent")

    details = ", ".join(details_list)

    debug("DM", f"Sending DM to {user.name}. {details}")
    await user.create_dm()
    await user.send(message, embed = embed, silent = silent)


async def send_dm_to_user_by_id(user_id: int, message: str = None, embed: discord.Embed = None, silent: bool = False):
    user = await bot.fetch_user(user_id)
    await send_dm_to_user(user, message, embed = embed, silent = silent)


#
# On Connect
#


@bot.event
async def on_ready():
    log("Populating data...")

    # Load debug channel statuses

    debug_dict = main_bot_data.dictionary_get(DEBUG_CHANNEL_DICT_PATH)
    if isinstance(debug_dict, dict) is True:
        for key in debug_dict.keys():
            value = debug_dict[key]
            debug_channel_dict[key] = value

    # Load Wordle Words

    if WORDLE_WORDS_FILE is not None and WORDLE_WORDS_FILE != "":
        words_from_file = load_file_lines(WORDLE_WORDS_FILE)
        for word in words_from_file:
            wordle_words.append(word.rstrip())

    # Done! Set Status

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
async def on_command_error(ctx: discord.ext.commands.Context, error: discord.ext.commands.CommandError):
    log(f"Command invocation threw an error: {error}")

    if not isinstance(ctx, commands.Context):
        raise ValueError("ctx is not a Context")
    if not isinstance(error, commands.CommandError):
        raise ValueError("error is not a CommandError")

    suberror_causes = []
    suberror = error

    # Collect causes
    while suberror.__cause__ is not None:
        suberror = suberror.__cause__
        suberror_causes.append(str(suberror))

    # Send error cause trace to log
    log(f"Command Invocation Failed: {error}")
    for suberror_cause in suberror_causes:
        log(f"Caused by: {suberror_cause}")

    # Send error cause trace to chat
    suberror_lines = []
    for cause in suberror_causes:
        suberror_lines.append(f"Caused by: `{cause}`")
    suberror_info = "\n".join(suberror_lines)
    await ctx.reply(f"Command Invocation Failed: `{error}`\n{suberror_info}")

    # await ctx.send("well that threw an error")
    # await ctx.send(random_error_message())


@bot.command(name = "hello", help = "Says hello")
async def hello_command(ctx):
    await ctx.send("Hello! I'm a bot.")


class ErrorButtons(discord.ui.View):
    def __init__(self, *, timeout=600):
        super().__init__(timeout=timeout)

    @discord.ui.button(label = "Button One", style = discord.ButtonStyle.blurple)
    async def blurple_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = random_error_message()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = "Button Two", style = discord.ButtonStyle.gray)
    async def gray_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = random_error_message()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = "Button Three", style = discord.ButtonStyle.green)
    async def green_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = random_error_message()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = "Button Four", style = discord.ButtonStyle.red)
    async def red_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.label = random_error_message()
        await interaction.response.edit_message(view = self)


@bot.command(name = "test_buttons", help = "", hidden = True)
async def test_buttons_command(ctx):
    async with ctx.typing():
        view = ErrorButtons()
        await ctx.send("This message is for testing buttons", view = view)


@bot.command(name = "info", help = "Send bot info")
async def info_command(ctx):
    async with ctx.typing():

        now = datetime.datetime.now()

        message = discord.Embed(colour = BOT_COLOR)

        message.set_thumbnail(url = BOT_ICON_URL)
        message.set_author(name = BOT_NAME, icon_url = BOT_ICON_URL)
        message.set_footer(text = f"Requested by {ctx.author}", icon_url = ctx.author.avatar.url)

        message.add_field(name = "Description", value = INFO_DESCRIPTION, inline = False)
        message.add_field(name = "Commands", value = INFO_USAGE, inline = False)
        message.add_field(name = "Source Code Repository", value = INFO_REPOSITORY_URL, inline = False)

        message.add_field(name = "Current Time", value = format_datetime(now))
        message.add_field(name = "Startup Time", value = format_datetime(startup_time))

        await ctx.channel.send(embed = message)


@bot.command(name = "match", help = "Perform Regular Expression matching on the given text or referenced message")
async def match_command(ctx, expr: str, text: str = None):
    async with ctx.typing():
        content = None
        message_reference = ctx.message.reference
        if message_reference is not None:
            try:
                referenced_message = await ctx.fetch_message(message_reference.message_id)
            except Exception as error:
                await ctx.reply(f"Failed to fetch message reference: {error}")
                return

            content = referenced_message.content
            if len(content) < 1 or len(content) > 3072:
                await ctx.reply("Sorry, I can't do that.")
                return
        else:
            if text is None:
                await ctx.reply("No text provided! Provide text by supplying a 2nd string or replying to another message.")
                return
            content = text

        matches = match_all_regex(expr, content)

        message = discord.Embed(colour = BOT_COLOR, title = "Regular Expression Match", description = f"`{expr}`")
        message.set_footer(text = f"Requested by {ctx.author}", icon_url = ctx.author.avatar.url)

        matches_formatted = []

        for match in matches:
            matches_formatted.append(f"`{match}`")

        message.add_field(name = "Matches", value = ", ".join(matches_formatted), inline = False)

        await ctx.channel.send(embed = message)


@bot.command(name = "plaque", help = "Professionally plaque a message")
async def plaque_command(ctx):
    async with ctx.typing():
        message_reference = ctx.message.reference
        if message_reference is None:
            await ctx.reply("Plaque *what*? Reply to the message that you want to place on a plaque.")
            return

        try:
            referenced_message = await ctx.fetch_message(message_reference.message_id)
        except Exception as error:
            await ctx.reply(f"Failed to fetch message reference: {error}")
            return

        content = referenced_message.content
        if len(content) < 1 or len(content) > 2048:
            await ctx.reply("Sorry, I can't do that.")
            return

        now = datetime.datetime.now()

        message = discord.Embed(colour = BOT_COLOR, title = referenced_message.author.display_name, description = referenced_message.content, timestamp = now)
        message.set_thumbnail(url = referenced_message.author.avatar.url)
        message.set_footer(text = f"Requested by {ctx.author}", icon_url = ctx.author.avatar.url)
        await ctx.channel.send(embed = message)


@bot.command(name = "debug", help = "(Admin-only) Enable/Disable specific debug channels", hidden = True)
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


@bot.command(name = "debugged", help = "(Admin-only) Show debug channel values", hidden = True)
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


@bot.command(name = "say", help = "(Admin-only) Forces the bot to send the given message", hidden = True)
async def say_command(ctx, message: str):
    if is_admin_user(ctx.author):
        await ctx.send(message)
    else:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)


@bot.command(name = "say_to", help = "(Admin-only) Forces the bot to send the given message to the given channel", hidden = True)
async def say_to_command(ctx, channel_id: int, message: str):
    if is_admin_user(ctx.author):
        channel = await bot.fetch_channel(channel_id)
        await channel.send(message)
    else:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)


@bot.command(name = "dm", help = "(Admin-only) Forces the bot to send the given message to the given user by ID", hidden = True)
async def dm_command(ctx, user_id: int, message: str):
    if is_admin_user(ctx.author):
        await send_dm_to_user_by_id(user_id, message)
    else:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)


@bot.command(name = "status", help = "(Admin-only) Changes the bot's status", hidden = True)
async def status_command(ctx, status: str, message: str):
    if is_admin_user(ctx.author) is False:
        await ctx.reply(NO_PERMISSION_ERROR_MESSAGE)
        return

    discord_status = status_str_to_discord_status(status)

    await update_presence(discord_status, message)


@bot.command(name = "joke", help = "Drop a joke into the chat")
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


@bot.command(name = "quote", help = "Drop a wise quote into the chat")
async def quote_command(ctx):
    async with ctx.typing():
        quotes = http_get_json_generic("https://zenquotes.io/api/random")

    quote = quotes[0]
    if quote is None:
        raise ValueError("'quote' is not set")

    line = quote["q"]
    author = quote["a"]

    await ctx.send(f"> {line} \n - {author}")


@bot.command(name = "kitty", help = "Drop a cute kitty photo into the chat")
async def kitty_command(ctx):
    async with ctx.typing():
        response_json = http_get_json_generic("https://api.thecatapi.com/v1/images/search")

    item = response_json[0]
    if item is None:
        raise ValueError("'item' is not set")

    url = item["url"]
    if url is None:
        raise ValueError("'url' is not set")

    embed = discord.Embed(title = "Cat", color = COLOR_GRAY)
    embed.set_image(url = url)

    await ctx.send(embed = embed)


@bot.command(name = "doggo", help = "Drop a cute dog photo into the chat")
async def doggo_command(ctx):
    async with ctx.typing():
        response_json = http_get_json_generic("https://api.thedogapi.com/v1/images/search")

    item = response_json[0]
    if item is None:
        raise ValueError("'item' is not set")

    url = item["url"]
    if url is None:
        raise ValueError("'url' is not set")

    embed = discord.Embed(title = "Dog", color = COLOR_RED)
    embed.set_image(url = url)

    await ctx.send(embed = embed)


@bot.command(name = "penguin", help = "Drop a penguin photo into the chat")
async def penguin_command(ctx):
    async with ctx.typing():
        # From https://github.com/samSharivker/PenguinImageAPI
        item = http_get_json_generic("https://penguin.sjsharivker.workers.dev/api")

    if item is None:
        raise ValueError("'item' is not set")

    url = item["img"]
    species = item["species"]

    if url is None:
        raise ValueError("'url' is not set")
    if species is None:
        raise ValueError("'species' is not set")

    embed = discord.Embed(title = "Penguin", description = f"**Species**: || {species} ||", color = COLOR_BLUE)
    embed.set_image(url = url)

    await ctx.send(embed = embed)


@bot.command(name = "no", help = "Send a creative way of just saying `no`")
async def random_no_command(ctx):
    async with ctx.typing():
        random_no = await get_random_no()

    if random_no is None:
        raise ValueError("'random_no' is not set")

    await ctx.send(f"{random_no}")


@bot.command(name = "error", help = "Send a random error message")
async def random_error_command(ctx):
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.reply(random_error_message())


@bot.command(name = "mock", help = "Generate and send a string mocking the given string")
async def mock_command(ctx, *args):
    message = ' '.join(args)
    mocked_message = mock_string(message)
    await ctx.send(mocked_message)


@bot.command(name = "roll_dice", help = "Rolls dice and sends the total")
async def roll_dice_command(ctx, num_dice: int, sides: int):
    if num_dice < 1 or sides < 1:
        await ctx.send(random_error_message())
        return
    if num_dice > 1000000 or sides > 1000000:
        await ctx.send(random_error_message())
        return

    total = roll_dice(num_dice, sides)

    embed = discord.Embed(title = f"{EMOJI_DICE} **{total}**", color = COLOR_RED)

    await ctx.reply(embed = embed)


@bot.command(name = "choose_random", help = "Choose a random item out of the given items")
async def choose_random_command(ctx, *args):
    choice = random.choice(args)

    embed = discord.Embed(title = f"{EMOJI_DICE} Random Choice", description = f"|| **{choice}** ||", color = COLOR_BLUE)

    await ctx.reply(embed = embed)


@bot.command(name = "fortune", help = "Ask a question and learn your fortune")
async def fortune_command(ctx):
    fortune = random.choice(FORTUNES)

    embed = discord.Embed(title = "Fortune", description = f"{fortune}", color = COLOR_RED)

    await ctx.reply(embed = embed)


async def create_hangman_game_in_channel(channel, word):
    word = word.lower()
    guesses = 4
    base_key = f"hangman.{channel.id}"
    main_bot_data.dictionary_set(f"{base_key}.word", word)
    main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
    main_bot_data.dictionary_set(f"{base_key}.guessed", [])
    await channel.send("Starting a game of hangman!")
    word_to_show = generate_hangman_current_word(word, [])
    await channel.send(f"`{word_to_show}` \nIncorrect Guesses Remaining: {guesses} \nUse `{COMMAND_PREFIX}letter <letter>` to guess a letter!")


@bot.command(name = "random_hangman", help = "Start a game of Hangman with a randomly chosen word")
async def random_hangman_command(ctx):
    async with ctx.typing():
        if len(wordle_words) < 1:
            await ctx.reply("Don't have any words to use! Sorry!")
            return
        word = random.choice(wordle_words)
        await create_hangman_game_in_channel(ctx.channel, word)


@bot.command(name = "hangman_channel", help = "Start a game of hangman in another channel")
async def hangman_command(ctx, channel: int = None, word: str = None):
    async with ctx.typing():
        if channel is None:
            response_string = "If you would like to create a game, please give me the channel ID and a word."
            response_string += f"\nFor this channel, the command would be: `{COMMAND_PREFIX}hangman_channel {ctx.channel.id} <word>`"
            response_string += f"\n-# You can DM this command to me or run it from a different channel so you don't reveal the answer"
            await ctx.reply(response_string)
            return

        if word is None:
            await ctx.reply("Please give me a word to use to run the game!")
            return

        if word.isalnum() is False:
            await ctx.reply("That's not a word!")
            return

        channel = await bot.fetch_channel(channel)
        if channel is None:
            ctx.reply("Could not find that channel.")
            return

        await create_hangman_game_in_channel(channel, word)
        await asyncio.sleep(1)

    await ctx.reply("Done!")


@bot.command(name = "letter", help = "Guess a letter for hangman")
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


async def create_wordle_game_in_channel(channel, word):
    word = word.lower()
    length = len(word)
    guesses = length + 1
    base_key = f"wordle.{channel.id}"
    main_bot_data.dictionary_set(f"{base_key}.word", word)
    main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
    main_bot_data.dictionary_set(f"{base_key}.guessed", [])

    embed = discord.Embed(title = "Wordle", color = COLOR_YELLOW)

    embed.add_field(name = "Starting a game of Wordle in this channel!", value = f"The word has `{length}` letters...", inline = False)
    embed.add_field(name = "What is it?", value = f"Use `{COMMAND_PREFIX}guess_word <word>` to guess!", inline = False)

    await channel.send(embed = embed)


@bot.command(name = "random_wordle", help = "Start a game of Wordle with a randomly chosen word")
async def random_wordle_command(ctx):
    async with ctx.typing():
        if len(wordle_words) < 1:
            await ctx.reply("Don't have any words to use! Sorry!")
            return
        word = random.choice(wordle_words)
        await create_wordle_game_in_channel(ctx.channel, word)


@bot.command(name = "wordle_channel", help = "Start a game of Wordle in another channel")
async def wordle_channel_command(ctx, channel: int = None, word: str = None):
    async with ctx.typing():
        if channel is None:
            response_string = "If you would like to create a game, please give me the channel ID and a word."
            response_string += f"\nFor this channel, the command would be: `{COMMAND_PREFIX}wordle_channel {ctx.channel.id} <word>`"
            response_string += f"\n-# You can DM this command to me or run it from a different channel so you don't reveal the answer"
            await ctx.reply(response_string)
            return

        if word is None:
            await ctx.reply("Please give me a word to use to run the game!")
            return

        if word.isalnum() is False:
            await ctx.reply("That's not a word!")
            return

        channel = await bot.fetch_channel(channel)
        if channel is None:
            ctx.reply("Could not find that channel.")
            return

        await create_wordle_game_in_channel(channel, word)
        await asyncio.sleep(1)

    await ctx.reply("Done!")


@bot.command(name = "guess_word", help = "Guess the word for Wordle")
async def wordle_guess_command(ctx, word_guess: str):
    if word_guess.isalnum() is False:
        await ctx.send(random_error_message())
        await ctx.reply("That's not a valid guess!")
        return

    async with ctx.typing():
        base_key = f"wordle.{ctx.channel.id}"
        wordle_dict = main_bot_data.dictionary_get(f"{base_key}")
        guesses = wordle_dict.get("guesses")

        if guesses is None or guesses < 1:
            await ctx.reply(f"The game is over! Please start a new one.")
            return

        word = wordle_dict["word"]
        word_guess = word_guess.lower()

        word_length = len(word)
        guess_len = len(word_guess)
        if guess_len != word_length:
            await ctx.reply(f"The word is {word_length} characters long, try again!")
            return

        guessed = wordle_dict["guessed"]
        guessed.append(word_guess)
        guesses -= 1

        result_lines = []
        for guess in guessed:
            guess_response = generate_wordle_guess_response(word, guess)
            result_lines.append(f"`{guess}` - `{guess_response}`")
        result_to_show = "\n".join(result_lines)

        guess_remaining_text = f"Guesses Remaining: {guesses}"
        embed = discord.Embed(title = "Wordle Results", description = f"{guess_remaining_text}\n\n{result_to_show}", color = COLOR_YELLOW)

        await ctx.reply(embed = embed)

        if word_guess == word:
            win_embed = discord.Embed(title = f"You Win! Great Job! {EMOJI_PARTY_POPPER}", color = COLOR_GREEN)
            await ctx.reply(embed = win_embed)
            guesses = 0
        elif guesses < 1:
            lose_embed = discord.Embed(title = "Better luck next time!", description = f"The word was: || {word} ||", color = COLOR_GRAY)
            await ctx.reply(embed = lose_embed)
            guesses = 0

        main_bot_data.dictionary_set(f"{base_key}.guesses", guesses)
        main_bot_data.dictionary_set(f"{base_key}.guessed", guessed)


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


#
# Activity
#


@bot.event
async def on_presence_update(before, after):
    handle_online_status_change(before, after)
    handle_activity_change(before, after)


# This is left over from early versions of the bot, as part of
# discovering discord.py and what was possible.
# This information is logged, but not otherwise used.
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


# This is left over from early versions of the bot, as part of
# discovering discord.py and what was possible.
# This information is logged, but not otherwise used.
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

    # if message.content.startswith('$hello'):
    #     await message.channel.send('Hello!')

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
