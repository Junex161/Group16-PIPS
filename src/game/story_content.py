"""Psychology content of the Prologue and Levels 2 and 3.

Like Level 1, every level tells one story with short animations (see
``story_animations.py``); the player collects them as insights. Each level
ends with a "big picture" animation and a quiz about its insights.

* Prologue, Open Science: why findings have to be replicated, what the
  Reproducibility Project found, why the file drawer hides null results and
  how Open Science helps.
* Level 2, response inhibition: stopping an action, go/no-go, the race
  between going and stopping, the Stroop effect, and a famous effect that
  did not replicate (ego depletion).
* Level 3, executive control: the three core executive functions and the
  tasks that measure them (n-back, Tower of London, task switching and
  card sorting).

``register()`` adds the insights and skills to the tables in ``content.py``
so that the animations, the notebook and the home screen know them.
"""

from . import content
from .content import Insight, Skill

STORY_INSIGHTS = {
    insight.key: insight
    for insight in (
        # ----- Prologue -----
        Insight(
            key="replication",
            term="REPLICATION",
            short_name="Replication",
            definition="A finding becomes trustworthy when another lab repeats the study and finds it again.",
            source="Open Science Collaboration (2015)",
        ),
        Insight(
            key="reproducibility",
            term="THE REPLICATION CRISIS",
            short_name="Replication crisis",
            definition="Of 100 repeated studies, 97% of the originals but only 36% of the "
            "replications were significant, with effects about half as large.",
            source="Open Science Collaboration (2015)",
        ),
        Insight(
            key="file_drawer",
            term="PUBLICATION BIAS",
            short_name="File drawer problem",
            definition="Significant results get published, null results vanish in the file "
            "drawer - so the literature looks more convincing than the evidence is.",
            source="Rosenthal (1979)",
        ),
        Insight(
            key="open_science",
            term="OPEN SCIENCE",
            short_name="Open Science",
            definition="Preregister the plan, share data and materials, and replicate - so that "
            "everyone can check the work.",
            source="Nosek et al. (2018); Munafo et al. (2017)",
        ),
        # ----- Level 2 -----
        Insight(
            key="inhibition",
            term="RESPONSE INHIBITION",
            short_name="Response inhibition",
            definition="Stopping an action that is no longer right - even when it is already on its way.",
            source="Logan & Cowan (1984)",
        ),
        Insight(
            key="go_nogo",
            term="GO / NO-GO",
            short_name="Go/no-go task",
            definition="React to frequent GO signals, hold still on rare NO-GO signals. Habit makes "
            "holding back hard.",
            source="Donders (1969)",
        ),
        Insight(
            key="horse_race",
            term="THE HORSE-RACE MODEL",
            short_name="Stop-signal race",
            definition="A GO process and a STOP process race. Whoever finishes first decides "
            "whether you act. Its speed is the SSRT.",
            source="Logan & Cowan (1984); Verbruggen et al. (2019)",
        ),
        Insight(
            key="stroop",
            term="THE STROOP EFFECT",
            short_name="Stroop effect",
            definition="Naming the ink colour of a colour word is slow when they clash: reading is "
            "automatic and has to be held back.",
            source="Stroop (1935)",
        ),
        Insight(
            key="ego_depletion",
            term="A MYTH BUSTED: EGO DEPLETION",
            short_name="Ego depletion",
            definition="Self-control as a battery that runs empty? 23 labs with 2,141 people found "
            "an effect close to zero.",
            source="Baumeister et al. (1998); Hagger et al. (2016)",
        ),
        # ----- Level 3 -----
        Insight(
            key="executive_functions",
            term="EXECUTIVE FUNCTIONS",
            short_name="Executive functions",
            definition="The mind's control room: updating, shifting and inhibiting - related, "
            "but separate abilities.",
            source="Miyake et al. (2000); Diamond (2013)",
        ),
        Insight(
            key="updating",
            term="WORKING-MEMORY UPDATING",
            short_name="Updating (n-back)",
            definition="Keeping the last few items in mind and replacing the oldest one, as in "
            "the n-back task.",
            source="Kirchner (1958); Owen et al. (2005)",
        ),
        Insight(
            key="planning",
            term="PLANNING",
            short_name="Planning (Tower of London)",
            definition="Thinking several moves ahead before acting - measured by the Tower of London.",
            source="Shallice (1982)",
        ),
        Insight(
            key="switching",
            term="TASK SWITCHING",
            short_name="Switch cost",
            definition="Changing from one task to another costs time, even when you know the switch is coming.",
            source="Rogers & Monsell (1995)",
        ),
        Insight(
            key="card_sorting",
            term="CARD SORTING & PERSEVERATION",
            short_name="Card sorting",
            definition="When a sorting rule changes without warning, people keep using the old one "
            "for a while - they perseverate.",
            source="Grant & Berg (1948); Milner (1963)",
        ),
    )
}

# The insights of each level, in the order they are met; the quiz asks about them.
LEVEL_INSIGHTS = {
    "prologue": ("replication", "reproducibility", "file_drawer", "open_science"),
    "level_2": ("inhibition", "go_nogo", "horse_race", "stroop", "ego_depletion"),
    "level_3": ("executive_functions", "updating", "planning", "switching", "card_sorting"),
}

STORY_SKILLS = {
    skill.key: skill
    for skill in (
        Skill(
            key="stop",
            name="Stop Signal",
            button="R",
            pages=("Press R: a STOP wave freezes nearby enemies, fire bars and bosses for a moment.",),
            source="Logan & Cowan (1984)",
        ),
    )
}
# Skills whose shrine first plays an animation.
STORY_SKILL_ANIMATIONS = {"stop": "stop_skill"}

# What each character says, kept to one short line per page.
DIALOGUES = {
    "shell_intro": (
        "Welcome, young researcher! I am Professor Shell - slow, but careful.",
        "Count Hackula has p-hacked our archive. Watch what he did ...",
    ),
    "shell_again": ("Check every finding! The pipe at the end leads into the archive.",),
    "shell_end": ("You freed the hidden results! Now show the owl what you learned.",),
    "drawer_intro": ("'Count Hackula's orders: only SHINY results get out of here!'",),
    "sam_intro": (
        "Beep! I'm Signal Sam. Count Hackula's Captain Impulse waits in the volcano.",
        "Learn to stop in my race and I'll open the city gate!",
    ),
    "sam_done": ("Green means go, red means stop. The gate is open!",),
    "impulse_intro": ("'Stopping is for losers! Hackula's champion ACTS FIRST!'",),
    "machine_intro": ("BZZT. Feed me letters, and I open the door to the control room.",),
    "machine_done": ("Memory banks full. The door to the control room is open!",),
    "tower_intro": ("Hackula locked this gate with the Tower of London. Plan before you move!",),
    "tower_done": ("Click! The gate swings open.",),
    "rules_intro": ("'I am Hackula's last trick: I change the rules whenever I like!'",),
    "owl_quiz": ("Which idea is on my board? Jump into the right block from below!",),
}


def register():
    """Add the new insights and skills to the tables in ``content.py``."""
    content.OTHER_INSIGHTS.update(STORY_INSIGHTS)
    content.SKILLS.update(STORY_SKILLS)
