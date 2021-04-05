import asyncio
from datetime import datetime
from random import choice, randint
from typing import Union

import discord
from discord.ext import commands

import dimond
import dimsecret
import raceline
import tribe
from bitbay import BitBay
from bruckserver.vireg import Verstapen
from echo import Bottas
from missile import Missile, dim_id
from mod.aegis import Aegis
from mod.ikaros import Ikaros

# Variables needed for initialising the bot
intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = intent.reactions = intent.voice_states = intent.typing = True
intent.presences = True
bot = commands.Bot(command_prefix=Missile.prefix_process, intents=intent)
bot.default_prefix = 't.' if dimsecret.debug else 'd.'
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = Bottas(bot)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.8.18.3"
# List of activities that will be randomly displayed every 5 minutes
activities = [
    discord.Activity(name='Echo', type=discord.ActivityType.listening),
    discord.Activity(name='YOASOBI ❤', type=discord.ActivityType.listening),
    discord.Activity(name='Sam yawning', type=discord.ActivityType.listening),
    discord.Activity(name='Lokeon', type=discord.ActivityType.listening),
    discord.Activity(name='Ricizus screaming', type=discord.ActivityType.listening),
    discord.Activity(name='Dim codes', type=discord.ActivityType.watching),
    discord.Activity(name='Matt plays R6', type=discord.ActivityType.watching),
    discord.Activity(name='Dim laughs', type=discord.ActivityType.watching),
    discord.Activity(name='comics', type=discord.ActivityType.watching),
    discord.Activity(name='Terry coughing', type=discord.ActivityType.listening),
    discord.Activity(name='Bruck sleeps', type=discord.ActivityType.watching),
    discord.Activity(name='Try not to crash', type=discord.ActivityType.competing),
    discord.Activity(name='Muzen train', type=discord.ActivityType.watching),
    discord.Activity(name="Heaven's Lost Property", type=discord.ActivityType.watching)
]
logger = bot.missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手の中にあります <https://streamlabs.com/pythonic_rainbow/tip> <https://www.patreon.com/ChingDim>'
reborn_channel = None


async def binvk(ctx: commands.Context):
    a = randint(1, 100)
    if a <= 20:
        if a <= 10:
            await ctx.send(sponsor_txt)
        else:
            await ctx.send('Rest in peace for those who lost their lives in the Taiwan train derail accident.')
    bot.missile.invoke_time = datetime.now()


bot.before_invoke(binvk)


async def ainvk(ctx: commands.Context):
    timedelta = (datetime.now() - bot.missile.invoke_time).total_seconds() * 1000
    await bot.get_channel(666431254312517633).send(f'**{ctx.command}**: {timedelta}ms')


bot.after_invoke(ainvk)

try:
    # If the bot is restarting, read the channel ID that invoked the restart command
    with open('final', 'r') as fi:
        logger.info('Found final file')
        reborn_channel = int(fi.readline())
    import os

    os.remove('final')
except FileNotFoundError:
    logger.info('No previous final file found')


@bot.event
async def on_message(msg: discord.Message):
    if msg.guild:
        if msg.content == msg.guild.me.mention:
            await msg.channel.send(f'My prefix is **{bot.default_prefix}**')
            return
        dim = msg.guild.get_member(dim_id)
        if dim and dim in msg.mentions and not msg.author.bot and dim.status != discord.Status.online:
            await msg.reply('My master is away atm.')
    elif msg.content == bot.user.mention:
        await msg.channel.send(f'My prefix is **{bot.default_prefix}**')
        return
    await bot.process_commands(msg)


@bot.event
async def on_ready():
    """Event handler when the bot has connected to the Discord endpoint"""
    # First, fetch all the special objects
    bot.missile.eggy = await bot.fetch_user(226664644041768960)
    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            bot.loop.create_task(guild.me.edit(nick=nickname))
    if reborn_channel:
        await bot.get_channel(reborn_channel).send("Arc-Cor𐑞: Pandora complete.")
    while True:
        logger.debug('Changed activity')
        await bot.change_presence(activity=choice(activities))
        await asyncio.sleep(300)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Updates DimBot's nickname in new servers"""
    await guild.me.edit(nick=nickname)


@bot.event
async def on_message_delete(msg: discord.Message):
    """Event handler when a message has been deleted"""
    if msg.author == msg.guild.me or msg.content.startswith(await Missile.prefix_process(bot, msg)):
        return
    # Stores the deleted message for snipe command
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    bot.missile.snipe.colour = msg.embeds[0].colour if msg.embeds else Missile.random_rgb()


@bot.event
async def on_command_error(ctx, error):
    """Event handler when a command raises an error"""
    if isinstance(error, commands.errors.CommandNotFound):  # Human error
        await ctx.reply('Stoopid. That is not a command.')
        return
    # Human error
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole) \
            or isinstance(error, commands.errors.CommandOnCooldown) or isinstance(error, commands.errors.UserNotFound) \
            or isinstance(error, commands.errors.MemberNotFound) or isinstance(error,
                                                                               commands.errors.MissingPermissions):
        await ctx.reply(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):  # Human error
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):  # Human error
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):  # Could be a human/program error
        await ctx.reply('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure):
        return
    raise error  # This is basically "unknown error", raise it for debug purposes


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    """Displays bot information"""
    from platform import python_version
    embed = discord.Embed(title=sponsor_txt,
                          description='Bot module descriptions have been moved to '
                                      f'`{bot.default_prefix}help <module name>`',
                          color=discord.Colour.random())
    embed.add_field(name='Guild count', value=str(len(bot.guilds)))
    embed.add_field(name='Uptime', value=datetime.now() - bot.missile.boot_time)
    embed.add_field(name='Python', value=python_version())
    embed.add_field(name='Discord.py', value=discord.__version__)
    embed.add_field(name='Codename', value='Barbados')
    embed.add_field(name='Devblog', value='[Instagram](http://www.instagram.com/techdim)')
    embed.add_field(name='Source code', value='[GitHub](http://github.com/TCLRainbow/DimBot)')
    embed.add_field(name='Discord server', value='[6PjhjCD](http://discord.gg/6PjhjCD)')
    await ctx.send(embed=embed)


@bot.command()
async def sponsor(ctx):
    """$.$"""
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
    """Commands for generating links"""
    pass


@link.command()
async def forge(ctx):
    """Generating MinecraftForge installer links"""
    msg = await bot.missile.ask_msg(ctx, 'Reply `Minecraft version`-`Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    """Generating Galaticraft mod download links"""
    mc = await bot.missile.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.missile.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


@bot.command()
async def snipe(ctx):
    """Displays the last deleted message"""
    await ctx.send(embed=bot.missile.snipe)


@bot.group()
@Missile.is_rainbow_cmd_check()
async def arccore(ctx):
    """Confidential"""
    pass


@arccore.command()
async def stealth(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **Stealth**')
    await bot.logout()


@arccore.command()
async def pandora(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **PANDORA**, self-evolving!')
    with open('final', 'w') as death_note:
        death_note.write(str(ctx.channel.id))
    logger.critical('RESTARTING')
    import subprocess
    subprocess.Popen(['sudo systemctl restart dimbot'], shell=True)


@arccore.command()
async def sch(ctx, ch: Union[discord.TextChannel, discord.User]):
    bot.missile.sch = ch


@arccore.command()
async def say(ctx, *, msg: str):
    await bot.missile.sch.send(msg)


@arccore.command()
async def shadow(c, *, cmd: str):
    msg = await bot.missile.sch.send('⠀')
    msg.content = bot.default_prefix + cmd
    msg.author = msg.guild.get_member(dim_id)
    await bot.invoke(await bot.get_context(msg))


# Eggy requested this command
@bot.command()
async def hug(ctx):
    """Hugs you"""
    gif = choice(['https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
                  'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
                  'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958'])
    await ctx.send(f'{gif}\nIn memory of our friendship, {bot.missile.eggy}\nHug {ctx.author.mention}')


@bot.command(aliases=['color'])
async def colour(ctx, a: str = None, *args):
    """Shows info about the color"""
    if not a:
        a = str(randint(1, 0xFFFFFF))
    try:
        is_hex = a[0] == '#'
        if is_hex:
            colour = discord.Colour(int(a[1:], 16))
        elif a.lower() == 'rgb':
            colour = discord.Colour.from_rgb(int(Missile.ensure_index_value(args, 0, 0)),
                                             int(Missile.ensure_index_value(args, 1, 0)),
                                             int(Missile.ensure_index_value(args, 2, 0)))
        elif a.lower() == 'hsv':
            colour = discord.Colour.from_hsv(int(Missile.ensure_index_value(args, 0, 0)),
                                             int(Missile.ensure_index_value(args, 1, 0)),
                                             int(Missile.ensure_index_value(args, 2, 0)))
        else:
            colour = discord.Colour(int(a))
        emb = discord.Embed(title=a if is_hex else f'#{colour.value:X}', color=colour)
        emb.add_field(name='R', value=colour.r)
        emb.add_field(name='G', value=colour.g)
        emb.add_field(name='B', value=colour.b)
        await ctx.reply(embed=emb)
    except ValueError:
        await ctx.reply('Invalid color. You can input an integer `2048` , a hex code `#ABCABC`, or a RGB/HSV '
                        'combination `rgb/hsv <> <> <>`')


async def ready_tasks():
    bot.add_cog(raceline.Ricciardo(bot))
    bot.add_cog(Verstapen(bot))
    bot.add_cog(bot.echo)
    bot.add_cog(BitBay(bot))
    bot.add_cog(dimond.Dimond(bot))
    bot.add_cog(Ikaros(bot))
    bot.add_cog(Aegis(bot))
    await bot.wait_until_ready()
    bot.add_cog(tribe.Hamilton(bot))


bot.loop.create_task(ready_tasks())
bot.run(dimsecret.discord)
