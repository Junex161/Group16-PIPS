"""Psychology content: insights, quiz topics, skills, texts and references.

An insight is what the player takes away from one short animation about an
attention phenomenon (see ``insight_animations.py``). The content is written
at the level of an introductory general psychology course and kept short:
the animations carry the explanation, the text only names it. On-screen text
is plain ASCII because the default pygame font has no special characters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Insight:
    """
    What the player takes away from one animation (see insight_animations.py).

    ``term`` is the key term in capitals, ``short_name`` the name used as an
    answer of the quiz and ``definition`` a single sentence.
    """

    key: str
    term: str
    short_name: str
    definition: str
    source: str


@dataclass(frozen=True)
class Skill:
    """A skill the hero can use; ``pages`` explain it when it is learned."""

    key: str
    name: str
    button: str
    pages: tuple
    source: str = ""


@dataclass(frozen=True)
class LevelInfo:
    """One entry of the level list on the home screen."""

    title: str
    topic: str
    description: str
    playable: bool = False


INSIGHTS = {
    insight.key: insight
    for insight in (
        Insight(
            key="attention",
            term="ATTENTION",
            short_name="Attention",
            definition="Selecting some information for further processing - and ignoring the rest.",
            source="James (1890); Broadbent (1958)",
        ),
        Insight(
            key="cocktail_party",
            term="SELECTIVE ATTENTION",
            short_name="Cocktail party effect",
            definition="Tuning in to one voice and out of the others - unless your own name comes up.",
            source="Cherry (1953); Moray (1959)",
        ),
        Insight(
            key="gorilla",
            term="INATTENTIONAL BLINDNESS",
            short_name="Inattentional blindness",
            definition="Missing something obvious because your attention is busy elsewhere.",
            source="Simons & Chabris (1999)",
        ),
        Insight(
            key="flanker",
            term="THE FLANKER EFFECT",
            short_name="Flanker effect",
            definition="Distractors next to a target slow you down when they point the other way.",
            source="Eriksen & Eriksen (1974)",
        ),
        Insight(
            key="spotlight",
            term="COVERT ATTENTION",
            short_name="Covert attention",
            definition="Moving the spotlight of attention without moving your eyes.",
            source="Posner (1980)",
        ),
    )
}

# Cards for animations that explain a skill rather than an insight.
SKILL_CARDS = {
    "qrp": Insight(
        key="qrp",
        term="QUESTIONABLE RESEARCH PRACTICES",
        short_name="QRPs",
        definition="p-hacking and HARKing turn chance into 'findings'. Fine against enemies - never in research!",
        source="Simmons et al. (2011); Kerr (1998)",
    ),
    "fear": Insight(
        key="fear",
        term="FEAR CONDITIONING",
        short_name="Fear conditioning",
        definition="A neutral stimulus that is paired with something frightening soon causes fear on its "
        "own. Little Albert learned to fear a white rat that had been paired with a loud noise.",
        source="Watson & Rayner (1920); Pavlov (1927)",
    ),
}
# Skills whose shrine first plays an animation, then shows the key to press.
SKILL_ANIMATIONS = {"blaster": "qrp", "fear": "fear"}

# The phenomena the owl's quiz asks about: it shows the animation of one of
# them and the player picks its name.
QUIZ_TOPICS = ("cocktail_party", "gorilla", "flanker", "spotlight")

SKILLS = {
    skill.key: skill
    for skill in (
        Skill(
            key="punch",
            name="Punch",
            button="F",
            pages=("Press F to punch enemies and cracked crates.",),
        ),
        Skill(
            key="blaster",
            name="QRP Blaster",
            button="G",
            pages=("Press G to fire Questionable Research Practices such as p-hacking. Take it with you to the next level!",),
            source="John et al. (2012); Kerr (1998)",
        ),
        Skill(
            key="double_jump",
            name="Double Jump",
            button="SPACE x2",
            pages=("Press SPACE again in the air to jump a second time.",),
        ),
        Skill(
            key="fear",
            name="Fear Conditioning",
            button="Q",
            pages=("Press Q: your bell scares nearby enemies away.",),
            source="Pavlov (1927); Watson & Rayner (1920)",
        ),
    )
}

# The "ammunition" of the QRP Blaster: questionable research practices.
QRP_SHOTS = (
    "p-hacking",
    "HARKing",
    "cherry-picking",
    "optional stopping",
    "selective reporting",
    "outlier fishing",
)

STORY = (
    "Something is wrong in the land of the Mind: knowledge about psychology has been "
    "scattered across its worlds. Travel through them, try famous experiments "
    "yourself and prove what you have learned!"
)

LEVELS = (
    LevelInfo(
        "Prologue: The Replication Crisis",
        "Open Science",
        "How the story begins. This level is still under construction.",
    ),
    LevelInfo(
        "Level 1: Focus Fields",
        "Attention",
        "What is attention? Travel through five worlds, collect five insight orbs, win "
        "Professor Fin's flanker challenge and pick the right pipe at the owl's quiz.",
        playable=True,
    ),
    LevelInfo(
        "Level 2",
        "Response Inhibition",
        "Can you stop yourself in time? This level is still under construction.",
    ),
    LevelInfo(
        "Level 3",
        "Executive Control",
        "Memory, planning and flexibility. This level is still under construction.",
    ),
)

# APA-style references for the main deliverable and the README.
REFERENCES = (
    "Broadbent, D. E. (1958). Perception and communication. Pergamon Press.",
    "Cherry, E. C. (1953). Some experiments on the recognition of speech, with one and "
    "with two ears. Journal of the Acoustical Society of America, 25(5), 975-979.",
    "Eriksen, B. A., & Eriksen, C. W. (1974). Effects of noise letters upon the "
    "identification of a target letter in a nonsearch task. Perception & Psychophysics, "
    "16(1), 143-149.",
    "James, W. (1890). The principles of psychology (Vol. 1). Henry Holt.",
    "John, L. K., Loewenstein, G., & Prelec, D. (2012). Measuring the prevalence of "
    "questionable research practices with incentives for truth telling. Psychological "
    "Science, 23(5), 524-532.",
    "Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. Personality "
    "and Social Psychology Review, 2(3), 196-217.",
    "Moray, N. (1959). Attention in dichotic listening: Affective cues and the influence "
    "of instructions. Quarterly Journal of Experimental Psychology, 11(1), 56-60.",
    "Pavlov, I. P. (1927). Conditioned reflexes: An investigation of the physiological "
    "activity of the cerebral cortex. Oxford University Press.",
    "Posner, M. I. (1980). Orienting of attention. Quarterly Journal of Experimental "
    "Psychology, 32(1), 3-25.",
    "Rueda, M. R., Fan, J., McCandliss, B. D., Halparin, J. D., Gruber, D. B., Lercari, "
    "L. P., & Posner, M. I. (2004). Development of attentional networks in childhood. "
    "Neuropsychologia, 42(8), 1029-1040.",
    "Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: "
    "Undisclosed flexibility in data collection and analysis allows presenting anything "
    "as significant. Psychological Science, 22(11), 1359-1366.",
    "Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained "
    "inattentional blindness for dynamic events. Perception, 28(9), 1059-1074.",
    "Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. Journal of "
    "Experimental Psychology, 3(1), 1-14.",
)
