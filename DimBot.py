import asyncio
import atexit
from random import choice

import discord
from discord.ext import commands

import bottas
import dimsecret
import hamilton
import norris
import ricciardo
from bruckserver import verstapen, albon
from missile import Missile

intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = True
bot = commands.Bot(command_prefix='d.', intents=intent)
bot.missile = Missile(bot)
bot.echo = bottas.Bottas(bot)
nickname = "DimBot | 0.6.11"
activities = [
    discord.Activity(name='Echo', type=discord.ActivityType.listening),
    discord.Activity(name='YOASOBI ❤', type=discord.ActivityType.listening),
    discord.Activity(name='Sam yawning', type=discord.ActivityType.listening),
    discord.Activity(name='Lokeon', type=discord.ActivityType.listening),
    discord.Activity(name='Ricizus screaming', type=discord.ActivityType.listening),
    discord.Activity(name='Rainbow codes', type=discord.ActivityType.watching),
    discord.Activity(name='Matt plays R6', type=discord.ActivityType.watching),
    discord.Activity(name='Rainbow laughs', type=discord.ActivityType.watching),
    discord.Activity(name='comics', type=discord.ActivityType.watching),
    discord.Activity(name='Terry coughing', type=discord.ActivityType.listening),
    discord.Activity(name='Bruck sleeps', type=discord.ActivityType.watching),
    discord.Activity(name='Try not to crash', type=discord.ActivityType.competing)
]
logger = bot.missile.get_logger('DimBot')
with open('.git/HEAD', 'r') as f:
    branch = f.readline().split('/')[-1]


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    from platform import python_version
    from boto3 import __version__ as boto3ver
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}** | Debug mode: **{dimsecret.debug}** | Branch: **{branch}**\n'
        f'This bot is coded with the programming language Python `{python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`, '
        f'Amazon Web Services via boto3 `{boto3ver}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n\n'
        'This bot has the following modules:\n'
        f'**Project Ricciardo** `{ricciardo.__version__}`: Relaying RSS to discord channels.\n'
        f'**Project Bottas** `{bottas.__version__}`: Add or search quotes through a SQLite database.\n'
        f'**Project Hamilton** `{hamilton.__version__}`: Adds additional feature per role\n'
        f'**Project Verstapen** `{verstapen.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Albon** `{albon.__version__}`: HTTP server sub-project used by `Vireg`.\n'
        f'**Project Norris** `{norris.__version__}` : Chat bot for answering BBM questions\n'
    )


def is_debug(ctx):
    return dimsecret.debug


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    if dimsecret.debug:
        bot.missile.announcement = bot.missile.bottyland
        status = discord.Status.idle
    else:
        bot.missile.announcement = bot.get_channel(425703064733876225)
        status = discord.Status.online
    bot.missile.logs = bot.get_channel(384636771805298689)
    logger.info(f'Guild count: {len(bot.guilds)}')
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            await guild.me.edit(nick=nickname)
    if bot.missile.new:
        bot.missile.new = False
        while True:
            logger.debug('Changed activity')
            await bot.change_presence(status=status, activity=choice(activities))
            await asyncio.sleep(300)


@bot.event
async def on_disconnect():
    bot.missile.new = True


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.BadArgument):
        await ctx.send('Bad argument.')


@bot.command()
@commands.check(Missile.is_rainbow)
async def exit(ctx):
    import builtins
    await bot.change_presence(status=discord.Status.dnd)
    await ctx.send(':dizzy_face:')
    builtins.exit()


def exit_handler():
    bot.echo.db.commit()


atexit.register(exit_handler)
bot.add_cog(ricciardo.Ricciardo(bot))
bot.add_cog(hamilton.Hamilton(bot))
bot.add_cog(verstapen.Verstapen(bot))
bot.add_cog(bot.echo)
bot.add_cog(norris.Norris(bot))
bot.run(dimsecret.discord)
