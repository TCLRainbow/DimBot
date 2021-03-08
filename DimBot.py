import asyncio
import re
from datetime import datetime
from random import choice
from typing import Union

import discord
from discord.ext import commands

import bitbay
import echo
import dimond
import dimsecret
import tribe
import raceline
from aegis import Aegis
from bruckserver import vireg
from ikaros import Ikaros
from missile import Missile

intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = intent.reactions = intent.voice_states = intent.typing = True
intent.presences = True


async def prefix_process(bot: commands.Bot, msg: discord.Message):
    tag_mention = re.search(f'^((<@.?{bot.user.id}> |DimBot), )', msg.content)
    if tag_mention:
        if Missile.is_rainbow(msg.author.id):
            return tag_mention.group(0)
        else:
            await msg.reply('Only my little pog champ can use authoritative orders!')
    return bot.default_prefix

bot = commands.Bot(command_prefix=prefix_process, intents=intent)
bot.default_prefix = 't.' if dimsecret.debug else 'd.'
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = echo.Bottas(bot)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.8"
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
    discord.Activity(name='Try not to crash', type=discord.ActivityType.competing),
    discord.Activity(name='Muzen train', type=discord.ActivityType.watching)
]
logger = bot.missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手の中にあります <https://streamlabs.com/pythonic_rainbow/tip>'
reborn_channel = None
try:
    with open('final', 'r') as fi:
        logger.info('Found final file')
        reborn_channel = int(fi.readline())
    import os
    os.remove('final')
except FileNotFoundError:
    logger.info('No previous final file found')


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(tribe.guild_id)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    if dimsecret.debug:
        bot.missile.announcement = bot.missile.bottyland  # In debug mode, rss,yt should send in bottyland
    else:
        bot.missile.announcement = bot.get_channel(425703064733876225)
    bot.missile.logs = bot.get_channel(384636771805298689)
    bot.missile.eggy = await bot.fetch_user(226664644041768960)
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            await guild.me.edit(nick=nickname)
    if reborn_channel:
        epilogue = "Arc-Cor𐑞: Reconnected with Discord, transform complete. Ready to kick some balls!\n" \
                   "https://data.whicdn.com/images/343444322/original.gif"
        await bot.get_channel(reborn_channel).send(epilogue)
    while True:
        logger.debug('Changed activity')
        await bot.change_presence(activity=choice(activities))
        await asyncio.sleep(300)


@bot.event
async def on_guild_join(guild: discord.Guild):
    await guild.me.edit(nick=nickname)


@bot.event
async def on_message_delete(msg: discord.Message):
    if msg.author == msg.guild.me or msg.content.startswith(await prefix_process(bot, msg)):
        return
    if msg.guild and msg.id in bot.missile.ghost_pings.keys():
        for m in bot.missile.ghost_pings[msg.id]:
            await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
        bot.missile.ghost_pings.pop(msg.id)
    elif msg.guild and msg.mentions and not msg.edited_at:
        for m in msg.mentions:
            if not m.bot:
                await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    bot.missile.snipe.colour = msg.embeds[0].colour if msg.embeds else Missile.random_rgb()


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.guild and not before.edited_at and before.mentions:
        bot.missile.ghost_pings[before.id] = [m for m in before.mentions if not m.bot]
    if before.guild and before.id in bot.missile.ghost_pings.keys():
        has_removed = False
        for m in bot.missile.ghost_pings[before.id]:
            if m not in after.mentions:
                has_removed = True
                await m.send(f'{before.author.mention} pinged you in **{before.guild.name}** and deleted it.')
                bot.missile.ghost_pings[before.id].remove(m)
        if has_removed:
            await before.channel.send(before.author.mention + ' has removed a ping from a message')
        if not bot.missile.ghost_pings[before.id]:
            bot.missile.ghost_pings.pop(before.id)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.reply('Stoopid. That is not a command.')
        return
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole) \
            or isinstance(error, commands.errors.CommandOnCooldown) or isinstance(error, commands.errors.UserNotFound) \
            or isinstance(error, commands.errors.MemberNotFound) or isinstance(error, commands.errors.MissingPermissions):
        await ctx.reply(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):
        await ctx.reply('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure) or isinstance(error, asyncio.TimeoutError):
        return
    raise error


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    from platform import python_version
    from boto3 import __version__ as boto3ver
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}** | Python: `{python_version()}` | Discord.py: `{discord.__version__}` | '
        f'boto3: `{boto3ver}`\nBot source code: https://github.com/TCLRainbow/DimBot\n'
        f'Bot module descriptions have been moved to `{bot.default_prefix}help <module name>`\n'
        f'Devblog: Instagram @techdim\nDiscord server: `6PjhjCD`\n\n{sponsor_txt}'
    )


@bot.command()
async def sponsor(ctx):
    await ctx.send(sponsor_txt)


@bot.command()
async def noel(ctx):
    """Listens to my heartbeat"""
    msg = await ctx.reply(f':heartbeat: {bot.latency * 1000:.3f}ms')
    tic = datetime.now()
    await msg.add_reaction('📡')
    toc = datetime.now()
    await msg.edit(content=msg.content + f' :satellite_orbital: {(toc - tic).total_seconds() * 1000:.3f}ms')


@bot.group()
async def link(ctx):
    pass


@link.command()
async def forge(ctx):
    msg = await bot.missile.ask_msg(ctx, 'Reply `Minecraft version-Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    mc = await bot.missile.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.missile.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


@bot.command()
async def snipe(ctx):
    await ctx.send(embed=bot.missile.snipe)


@bot.group(invoke_without_command=True)
async def arccore(ctx):
    pass


@arccore.command()
@Missile.is_rainbow_cmd_check()
async def off(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **OFF**\nhttps://pbs.twimg.com/media/ED4Ia8AWkAMcXvK.jpg')
    await bot.logout()


@arccore.command()
@Missile.is_rainbow_cmd_check()
async def transform(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **TRANSFORM**\nInitiating update and restart operations!')
    with open('final', 'w') as death_note:
        death_note.write(str(ctx.channel.id))
    logger.critical('RESTARTING')
    import subprocess
    subprocess.Popen(['sudo systemctl restart dimbot'], shell=True)


@bot.command()
@Missile.is_rainbow_cmd_check()
async def sch(ctx, ch: Union[discord.TextChannel, discord.User]):
    bot.missile.sch = ch


@bot.command()
@Missile.is_rainbow_cmd_check()
async def say(ctx, *, msg: str):
    await bot.missile.sch.send(msg)


@bot.command()
@Missile.is_rainbow_cmd_check()
async def shadow(c, *, cmd: str):
    msg = await bot.missile.sch.send('⠀')
    msg.content = bot.default_prefix + cmd
    msg.author = msg.guild.get_member(bot.owner_id)
    await bot.invoke(await bot.get_context(msg))


# Eggy requested this command
@bot.command()
async def hug(ctx):
    gif = choice(['https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
                  'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
                  'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958'])
    await ctx.send(f'{gif}\nIn memory of our friendship, {bot.missile.eggy}\nHug {ctx.author.mention}')


bot.add_cog(raceline.Ricciardo(bot))
bot.add_cog(tribe.Hamilton(bot))
bot.add_cog(vireg.Verstapen(bot))
bot.add_cog(bot.echo)
bot.add_cog(bitbay.BitBay(bot))
bot.add_cog(dimond.Dimond(bot))
bot.add_cog(Ikaros(bot))
bot.add_cog(Aegis(bot))
bot.run(dimsecret.discord)
