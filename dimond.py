from typing import Optional

import discord
from discord.ext import commands

from missile import Missile


class Dimond(commands.Cog):
    """Named by Anqaa' (uid: 98591077975465984)
    Report users/channels/servers details. Literally CIA
    Version: 1.1"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.group(invoke_without_command=True)
    async def user(self, ctx, u: discord.User = None):
        """Shows user info"""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.User
        u = u if u else ctx.author
        desc = f"Send `{self.bot.default_prefix}user f [user]` for flag details,\n`{self.bot.default_prefix}perm " \
               "[user|channel] [channel]` for permission details"
        emb = discord.Embed(title=str(u), description=desc)
        emb.set_thumbnail(url=u.avatar_url)
        if u.avatar:
            emb.set_footer(text='Avatar hash: ' + u.avatar)
        emb.add_field(name='❄ ID', value=u.id)
        emb.add_field(name='Is bot?', value=u.bot)
        emb.add_field(name='Public flags', value=u.public_flags.value)
        emb.add_field(name='Created at', value=u.created_at)
        member: Optional[discord.Member] = None
        # A hacky way to try getting data that can only be accessed as a Member
        for g in self.bot.guilds:
            m = g.get_member(u.id)
            if m:
                member = m
                if m.voice:  # Searches whether the 'member' is in a VC
                    break   # A user can only be in 1 VC
        # TODO: Use user.mutual_guilds to check status&activities instead when d.py 1.7 is released
        if member:  # Data that can only be accessed as a Member
            emb.add_field(name='Number of activities', value=str(len(member.activities)) if member.activities else '0')
            stat = str(member.status)
            if member.desktop_status != discord.Status.offline:
                stat += ' 💻'
            if member.mobile_status != discord.Status.offline:
                stat += ' 📱'
            if member.web_status != discord.Status.offline:
                stat += ' 🌐'
            emb.add_field(name='Status', value=stat)
            if member.voice:
                v_state = str(member.voice.channel.id)
                if member.voice.self_mute:
                    v_state += ' **Muted**'
                if member.voice.self_deaf:
                    v_state += ' **Deaf**'
                if member.voice.self_stream:
                    v_state += ' **Streaming**'
                emb.add_field(name='Voice channel ❄ ID', value=v_state)
        # Guild specific data
        if ctx.guild:
            member = ctx.guild.get_member(u.id)
            if member:
                emb.add_field(name='Joined at', value=member.joined_at)
                emb.add_field(name='Pending member?', value=member.pending)
                emb.add_field(name='Nitro boosting server since', value=member.premium_since)
                emb.add_field(name='Roles', value=' '.join([role.mention for role in member.roles[1:]][::-1]))
                emb.colour = member.color
        emb.set_author(name=member.display_name if member else u.name, icon_url=u.default_avatar_url)
        await ctx.reply(embed=emb)

    @user.command(aliases=['f'])
    async def flags(self, ctx, u: discord.User = None):
        """Shows public flags of a user"""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.PublicUserFlags
        u = u if u else ctx.author
        bin_value = f'{u.public_flags.value:b}'
        hex_value = f'{u.public_flags.value:X}'
        emb = discord.Embed(title=u.name + "'s public flags",
                            description=f"{u.public_flags.value}, 0b{bin_value.zfill(18)}, 0x{hex_value.zfill(5)}",
                            color=Missile.random_rgb())
        emb.add_field(name='Verified bot developer', value=u.public_flags.verified_bot_developer)  # 2^17
        emb.add_field(name='Verified bot', value=u.public_flags.verified_bot)  # 2^16
        if u.public_flags.bug_hunter_level_2:
            emb.add_field(name='Bug hunter', value='**Level 2**')  # 2^14
        else:
            emb.add_field(name='Bug hunter', value=u.public_flags.bug_hunter)  # 2^3
        emb.add_field(name='Discord system', value=u.public_flags.system)  # 2^12
        emb.add_field(name='Team User', value=u.public_flags.team_user)  # 2^10
        emb.add_field(name='Early supporter', value=u.public_flags.early_supporter)  # 2^9
        if u.public_flags.hypesquad_balance:
            emb.add_field(name='HypeSquad', value='Balance')  # 2^8
        elif u.public_flags.hypesquad_brilliance:
            emb.add_field(name='HypeSquad', value='Brilliance')  # 2^7
        elif u.public_flags.hypesquad_bravery:
            emb.add_field(name='HypeSquad', value='Bravery')  # 2^6
        else:
            emb.add_field(name='HypeSquad', value=u.public_flags.hypesquad)  # 2^2
        emb.add_field(name='Discord partner', value=u.public_flags.partner)  # 2^1
        emb.add_field(name='Discord employee', value=u.public_flags.staff)  # 2^0
        await ctx.reply(embed=emb)

    @commands.command(aliases=['perm', 'perms', 'permission'])
    @Missile.guild_only()
    async def permissions(self, ctx, *args):
        """Shows a user's permission server/channel wise"""
        # TODO: Maybe first arg use Union[User, TextCh, VC, Category, None],
        #  second arg use Optional[TextCh, VC, Category]

        # If cmd has no args, evaluates sender's perms server-wise
        if len(args) == 0:
            mem = ctx.author
            channel = None
        else:
            # Process the first argument. If cmd only has 1 arg, its either member or channel
            # So first attempt to process member.
            try:
                mem = await commands.MemberConverter().convert(ctx, args[0])
            except commands.MemberNotFound:
                mem = ctx.author
            # Then attempt to process channel. If above failed, args[0] should be a channel so these converters should
            # work. If above succeed, these converters should fail.
            # If 2 args, then first arg must be a Member, which processed above. So 2nd arg should be a channel.
            ch_wanna_be = args[0] if len(args) == 1 else args[1]
            try:
                channel = await commands.TextChannelConverter().convert(ctx, ch_wanna_be)
            except commands.ChannelNotFound:
                try:
                    channel = await commands.VoiceChannelConverter().convert(ctx, ch_wanna_be)
                except commands.ChannelNotFound:
                    try:
                        channel = await commands.CategoryChannelConverter().convert(ctx, ch_wanna_be)
                    except commands.ChannelNotFound:
                        channel = None
        if channel:  # If no channel specified, then  check permission server-wise
            perm = channel.permissions_for(mem)
            title = channel.name
        else:  # Check permission of the member in that channel
            perm = mem.guild_permissions
            title = 'the server'

        # https://discordpy.readthedocs.io/en/latest/api.html#discord.Permissions
        bin_value = f'{perm.value:b}'
        hex_value = f'{perm.value:X}'
        emb = discord.Embed(title=f'Permissions for {mem.name} in ' + title,
                            description=f"{perm.value}, 0b{bin_value.zfill(30)}, 0x{hex_value.zfill(8)}",
                            color=Missile.random_rgb())
        emb.add_field(name='Manage webhooks', value=perm.manage_webhooks)  # 2^29
        emb.add_field(name='Manage permissions and roles', value=perm.manage_permissions)  # 2^28
        emb.add_field(name='Manage nicknames', value=perm.manage_nicknames)  # 2^27
        emb.add_field(name='Change nickname', value=perm.change_nickname)  # 2^26
        emb.add_field(name='Use voice activation', value=perm.use_voice_activation)  # 2^25
        emb.add_field(name='Move members to voice channels', value=perm.move_members)  # 2^24
        emb.add_field(name='Deaf members', value=perm.deafen_members)  # 2^23
        emb.add_field(name='Mute members', value=perm.mute_members)  # 2^22
        emb.add_field(name='Speak', value=perm.speak)  # 2^21
        emb.add_field(name='Connect to voice channels', value=perm.connect)  # 2^20
        emb.add_field(name='View server insights', value=perm.view_guild_insights)  # 2^19
        emb.add_field(name='Use external emojis', value=perm.external_emojis)  # 2^18
        emb.add_field(name='Mention everyone', value=perm.mention_everyone)  # 2^17
        emb.add_field(name='Read message history', value=perm.read_message_history)  # 2^16
        emb.add_field(name='Attach files', value=perm.attach_files)  # 2^15
        emb.add_field(name='Embed links', value=perm.embed_links)  # 2^14
        emb.add_field(name='Manage messages', value=perm.manage_messages)  # 2^13
        emb.add_field(name='Send Text-to-Speech', value=perm.send_tts_messages)  # 2^12
        emb.add_field(name='Send messages', value=perm.send_messages)  # 2^11
        emb.add_field(name='View channel and read messages', value=perm.read_messages)  # 2^10
        emb.add_field(name='Stream', value=perm.stream)  # 2^9
        emb.add_field(name='Priority speaker', value=perm.priority_speaker)  # 2^8
        emb.add_field(name='View audit log', value=perm.view_audit_log)  # 2^7
        emb.add_field(name='Add reactions', value=perm.add_reactions)  # 2^6
        await ctx.reply(content=f"Manage server: **{perm.manage_guild}** "  # 2^5
                        f"Manage channels: **{perm.manage_channels}** "  # 2^4
                        f"Administrator: **{perm.administrator}** "  # 2^3
                        f"Ban members: **{perm.ban_members}** "  # 2^2
                        f"Kick members: **{perm.kick_members}** "  # 2^1
                        f"Create invites: **{perm.create_instant_invite}**", embed=emb)  # 2^0
