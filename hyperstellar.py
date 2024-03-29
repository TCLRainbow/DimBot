import dimsecret
import missile
import coc

clan_tag = '#2QU2UCJJC'


class Hyperstellar(missile.Cog):

    def __init__(self, bot):
        super().__init__(bot, 'Hyperstellar')
        self.clan_log = None
        self.coc = coc.EventsClient()
        self.coc.add_war_updates(clan_tag)

        @self.coc.event
        @coc.WarEvents.state()
        async def on_war_state(old, new: coc.ClanWar):
            if not new.is_cwl:
                if new.state == 'inWar':
                    await self.clan_log.send('War has started: ' + new.opponent.name)
                elif new.state == 'warEnded':
                    msg = "War has ended. The following members didn't attack:\n" + \
                          f"{', '.join(member.name for member in new.members if not member.is_opponent and not member.attacks)}"
                    await self.clan_log.send(msg)

        @self.coc.event
        @coc.WarEvents.war_attack()
        async def on_war_atk(atk: coc.WarAttack, war: coc.ClanWar):
            attacker, defender = atk.attacker, atk.defender
            if not attacker.is_opponent and not war.is_cwl:
                name, pos = attacker.name, f'({attacker.map_position}) => ({defender.map_position})'
                atk_s = -war.start_time.seconds_until - atk.duration
                atk_h, atk_s = divmod(atk_s, 3600)
                atk_m, atk_s = divmod(atk_s, 60)
                atk_time = f'{atk_h}h {atk_m}m {atk_s}s'
                attack_count = str(len(attacker.attacks))
                if attack_count == '2' and atk_h < 12:
                    atk_time += ' ⚠️ Early'
                elif attack_count == '1' and atk_h >= 12:
                    atk_time += ' ⚠️ Late'
                if attacker.map_position != defender.map_position and atk_h < 12:
                    pos = missile.underline(pos, 2)
                await self.clan_log.send(f'[ATK] {name} {pos} {attack_count}⚔️ @{atk_time}')

    @missile.Cog.listener()
    async def on_ready(self):
        self.clan_log = self.bot.get_cog('Hamilton').bot_test if dimsecret.debug else self.bot.get_channel(
            1099026457268863017)
        await self.coc.login_with_tokens(dimsecret.coc)
