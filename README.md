# Group16-PIPS
Group 16 in the PIPS Assignment :))

## Mind Quest

Mind Quest is an educational jump-and-run game about general psychology, written in Python with pygame. It is our group project for the Programming in Psychological Science (PIPS) course of the Research Master Psychology at the University of Amsterdam.

Level 1, "Focus Fields", is about **attention**. The player crosses a meadow, a dark cave and the sunset heights, collects six notes about attention, has to pass a child flanker task (the mini boss in the middle of the level) and answers a multiple-choice question at the end. The flanker task doubles as an experiment script: every attempt is saved as a CSV file in `data/`.

## Getting started

The game needs Python 3.12 or newer and pygame:

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

saved_files = run_game(participant_id="p-001")  # returns the flanker data files
```

## How to play

| Key | Action |
| --- | --- |
| A / D | walk left and right |
| Space or W | jump (press again in the air for a double jump, once learned) |
| S | fall faster |
| F | punch enemies and crates |
| G | fire the QRP Blaster: its shots are questionable research practices such as p-hacking |
| Q | fear conditioning (once learned): nearby enemies run away |
| E | talk and read signs |
| Tab | open the notebook with the collected notes |
| M | sound on / off |
| Esc | pause |
| P (or F1) | admin mode for testing: fly, take no damage, and skip challenges with the keys 1 to 4 |

Admin mode can be switched off for data collection with `run_game(allow_admin=False)`; a skipped flanker task never writes a data file.

The player has three hearts. Enemies and spikes cost a heart, falling costs a heart and sends the player back to the last checkpoint, and without hearts the game starts again from the beginning.

The home screen offers three difficulty modes with the same map. **Easy** gives five hearts, higher jumps, narrower pits, half as many and slower enemies, no heart loss for falling or wrong quiz answers, and a 75% pass mark in the flanker task. **Medium** is the standard game. **Hard** has faster enemies and less room for mistakes. The modes are defined in `DIFFICULTIES` in `src/game/config.py`.

## Flanker data

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

## Repository structure

```text
Group16-PIPS/
├── data/                  # flanker data written by the game
├── src/
│   └── game/              # the game
│       ├── app.py         # window, main loop, run_game()
│       ├── config.py      # all settings
│       ├── content.py     # notes, quiz questions, skills, references
│       ├── flanker_task.py    # flanker logic and data export (no pygame)
│       ├── flanker_scene.py   # flanker task on screen
│       ├── level.py, level_one.py   # level format and the layout of Level 1
│       ├── entities.py    # player, enemies, moving platforms
│       ├── play_scene.py  # the platformer and its rules
│       ├── scenes.py, menu_scenes.py, quiz_scene.py   # menus, text boxes, quiz
│       ├── graphics.py, ui.py, characters.py   # drawing (no image files needed)
│       └── audio.py       # music and sound effects, synthesised in code
├── tests/                 # run with: python -m unittest discover -s tests -t .
├── run_game.py            # starts the game
└── requirements.txt
```

## Dependencies

The game only uses [pygame](https://www.pygame.org) (2.5 or newer) and the Python standard library. All graphics, the music and the sound effects are generated in code, so there are no asset files and no third-party assets.

## References

The same list is shown in the game (home screen, "References") and is available in code as `src.game.REFERENCES`.

Broadbent, D. E. (1958). *Perception and communication*. Pergamon Press.

Cherry, E. C. (1953). Some experiments on the recognition of speech, with one and with two ears. *Journal of the Acoustical Society of America, 25*(5), 975–979.

Eriksen, B. A., & Eriksen, C. W. (1974). Effects of noise letters upon the identification of a target letter in a nonsearch task. *Perception & Psychophysics, 16*(1), 143–149.

Fan, J., McCandliss, B. D., Sommer, T., Raz, A., & Posner, M. I. (2002). Testing the efficiency and independence of attentional networks. *Journal of Cognitive Neuroscience, 14*(3), 340–347.

John, L. K., Loewenstein, G., & Prelec, D. (2012). Measuring the prevalence of questionable research practices with incentives for truth telling. *Psychological Science, 23*(5), 524–532.

Kerr, N. L. (1998). HARKing: Hypothesizing after the results are known. *Personality and Social Psychology Review, 2*(3), 196–217.

Pavlov, I. P. (1927). *Conditioned reflexes: An investigation of the physiological activity of the cerebral cortex*. Oxford University Press.

Posner, M. I. (1980). Orienting of attention. *Quarterly Journal of Experimental Psychology, 32*(1), 3–25.

Posner, M. I., & Petersen, S. E. (1990). The attention system of the human brain. *Annual Review of Neuroscience, 13*, 25–42.

Rueda, M. R., Fan, J., McCandliss, B. D., Halparin, J. D., Gruber, D. B., Lercari, L. P., & Posner, M. I. (2004). Development of attentional networks in childhood. *Neuropsychologia, 42*(8), 1029–1040.

Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: Undisclosed flexibility in data collection and analysis allows presenting anything as significant. *Psychological Science, 22*(11), 1359–1366.

Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained inattentional blindness for dynamic events. *Perception, 28*(9), 1059–1074.

Treisman, A. M. (1964). Selective attention in man. *British Medical Bulletin, 20*(1), 12–16.

Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. *Journal of Experimental Psychology, 3*(1), 1–14.
