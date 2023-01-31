import datetime

from typing import DefaultDict, List

from twitchio.ext import commands
from twitchio.ext.commands.core import Command

import config

import planning


def assert_user_is_mod(ctx):
    if not ctx.author.is_mod:
        raise Exception(f"User {ctx.author.name} executed unauthorized command {ctx.command.name}")


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=config.TWITCH_CHAT_TOKEN,
                         prefix='!',
                         nick="DiFFtY",
                         initial_channels=['piquetdestream'])
        
    async def event_ready(self):
        print(f'Logged in as | {self.nick}')

    @commands.command()
    async def setnexttitle(self, ctx: commands.Context):
        assert_user_is_mod(ctx)

        next_show = planning.find_next_show(datetime.datetime.now())

        for channel in self.connected_channels:
            await channel.send(f'!settitle {next_show["title"]} avec {next_show["streamer"]}')

    @commands.command(aliases=["lasuite", "suite", "ensuite", "next"])
    async def nextup(self, ctx: commands.Context):
        next_show = planning.find_next_show(datetime.datetime.now())
        start_time_str = str(next_show["start"].hour).zfill(2) + "h" + str(next_show["start"].minute).zfill(2)
        end_time_str = str(next_show["end"].hour).zfill(2) + "h" + str(next_show["end"].minute).zfill(2)
        await ctx.send(f'Prochain live : "{next_show["title"]}" avec {next_show["streamer"]} de {start_time_str} à {end_time_str} !')


if __name__ == "__main__":
    bot = Bot()
    bot.run()
