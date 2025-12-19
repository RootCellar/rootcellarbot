import os
import re
import requests
import random
import datetime

import discord
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv()

ADMIN_USERS = os.getenv('ADMIN_USERS')
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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
intents.emojis = True
intents.reactions = True
intents.expressions = True
intents.typing = True

bot = commands.Bot(command_prefix='rc!', intents=intents)

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

async def update_presence(status, message):
  game = discord.Game(message)
  await bot.change_presence(status=status, activity=game)

def is_admin_user(user):
    users = ADMIN_USERS.split(",")
    for name in users:
        if user.name == name:
            return True
    return False

def log(message):
    now = datetime.datetime.now()
    formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = strip_non_ascii(message)
    message_to_write = f"{formatted_datetime} - {formatted_message}"
    print(message_to_write)
    with open('info.log', 'a') as file:
        file.write(f"{message_to_write} \n")

#
# On Connect
#

@bot.event
async def on_ready():
    log(f"Logged in as {bot.user}!")
    await update_presence(discord.Status.online, "Running :D")

#
# Commands
#

@bot.event
async def on_command_error(ctx, error):
    log(f"Command invocation threw an error: {error}")
    await ctx.send("well that threw an error")
    await ctx.send(random_error_message())

@bot.command(name="hello")
async def hello_command(ctx):
    await ctx.send("Hello! I'm a bot.")  # Responds to '!hello'

@bot.command(name="say")
async def say_command(ctx, message: str):
    if is_admin_user(ctx.author):
        await ctx.send(message)

@bot.command(name="status")
async def status_command(ctx, status: str, message: str):
    if is_admin_user(ctx.author) is False:
        return

    if status == "online":
        await update_presence(discord.Status.online, message)
    elif status == "idle":
        await update_presence(discord.Status.idle, message)
    elif status == "dnd":
        await update_presence(discord.Status.do_not_disturb, message)
    elif status == "invisible":
        await update_presence(discord.Status.invisible, message)
    else:
        await ctx.send(random_error_message())

@bot.command(name="joke", help="Drop a joke into the chat")
async def joke_command(ctx):
    async with ctx.typing():
        request = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit")
        joke = request.json()

    assert joke["error"] == False

    if joke["type"] == "twopart":
        setup = joke["setup"]
        delivery = joke["delivery"]
        await ctx.send(f"{setup} \n || {delivery} ||")
    else:
        delivery = joke["joke"]
        await ctx.send(f"{delivery}")

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
    joined = ' '.join(args)
    fortune = random.choice(FORTUNES)
    await ctx.send(fortune)

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
        log(f"Status: {username} is now playing {after_playing.name}")

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

    # Only handle messages from other users
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # Required to use discord.py builtin command processing
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

token = os.getenv('DISCORD_TOKEN')

bot.run(token)
