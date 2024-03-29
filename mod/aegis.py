import asyncio
import contextlib
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ext.commands import Cog

import missile
from menus import WhoPing

ext = missile.MsgExt('Aegis')


class Aegis(Cog):
    """Passive(Auto) moderation system
    Version 0.6.2"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}
        self.ghost_pings = {}  # Ghost ping message cache
        self.skip_ghost_ping = []  # List of channel IDs to temporarily skip ghost ping checks
        # List of channel IDs to temporarily suppress ghost ping notifications
        self.suppress_ghost_ping_notification = []

    def act_wrap(self, msg: discord.Message, warn_type: str):
        self.count[msg.author.id][1] += 1
        self.count[msg.author.id][0] = []
        self.bot.loop.create_task(ext.reply(msg, f'Detected spam by {msg.author.mention}, type {warn_type}. '
                                                 f'Warn: {self.count[msg.author.id][1]}'))
        self.bot.loop.create_task(self.act(msg, f'Aegis: Spam, type {warn_type}'))

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Check whether message needs to be scanned by Aegis
        if not msg.guild or msg.author == msg.guild.me:
            return
        if re.search(r".*who +ping", msg.content, re.IGNORECASE) and not msg.author.bot:
            await msg.reply('Someone ghost-pinged you? Try out `d.whoping`!')
        # Checks for crash gifs
        if re.search(r".*(gfycat.com/safeofficialharvestmouse|gfycat.com/grizzledwildinsect)", msg.content):
            await msg.delete()
            await ext.send(msg.channel, 'Detected crash GIF by ' + msg.author.mention)

        if msg.author.id not in self.count:  # Creates record for the message author
            self.count[msg.author.id] = [[], 0]  # [Tracked messages, warn count]

        # Checks for scam gift links
        if re.search(r"https?://disceord.gift", msg.content, re.IGNORECASE):
            self.count[msg.author.id][1] += 2
            self.bot.loop.create_task(ext.reply(msg,
                                                f'Detected scam gift link. Warn: {self.count[msg.author.id][1]}'))
            self.bot.loop.create_task(self.act(msg, 'Aegis: Scam gift links'))

        raw_mention_count = len(msg.raw_mentions)
        mass_ping_count = 20 if msg.author.bot else 5
        if raw_mention_count >= mass_ping_count:  # Mass ping
            self.count[msg.author.id][1] += 3
            self.bot.loop.create_task(ext.send(msg,
                                               f'Detected mass ping ({raw_mention_count}) by {msg.author.mention}. '
                                               f'Warn: {self.count[msg.author.id][1]}'))
            self.bot.loop.create_task(self.act(msg, 'Aegis: Mass ping'))
        elif msg.channel.id != 826418682154188851:  # Checks whether channel ignores spam
            ml = len(self.count[msg.author.id][0])
            if ml == 9:  # There are 9 previous messages:
                if (msg.created_at - self.count[msg.author.id][0][0]).total_seconds() < 10:  # 10 msg in 10s
                    self.act_wrap(msg, 'X')
                else:
                    self.count[msg.author.id][0].pop(0)  # We only track up to 10 previous messages
            if not msg.author.bot:
                if ml >= 4:  # There are 4 previous messages
                    if (msg.created_at - self.count[msg.author.id][0][ml - 4]).total_seconds() < 5:  # 5 msg in 5s
                        self.act_wrap(msg, 'V')
                # ml = len(self.count[msg.author.id][0])
                elif ml > 1 > (msg.created_at - self.count[msg.author.id][0][ml - 2]).total_seconds():  # 3 msg in 1s
                    self.act_wrap(msg, 'I')
            for t in self.count[msg.author.id][0]:  # If previous messages are >10s older than current, purge cache
                if (msg.created_at - t).total_seconds() >= 10:
                    self.count[msg.author.id][0].pop(0)
            self.count[msg.author.id][0].append(msg.created_at)  # Add current message for tracking

    async def act(self, msg: discord.Message, reason: str):
        """Takes action"""
        if type(msg.author) == discord.User:
            await msg.channel.send('⚠DETECTED UNUSUAL WEBHOOK ACTIVITIES, DELETING THE WEBHOOK\nPlease notify '
                                   'admins in this server!')
            webhooks = await msg.channel.webhooks()
            for webhook in webhooks:
                if webhook.id == msg.author.id:
                    webhook.delete(reason='Aegis: Unusual webhook activities')
                    await msg.channel.send(f'Deleted webhook <@{webhook.id}>')
                    return
            return
        ikaros = self.bot.get_cog('Ikaros')
        if self.count[msg.author.id][1] == 2:  # 3 warns in the past 2h
            await ikaros.mute(msg, msg.author, 10, 0, reason + ', threat level 1')  # 10s mute
        elif self.count[msg.author.id][1] == 3:  # 3 warns in the past 2h
            await ikaros.mute(msg, msg.author, 3600, 0, reason + ', threat level 2')  # 1h mute
        elif self.count[msg.author.id][1] == 4:  # 4 warns in the past 2h
            await ikaros.kick(msg, msg.author, 0, reason + ', threat level 3')  # Immediate kick
        elif self.count[msg.author.id][1] >= 5:  # >5 warns in the past 2h
            await ikaros.ban(msg, msg.author, 0, 0, reason + ', threat level 4')  # Immediate ban
        await asyncio.sleep(7200)  # Reduces total warn count by 1 after 2h
        self.count[msg.author.id][1] -= 1

    @Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        """Event handler when a message has been deleted"""
        # Ghost ping detector
        # Check whether the message is related to the bot
        if not msg.guild or msg.author == msg.guild.me or msg.channel.id in self.skip_ghost_ping:
            return
        if msg.id in self.ghost_pings.keys():  # The message has/used to have pings
            for m in self.ghost_pings[msg.id]:
                # Tells the victim that he has been ghost pinged
                await self.bot.sql.add_who_ping(
                    self.bot.db,
                    victim=m.id, pinger=msg.author.id, content=msg.content, time=datetime.now(), guild=msg.guild.id
                )

            # Reports in the incident channel that the culprit deleted a ping
            # if msg.channel.id not in self.suppress_ghost_ping_notification:
            #     await ext.send(msg, msg.author.mention + ' has deleted a ping. Try out `d.whoping`!')

            # Removes the message from the cache as it has been deleted on Discord
            del self.ghost_pings[msg.id]
        elif (msg.mentions or msg.role_mentions) and not msg.edited_at:  # The message has pings and has not been edited
            members = set().union(msg.mentions, *(r.members for r in msg.role_mentions))
            has_pinged = False
            for m in members:
                if not m.bot and m != msg.author:
                    # Tells the victim that he has been ghost pinged
                    await self.bot.sql.add_who_ping(
                        self.bot.db,
                        victim=m.id, pinger=msg.author.id, content=msg.content, time=datetime.now(), guild=msg.guild.id
                    )
                    has_pinged = True
            # Reports in the incident channel that the culprit deleted a ping
            # if has_pinged and msg.channel.id not in self.suppress_ghost_ping_notification:
            #     await ext.send(msg, msg.author.mention + ' has deleted a ping. Try out `d.whoping`!')

    @contextlib.contextmanager
    def no_ghost_ping_notification(self, ch: int):
        """A message won't be sent to the channel when a ping has been deleted."""
        self.suppress_ghost_ping_notification.append(ch)
        yield
        self.suppress_ghost_ping_notification.remove(ch)

    @contextlib.contextmanager
    def no_ghost_ping(self, ch: int):
        """Completely skips the Ghost Ping detector logic for that channel"""
        self.skip_ghost_ping.append(ch)
        yield
        self.skip_ghost_ping.remove(ch)

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Event handler when a message has been edited. Detect ghost pings due to edited message"""
        # A message that contains pings has been edited
        if before.guild and not before.edited_at and (before.mentions or before.role_mentions):
            #  Add the message to ghost pings cache
            pre = set().union(before.mentions, *(r.members for r in before.role_mentions))
            pre = set(m for m in pre if not m.bot and m != before.author)
            if pre:
                self.ghost_pings[before.id] = pre
        if before.guild and before.id in self.ghost_pings.keys():  # Message requires ghost ping checking
            has_removed = False
            for m in self.ghost_pings[before.id]:
                if m not in after.mentions:  # A ping has been removed
                    has_removed = True
                    # Tells the victim that he has been ghost pinged
                    await self.bot.sql.add_who_ping(
                        self.bot.db,
                        victim=m.id, pinger=before.author.id, content=before.content, time=datetime.now(),
                        guild=before.guild.id
                    )
                    self.ghost_pings[before.id].remove(m)
            if has_removed:
                # Reports in the incident channel that the culprit deleted a ping
                await ext.send(before, before.author.mention + ' has removed a ping from a message')
            if not self.ghost_pings[before.id]:  # All original pings have bene removed.
                self.ghost_pings.pop(before.id)  # No longer have to track as there are no pings anymore.

    @Cog.listener()
    async def on_ready(self):
        while True:
            await self.bot.sql.daily_clean_who_ping(self.bot.db, time=datetime.now() - timedelta(days=1))
            await asyncio.sleep(86400)

    @commands.group(invoke_without_command=True, brief='Commands for the ghost ping detector')
    async def whoping(self, ctx: commands.Context):
        """If no subcommand, displays an inspector menu for you to see who ghost pinged you."""
        is_guild = True
        if ctx.guild:
            pings = await self.bot.sql.get_who_ping(self.bot.db, guild=ctx.guild.id, victim=ctx.author.id)
        else:
            pings = await self.bot.sql.get_all_who_ping(self.bot.db, victim=ctx.author.id)
            is_guild = False
        if pings:
            await WhoPing(pings, is_guild).start(ctx)
        else:
            await ctx.reply('No one has pinged you in this server yet!')

    @whoping.command()
    @missile.guild_only()
    async def read(self, ctx: commands.Context):
        """Clears your WhoPing records in the server"""
        await self.bot.sql.clear_who_ping(self.bot.db, victim=ctx.author.id, guild=ctx.guild.id)
        await ctx.reply('Cleared your WhoPing records in this server.')

    @whoping.command()
    async def clear(self, ctx: commands.Context):
        """Clears your WhoPing records across all servers"""
        await self.bot.sql.clear_all_who_ping(self.bot.db, victim=ctx.author.id)
        await ctx.reply('Cleared all of your WhoPing records.')
