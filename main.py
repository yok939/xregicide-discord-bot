import os
from dotenv import load_dotenv

import datetime
import zoneinfo

import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("TOKEN")

target_time = datetime.datetime(year=2026, month=6, day=20, hour=13, minute=39, tzinfo=zoneinfo.ZoneInfo("Asia/Taipei"))

intents = discord.Intents.all()
bot = commands.Bot(intents=intents)

cogs_list = [
    'fun',
    'event'
]

for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")

bot.run(TOKEN)
