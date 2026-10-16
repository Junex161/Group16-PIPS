# Group16-PIPS
Group 16 in the PIPS Assignment :))

## Mind Quest

Mind Quest is an educational jump-and-run game about general psychology, written in Python with pygame. It is our group project for the Programming in Psychological Science (PIPS) course of the Research Master Psychology at the University of Amsterdam.

The game tells one story: Count Hackula has p-hacked the land of the Mind. A prologue introduces Open Science, and three levels teach attention, response inhibition and executive control. Every level teaches with short animations instead of long texts, contains a real experiment whose data are saved, has a boss that turns the topic into a game mechanic, and closes with a quiz. Levels are chosen on the home screen and follow each other in story order; each starts with a title card that tells the next part of the story, bosses and new mechanics are shown in short animations before they are needed, and the story ends with a finale after the last boss.

| Level | Topic | Worlds | Experiment (data saved) | Boss |
| --- | --- | --- | --- | --- |
| Prologue: The Replication Crisis | Open Science | Old Campus, the Archive | - (tutorial level) | The File Drawer: punch its drawers open to free hidden null results (publication bias) |
| Level 1: Focus Fields | Attention | meadow, woods, cave, sky, sunset | child flanker task | Professor Fin's flanker task is the mini boss |
| Level 2: Hold Your Horses | Response inhibition | Frost Peaks (slippery ice), Neon City (red-light zones), Volcano Fortress | stop-signal task | Captain Impulse: hit it on green, hold back on red |
| Level 3: Mission Control | Executive control | Clockwork Factory (conveyors, switch blocks), Space Station (low gravity) | 2-back task, Tower of London | The Rule Keeper: a card-sorting fight whose rule changes without warning |

### Level 1

Level 1, "Focus Fields", is about **attention**. The level tells one story about what attention is, mostly with pictures: touching a glowing orb plays a short animation (a few beats with one caption line each), and the player collects five insights:

| Insight | What the animation shows | Source |
| --- | --- | --- |
| Attention | a flood of information, a bottleneck, and attention selecting what gets through | James (1890); Broadbent (1958) |
| Selective attention | a party where you tune in to one voice, until your own name breaks through | Cherry (1953); Moray (1959) |
| Inattentional blindness | counting ball passes while a gorilla walks through | Simons & Chabris (1999) |
| The flanker effect | fish swimming the other way pull at your answer (after Professor Fin's flanker task) | Eriksen & Eriksen (1974) |
| Covert attention | an arrow moves the spotlight of attention while the eyes stay still | Posner (1980) |

Before the end, the owl shows "the big picture", a map that connects the four phenomena to attention. Then it plays one of the animations on its board, and the player enters the pipe with the right name; only that pipe leads to the goal. The level has six worlds that are connected by pipes: the meadow, the Whispering Woods, the Crystal Cave, the Sky Bridge, the Sunset Heights and a secret bonus room. Besides enemies, spikes and moving platforms they contain springs, crumbling platforms and spinning fire bars.

Professor Fin's Pond Challenge in the middle of the level is a real child flanker task (Rueda et al., 2004) and doubles as the experiment script: every attempt is saved as a CSV file in `data/`, and the player sees a bar chart of their own reaction times.

### Prologue, Level 2 and Level 3

| Level | Insights (one animation each) | Sources |
| --- | --- | --- |
| Prologue | replication; the Reproducibility Project (97% of 100 original studies vs. 36% of their replications significant, effects about half as large); the file drawer problem; Open Science | Open Science Collaboration (2015); Rosenthal (1979); Nosek et al. (2018); Munafo et al. (2017) |
| Level 2 | response inhibition; go/no-go; the horse-race model of stopping; the Stroop effect; a myth check on ego depletion | Logan & Cowan (1984); Donders (1969); Verbruggen et al. (2019); Stroop (1935); Baumeister et al. (1998); Hagger et al. (2016) |
| Level 3 | executive functions (updating, shifting, inhibiting); n-back updating; planning; task switching; card sorting and perseveration | Miyake et al. (2000); Diamond (2013); Kirchner (1958); Owen et al. (2005); Shallice (1982); Rogers & Monsell (1995); Grant & Berg (1948); Milner (1963) |

Signal Sam's stop-signal race in Neon City opens the city gate and teaches the new skill **Stop Signal** (R), which freezes nearby enemies, fire bars and bosses for a moment. In Level 3 the Tower of London opens the factory gate and the Memory Machine's 2-back task opens the door to the control room. The Prologue doubles as the tutorial: every move is introduced before it is needed.

## Getting started

The game needs Python 3.12 or newer, pygame and NumPy:

```bash
git clone https://github.com/Junex161/Group16-PIPS.git
cd Group16-PIPS
pip install -r requirements.txt
```

Start the game from the project folder with

```bash
python run_game.py
```

or run `run_game.py` in PyCharm. From a notebook or another script:

```python
from src.game import run_game

saved_files = run_game(participant_id="p-001")  # returns the data files of all experiments
```

## How to play

| Key | Action |
| --- | --- |
| A / D | walk left and right |
| Space or W | jump (press again in the air for a double jump, once learned) |
| S | fall faster; standing on a pipe: enter it |
| F | punch enemies and crates |
| G | fire the QRP Blaster (unlocked at the end of Level 1): its shots are questionable research practices such as p-hacking |
| Q | fear conditioning (once learned): nearby enemies run away |
| R | Stop Signal (learned in Level 2): freeze nearby enemies, fire bars and bosses |
| E | talk and read signs |
| Tab | open the notebook with the earned insights |
| M | sound on / off |
| Esc | pause |
| P (or F1) | admin mode for testing: fly, take no damage, and skip challenges with the number keys |

Admin mode can be switched off for data collection with `run_game(allow_admin=False)`; a skipped experiment never writes a data file.

Question blocks hold sparks, hearts and three items: the Zoom-shroom (run faster), the Focus Star (invincible for a few seconds) and the Shield (absorbs one hit). New skills come with short animations as well: punching, fear conditioning (a bell is paired with a scary flash until the bell alone scares enemies away) and, as the reward at the very end, the QRP Blaster (p-hacking and HARKing). Pipes show a short loading screen, the Pond Challenge has its own calm music, and reaching the goal sets off fireworks.

The player has three hearts. Enemies and spikes cost a heart, falling costs a heart and sends the player back to the last checkpoint, and without hearts the level starts again from its beginning.

The home screen offers three difficulty modes with the same map. **Easy** gives five hearts, higher jumps, narrower pits, half as many and slower enemies, no heart loss for falling or wrong quiz answers, and a 75% pass mark in the flanker task. **Medium** is the standard game. **Hard** has faster enemies and less room for mistakes. The modes are defined in `DIFFICULTIES` in `src/game/config.py`.

## Experiment data

Every attempt at an experiment writes one CSV file `data/<task>_<participant>_<timestamp>_attempt-<n>.csv` with one row per trial. All files start with the columns `participant_id` and `attempt`. Design and timing of each task can be changed in `src/game/config.py`.

### Flanker task (Level 1)

Each attempt at Professor Fin's Pond Challenge writes one file `data/flanker_<participant>_<timestamp>_attempt-<n>.csv` with one row per trial:

| Column | Meaning |
| --- | --- |
| `participant_id` | anonymous participant label |
| `attempt` | number of the attempt within the game session |
| `block` | `practice` or `test` |
| `trial` | trial number within the block |
| `condition` | `congruent`, `incongruent` or `neutral` (target alone) |
| `target_direction` | direction of the middle fish, `left` or `right` |
| `response` | `left`, `right` or empty (no response within 1.7 seconds) |
| `correct` | `True` or `False` |
| `rt_ms` | reaction time in milliseconds, empty without a response |

The task is modelled on the flanker part of the child Attention Network Test (Rueda et al., 2004). Its design and timing can be changed with `FlankerSettings` in `src/game/config.py`.

### Stop-signal task (Level 2), `stopsignal_*.csv`

A race car points left or right (press A or D); on a quarter of the trials a STOP sign follows after the stop-signal delay, and no key should be pressed. The delay follows a staircase in steps of 50 ms (Verbruggen et al., 2019). Settings: `StopSignalSettings`.

| Column | Meaning |
| --- | --- |
| `block`, `trial` | `practice` or `test`, and the trial number |
| `trial_type` | `go` or `stop` |
| `direction` | direction of the car, `left` or `right` |
| `ssd_ms` | stop-signal delay in milliseconds (empty on go trials) |
| `response` | `left`, `right` or empty (no key pressed within 1.25 seconds) |
| `correct` | go: the right key in time; stop: no key pressed |
| `rt_ms` | reaction time in milliseconds, empty without a response |

### 2-back task (Level 3), `nback_*.csv`

Letters appear one by one; the player presses SPACE when a letter equals the one two steps back (Kirchner, 1958). Columns: `block`, `n`, `trial`, `letter`, `is_target`, `responded`, `correct` and `rt_ms`. It is passed with 80% correct answers and at least half of the matches caught, so that never pressing the key does not pass. Settings: `NBackSettings`.

### Tower of London (Level 3), `tower_*.csv`

One row per puzzle (Shallice, 1982): `problem`, `min_moves`, `moves`, `solved`, `planning_time_ms` (time until the first ball is lifted) and `solution_time_ms`. Settings: `TowerSettings`.

### Card sorting with the Rule Keeper (Level 3), `cardsort_*.csv`

One row per sorted card in the final boss fight: `trial`, `rule` (the hidden rule: `color`, `shape` or `number`), `chosen_dimension`, `correct` and `perseverative` (a wrong choice that follows the previous rule; Milner, 1963).

## Repository structure

```text
Group16-PIPS/
├── data/                  # experiment data written by the game
├── src/
│   └── game/              # the game
│       ├── app.py         # window, main loop, run_game()
│       ├── config.py      # all settings
│       ├── content.py     # insights, quiz questions, skills, references
│       ├── flanker_task.py    # flanker logic and data export (no pygame)
│       ├── flanker_scene.py   # flanker task on screen
│       ├── insight_animations.py   # the animations that explain attention
│       ├── level.py, level_one.py   # level format and the layout of Level 1
│       ├── levels.py      # all levels in story order
│       ├── prologue.py, level_two.py, level_three.py   # layouts of the other levels
│       ├── story_level.py, story_scene.py   # gates, quiz blocks, ice, low gravity, bosses in play
│       ├── story_content.py, story_animations.py   # insights and animations of the other levels
│       ├── stop_signal_task.py, nback_task.py, tower_task.py   # experiment logic (no pygame)
│       ├── experiment_scenes.py, task_data.py   # the experiments on screen and their data files
│       ├── bosses.py, story_entities.py   # bosses and the new enemies
│       ├── worlds.py, story_music.py   # look and music of the new worlds
│       ├── entities.py    # player, enemies, moving platforms
│       ├── play_scene.py  # the platformer and its rules
│       ├── scenes.py, menu_scenes.py   # menus, text boxes, notebook
│       ├── graphics.py, ui.py, characters.py   # drawing (no image files needed)
│       └── audio.py       # music and sound effects, synthesised in code
├── tests/                 # run with: python -m unittest discover -s tests -t .
├── run_game.py            # starts the game
└── requirements.txt
```

## Dependencies

The game uses [pygame](https://www.pygame.org) (2.5 or newer) for graphics, input and sound, and [NumPy](https://numpy.org) to synthesise the music. All graphics, the music and the sound effects are generated in code, so there are no asset files and no third-party assets.

## References

The same list is shown in the game (home screen, "References") and is available in code as `src.game.REFERENCES`.

Baumeister, R. F., Bratslavsky, E., Muraven, M., & Tice, D. M. (1998). Ego depletion: Is the active self a limited resource? Journal of Personality and Social Psychology, 74(5), 1252-1265.

Broadbent, D. E. (1958). Perception and communication. Pergamon Press.

Cherry, E. C. (1953). Some experiments on the recognition of speech, with one and with two ears. Journal of the Acoustical Society of America, 25(5), 975-979.

Diamond, A. (2013). Executive functions. Annual Review of Psychology, 64, 135-168.

Donders, F. C. (1969). On the speed of mental processes (W. G. Koster, Trans.). Acta Psychologica, 30, 412-431. (Original work published 1868)

Eriksen, B. A., & Eriksen, C. W. (1974). Effects of noise letters upon the identification of a target letter in a nonsearch task. Perception & Psychophysics, 16(1), 143-149.

Grant, D. A., & Berg, E. A. (1948). A behavioral analysis of degree of reinforcement and ease of shifting to new responses in a Weigl-type card-sorting problem. Journal of Experimental Psychology, 38(4), 404-411.

Hagger, M. S., Chatzisarantis, N. L. D., Alberts, H., Anggono, C. O., Batailler, C., Birt, A. R., et al. (2016). A multilab preregistered replication of the ego-depletion effect. Perspectives on Psychological Science, 11(4), 546-573.

Hautus, M. J. (1995). Corrections for extreme proportions and their biasing effects on estimated values of d'. Behavior Research Methods, Instruments, & Computers, 27(1), 46-51.

James, W. (1890). The principles of psychology (Vol. 1). Henry Holt.

John, L. K., Loewenstein, G., & Prelec, D. (2012). Measuring the prevalence of questionable research practices with incentives for truth telling. Psychological Science, 23(5), 524-532.

Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. Personality and Social Psychology Review, 2(3), 196-217.

Kirchner, W. K. (1958). Age differences in short-term retention of rapidly changing information. Journal of Experimental Psychology, 55(4), 352-358.

Logan, G. D., & Cowan, W. B. (1984). On the ability to inhibit thought and action: A theory of an act of control. Psychological Review, 91(3), 295-327.

Milner, B. (1963). Effects of different brain lesions on card sorting: The role of the frontal lobes. Archives of Neurology, 9(1), 90-100.

Miyake, A., Friedman, N. P., Emerson, M. J., Witzki, A. H., Howerter, A., & Wager, T. D. (2000). The unity and diversity of executive functions and their contributions to complex 'frontal lobe' tasks: A latent variable analysis. Cognitive Psychology, 41(1), 49-100.

Moray, N. (1959). Attention in dichotic listening: Affective cues and the influence of instructions. Quarterly Journal of Experimental Psychology, 11(1), 56-60.

Munafo, M. R., Nosek, B. A., Bishop, D. V. M., Button, K. S., Chambers, C. D., Percie du Sert, N., Simonsohn, U., Wagenmakers, E.-J., Ware, J. J., & Ioannidis, J. P. A. (2017). A manifesto for reproducible science. Nature Human Behaviour, 1, 0021.

Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The preregistration revolution. Proceedings of the National Academy of Sciences, 115(11), 2600-2606.

Open Science Collaboration. (2015). Estimating the reproducibility of psychological science. Science, 349(6251), aac4716.

Owen, A. M., McMillan, K. M., Laird, A. R., & Bullmore, E. (2005). N-back working memory paradigm: A meta-analysis of normative functional neuroimaging studies. Human Brain Mapping, 25(1), 46-59.

Pavlov, I. P. (1927). Conditioned reflexes: An investigation of the physiological activity of the cerebral cortex. Oxford University Press.

Posner, M. I. (1980). Orienting of attention. Quarterly Journal of Experimental Psychology, 32(1), 3-25.

Rogers, R. D., & Monsell, S. (1995). Costs of a predictable switch between simple cognitive tasks. Journal of Experimental Psychology: General, 124(2), 207-231.

Rosenthal, R. (1979). The file drawer problem and tolerance for null results. Psychological Bulletin, 86(3), 638-641.

Rueda, M. R., Fan, J., McCandliss, B. D., Halparin, J. D., Gruber, D. B., Lercari, L. P., & Posner, M. I. (2004). Development of attentional networks in childhood. Neuropsychologia, 42(8), 1029-1040.

Shallice, T. (1982). Specific impairments of planning. Philosophical Transactions of the Royal Society of London. B, Biological Sciences, 298(1089), 199-209.

Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: Undisclosed flexibility in data collection and analysis allows presenting anything as significant. Psychological Science, 22(11), 1359-1366.

Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained inattentional blindness for dynamic events. Perception, 28(9), 1059-1074.

Stroop, J. R. (1935). Studies of interference in serial verbal reactions. Journal of Experimental Psychology, 18(6), 643-662.

Verbruggen, F., Aron, A. R., Band, G. P. H., Beste, C., Bissett, P. G., Brockett, A. T., et al. (2019). A consensus guide to capturing the ability to inhibit actions and impulsive behaviors in the stop-signal task. eLife, 8, e46323.

Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. Journal of Experimental Psychology, 3(1), 1-14.
