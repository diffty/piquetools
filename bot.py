import datetime
import asyncio

from typing import DefaultDict, List

from twitchio.ext import commands
from twitchio.ext.commands.core import Command

import config

import planning


AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW = 5 * 60
AUTO_UPDATE_TIME = 3 * 60


def assert_user_is_mod(ctx):
    if not ctx.author.is_mod:
        raise Exception(f"User {ctx.author.name} executed unauthorized command {ctx.command.name}")


class Bot(commands.Bot):
    def __init__(self):
        self.time_before_next_auto_check = 0
        self.running = False

        next_show = planning.find_next_show(datetime.datetime.now())

        if next_show is not None and planning.time_before_show(next_show) < AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW:
            self.time_before_next_auto_check = AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW
        
        super().__init__(token=config.TWITCH_CHAT_TOKEN,
                         prefix='!',
                         nick="DiFFtY",
                         initial_channels=['diffty'])
        
    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        task = asyncio.get_event_loop().create_task(self.autochecker_loop())

    @commands.command()
    async def autoupdatetitle(self, ctx: commands.Context):
        assert_user_is_mod(ctx)
        await self.auto_update_title()

    @commands.command(aliases=["lasuite", "suite", "ensuite", "next"])
    async def nextup(self, ctx: commands.Context):
        next_show = planning.find_next_show(datetime.datetime.now())
        await ctx.send(self.get_announce_for_next_show(next_show))

    async def auto_update_title(self):
        next_show = planning.find_next_show(datetime.datetime.now())

        if next_show is not None and planning.time_before_show(next_show) < AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW:
            await self.update_title_for_show(next_show)
        else:
            curr_show = planning.find_current_show(datetime.datetime.now())
            if curr_show:
                await self.update_title_for_show(curr_show)
            elif next_show is not None:
                await self.update_title_for_show(next_show)
        
    async def update_title_for_show(self, show: dict):
        for channel in self.connected_channels:
            await channel.send(f'!settitle {show["title"]} avec {show["streamer"]} !dons')
        
    def get_announce_for_next_show(self, show: dict):
        return f'Prochain live : {self.get_announce_from_show_data(show)}'
        
    def get_announce_from_show_data(self, show: dict):
        start_time_str = str(show["start"].hour).zfill(2) + "h" + str(show["start"].minute).zfill(2)
        end_time_str = str(show["end"].hour).zfill(2) + "h" + str(show["end"].minute).zfill(2)
        return f'"{show["title"]}" avec {show["streamer"]} de {start_time_str} à {end_time_str} !'
    
    async def autochecker_loop(self):
        if not self.running:
            self.running = True
        
        while self.running:
            print(f"Waiting {self.time_before_next_auto_check}s before next check.")
            await asyncio.sleep(self.time_before_next_auto_check)

            next_show = planning.find_next_show(datetime.datetime.now())
            print(f"Next show will begin in {planning.time_before_show(next_show)}.")
            
            if next_show is not None and planning.time_before_show(next_show) < AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW:
                await self.auto_update_title()
                self.time_before_next_auto_check = AUTO_UPDATE_TIME_BEFORE_NEXT_SHOW
            else:
                self.time_before_next_auto_check = AUTO_UPDATE_TIME
    
    
if __name__ == "__main__":
    bot = Bot()
    bot.run()
