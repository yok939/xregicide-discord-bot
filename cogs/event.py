import os
import pathlib
from discord.abc import GuildChannel
from discord.commands.permissions import default_permissions
from dotenv import load_dotenv

import math
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
        DIR = 'data/event'
        if pathlib.Path.is_file(pathlib.Path(f"{DIR}/base_data.json")) == False:
            base_data = {
                "total_id": 0
            }
            pathlib.Path.touch(pathlib.Path(f"{DIR}/base_data.json"))
            with open(f"{DIR}/base_data.json", 'w') as f:
                json.dump(base_data, f)
            
        #self.update_missing_file.start()

    # Task: check the remaining files are qualified to send, and delete the file if valid
    @tasks.loop(seconds=5)
    async def update_schedule(self): 
        DIR = 'data/event'
        files = pathlib.Path(DIR).rglob("*")
        target_time = datetime.datetime.now()
        current_time = datetime.datetime.now()
        for file_name in files:
            if file_name.name == "base_data.json":
                continue
            with open(f"{DIR}/{file_name.name}", 'r') as f:
                data = json.load(f) 
                target_time = datetime.datetime(
                    year=int(data["date"][0:4]), 
                    month=int(data["date"][5:7]), 
                    day=int(data["date"][8:10]), 
                    hour=int(data["time"][0:2]), 
                    minute=int(data["time"][3:5]), 
                    tzinfo=zoneinfo.ZoneInfo(data["timezone"])
                )
            current_time = current_time.replace(tzinfo=zoneinfo.ZoneInfo(data["timezone"]))
            if target_time < current_time:
                channel = self.bot.get_channel(data["channel_id"])
                pathlib.Path.unlink(pathlib.Path(f"{DIR}/{file_name.name}"))
                await channel.send(data["context"])


    # Create scheduled message
    @discord.slash_command(
        name="create_schedule",
        description="Create a scheduled message to send out. (s_date = YYYY-MM-DD, s_time = HH:MM)" 
    )
    @default_permissions(administrator=True)
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
            target_time = datetime.datetime(
                    year=int(selected_date[0:4]), 
                    month=int(selected_date[5:7]), 
                    day=int(selected_date[8:10]), 
                    hour=int(selected_time[0:2]), 
                    minute=int(selected_time[3:5]), 
                    tzinfo=zoneinfo.ZoneInfo(selected_timezone)
            )

            self.update_schedule.restart()
            DIR = 'data/event'
            base_data = 0
            data = 0

            with open(f"{DIR}/base_data.json", "r") as f:
                base_data = json.load(f)

            base_data["total_id"] += 1

            with open(f"{DIR}/base_data.json", "w") as f:
                json.dump(base_data, f)

            pathlib.Path.touch(pathlib.Path(f"{DIR}/event_{base_data["total_id"]:04d}.json"))
            data = {
                "schedule_id": base_data["total_id"],
                "date": selected_date,
                "time": selected_time,
                "timezone": selected_timezone,
                "context": selected_context,
                "channel_id": selected_channel.id
            }
            with open(f"{DIR}/event_{base_data["total_id"]:04d}.json", 'w') as f:
                json.dump(data, f, indent=4, default=str) 
            
        except:
            await ctx.respond(f"The time format is not valid.", ephemeral=True)
            return

        await ctx.respond(f"Scheduled message created at {target_time.strftime("%Y-%m-%dT%H:%M:%SZ")}.\nContext: ``{selected_context}``.", ephemeral=True)

    # Delete scheduled message
    @discord.slash_command(
        name="delete_schedule",
        description="Delete a scheduled message." 
    )
    @default_permissions(administrator=True)
    async def delete_schedule_command(self, 
                                      ctx, 
                                      selected_id: int):
            self.update_schedule.restart()
            DIR = 'data/event'
            try: 
                pathlib.Path.unlink(pathlib.Path(f"{DIR}/event_{selected_id:04d}.json"))
                await ctx.respond(f"Scheduled message (id: ``{selected_id}``) has been removed.", ephemeral=True)
            except:
                await ctx.respond(f"The selected event does not exist.", ephemeral=True)
                return
                 

    # List scheduled messages
    @discord.slash_command(
        name="list_schedule",
        description="List out scheduled messages." 
    )
    @default_permissions(administrator=True)
    async def list_schedule_command(self, 
                                    ctx, 
                                    selected_page: int):
            self.update_schedule.restart()
            DIR = 'data/event'
            files = []
            for file_name in pathlib.Path(DIR).rglob("*"):
                if file_name.name == "base_data.json":
                    continue
                files.append(file_name.name)

            max_page = math.ceil(len(files)/10.0)
            if selected_page > max_page or selected_page < 1: 
                await ctx.respond(f"The selected page is out of bound.", ephemeral=True)
                return

            formated_list = f""""""
            formated_list += (f"List of scheduled message.\n")
            for i in range((selected_page - 1) * 10, min(len(files), selected_page * 10)):
                with open(f"{DIR}/{files[i]}", 'r') as f:
                    detailed_context = json.load(f)["context"]
                formated_list += (f"* id: ``{int(files[i][6:10])}``, context: \"{detailed_context}\"\n")
            formated_list += (f"``Page {selected_page}/{max_page}``\n")
            await ctx.respond(formated_list, ephemeral=True)
            


def setup(bot):
    bot.add_cog(Event(bot))
