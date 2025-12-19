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
# RUN
#

token = os.getenv('DISCORD_TOKEN')

bot.run(token)
