import pathlib
from dotenv import load_dotenv

import math
import json
import datetime
import pytz
import asyncio

import discord
from discord.ext import commands, tasks
from discord.abc import GuildChannel
from discord.commands.permissions import default_permissions

"""
TO-DO LIST

* Check every single commands' readability
    [ ] - update_schedule
    [ ] - delete_schedule
    [ ] - list_schedule

* Standardize the format of each message
    * Error message (``self._EM()``)
    * Datetime message
    * Command specific message

"""

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DIR = 'data/event'
        if pathlib.Path.is_file(pathlib.Path(f"{DIR}/base_data.json")) == False:
            base_data = {
                "total_id": 0
            }
            pathlib.Path.touch(pathlib.Path(f"{DIR}/base_data.json"))
            with open(f"{DIR}/base_data.json", 'w') as f:
                json.dump(base_data, f)

            
        self.update_schedule.start()
        #self.update_missing_file.start()

    def _EM(self, message, is_time):
        temp_str = f""""""
        if is_time == True:
            temp_str += f"TIME: {datetime.datetime.now(tz=pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%dT %H:%M:%S")}\n"
        temp_str += f"ERROR ENCOUNTER: {message}"
        return temp_str

    # LATER CLEAN
    # Task: check the remaining files are qualified to send, and delete the file if valid
    @tasks.loop(seconds=5)
    async def update_schedule(self): 
        try:
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
                    tzinfo=pytz.timezone(data["timezone"])
                )
                current_time = datetime.datetime.now(tz=pytz.timezone(data["timezone"]))
                current_time = current_time.replace(tzinfo=pytz.timezone(data["timezone"]))

                """
                print(f"File name   : {file_name}")
                print(f"Current time: {current_time}")
                print(f"Target time : {target_time}")
                """

                if target_time < current_time:
                    channel = (self.bot.get_channel(data["channel_id"]) or await self.bot.fetch_channel(data["channel_id"]))
                    pathlib.Path.unlink(pathlib.Path(f"{DIR}/{file_name.name}"))
                    await channel.send(data["context"])
        except:
           print(self._EM("Cannot send message", 0))



    # LATER CLEAN
    # Create scheduled message
    @discord.slash_command(
        name="create_schedule",
        description="Create a scheduled message to send out. (s_date = YYYY-MM-DD, s_time = HH:MM)",
    )
    @default_permissions(administrator=True)
    async def create_schedule_command(
        self, 
        ctx, 
        selected_date: discord.Option(
            str, 
            description="Date setting. (format: YYYY/MM/DD)"
        ),
        selected_time: discord.Option(
            str, 
            description="Time setting. (format: HH:MM)"
        ),  
        selected_channel: discord.Option(
            GuildChannel, 
            description="Channel setting."
        ),
        selected_context: discord.Option(
            str, 
            required=False,
            default=None, 
            description="Context setting. (Currently only support single line message in argument)"
        ),
        selected_timezone: discord.Option(
            str, 
            required=False,
            default="America/Toronto", 
            description="Timezone setting. (format: tz database)"
        )
    ):
        

        bot_id = self.bot.user.id
        bot_member = ctx.channel.guild.get_member(bot_id)
        if not discord.Permissions.view_channel in ctx.channel.permissions_for(bot_member):
            print(self. _EM("Missing ``View Channel`` permissions.", 1))
            await ctx.respond(self. _EM("Missing ``View Channel`` permissions.", 0), ephemeral=True)
            return
            
        try:

            def _checker(received):
                return ctx.author == received.author and ctx.channel == received.channel

            if selected_context == None:
                await ctx.respond(f"Send needed message below this message (Timeout: ``1 minute``)", ephemeral=True)
                _msg = await self.bot.wait_for('message', timeout=60.0, check=_checker)
                selected_context = _msg.content
                await _msg.delete()

            target_time = datetime.datetime(
                year=int(selected_date[0:4]), 
                month=int(selected_date[5:7]), 
                day=int(selected_date[8:10]), 
                hour=int(selected_time[0:2]), 
                minute=int(selected_time[3:5]), 
                tzinfo=pytz.timezone(selected_timezone)
            )

            DIR = 'data/event'
            base_data = 0
            data = 0

            with open(f"{DIR}/base_data.json", "r") as f:
                base_data = json.load(f)
            base_data["total_id"] += 1
            with open(f"{DIR}/base_data.json", "w") as f:
                json.dump(base_data, f)

            data = {
                "schedule_id": base_data["total_id"],
                "date": selected_date,
                "time": selected_time,
                "timezone": selected_timezone,
                "context": selected_context,
                "channel_id": selected_channel.id
            }

            pathlib.Path.touch(pathlib.Path(f"{DIR}/event_{base_data["total_id"]:04d}.json"))
            with open(f"{DIR}/event_{base_data["total_id"]:04d}.json", 'w') as f:
                json.dump(data, f, indent=4, default=str) 

            self.update_schedule.restart()
        except asyncio.TimeoutError:            
            print(self. _EM("Bot timed out due to no message been sent.", 1))
            await ctx.respond(self. _EM("Bot timed out due to no message been sent.", 0), ephemeral=True)
            return
        except:
            print(self. _EM("The command got an unexpected error.", 1))
            await ctx.respond(self. _EM("The command got an unexpected error.", 0), ephemeral=True)
            return
        else:
            respond_message = f"Scheduled message created to be sent at **{target_time.strftime("%Y-%m-%dT %H:%M:%S %Z%z")}**.\n**Context**:\n{selected_context}"
            await ctx.respond(respond_message, ephemeral=True)

    # Delete scheduled message
    @discord.slash_command(
        name="delete_schedule",
        description="Delete a scheduled message." 
    )
    @default_permissions(administrator=True)
    async def delete_schedule_command(
        self, 
        ctx, 
        selected_id: discord.Option(
            int, 
            description="Scheduled message ID selection."
        )
    ):
        self.update_schedule.restart()
        DIR = 'data/event'
        try: 
            pathlib.Path.unlink(pathlib.Path(f"{DIR}/event_{selected_id:04d}.json"))
            await ctx.respond(f"Scheduled message (id: ``{selected_id}``) has been removed.", ephemeral=True)
        except:
            print(self. _EM("The selected event does not exist.", 1))
            await ctx.respond(self. _EM("The selected event does not exist.", 0), ephemeral=True)
            return
                 

    # List scheduled messages
    @discord.slash_command(
        name="list_schedule",
        description="List out scheduled messages." 
    )
    @default_permissions(administrator=True)
    async def list_schedule_command(
        self, 
        ctx, 
        selected_page: discord.Option(
              int, 
              description="Page selection."
        )

    ):
        self.update_schedule.restart()
        DIR = 'data/event'
        files = []
        for file_name in pathlib.Path(DIR).rglob("*"):
            if file_name.name == "base_data.json":
                continue
            files.append(file_name.name)

        max_page = math.ceil(len(files)/10.0)
        if selected_page > max_page or selected_page < 1: 
            print(self. _EM("the selected page is out of bound.", 1))
            await ctx.respond(self. _EM("the selected page is out of bound.", 0), ephemeral=True)
            return

        formated_list = f""""""
        formated_list += (f"List of scheduled message:\n")
        for i in range((selected_page - 1) * 10, min(len(files), selected_page * 10)):
            with open(f"{DIR}/{files[i]}", 'r') as f:
                detailed_context = json.load(f)["context"]
            formated_list += (f"Message id: ``{int(files[i][6:10])}``\n**Context**: \n{detailed_context}\n\n")
        formated_list += (f"``Page {selected_page}/{max_page}``\n")
        await ctx.respond(formated_list)
            


def setup(bot):
    bot.add_cog(Event(bot))
