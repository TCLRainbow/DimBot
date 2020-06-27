import logging

import discord
from discord.ext import commands

import dimsecret


class Missile:

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if dimsecret.debug:
            self.lvl = logging.DEBUG
        else:
            self.lvl = logging.INFO
        self.guild = None
        self.bottyland = None
        self.newsfeed = None
        self.announcement = None
        self.loop = False
        self.new = True  # For DimBot change activity loop

    def get_logger(self, name: str):
        logger = logging.getLogger(name)
        logger.setLevel(self.lvl)
        ch = logging.StreamHandler()
        ch.setLevel(self.lvl)
        preformat = f'[{logger.name}]'
        ch.setFormatter(logging.Formatter(fmt=preformat + ' [%(threadName)s/%(levelname)s] [%(asctime)s] %(message)s',
                                          datefmt='%H:%M:%S'))
        logger.addHandler(ch)
        return logger

    @staticmethod
    async def append_message(msg: discord.Message, append_content: str, delimiter: str = '\n'):
        await msg.edit(content=f'{msg.content}{delimiter}{append_content}')
