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
            key="open_science",
            term="OPEN SCIENCE",
            short_name="Open Science",
            definition="Making every step of research - plan, data, analysis, paper - transparent, "
            "checkable and free to access.",
            source="Nosek et al. (2018); Munafo et al. (2017)",
        ),
        Insight(
            key="qrps",
            term="QUESTIONABLE RESEARCH PRACTICES",
            short_name="QRPs",
            definition="p-hacking, HARKing and cherry-picking push results towards 'significant' - "
            "usually not out of bad intent, but under pressure to publish.",
            source="John et al. (2012); Kerr (1998); Simmons et al. (2011)",
        ),
        Insight(
            key="reproducibility",
            term="THE REPLICATION CRISIS",
            short_name="Replication crisis",
            definition="100 psychology studies were repeated: 97 originals were significant, but only "
            "35 of their replications (36%), with effects about half as large.",
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
            key="open_practices",
            term="THE OPEN SCIENCE TOOLBOX",
            short_name="Preregistration & open data",
            definition="Preregister (or use a Registered Report), share data, materials and scripts "
            "(FAIR), and replicate - so that everyone can check the work.",
            source="Nosek et al. (2018); Chambers (2013); Wilkinson et al. (2016)",
        ),
        # ----- Level 2 -----
        Insight(
            key="inhibition",
            term="RESPONSE INHIBITION",
            short_name="Response inhibition",
            definition="Holding back a strong, automatic ('prepotent') response that no longer fits - "
            "even when it is already on its way.",
            source="Logan & Cowan (1984); Verbruggen et al. (2019)",
        ),
        Insight(
            key="go_nogo",
            term="GO / NO-GO",
            short_name="Go/no-go task",
            definition="Respond to frequent GO signals, not to rare NO-GO signals. It measures "
            "holding back BEFORE acting (restraint); the stop-signal task measures cancelling.",
            source="Donders (1969); Schachar et al. (2007)",
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
            key="brain_brake",
            term="THE BRAIN'S BRAKE",
            short_name="Inhibition in brain & life",
            definition="A network around the right inferior frontal cortex helps stop actions. People "
            "with ADHD stop more slowly on average (longer SSRT).",
            source="Aron et al. (2004); Lijffijt et al. (2005)",
        ),
        # ----- Level 3 -----
        Insight(
            key="executive_functions",
            term="EXECUTIVE FUNCTIONS",
            short_name="Executive functions",
            definition="Top-down control in the prefrontal cortex: working memory, inhibition and "
            "cognitive flexibility - related, but separate. Planning builds on them.",
            source="Miyake et al. (2000); Diamond (2013)",
        ),
        Insight(
            key="updating",
            term="WORKING MEMORY",
            short_name="Working memory (n-back)",
            definition="A small mental workspace for about four items. The n-back task tests how well "
            "we keep it up to date.",
            source="Baddeley & Hitch (1974); Cowan (2001); Kirchner (1958)",
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
            "for a while - patients with frontal-lobe damage much longer.",
            source="Grant & Berg (1948); Milner (1963)",
        ),
    )
}

# The insights of each level, in the order they are met; the quiz asks about them.
LEVEL_INSIGHTS = {
    "prologue": ("open_science", "qrps", "reproducibility", "file_drawer", "open_practices"),
    "level_2": ("inhibition", "go_nogo", "horse_race", "stroop", "brain_brake"),
    "level_3": ("executive_functions", "updating", "planning", "switching", "card_sorting"),
    # The finale has no new insights: it tests everything with the last boss.
    "finale": (),
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
    "hackula_intro": ("'So you checked all my findings? You will never see the light of day again!'",),
    "owl_quiz": ("Which idea is on my board? Jump into the right block from below!",),
}


def register():
    """Add the new insights and skills to the tables in ``content.py``."""
    content.OTHER_INSIGHTS.update(STORY_INSIGHTS)
    content.SKILLS.update(STORY_SKILLS)
