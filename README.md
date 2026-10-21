# Mind Quest

Mind Quest is an educational jump-and-run game about attention, response inhibition and executive control, with real experiments built into its levels. We made it for the group project of the Programming in Psychological Science (PIPS) course of the Research Master Psychology at the University of Amsterdam.

While playing, a player answers a short questionnaire about screen habits, gaming and alertness and completes a flanker task, a stop-signal task, a 2-back task and the Tower of London; every experiment is saved as a CSV file. The main notebook then **bootstraps** the player's trials to show how precise their scores are, and **simulates a group of players** whose typical scores come from that player and whose differences come from the literature. The simulated group has the same format as real data, so analyses can be planned and checked before many people have played.

## Citation

Group 16 (2026). *Mind Quest: An educational game with built-in experiments on attention, response inhibition and executive control* [Computer software]. Programming in Psychological Science, University of Amsterdam. https://github.com/Junex161/Group16-PIPS

## Getting started

The project needs Python 3.12 or newer. Clone the repository, install the requirements and open the notebook:

```bash
git clone https://github.com/Junex161/Group16-PIPS.git
cd Group16-PIPS
pip install -r requirements.txt
jupyter lab main.ipynb
```

Run `main.ipynb` from top to bottom. The game cell opens a window: play as long as you like and close the window to continue. Set `PLAY_GAME = False` in that cell to skip the game and use the data of whoever played last; without any data the notebook still runs on published values.

The game uses [pygame-ce](https://pyga.me), a maintained version of pygame that also installs on the newest Python versions. If the original `pygame` is already installed, remove it first with `pip uninstall pygame`, because both provide the same `pygame` module.

## Using the project

`main.ipynb` walks through four steps:

1. **Play** the game; every experiment writes its data to `data/`.
2. **Bootstrap** the player's flanker, stop-signal and 2-back trials (5,000 resamples within each condition) for standard errors and 95% confidence intervals of the flanker effect, the SSRT, d' and related measures; the results are saved in `data/simulated/`.
3. **Simulate** 50 players (questionnaire plus every trial of the three tasks) and save them to `data/simulated/`.
4. **Analyse** the simulated group (statistical analysis to be added).

The game can also be started on its own with `python run_game.py`. The tests run with `python -m unittest discover -s tests -t .`.

How to play, all levels and the columns of every data file are described in [docs/GAME.md](docs/GAME.md).

## The simulation

Every simulated player gets their own true scores, drawn from normal distributions:

| Score | Mean | Between-person SD |
| --- | --- | --- |
| Flanker baseline RT and flanker effect | bootstrap of the player | Kaufman et al. (2016), Table 2, young adults |
| Go RT and SSRT | bootstrap of the player | Congdon et al. (2014), Table 1, healthy controls |
| 2-back d' | bootstrap of the player | Forsberg et al. (2020), Table 3, younger adults |
| Daily screen time | Sedaghat et al. (2025) | Sedaghat et al. (2025) |

For tasks the player did not complete, the published means are used. Values without a published source (error rates, the 2-back response criterion and RTs, and the answer distributions of the 1-5 questions) are marked as assumptions in `src/simulation.py`. The links between questionnaire and performance (for example, more screen time with a larger flanker effect) are hypothetical effects that can be changed or set to 0 in `Effects`; the simulation contains exactly the effects put into it.

Trials are generated with the game's own trial lists: RT = baseline + flanker effect + noise in the flanker task, a race between going and stopping in the stop-signal task (Logan & Cowan, 1984), and signal detection theory in the 2-back task (Stanislaw & Todorov, 1999).

## Repository structure

```text
Group16-PIPS/
├── data/                  # experiment data written by the game
│   └── simulated/         # bootstrap results and simulated players written by main.ipynb (not in Git)
├── docs/
│   └── GAME.md            # levels, controls and the columns of every data file
├── src/
│   ├── data.py            # loading the data files of all players or of one session
│   ├── bootstrap.py       # bootstrapping one player's trials
│   ├── simulation.py      # simulating players; literature values and assumptions
│   └── game/              # the game (pygame)
│       ├── app.py         # window, main loop, run_game()
│       ├── config.py      # all settings, including the design of every experiment
│       ├── flanker_task.py, stop_signal_task.py, nback_task.py, tower_task.py   # experiment logic (no pygame)
│       ├── experiment_scenes.py, flanker_scene.py, questionnaire.py   # experiments and questionnaire on screen
│       └── ...            # levels, bosses, animations, graphics and sound (see docs/GAME.md)
├── tests/                 # unit tests
├── main.ipynb             # main deliverable: play, bootstrap, simulate, analyse
├── run_game.py            # starts only the game
└── requirements.txt
```

## Dependencies

| Package | Used for |
| --- | --- |
| [pygame-ce](https://pyga.me) | the game: graphics, input and sound |
| [NumPy](https://numpy.org) | the bootstrap, the simulation and the synthesised music |
| [pandas](https://pandas.pydata.org) | loading and saving data |
| [Jupyter](https://jupyter.org) | running `main.ipynb` |

All graphics, music and sound effects are generated in code, so there are no asset files and no third-party assets.

## References

### Bootstrap and simulation

Congdon, E., Altshuler, L. L., Mumford, J. A., Karlsgodt, K. H., Sabb, F. W., Ventura, J., McGough, J. J., London, E. D., Cannon, T. D., Bilder, R. M., & Poldrack, R. A. (2014). Neural activation during response inhibition in adult attention-deficit/hyperactivity disorder: Preliminary findings on the effects of medication and symptom severity. Psychiatry Research: Neuroimaging, 222, 17-28. https://doi.org/10.1016/j.pscychresns.2014.02.002

Efron, B. (1979). Bootstrap methods: Another look at the jackknife. The Annals of Statistics, 7(1), 1-26. https://doi.org/10.1214/aos/1176344552

Forsberg, A., Fellman, D., Laine, M., Johnson, W., & Logie, R. H. (2020). Strategy mediation in working memory training in younger and older adults. Quarterly Journal of Experimental Psychology, 73(8), 1206-1226. https://doi.org/10.1177/1747021820915107

Kaufman, D. A. S., Sozda, C. N., Dotson, V. M., & Perlstein, W. M. (2016). An event-related potential investigation of the effects of age on alerting, orienting, and executive function. Frontiers in Aging Neuroscience, 8, 99. https://doi.org/10.3389/fnagi.2016.00099

Sedaghat, D., Lee, E., Garcia, J., & Brazendale, K. (2025). Screen time and objectively measured sleep of U.S. college students: A brief report. International Journal of Exercise Science, 18(4), 747-756. https://doi.org/10.70252/XDUT8341

Stanislaw, H., & Todorov, N. (1999). Calculation of signal detection theory measures. Behavior Research Methods, Instruments, & Computers, 31(1), 137-149. https://doi.org/10.3758/BF03207704

### The game

The same list is shown in the game (home screen, "References") and is available in code as `src.game.REFERENCES`.

Aron, A. R., Robbins, T. W., & Poldrack, R. A. (2004). Inhibition and the right inferior frontal cortex. Trends in Cognitive Sciences, 8(4), 170-177.

Baddeley, A. D., & Hitch, G. (1974). Working memory. In G. H. Bower (Ed.), The psychology of learning and motivation (Vol. 8, pp. 47-89). Academic Press.

Baumeister, R. F., Bratslavsky, E., Muraven, M., & Tice, D. M. (1998). Ego depletion: Is the active self a limited resource? Journal of Personality and Social Psychology, 74(5), 1252-1265.

Broadbent, D. E. (1958). Perception and communication. Pergamon Press.

Chambers, C. D. (2013). Registered Reports: A new publishing initiative at Cortex. Cortex, 49(3), 609-610.

Cherry, E. C. (1953). Some experiments on the recognition of speech, with one and with two ears. Journal of the Acoustical Society of America, 25(5), 975-979.

Cowan, N. (2001). The magical number 4 in short-term memory: A reconsideration of mental storage capacity. Behavioral and Brain Sciences, 24(1), 87-114.

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

Lijffijt, M., Kenemans, J. L., Verbaten, M. N., & van Engeland, H. (2005). A meta-analytic review of stopping performance in attention-deficit/hyperactivity disorder: Deficient inhibitory motor control? Journal of Abnormal Psychology, 114(2), 216-222.

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

Schachar, R., Logan, G. D., Robaey, P., Chen, S., Ickowicz, A., & Barr, C. (2007). Restraint and cancellation: Multiple inhibition deficits in attention deficit hyperactivity disorder. Journal of Abnormal Child Psychology, 35(2), 229-238.

Shallice, T. (1982). Specific impairments of planning. Philosophical Transactions of the Royal Society of London. B, Biological Sciences, 298(1089), 199-209.

Simmons, J. P., Nelson, L. D., & Simonsohn, U. (2011). False-positive psychology: Undisclosed flexibility in data collection and analysis allows presenting anything as significant. Psychological Science, 22(11), 1359-1366.

Simons, D. J., & Chabris, C. F. (1999). Gorillas in our midst: Sustained inattentional blindness for dynamic events. Perception, 28(9), 1059-1074.

Stroop, J. R. (1935). Studies of interference in serial verbal reactions. Journal of Experimental Psychology, 18(6), 643-662.

Verbruggen, F., Aron, A. R., Band, G. P. H., Beste, C., Bissett, P. G., Brockett, A. T., et al. (2019). A consensus guide to capturing the ability to inhibit actions and impulsive behaviors in the stop-signal task. eLife, 8, e46323.

Watson, J. B., & Rayner, R. (1920). Conditioned emotional reactions. Journal of Experimental Psychology, 3(1), 1-14.

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data, 3, 160018.
