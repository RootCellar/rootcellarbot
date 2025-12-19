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
