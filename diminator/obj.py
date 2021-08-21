from enum import IntEnum

from discord.ext.commands import CommandError


class UltraRockPaperScissor(IntEnum):
    ROCK = 1
    GUN = 2
    LIGHTNING = 3
    DEVIL = 4
    DRAGON = 5
    WATER = 6
    AIR = 7
    PAPER = 8
    SPONGE = 9
    WOLF = 10
    TREE = 11
    HUMAN = 12
    SNAKE = 13
    SCISSOR = 14
    FIRE = 15

    def resolve(self, opponent):
        if self == opponent:
            return 0
        if opponent < self:
            opponent += 15
        if opponent - self > 7:
            return 1
        return -1


class BasePPException(CommandError):
    def __init__(self, message=None, *args):
        self.message = message
        super().__init__(message, args)

    def __str__(self):
        return self.message


class PPNotFound(BasePPException):

    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__("Please set up your pp by `{0}pp`!")
        else:
            super().__init__('Target has no pp.')


class PPStunned(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is stunned! Please use `{0}pp sf` to remove the effect!')
        else:
            super().__init__('Target is stunned!')


class PPLocked(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is locked! Please use `{0}pp lock` to unlock!')
        else:
            super().__init__('Target has enabled lock!')


max_pp_size = 69


class PP:

    def __init__(self, size: int, viagra, sesami, stun=0):
        self.size: int = size
        self.viagra: int = viagra  # -1: Not available 0: Not activated 1-3: rounds left
        self.score = 0
        self.sesami_oil: bool = sesami
        self.stun: int = stun
        self.lock: bool = False

    def draw(self) -> str:
        """Returns the string for displaying pp"""
        description = f'Ɛ{"Ξ" * self.size}＞'
        if self.lock:
            description = f"🔒Locked\n{description}"
        if self.viagra > 0:
            description = f'**{description}**\nViagra rounds left: {self.viagra}'
        elif self.viagra == 0:
            description += '\nViagra available!'
        if self.sesami_oil:
            description += '\nSesami oil'
        if self.size == max_pp_size:
            description += '\n**MAX POWER**'
        if self.stun:
            description += f'\n**STUNNED:** {self.stun} rounds left'
        return description

    def check_lock(self, b):
        if self.lock:
            raise PPLocked(b)
        return self

    def check_stun(self, b):
        if self.stun:
            raise PPStunned(b)
        return self

    def check_all(self, b):
        return self.check_lock(b).check_stun(b)
