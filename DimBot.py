import asyncio
import time
from datetime import datetime, timedelta
from random import choice, randint
from typing import Union

import aiosql
import discord
import psutil
from discord.ext import commands
from discord.ext.commands import errors

import dimond
import dimsecret
import missile
import tribe
import os
# from bruckserver.vireg import Verstapen
from diminator.cog import Diminator
from diminator.obj import BasePPException
from echo import Bottas
from hyperstellar import Hyperstellar
from mod.aegis import Aegis
from mod.ikaros import Ikaros
from nene import Nene
from raceline import Ricciardo
# from skybow import SkyBow
from xp import XP

# Variables needed for initialising the bot
intent = discord.Intents()
intent.value = 0b1111110000011  # https://discord.com/developers/docs/topics/gateway#list-of-intents
bot = missile.Bot(intents=intent)
logger = missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手にある <https://streamlabs.com/pythonic_rainbow/tip> <https://www.patreon.com/ChingDim>'
reborn_channel = None
last_modified = int(os.path.getmtime('DimBot.py'))

try:
    # If the bot is restarting, read the channel ID that invoked the restart command
    with open('final', 'r') as fi:
        logger.info('Found final file')
        reborn_channel = int(fi.readline())
    import os

    os.remove('final')
except FileNotFoundError:
    logger.info('No previous final file found')


@bot.before_invoke
async def b_invoke(ctx: commands.Context):
    if randint(1, 100) <= 5:
        await ctx.send(sponsor_txt)


@bot.after_invoke
async def a_invoke(ctx: commands.Context):
    if ctx.author.id != bot.owner_id and (not ctx.guild or ctx.guild != bot.get_cog('Hamilton').guild):
        emb = missile.Embed(description=ctx.message.content)
        emb.add_field('By', ctx.author.mention)
        emb.add_field('In', ctx.guild.id if ctx.guild else 'DM')
        await bot.get_cog('Hamilton').bot_test.send(embed=emb)


@bot.event
async def on_message_delete(msg: discord.Message):
    """Event handler when a message has been deleted"""
    if not msg.guild or msg.author == msg.guild.me or msg.content.startswith(await missile.prefix_process(bot, msg)):
        return
    # Stores the deleted message for snipe command
    snipe_cfg = await bot.sql.get_snipe_cfg(bot.db, guild=msg.guild.id)
    if snipe_cfg:
        content = msg.content if msg.content else msg.embeds[0].title
        emb = missile.Embed(msg.guild.name, content,
                            msg.embeds[0].colour if msg.embeds else discord.Colour.random(),
                            msg.guild.icon_url)
        emb.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
        bot.guild_store[msg.guild.id] = emb
        if snipe_cfg == 2:
            bot.guild_store[0] = emb


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.errors.CommandInvokeError):
    """Event handler when a command raises an error"""
    if isinstance(error, errors.CommandNotFound):  # Human error
        await ctx.reply('Stoopid. That is not a command.')
    # Human error
    elif isinstance(error, (errors.MissingRequiredArgument, errors.MissingAnyRole, errors.CommandOnCooldown,
                            errors.UserNotFound, errors.MemberNotFound, errors.MissingPermissions,
                            errors.BadInviteArgument, errors.BadColourArgument)) \
            or isinstance(error, errors.BadUnionArgument) and not ctx.command.has_error_handler():
        await ctx.reply(str(error))
    elif isinstance(error, BasePPException):  # Human error
        await ctx.reply(str(error).format(ctx.bot.default_prefix))
    elif isinstance(error, errors.ChannelNotFound):  # Human error
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
    elif isinstance(error, errors.RoleNotFound):  # Human error
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
    elif isinstance(error, errors.GuildNotFound):
        await ctx.reply('I am not in that server.')
    elif isinstance(error, errors.BadArgument):
        # Could be a human/program error
        await ctx.reply('Bad arguments.')
    elif isinstance(error, errors.CheckFailure):
        return
    else:
        # This is basically "unknown error"
        import traceback
        content = f'```python\n{ctx.message.content}\n'
        for tb in traceback.format_tb(error.original.__traceback__):
            content += tb
        content += str(error.original) + '```'
        msg = await bot.get_cog('Hamilton').bot_test.send(content[:2000])
        await ctx.reply(f'Hmm... Report ID: **{msg.id}**')
        if len(content) > 2000:
            raise error


@bot.command(aliases=('bot',), brief='Displays bot info')
async def botinfo(ctx):
    from platform import python_version
    embed = missile.Embed(sponsor_txt)
    embed.add_field('Guild count', str(len(bot.guilds)))
    embed.add_field('Uptime', datetime.now() - bot.boot_time)
    embed.add_field('Python', python_version())
    embed.add_field('Discord.py', discord.__version__)
    embed.add_field('Codename', 'みずはら')
    embed.add_field('Devblog', '[Instagram](https://www.instagram.com/techdim)')
    embed.add_field('Source code', '[GitHub](https://github.com/TCLRainbow/DimBot)')
    embed.add_field('Discord server', '[6PjhjCD](https://discord.gg/6PjhjCD)')
    process = psutil.Process()
    with process.oneshot():
        embed.add_field('CPU usage %', psutil.cpu_percent(percpu=True))
        embed.add_field(
            'Process RAM usage / available (MiB)',
            f'{process.memory_info()[0] / 1024 ** 2:.1f} / {psutil.virtual_memory().available / 1024 ** 2:.1f}'
        )
    emoji = choice(tuple(e for e in bot.get_cog('Hamilton').guild.emojis
                         if e.name.startswith('sayu') or e.name.startswith('chloe')))
    n = 4 if emoji.name.startswith('sayu') else 5
    embed.set_footer(text='Mood: ' + emoji.name[n:])
    if n == 5:
        embed.color = discord.Colour.red()
    embed.set_author(name='Click here to let me join your server! [Open Beta]',
                     url='https://discord.com/api/oauth2/authorize?client_id=574617418924687419&permissions=8&scope=bot'
                     )
    embed.set_image(url=emoji.url)
    await ctx.send(embed=embed)


@bot.command(brief='$.$')
async def sponsor(ctx):
    await ctx.send(sponsor_txt)


@bot.command(aliases=('ping', 'heartbeat'),
             brief='Listens to my heartbeat (gateway latency & total message reaction latency)')
async def noel(ctx):
    msg = await ctx.reply(f'💓 {bot.latency * 1000:.3f}ms')
    tic = datetime.now()
    await msg.add_reaction('📡')
    toc = datetime.now()
    await msg.edit(content=msg.content + f' 🛰️ {(toc - tic).total_seconds() * 1000:.3f}ms')


@bot.group(invoke_without_command=True, brief='Commands for generating links')
async def link(ctx):
    bot.help_command.context = ctx
    await bot.help_command.send_group_help(ctx.command)


@link.command(brief='Generating MinecraftForge installer links')
async def forge(ctx):
    msg = await bot.ask_msg(ctx, 'Reply `Minecraft version`-`Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command(brief='Generating Galaticraft mod download links')
async def galacticraft(ctx):
    mc = await bot.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


@link.command(aliases=('m',), brief='Shows a Discord message link')
async def message(ctx, msg: discord.Message):
    """`link message <msg>
    msg: The message, usually its ID."""
    await ctx.reply(msg.jump_url)


@bot.command(aliases=('gsnipe',),
             brief='Displays the last deleted message in this server.'
                   ' `gsnipe` to display last deleted message across servers')
@missile.guild_only()
async def snipe(ctx):
    gid = 0 if ctx.invoked_with[0] == 'g' else ctx.guild.id
    await ctx.send(embed=bot.guild_store.get(gid, missile.Embed(description='No one has deleted anything yet...')))


@bot.group(brief='Confidential')
@missile.is_rainbow()
async def arccore(ctx: commands.Context):
    if not ctx.invoked_subcommand:
        raise commands.errors.CommandNotFound


@arccore.command()
async def stealth(ctx):
    await bot.db.commit()
    await bot.db.close()
    await ctx.send('Arc-Cor𐑞: **Stealth**')
    await bot.close()


@arccore.command()
async def pandora(ctx):
    await bot.db.commit()
    await bot.db.close()
    await ctx.send('Arc-Cor𐑞: **PANDORA**, self-evolving!')
    with open('final', 'w') as death_note:
        death_note.write(str(ctx.channel.id))
    logger.critical('RESTARTING')
    import subprocess
    subprocess.Popen(['sudo systemctl restart dimbot'], shell=True)


@arccore.command()
async def sch(ctx, ch: Union[discord.TextChannel, discord.User]):
    bot.sch = ch


@arccore.command()
async def say(ctx, *, msg: str):
    await bot.sch.send(msg)


@arccore.command()
async def shadow(c, *, cmd: str):
    msg = await bot.sch.send('⠀')
    msg.content = bot.default_prefix + cmd
    msg.author = msg.guild.get_member(bot.owner_id)
    await bot.invoke(await bot.get_context(msg))


@arccore.command()
async def leave(ctx: commands.Context, s: discord.Guild):
    await s.leave()
    await ctx.reply('Done.')


@arccore.command()
async def exe(ctx, *, msg: str):
    # Directly executes SQL statements
    import sqlite3
    try:
        tic = datetime.now()  # Measure execution time
        msg = f"--name: sqlexe\n{msg}"""
        query = aiosql.from_str(msg, 'aiosqlite')
        async with query.sqlexe_cursor(bot.db) as cursor:
            result = await cursor.fetchall()
            toc = datetime.now()
            await ctx.reply(f"{result}\n{cursor.rowcount} row affected in {(toc - tic).total_seconds() * 1000}ms")
    except sqlite3.Error as e:
        await ctx.send(f"**{e.__class__.__name__}**: {e}")


@arccore.command()
async def save(ctx):
    # Forcefully saves the db
    await bot.db.commit()
    await ctx.send('Saved')


@arccore.command()
async def typing(ctx):
    if bot.arccore_typing:
        await bot.arccore_typing.__aexit__(None, None, None)
        bot.arccore_typing = None
    else:
        bot.arccore_typing = await bot.sch.typing().__aenter__()


async def __maintenance__(context):
    owner = context.author.id == bot.owner_id
    if not owner:
        await context.reply("My pog champ is taking care of me <:ikaros:823581166715928588>")
    return owner


@arccore.command()
async def mt(ctx: commands.Context, minutes: int = 5):
    if bot.maintenance:
        bot.remove_check(__maintenance__)
        bot.status = discord.Status.online
        await bot.change_presence()
        await ctx.reply('Removed maintenance')
    elif await bot.ask_reaction(ctx, f'Enable maintenance mode after {minutes}min?'):
        now = datetime.now() + timedelta(minutes=minutes)

        async def prep(context: commands.Context):
            stamp = (now - datetime.now()).total_seconds()
            if stamp >= 60:
                stamp = f"{(stamp // 60):.0f}m {(stamp % 60):.0f}s"
            else:
                stamp = f"{stamp:.0f}s"
            await context.send(f"⚠Maintenance mode in **{stamp}**!")
            return True

        bot.add_check(prep)
        bot.status = discord.Status.idle
        await bot.change_presence(status=bot.status)
        m = await ctx.send('Preparing maintenance')
        await asyncio.sleep(minutes * 60)
        bot.remove_check(prep)
        bot.add_check(__maintenance__)
        bot.maintenance = True
        bot.status = discord.Status.dnd
        await bot.change_presence(status=bot.status)
        await missile.append_msg(m, 'Started')


@arccore.command()
async def ms(ctx: commands.Context, user: discord.User):
    await ctx.reply('\n'.join(set(g.name for g in user.mutual_guilds)) if user.mutual_guilds else 'None.')


@arccore.command()
async def ls(ctx: commands.Context):
    content = ''
    for g in bot.guilds:
        content += f'{g.id} {g.name}\n'
    await ctx.reply(content)


@arccore.command()
@missile.guild_only()
async def lch(ctx: commands.Context, g: discord.Guild = None):
    g = g if g else ctx.guild
    msg = ''
    for ch in g.channels:
        msg += f'{ch.id} {ch.type} {ch.name}\n'
    await ctx.reply(msg)


@arccore.command()
async def bs(ctx: commands.Context, server: int):
    if await bot.ask_reaction(ctx, 'Confirm?'):
        await asyncio.wait((
            bot.sql.ban_guild(bot.db, id=server),
            bot.sql.remove_guild_cfg(bot.db, guildID=server),
            bot.sql.remove_guild_tags(bot.db, guildID=server),
            bot.sql.clear_guild_xp(bot.db, guildID=server)
        ))
        await ctx.reply('Banned')


@arccore.command()
async def changelog(ctx):
    ch = 666431254312517633 if dimsecret.debug else 977778385247944754
    await bot.get_channel(ch).send(f"""# __{missile.ver} (<t:{last_modified}>)__
Added `d.de` and `d.de3`: OpenAI DALL-E image generation.
__PLEASE DO NOT SPAM THE COMMAND IT COSTS ME A FUCK TON OF MONEY!!!!!__
""")


hug_gifs = ('https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
            'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
            'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958',
            'https://tenor.com/view/love-kirby-hug-gif-13854608')

nene_gifs = ('https://imgur.com/sB7ZkbQ', 'https://imgur.com/XofnZ9B', 'https://imgur.com/XT7b1YX')


@bot.command(brief='Hug one another every day for streaks!')
@missile.guild_only()
async def hug(ctx: commands.Context, *target: discord.Member):
    """Original idea by <@226664644041768960>
    `hug <user>` to start hugging them and earn streaks. You can also just `hug` if you want to..."""
    if target:
        gif = choice(hug_gifs)
        s = ''

        for m in target:
            s += '\n'
            if m == ctx.guild.me:
                gif = choice(nene_gifs)
                name = 'me'
            else:
                name = m.name
            t = time.time()
            hug_record = await bot.sql.get_hug(bot.db, hugger=ctx.author.id, huggie=m.id)
            if hug_record:
                delta = t - hug_record[1]
                if delta < 86400:
                    wait = time.gmtime(86400 - delta)
                    s += f"You've already hugged {name} today! Streaks: **{hug_record[0]}**. " \
                         f"Please wait for {wait.tm_hour}h {wait.tm_min}m {wait.tm_sec}s"
                elif delta < 172800:
                    new_streak = hug_record[0] + 1
                    await bot.sql.update_hug(bot.db, hugger=ctx.author.id, huggie=m.id, streak=new_streak,
                                             hugged=t)
                    s += f'You hugged {name}! Streaks: **{new_streak}**'
                else:
                    if m == ctx.guild.me:
                        gif = 'https://tenor.com/view/angry-nene-nenechi-nene-konnene-matanene-gif-21412090'
                    await bot.sql.update_hug(bot.db, hugger=ctx.author.id, huggie=m.id, streak=1, hugged=t)
                    s += f"You haven't hugged {name} in 48h so you've lost your streak!"
            else:
                await bot.sql.add_hug(bot.db, hugger=ctx.author.id, huggie=m.id, hugged=t)
                s += f'You hugged {name}! Streaks: **1**'

        await ctx.reply(gif + s)
    else:
        await ctx.reply('Fine, I guess I will give you a hug\n'
                        'https://tenor.com/view/dance-moves-dancing-singer-groovy-gif-17029825')


@bot.command(brief='Huh?')
async def huh(ctx: commands.Context):
    """Inspired by meraki's typo: hug->huh"""
    await ctx.reply('<:what:885927400691605536>')


@bot.group(aliases=('color',), invoke_without_command=True, brief='Shows color')
async def colour(ctx: commands.Context, c: discord.Colour = None):
    """`colour [c]`
    `c` can be an integer, a 6-digit hexadecimal number (optionally with a # prepending it),
    or even `rgb(<r>, <g>, <b>)` which is a CSS representation. If `c` is not supplied,
    randomly generates a HSV color with max saturation.
    """
    if not c:
        c = discord.Colour.random()
    value = f'{c.value:X}'
    emb = missile.Embed(f'#{value.zfill(6)}', color=c)
    emb.add_field('R', c.r)
    emb.add_field('G', c.g)
    emb.add_field('B', c.b)
    await ctx.reply(embed=emb)


@colour.command()
async def hsv(ctx: commands.Context, h: int = 0, s: int = 0, v: int = 0):
    """`colour hsv <h> <s> <v>`
    Same with `colour` command but accepts HSV values. Cannot randomly generates color."""
    color = discord.Colour.from_hsv(h, s, v)
    if 0 <= color.value <= 0xFFFFFF:
        await bot.get_command('color')(ctx, color)
    else:
        raise errors.BadColorArgument(color)


@bot.command(aliases=('enc',), brief='Encodes a message to base64')
async def encode(ctx: commands.Context, *, content: str):
    """encode <content>
    If the content is a URL, sends a link which will auto redirect to the original link.
    If content is not a URL, prepends the content with an author ping, encodes then send it."""
    if ctx.channel.type == discord.ChannelType.text:
        await ctx.message.delete()
    if missile.is_url(content):
        await ctx.send(f'<{bot.ip}b64d?s={missile.encode(content)}>')
    else:
        content = ctx.author.mention + ': ' + content
        await ctx.send(missile.encode(content))


@bot.command(aliases=('dec',), brief='Decodes the base64 message and send it to your DM.')
async def decode(ctx: commands.Context, content: str):
    """decode <content>"""
    import binascii
    try:
        await ctx.author.send(missile.decode(content))
        await ctx.message.add_reaction('✅')
    except (UnicodeDecodeError, binascii.Error):
        await ctx.send('Malformed base64 string.')


@missile.guild_only()
@missile.bot_has_perm(mention_everyone=True)
@bot.command(brief='If the user is in the role, pings the role')
async def roleping(ctx: commands.Context, role: discord.Role):
    """roleping <role>"""
    if not role.is_default() and not role.is_premium_subscriber() and role in ctx.author.roles:
        await ctx.reply(role.mention)


async def ready_tasks():
    bot.add_cog(Ricciardo(bot))
    # bot.add_cog(Verstapen(bot))
    bot.add_cog(Bottas(bot))
    bot.add_cog(dimond.Dimond(bot))
    bot.add_cog(Ikaros(bot))
    bot.add_cog(Aegis(bot))
    bot.add_cog(XP(bot))
    bot.add_cog(Diminator(bot))
    # bot.add_cog(SkyBow(bot))
    bot.add_cog(Nene(bot))
    if not dimsecret.debug:
        bot.add_cog(Hyperstellar(bot))
    await bot.wait_until_ready()
    bot.add_cog(tribe.Hamilton(bot))
    psutil.cpu_percent(percpu=True)
    await bot.is_owner(bot.user)  # Trick to set bot.owner_id
    logger.info('Ready')
    if reborn_channel:  # Post-process Pandora if needed
        await bot.get_channel(reborn_channel).send("Arc-Cor𐑞: Pandora complete.")
    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != bot.nickname and guild.me.guild_permissions.change_nickname:
            bot.loop.create_task(guild.me.edit(nick=bot.nickname))
    while True:
        try:
            activity = await bot.sql.get_activity(bot.db)
            await bot.change_presence(
                activity=discord.Activity(name=activity[0], type=discord.ActivityType(activity[1])),
                status=bot.status)
        except:
            logger.error('Update activity failed!')
        await asyncio.sleep(300)
        try:
            await bot.db.commit()
            logger.debug('DB auto saved')
        except:
            logger.error('DB autosave failed!')


bot.loop.create_task(bot.async_init())
bot.loop.create_task(ready_tasks())
try:
    bot.loop.run_until_complete(bot.start(dimsecret.discord))
except Exception as e:
    bot.loop.run_until_complete(bot.db.close())
    raise e
except:
    bot.loop.run_until_complete(bot.db.close())
