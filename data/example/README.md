# Demo playthrough

This folder holds the data of one complete game session. `main.ipynb` uses it when nobody has played the flanker, stop-signal or 2-back task yet (for example, right after cloning the repository), so the bootstrap and the simulation always have a session to start from.

**These data do not come from a person.** They were recorded by the automated test player we used to check that every level can be finished. It plays the real game (Easy, admin mode off) and answers with scripted rules:

- Questionnaire: the same answer option on every question.
- Flanker: response times drawn uniformly between 350 and 650 ms, 96% correct, with no built-in difference between congruent and incongruent trials.
- Stop-signal: go responses after 380 to 550 ms; it stops when the stop signal comes more than 200 ms before its planned response.
- 2-back: responses after 450 to 900 ms, 95% correct.
- Tower of London: solved by searching for the shortest path.
- Card sorting: keeps a guessed rule and switches to another rule after a wrong answer.

So the demo shows how the pipeline works, not how real players perform: for example, its flanker effect is close to 0 ms.

To replace it, play the whole game once with admin mode off and copy the new files of that session from `data/` into this folder: the questionnaire and the flanker, stop-signal and 2-back files (`attempt-1`), and optionally the Tower of London and card-sorting files. Remove the previous files, so that the folder holds a single player.
