# The game: Mind Quest

Mind Quest is an educational jump-and-run game about general psychology, written in Python with pygame. It is our group project for the Programming in Psychological Science (PIPS) course of the Research Master Psychology at the University of Amsterdam.

The game tells one story: Count Hackula has p-hacked the land of the Mind. A prologue introduces Open Science, three levels teach attention, response inhibition and executive control, and a finale in Count Hackula's castle brings all three together. Every level teaches with short animations instead of long texts, contains a real experiment whose data are saved, has a boss that turns the topic into a game mechanic, and closes with a quiz. Before the game starts, a short questionnaire asks about screen habits, gaming and alertness. Levels are chosen on the home screen, which shows a small preview of each level, and follow each other in story order: a level only opens once the level before it is finished. Each level starts with a title card that tells the next part of the story, and bosses and new mechanics are shown in short animations before they are needed.

| Level | Topic | Worlds | Experiment (data saved) | Boss |
| --- | --- | --- | --- | --- |
| Prologue: The Replication Crisis | Open Science | Old Campus, the Archive | - (tutorial level) | The File Drawer: punch its drawers open to free hidden null results (publication bias); a drawer rattles before it opens |
| Level 1: Focus Fields | Attention | meadow, woods, cave, sky, sunset | child flanker task | Professor Fin's flanker task is the mini boss |
| Level 2: Hold Your Horses | Response inhibition | Frost Peaks (slippery ice), Neon City (red-light zones), Volcano Fortress | stop-signal task | Captain Impulse: hit it on green, hold back on red; it steams before it charges and, in the last phase, sends shock waves |
| Level 3: Mission Control | Executive control | Clockwork Factory (conveyors, switch blocks), Space Station (low gravity) | 2-back task, Tower of London | The Rule Keeper: a card-sorting fight whose rule changes without warning; after several wrong choices in a row it lets slip a hint |
| Finale: Count Hackula's Castle | All three topics | the castle | - | Count Hackula (see below) |

## Level 1

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

## Prologue, Level 2 and Level 3

| Level | Insights (one animation each) | Sources |
| --- | --- | --- |
| Prologue | Open Science; questionable research practices (p-hacking, HARKing, cherry-picking); the replication crisis (97% of 100 original studies vs. 36% of their replications significant); publication bias and the file drawer; the Open Science toolbox (preregistration, Registered Reports, open data and materials) | Nosek et al. (2018); Munafo et al. (2017); John et al. (2012); Kerr (1998); Simmons et al. (2011); Open Science Collaboration (2015); Rosenthal (1979); Chambers (2013); Wilkinson et al. (2016) |
| Level 2 | response inhibition; go/no-go; the horse-race model of stopping; the Stroop effect; the brain's brake (right inferior frontal cortex, stopping in ADHD) | Logan & Cowan (1984); Verbruggen et al. (2019); Donders (1969); Schachar et al. (2007); Stroop (1935); Aron et al. (2004); Lijffijt et al. (2005) |
| Level 3 | executive functions (updating, shifting, inhibiting); working memory and the n-back task; planning; task switching; card sorting and perseveration | Miyake et al. (2000); Diamond (2013); Baddeley & Hitch (1974); Cowan (2001); Kirchner (1958); Shallice (1982); Rogers & Monsell (1995); Grant & Berg (1948); Milner (1963) |

Signal Sam's stop-signal race in Neon City opens the city gate and teaches the new skill **Stop Signal** (R), which freezes nearby enemies, fire bars and bosses for a moment. In Level 3 the Tower of London opens the factory gate and the Memory Machine's 2-back task opens the door to the control room. The Prologue doubles as the tutorial: every move is introduced before it is needed.

## Finale: Count Hackula's Castle

A short castle level in which every level returns once: lava and fire bars, a red-light zone, a Brute that only fear conditioning moves, and a switch puzzle. The hero starts with every skill of the game. In the throne room waits the final boss, Count Hackula, whose three phases test the three topics of the game:

1. **Shadows (attention):** the Count is almost invisible; only his shadow and glowing eyes give him away.
2. **Swoops (response inhibition):** he swoops across the hall. Attack on green eyes, stay on the ground on red eyes; attacking on red heals him (a commission error). The Stop Signal (R) freezes him in the air.
3. **Sunlight (executive control and Open Science):** three windows stand for Preregister, Open data and Replicate. Count Hackula shows them in an order, and the player hits the window blocks in the same order to let the sunlight in, which finishes the vampire.

The story ends with a finale animation.

## Ghost races

Like the time trials in Mario Kart, the best run of each level (per difficulty) is saved and comes back as a see-through ghost the next time the level is played, and the screen shows how far ahead or behind the player is. Ghost races are off by default and can be switched on in the home screen. Ghosts are saved in the `ghosts/` folder and the unlocked levels in `save/progress.json`; both folders are ignored by Git. Because they are shared by everyone who plays on the same computer, clear them between participants when collecting data.

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
| P (or F1) | admin mode for testing: fly, take no damage, skip challenges with the number keys, and open every level on the home screen |

Admin mode can be switched off for data collection with `run_game(allow_admin=False)`; a skipped experiment never writes a data file.

Question blocks hold sparks, hearts and three items: the Zoom-shroom (run faster), the Focus Star (invincible for a few seconds) and the Shield (absorbs one hit). New skills come with short animations as well: punching, fear conditioning (a bell is paired with a scary flash until the bell alone scares enemies away) and, as the reward at the very end, the QRP Blaster (p-hacking and HARKing). Pipes show a short loading screen, the Pond Challenge has its own calm music, and reaching the goal sets off fireworks.

The player has three hearts. Enemies and spikes cost a heart, falling costs a heart and sends the player back to the last checkpoint, and without hearts the level starts again from its beginning.

The home screen offers three difficulty modes with the same map. **Easy** gives five hearts, higher jumps, narrower pits, half as many and slower enemies, no heart loss for falling or wrong quiz answers, and a 75% pass mark in the flanker task. **Medium** is the standard game. **Hard** has faster enemies and less room for mistakes. The modes are defined in `DIFFICULTIES` in `src/game/config.py`.

## Experiment data

Every attempt at an experiment writes one CSV file `data/<task>_<participant>_<timestamp>_attempt-<n>.csv` with one row per trial. All files start with the columns `participant_id` and `attempt`. Design and timing of each task can be changed in `src/game/config.py`.

### Questionnaire (start of the game), `questionnaire_*.csv`

After the title screen the player answers five questions, one at a time (A/D or the arrow keys to choose, SPACE to confirm; ESC skips the questionnaire, and then nothing is saved). The answers are saved as one row, so that the analysis can relate screen habits to performance in the experiments while controlling for gaming experience and fatigue. Every answer starts at the middle of its scale.

| Column | Question | Answer |
| --- | --- | --- |
| `screen_time_hours` | On a typical day, how many hours do you spend on screens in your free time? | 0 to 16 hours in steps of 0.5 |
| `short_video_frequency` | How often do you watch short videos (TikTok, Reels, Shorts)? | 1 (never) to 5 (several times a day) |
| `psychology_interest` | How interested are you in psychology? | 1 (not at all) to 5 (very much) |
| `gaming_frequency` | How often do you play video games? | 1 (never) to 5 (daily) |
| `alertness` | How awake and alert do you feel right now? | 1 (very tired) to 5 (very alert) |

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
| `spacing` | gap between neighbouring fish in pixels (`35` or `85`; empty on neutral trials) |
| `nr_flankers` | number of flanking fish, half on each side (`4`, `6` or `8`; `0` on neutral trials) |
| `response` | `left`, `right` or empty (no response within 1.7 seconds) |
| `correct` | `True` or `False` |
| `rt_ms` | reaction time in milliseconds, empty without a response |

The task is modelled on the flanker part of the child Attention Network Test (Rueda et al., 2004). To make it less easy and to vary how strongly the flankers interfere, congruent and incongruent displays cross the spacing (2 levels) with the number of flankers (3 levels); neutral trials are repeated to match, so the test block has 36 trials in which every combination appears equally often. Its design and timing can be changed with `FlankerSettings` in `src/game/config.py`.

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

One row per sorted card in the boss fight at the end of Level 3: `trial`, `rule` (the hidden rule: `color`, `shape` or `number`), `chosen_dimension`, `correct` and `perseverative` (a wrong choice that follows the previous rule; Milner, 1963).
