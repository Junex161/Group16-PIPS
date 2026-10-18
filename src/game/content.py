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
    # Key of the level in levels.LEVEL_SCENES.
    key: str = ""


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

# Insights of the other levels; story_content.py fills this table.
OTHER_INSIGHTS = {}


def find_insight(key):
    """Return the insight ``key`` of any level, or None."""
    return INSIGHTS.get(key) or OTHER_INSIGHTS.get(key)


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
    "Count Hackula has p-hacked the land of the Mind, and its findings are crumbling. "
    "Learn how science checks itself, travel through its worlds, try famous "
    "experiments yourself and beat the Count's bosses!"
)

LEVELS = (
    LevelInfo(
        "Prologue: The Replication Crisis",
        "Open Science",
        "Why do so many findings fail to replicate? Explore the old campus and the archive, "
        "learn the basic moves and free the hidden results from the File Drawer.",
        playable=True,
        key="prologue",
    ),
    LevelInfo(
        "Level 1: Focus Fields",
        "Attention",
        "What is attention? Travel through five worlds, collect five insight orbs, win "
        "Professor Fin's flanker challenge and pick the right pipe at the owl's quiz.",
        playable=True,
        key="level_1",
    ),
    LevelInfo(
        "Level 2: Hold Your Horses",
        "Response Inhibition",
        "Can you stop in time? Slide over the ice, freeze at red lights in Neon City, win "
        "Signal Sam's stop-signal race and beat Captain Impulse in the volcano.",
        playable=True,
        key="level_2",
    ),
    LevelInfo(
        "Level 3: Mission Control",
        "Executive Control",
        "Memory, planning and flexibility: feed the Memory Machine, crack the Tower of London "
        "and outwit the Rule Keeper on the space station.",
        playable=True,
        key="level_3",
    ),
    LevelInfo(
        "Finale: Count Hackula's Castle",
        "Everything",
        "The last castle: lava, red lights and a Brute - and Count Hackula himself. "
        "Find him in the dark, hold back on red and let the light of open science in!",
        playable=True,
        key="finale",
    ),
)

# APA-style references for the main deliverable and the README.
REFERENCES = (
    "Aron, A. R., Robbins, T. W., & Poldrack, R. A. (2004). Inhibition and the right inferior "
    "frontal cortex. Trends in Cognitive Sciences, 8(4), 170-177.",
    "Baddeley, A. D., & Hitch, G. (1974). Working memory. In G. H. Bower (Ed.), The psychology "
    "of learning and motivation (Vol. 8, pp. 47-89). Academic Press.",
    "Baumeister, R. F., Bratslavsky, E., Muraven, M., & Tice, D. M. (1998). Ego depletion: "
    "Is the active self a limited resource? Journal of Personality and Social Psychology, "
    "74(5), 1252-1265.",
    "Broadbent, D. E. (1958). Perception and communication. Pergamon Press.",
    "Chambers, C. D. (2013). Registered Reports: A new publishing initiative at Cortex. Cortex, "
    "49(3), 609-610.",
    "Cherry, E. C. (1953). Some experiments on the recognition of speech, with one and "
    "with two ears. Journal of the Acoustical Society of America, 25(5), 975-979.",
    "Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental "
    "storage capacity. Behavioral and Brain Sciences, 24(1), 87-114.",
    "Diamond, A. (2013). Executive functions. Annual Review of Psychology, 64, 135-168.",
    "Donders, F. C. (1969). On the speed of mental processes (W. G. Koster, Trans.). Acta "
    "Psychologica, 30, 412-431. (Original work published 1868)",
    "Eriksen, B. A., & Eriksen, C. W. (1974). Effects of noise letters upon the "
    "identification of a target letter in a nonsearch task. Perception & Psychophysics, "
    "16(1), 143-149.",
    "Grant, D. A., & Berg, E. A. (1948). A behavioral analysis of degree of reinforcement "
    "and ease of shifting to new responses in a Weigl-type card-sorting problem. Journal "
    "of Experimental Psychology, 38(4), 404-411.",
    "Hagger, M. S., Chatzisarantis, N. L. D., Alberts, H., Anggono, C. O., Batailler, C., "
    "Birt, A. R., et al. (2016). A multilab preregistered replication of the ego-depletion "
    "effect. Perspectives on Psychological Science, 11(4), 546-573.",
    "Hautus, M. J. (1995). Corrections for extreme proportions and their biasing effects "
    "on estimated values of d'. Behavior Research Methods, Instruments, & Computers, "
    "27(1), 46-51.",
    "James, W. (1890). The principles of psychology (Vol. 1). Henry Holt.",
    "John, L. K., Loewenstein, G., & Prelec, D. (2012). Measuring the prevalence of "
    "questionable research practices with incentives for truth telling. Psychological "
    "Science, 23(5), 524-532.",
    "Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. Personality "
    "and Social Psychology Review, 2(3), 196-217.",
    "Kirchner, W. K. (1958). Age differences in short-term retention of rapidly changing "
    "information. Journal of Experimental Psychology, 55(4), 352-358.",
    "Lijffijt, M., Kenemans, J. L., Verbaten, M. N., & van Engeland, H. (2005). A meta-analytic "
    "review of stopping performance in attention-deficit/hyperactivity disorder: Deficient "
    "inhibitory motor control? Journal of Abnormal Psychology, 114(2), 216-222.",
    "Logan, G. D., & Cowan, W. B. (1984). On the ability to inhibit thought and action: "
    "A theory of an act of control. Psychological Review, 91(3), 295-327.",
    "Milner, B. (1963). Effects of different brain lesions on card sorting: The role of "
    "the frontal lobes. Archives of Neurology, 9(1), 90-100.",
    "Miyake, A., Friedman, N. P., Emerson, M. J., Witzki, A. H., Howerter, A., & Wager, "
    "T. D. (2000). The unity and diversity of executive functions and their contributions "
    "to complex 'frontal lobe' tasks: A latent variable analysis. Cognitive Psychology, "
    "41(1), 49-100.",
    "Moray, N. (1959). Attention in dichotic listening: Affective cues and the influence "
    "of instructions. Quarterly Journal of Experimental Psychology, 11(1), 56-60.",
    "Munafo, M. R., Nosek, B. A., Bishop, D. V. M., Button, K. S., Chambers, C. D., Percie "
    "du Sert, N., Simonsohn, U., Wagenmakers, E.-J., Ware, J. J., & Ioannidis, J. P. A. "
    "(2017). A manifesto for reproducible science. Nature Human Behaviour, 1, 0021.",
    "Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The "
    "preregistration revolution. Proceedings of the National Academy of Sciences, 115(11), "
    "2600-2606.",
    "Open Science Collaboration. (2015). Estimating the reproducibility of psychological "
    "science. Science, 349(6251), aac4716.",
    "Owen, A. M., McMillan, K. M., Laird, A. R., & Bullmore, E. (2005). N-back working "
    "memory paradigm: A meta-analysis of normative functional neuroimaging studies. Human "
    "Brain Mapping, 25(1), 46-59.",
    "Pavlov, I. P. (1927). Conditioned reflexes: An investigation of the physiological "
    "activity of the cerebral cortex. Oxford University Press.",
    "Posner, M. I. (1980). Orienting of attention. Quarterly Journal of Experimental "
    "Psychology, 32(1), 3-25.",
    "Rogers, R. D., & Monsell, S. (1995). Costs of a predictable switch between simple "
    "cognitive tasks. Journal of Experimental Psychology: General, 124(2), 207-231.",
    "Rosenthal, R. (1979). The file drawer problem and tolerance for null results. "
    "Psychological Bulletin, 86(3), 638-641.",
    "Rueda, M. R., Fan, J., McCandliss, B. D., Halparin, J. D., Gruber, D. B., Lercari, "
    "L. P., & Posner, M. I. (2004). Development of attentional networks in childhood. "
    "Neuropsychologia, 42(8), 1029-1040.",
    "Schachar, R., Logan, G. D., Robaey, P., Chen, S., Ickowicz, A., & Barr, C. (2007). Restraint "
    "and cancellation: Multiple inhibition deficits in attention deficit hyperactivity disorder. "
    "Journal of Abnormal Child Psychology, 35(2), 229-238.",
    "Shallice, T. (1982). Specific impairments of planning. Philosophical Transactions of "
    "the Royal Society of London. B, Biological Sciences, 298(1089), 199-209.",
    "Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: "
    "Undisclosed flexibility in data collection and analysis allows presenting anything "
    "as significant. Psychological Science, 22(11), 1359-1366.",
    "Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained "
    "inattentional blindness for dynamic events. Perception, 28(9), 1059-1074.",
    "Stroop, J. R. (1935). Studies of interference in serial verbal reactions. Journal of "
    "Experimental Psychology, 18(6), 643-662.",
    "Verbruggen, F., Aron, A. R., Band, G. P. H., Beste, C., Bissett, P. G., Brockett, "
    "A. T., et al. (2019). A consensus guide to capturing the ability to inhibit actions "
    "and impulsive behaviors in the stop-signal task. eLife, 8, e46323.",
    "Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. Journal of "
    "Experimental Psychology, 3(1), 1-14.",
    "Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., "
    "et al. (2016). The FAIR Guiding Principles for scientific data management and "
    "stewardship. Scientific Data, 3, 160018.",
)
