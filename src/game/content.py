"""Psychology content: attention notes, quiz questions, skills, references.

The notes are the cues hidden in the level. Each quiz question can be answered
with exactly one note. The content is written at the level of an introductory
general psychology course. On-screen text is kept to plain ASCII because the
default pygame font has no special characters.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cue:
    """One attention note the player can find in the level."""

    key: str
    title: str
    text: str
    source: str


@dataclass(frozen=True)
class Question:
    """A multiple-choice question that the note ``cue_key`` answers."""

    cue_key: str
    prompt: str
    options: tuple
    correct_index: int
    explanation: str


CUES = {
    cue.key: cue
    for cue in (
        Cue(
            key="cocktail_party",
            title="The Cocktail Party Effect",
            text=(
                "At a noisy party you can follow one conversation and tune out all the "
                "others. Focusing on one source of information while ignoring the rest "
                "is called SELECTIVE ATTENTION."
            ),
            source="Cherry (1953)",
        ),
        Cue(
            key="filter",
            title="Broadbent's Filter",
            text=(
                "Broadbent described attention as a bottleneck. An early FILTER selects "
                "one message by its physical features, such as pitch or location, BEFORE "
                "its meaning is processed. Treisman later argued that unattended "
                "messages are only turned down (attenuated), not blocked completely."
            ),
            source="Broadbent (1958); Treisman (1964)",
        ),
        Cue(
            key="gorilla",
            title="The Invisible Gorilla",
            text=(
                "People who count basketball passes in a video often miss a person in a "
                "gorilla suit walking right through the scene. Failing to notice a "
                "clearly visible but unexpected object while your attention is busy "
                "elsewhere is called INATTENTIONAL BLINDNESS."
            ),
            source="Simons & Chabris (1999)",
        ),
        Cue(
            key="flanker",
            title="The Flanker Effect",
            text=(
                "When a target is surrounded by flankers that point the OPPOSITE way "
                "(incongruent), people respond more slowly and make more errors than "
                "when the flankers point the same way (congruent). This difference is "
                "the FLANKER EFFECT. It shows that we cannot fully ignore distractors."
            ),
            source="Eriksen & Eriksen (1974)",
        ),
        Cue(
            key="spotlight",
            title="The Spotlight of Attention",
            text=(
                "Attention works like a spotlight that you can move without moving your "
                "eyes. Shifting attention while the eyes stay still is COVERT attention; "
                "moving your eyes to a location is OVERT attention. A cue that tells you "
                "where a target will appear makes you respond faster."
            ),
            source="Posner (1980)",
        ),
        Cue(
            key="networks",
            title="Three Attention Networks",
            text=(
                "Attention is not one single thing. Three networks work together: "
                "ALERTING (getting and staying ready), ORIENTING (selecting where to "
                "attend) and EXECUTIVE CONTROL (resolving conflict, such as ignoring "
                "flankers). The Attention Network Test measures all three."
            ),
            source="Posner & Petersen (1990); Fan et al. (2002)",
        ),
    )
}

@dataclass(frozen=True)
class Skill:
    """A skill Pip can use; ``pages`` explain it when it is learned."""

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


SKILLS = {
    skill.key: skill
    for skill in (
        Skill(
            key="punch",
            name="Punch",
            button="F",
            pages=(
                "Press F to punch. A punch knocks out most enemies in front of you, even "
                "spiky ones that you cannot jump on, and it smashes cracked crates.",
            ),
        ),
        Skill(
            key="double_jump",
            name="Double Jump",
            button="SPACE x2",
            pages=(
                "You learned the DOUBLE JUMP! Jump with SPACE (or W), then press SPACE "
                "(or W) AGAIN while you are in the air. The timing does not matter. Use it "
                "to climb high walls and to cross wide pits.",
            ),
        ),
        Skill(
            key="fear",
            name="Fear Conditioning",
            button="Q",
            pages=(
                "You learned FEAR CONDITIONING! In classical conditioning a neutral "
                "stimulus is paired with something frightening. Soon the neutral "
                "stimulus alone triggers fear: it has become a CONDITIONED STIMULUS.",
                "In a famous study a child, 'Little Albert', learned to fear a white rat "
                "after it was shown together with a loud, scary noise.",
                "Press Q to ring your bell together with a scary flash. Enemies nearby "
                "learn to fear the bell and run away. Some enemies are too tough to "
                "punch: scaring them is the only way past!",
            ),
            source="Pavlov (1927); Watson & Rayner (1920)",
        ),
    )
}

STORY = (
    "Something is wrong in the land of the Mind: knowledge about psychology has been "
    "scattered across its worlds. Travel through them, collect the lost notes, master "
    "famous experiments and prove what you have learned!"
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
        "Cross meadows, a dark cave and the sunset heights. Find six notes about "
        "attention, win Professor Fin's flanker challenge and answer the owl's question.",
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

QUESTIONS = (
    Question(
        cue_key="cocktail_party",
        prompt=(
            "At a loud party you follow one conversation and ignore the others. "
            "What is this ability called?"
        ),
        options=(
            "Divided attention",
            "Selective attention",
            "Inattentional blindness",
            "Sustained attention",
        ),
        correct_index=1,
        explanation="Focusing on one source while ignoring others is selective attention.",
    ),
    Question(
        cue_key="filter",
        prompt="According to Broadbent's filter model, when is information selected?",
        options=(
            "Late, after the meaning of every message is analysed",
            "Never, all information is processed fully",
            "Early, by physical features, before meaning is processed",
            "Only while the eyes are moving",
        ),
        correct_index=2,
        explanation="Broadbent proposed an early filter based on physical features.",
    ),
    Question(
        cue_key="gorilla",
        prompt=(
            "Viewers counting basketball passes fail to see a gorilla walking through "
            "the scene. What is this phenomenon called?"
        ),
        options=(
            "Inattentional blindness",
            "The cocktail party effect",
            "The flanker effect",
            "Covert orienting",
        ),
        correct_index=0,
        explanation="Missing an unexpected, visible object is inattentional blindness.",
    ),
    Question(
        cue_key="flanker",
        prompt="What is the flanker effect?",
        options=(
            "Faster responses when flankers point the opposite way",
            "Seeing flankers that are not really there",
            "Responding equally fast to all displays",
            "Slower, less accurate responses when flankers point the opposite way",
        ),
        correct_index=3,
        explanation="Incongruent flankers create conflict that slows responses down.",
    ),
    Question(
        cue_key="spotlight",
        prompt="What is COVERT attention?",
        options=(
            "Moving your eyes towards an object",
            "Shifting attention without moving your eyes",
            "Paying attention to two tasks at once",
            "Staying alert for a long time",
        ),
        correct_index=1,
        explanation="Covert attention shifts the 'spotlight' while the eyes stay still.",
    ),
    Question(
        cue_key="networks",
        prompt="Which three attention networks did Posner and Petersen describe?",
        options=(
            "Seeing, hearing and touching",
            "Encoding, storage and retrieval",
            "Alerting, orienting and executive control",
            "Filtering, attenuation and late selection",
        ),
        correct_index=2,
        explanation="The three networks are alerting, orienting and executive control.",
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
    "Fan, J., McCandliss, B. D., Sommer, T., Raz, A., & Posner, M. I. (2002). Testing the "
    "efficiency and independence of attentional networks. Journal of Cognitive "
    "Neuroscience, 14(3), 340-347.",
    "Pavlov, I. P. (1927). Conditioned reflexes: An investigation of the physiological "
    "activity of the cerebral cortex. Oxford University Press.",
    "Posner, M. I. (1980). Orienting of attention. Quarterly Journal of Experimental "
    "Psychology, 32(1), 3-25.",
    "Posner, M. I., & Petersen, S. E. (1990). The attention system of the human brain. "
    "Annual Review of Neuroscience, 13, 25-42.",
    "Rueda, M. R., Fan, J., McCandliss, B. D., Halparin, J. D., Gruber, D. B., Lercari, "
    "L. P., & Posner, M. I. (2004). Development of attentional networks in childhood. "
    "Neuropsychologia, 42(8), 1029-1040.",
    "Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained "
    "inattentional blindness for dynamic events. Perception, 28(9), 1059-1074.",
    "Treisman, A. M. (1964). Selective attention in man. British Medical Bulletin, "
    "20(1), 12-16.",
    "Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. Journal of "
    "Experimental Psychology, 3(1), 1-14.",
)
