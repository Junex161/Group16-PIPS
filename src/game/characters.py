"""The heroes the player can choose from. They differ only in their looks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    """Looks of a playable character; colours are RGB tuples.

    ``ears`` is "pointed" or "long" and ``tail`` is "bushy", "thin" or "puff".
    """

    key: str
    name: str
    description: str
    fur: tuple
    jacket: tuple
    scarf: tuple
    ears: str = "pointed"
    tail: str = "bushy"


CHARACTERS = (
    Character("pip", "Pip", "A curious fox who never misses a detail.", (240, 140, 52), (58, 158, 172), (222, 62, 66)),
    Character("luna", "Luna", "A calm cat with razor-sharp focus.", (132, 126, 168), (236, 120, 150), (250, 214, 90), tail="thin"),
    Character("bo", "Bo", "A quick bunny who is always alert.", (236, 232, 224), (96, 170, 96), (70, 120, 220), ears="long", tail="puff"),
)
