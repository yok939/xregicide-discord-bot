import os
import pathlib
from discord.abc import GuildChannel
from dotenv import load_dotenv

import json
import datetime
import typing
import zoneinfo

import discord
from discord.ext import commands, tasks


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_schedule.start()
        self.update_missing_file.start()

    # Task: check the remaining files are qualified to send, and delete the file if valid
    @tasks.loop(seconds=20)
    async def update_schedule(self): 
        DIR = 'data/event'
        files = os.listdir(DIR)
        target_time = datetime.datetime.now()
        current_time = datetime.datetime.now()
        for name in files:
            with open(f"{DIR}/{name}", 'r') as f:
                data = json.load(f) 
                target_time = datetime.datetime(year=int(data["date"][0:4]), 
                                                month=int(data["date"][5:7]), 
                                                day=int(data["date"][8:10]), 
                                                hour=int(data["time"][0:2]), 
                                                minute=int(data["time"][3:5]), 
                                                tzinfo=zoneinfo.ZoneInfo(data["timezone"]))
            current_time = current_time.replace(tzinfo=zoneinfo.ZoneInfo(data["timezone"]))
            if target_time < current_time:
                channel = self.bot.get_channel(data["channel_id"])
                pathlib.Path.unlink(pathlib.Path(f"{DIR}/{name}"))
                await channel.send(data["context"])

    # Task: check the missing files in 'data/event' folder, and changing the remaining files to fill up the gap
    @tasks.loop(seconds=10)
    async def update_missing_file(self):
        DIR = 'data/event'
        files = os.listdir(DIR)
        j = 0
        for name in files:
            if name == f"event_{j:04d}":
                continue
            data = ""
            with open(f"{DIR}/{name}", 'r') as f:
                data = json.load(f) 
            pathlib.Path.unlink(pathlib.Path(f"{DIR}/{name}"))
            pathlib.Path.touch(pathlib.Path(f"{DIR}/event_{j:04d}"))
            with open(f"{DIR}/event_{j:04d}", 'r') as f:
                json.dump(f, data) 
            j += 1

    # Create scheduled message
    @discord.slash_command(
        name="create_schedule",
        description="Create a scheduled message to send out. (s_date = YYYY-MM-DD, s_time = HH:MM)"
    )
    async def create_schedule_command(self, 
                                      ctx, 
                                      selected_date: str, 
                                      selected_time: str,  
                                      selected_channel: GuildChannel, 
                                      selected_context: str,
                                      selected_timezone: typing.Optional[str] = None):
        
        if selected_timezone == None:
            selected_timezone = "America/Toronto"

        try:
            target_time = datetime.datetime(year=int(selected_date[0:4]), 
                                            month=int(selected_date[5:7]), 
                                            day=int(selected_date[8:10]), 
                                            hour=int(selected_time[0:2]), 
                                            minute=int(selected_time[3:5]), 
                                            tzinfo=zoneinfo.ZoneInfo(selected_timezone))
            data = {
                "date": selected_date,
                "time": selected_time,
                "timezone": selected_timezone,
                "context": selected_context,
                "channel_id": selected_channel.id
            }
            DIR = 'data/event'
            total_amount = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
            pathlib.Path.touch(pathlib.Path(f"{DIR}/event_{total_amount:04d}"))
            with open(f"{DIR}/event_{total_amount:04d}", 'w') as f:
                json.dump(data, f, indent=4, default=str) 

        except:
            await ctx.respond(f"The time format is not valid.", ephemeral=True)
            return


        await ctx.respond(f"Scheduled message created at {target_time.strftime("%Y-%m-%dT%H:%M:%SZ")}.\nContext: ``{selected_context}``.", ephemeral=True)

def setup(bot):
    bot.add_cog(Event(bot))
