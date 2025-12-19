import os
import re
import requests
import random
import datetime

import discord
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv()

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
    toRet = ""
    for i in range(0, len(message)):
        rand = random.randint(0, 2)
        if rand == 0:
            toRet += message[i].upper()
        else:
            toRet += message[i].lower()
    return toRet

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

    if after_spotify != before_spotify and isinstance(after_spotify, discord.Spotify):
        log(f"Status: {username} is now listening to {after_spotify.artist} - {after_spotify.title}")

def get_spotify_activity(activities):
    for activity in activities:
        if isinstance(activity, discord.Spotify):
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
