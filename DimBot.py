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

import diminator
import dimond
import dimsecret
import missile
import tribe
from bruckserver.vireg import Verstapen
from echo import Bottas
from games.cog import Games
from mod.aegis import Aegis
from mod.ikaros import Ikaros
from raceline import Ricciardo
from xp import XP

# Variables needed for initialising the bot
intent = discord.Intents()
intent.value = 0b1111110000011  # https://discord.com/developers/docs/topics/gateway#list-of-intents
bot = missile.Bot(intents=intent)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.10.5"
logger = missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手の中にあります <https://streamlabs.com/pythonic_rainbow/tip> <https://www.patreon.com/ChingDim>'
reborn_channel = None


async def binvk(ctx: commands.Context):
    if randint(1, 100) <= 5:
        await ctx.send(sponsor_txt)


bot.before_invoke(binvk)


async def ainvk(ctx: commands.Context):
    if ctx.command.qualified_name.startswith('arccore'):
        return
    emb = missile.Embed(description=ctx.message.content)
    emb.add_field('By', ctx.author.mention)
    emb.add_field('In', ctx.guild.id if ctx.guild else 'DM')
    await bot.get_cog('Hamilton').bot_test.send(embed=emb)


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
    if msg.guild and msg.content == msg.guild.me.mention:
        p = await bot.get_prefix(msg)
        if p == bot.default_prefix:
            await msg.channel.send(f'My prefix is **{bot.default_prefix}**')
        else:
            await msg.channel.send(f"My prefixes are **{'**, **'.join(p)}**")
        return
    await bot.process_commands(msg)


@bot.event
async def on_guild_join(guild: discord.Guild):
    await bot.get_cog('Hamilton').bot_test.send(f'Joined server {guild.id} {guild.name} <@{bot.owner_id}>')
    if await bot.sql.is_guild_banned(bot.db, id=guild.id):
        await guild.leave()
        return
    await bot.sql.add_guild_cfg(bot.db, guildID=guild.id)
    await guild.me.edit(nick=nickname)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    await bot.get_cog('Hamilton').bot_test.send(f'Left server {guild.id} {guild.name}')


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
    elif isinstance(error, diminator.BasePPException):  # Human error
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
        msg = await bot.get_cog('Hamilton').bot_test.send(content)
        await ctx.reply(f'Hmm... Report ID: **{msg.id}**')


async def solo_vc(vs):
    print('Counting')
    await asyncio.sleep(vs.channel.guild.afk_timeout)
    print('Done counting')
    if len(vs.channel.members) == 1:
        await vs.channel.members[0].move_to(None, reason='Solo AFKing in a VC')


@bot.event
async def on_voice_state_update(m: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel and len(before.channel.members) == 1 and not after.channel \
            and before.channel.guild.me.guild_permissions.move_members:
        await solo_vc(before)
    elif after.channel and after.channel.guild.me.guild_permissions.move_members:
        if after.afk:
            await m.move_to(None, reason='Joined AFK VC')
        elif len(after.channel.members) == 1:
            await solo_vc(after)


@bot.command(aliases=('bot',))
async def botinfo(ctx):
    """Displays bot info"""
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
    emoji = choice(tuple(e for e in bot.get_cog('Hamilton').guild.emojis if e.name.startswith('sayu')))
    embed.set_footer(text='Mood: ' + emoji.name[4:])
    embed.set_author(name='Click here to let me join your server! [Open Beta]',
                     url='https://discord.com/api/oauth2/authorize?client_id=574617418924687419&permissions=8&scope=bot'
                     )
    embed.set_image(url=emoji.url)
    await ctx.send(embed=embed)


@bot.command()
async def sponsor(ctx):
    """$.$"""
    await ctx.send(sponsor_txt)


@bot.command(aliases=('ping', 'heartbeat'))
async def noel(ctx):
    """Listens to my heartbeat (gateway latency & total message reaction latency)"""
    msg = await ctx.reply(f'💓 {bot.latency * 1000:.3f}ms')
    tic = datetime.now()
    await msg.add_reaction('📡')
    toc = datetime.now()
    await msg.edit(content=msg.content + f' 🛰️ {(toc - tic).total_seconds() * 1000:.3f}ms')


@bot.group(invoke_without_command=True)
async def link(ctx):
    """Commands for generating links"""
    bot.help_command.context = ctx
    await bot.help_command.send_group_help(ctx.command)


@link.command()
async def forge(ctx):
    """Generating MinecraftForge installer links"""
    msg = await bot.ask_msg(ctx, 'Reply `Minecraft version`-`Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    """Generating Galaticraft mod download links"""
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


@bot.command(aliases=('gsnipe',))
@missile.guild_only()
async def snipe(ctx):
    """Displays the last deleted message in this server. `gsnipe` to display last deleted message across servers"""
    gid = 0 if ctx.invoked_with[0] == 'g' else ctx.guild.id
    await ctx.send(embed=bot.guild_store.get(gid, missile.Embed(description='No one has deleted anything yet...')))


@bot.group()
@missile.is_rainbow()
async def arccore(ctx: commands.Context):
    """Confidential"""
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


hug_gifs = ('https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
            'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
            'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958')


@bot.command(brief='Hug one another every day for streaks!')
@missile.guild_only()
async def hug(ctx, target: discord.Member = None):
    """Original idea by <@226664644041768960>
    `hug <user>` to start hugging them and earn streaks. You can also just `hug` if you want to..."""
    if target:
        if target.bot or target == ctx.author:
            await ctx.reply("You can't hug a bot or yourself! Maybe you should hug my pog champ instead?")
        else:
            gif = choice(hug_gifs)
            t = time.time()
            hug_record = await bot.sql.get_hug(bot.db, hugger=ctx.author.id, huggie=target.id)
            if hug_record:
                delta = t - hug_record[1]
                if delta < 86400:
                    wait = time.gmtime(86400 - delta)
                    await ctx.reply(f"{gif}\nYou've already hugged {target} today! Streaks: **{hug_record[0]}**\n"
                                    f"Please wait for {wait.tm_hour}h {wait.tm_min}m {wait.tm_sec}s")
                elif delta < 172800:
                    new_streak = hug_record[0] + 1
                    await bot.sql.update_hug(bot.db, hugger=ctx.author.id, huggie=target.id, streak=new_streak,
                                             hugged=t)
                    await ctx.reply(f'{gif}\nYou hugged {target}! Streaks: **{new_streak}**\n'
                                    'Send the command again tomorrow to earn streaks!')
                else:
                    await bot.sql.update_hug(bot.db, hugger=ctx.author.id, huggie=target.id, streak=1, hugged=t)
                    await ctx.reply(f"{gif}\nYou haven't hugged {target} for 2 days so you've lost your streak!")
            else:
                await bot.sql.add_hug(bot.db, hugger=ctx.author.id, huggie=target.id, hugged=t)
                await ctx.reply(f'{gif}\nYou hugged {target}! Streaks: **1**\n'
                                'Send the command again tomorrow to earn streaks!')
    else:
        await ctx.reply('Fine, I guess I will give you a hug\n'
                        'https://tenor.com/view/dance-moves-dancing-singer-groovy-gif-17029825')


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


@bot.group()
@missile.guild_only()
@commands.has_guild_permissions(manage_guild=True)
async def guild(ctx: commands.Context):
    """Settings for server"""
    if not ctx.invoked_subcommand:
        bot.help_command.context = ctx
        await bot.help_command.send_group_help(ctx.command)


@guild.command(brief='Changes the custom prefix of DimBot')
async def prefix(ctx: commands.Context, *, p: str = None):
    """`guild  prefix [p]`
    `p` is a SENTENCE so you can send like `Super bad prefix` as `p` without quotation marks.
    Note that d. will still work. Send the command without arguments to remove the custom prefix."""
    if p and (p.lower().startswith('dimbot') or ctx.me.mention in p):
        await ctx.reply('Only my little pog champ can use authoritative orders!')
    else:
        await bot.sql.update_guild_prefix(bot.db, guildID=ctx.guild.id, prefix=p)
        await ctx.reply('Updated server prefix.')


@guild.command(brief='Sets the moderation role of the server')
async def modrole(ctx: commands.Context, role: discord.Role):
    """guild modrole <role>"""
    await bot.sql.set_mod_role(bot.db, role=role.id, guild=ctx.guild.id)
    await ctx.reply('Updated moderation role to ' + role.name)


@guild.command(name='snipe', brief='Sets snipe discovery for the server')
async def guild_snipe(ctx: commands.Context, level: int = 2):
    """This command sets whether snipes can work and whether they are visible in other servers.

    0: Snipe/GSnipe will not detect deleted messages in this server at all.
    1: Snipe will detect but the detected messages are only visible in this server (`gsnipe` won't display)
    2 (default): Snipe will detect and they are visible in other servers (`gsnipe` can display this server's snipes)"""
    if 0 <= level <= 2:
        await bot.sql.set_snipe_cfg(bot.db, snipe=level, guild=ctx.guild.id)
        await ctx.reply('Updated snipe discovery level')
    else:
        await ctx.reply(f'Invalid discovery level! Please send `{await bot.get_prefix(ctx.message)}help guild snipe`!')


@guild.command(brief='Toggles auto kicking members from VC when they afk')
async def antiafk(ctx: commands.Context, enable: bool = True):
    await bot.sql.set_anti_afk(bot.db, antiafk=enable, guild=ctx.guild.id)
    await ctx.reply('Updated!')


@bot.command()
async def changelog(ctx):
    """Shows the latest release notes of DimBot"""
    await ctx.reply("""
**__0.10.4 (Aug 5, 2021 1:35AM GMT+8)__**
Introducing **Local Snipes**!

Since `d.snipe` has debuted, the detected messages are visible across servers. There was pretty much no customisation for it,
and some of you had given me feedbacks about it. With this update, you can now use `d.snipe` for **local** snipes that scans
only in your server, as well as the OG `d.gsnipe` for **global** snipes.

You can even customise whether other servers can view your snipes, or simply disable the entire snipe command in your server.
More info can be found in `d.help guild snipe`. Happy sniping!
""")


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


async def ready_tasks():
    bot.add_cog(Ricciardo(bot))
    bot.add_cog(Verstapen(bot))
    bot.add_cog(Bottas(bot))
    bot.add_cog(diminator.Diminator(bot))
    bot.add_cog(dimond.Dimond(bot))
    bot.add_cog(Ikaros(bot))
    bot.add_cog(Aegis(bot))
    bot.add_cog(XP(bot))
    bot.add_cog(Games(bot))
    await bot.wait_until_ready()
    bot.add_cog(tribe.Hamilton(bot))
    bot.after_invoke(ainvk)
    psutil.cpu_percent(percpu=True)
    await bot.is_owner(bot.user)  # Trick to set bot.owner_id
    logger.info('Ready')
    if reborn_channel:  # Post-process Pandora if needed
        await bot.get_channel(reborn_channel).send("Arc-Cor𐑞: Pandora complete.")
    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != nickname and guild.me.guild_permissions.change_nickname:
            bot.loop.create_task(guild.me.edit(nick=nickname))
    while True:
        activity = await bot.sql.get_activity(bot.db)
        await bot.change_presence(activity=discord.Activity(name=activity[0], type=discord.ActivityType(activity[1])),
                                  status=bot.status)
        await asyncio.sleep(300)
        await bot.db.commit()
        logger.debug('DB auto saved')


bot.loop.create_task(bot.async_init())
bot.loop.create_task(ready_tasks())
bot.run(dimsecret.discord)
