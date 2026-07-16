import os
from dotenv import load_dotenv

import datetime
import zoneinfo

import discord
from discord.ext import commands

target_time = datetime.datetime(year=2026, month=6, day=20, hour=13, minute=39, tzinfo=zoneinfo.ZoneInfo("Asia/Taipei"))

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.__last_member = None

    @discord.slash_command(
        name="death_count",
        description="Gives how many times Cam died in the #dead-office"
    )
    async def death_count_command(self, ctx):
        channel = self.bot.get_channel(1413987605124743178)
        try:
            messages = await channel.history(limit=1000, after=target_time).flatten()
        except:
            await ctx.respond(f"Cam is not in this clan")
            return
        target_messages = []
        for msg in messages:
            if msg.webhook_id and "Zarlorek" in msg.content:
                target_messages.append(msg)
        await ctx.respond(f"Since <t:1781933940:f>, Cam has died **{target_messages.__len__()}** times.")

def setup(bot):
    bot.add_cog(Fun(bot))
