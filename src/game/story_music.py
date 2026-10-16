"""Music and extra sounds of the Prologue and Levels 2 and 3.

Every world and every boss hall has its own track, written in the same
text notation as the tracks in ``audio.py``. Chord, bass and arpeggio parts
are generated from a chord progression, so only the melodies are written
out note by note. Melodies stay below G5 (784 Hz), so nothing is shrill.

``register()`` adds the tracks to ``audio.TRACKS``; ``install_sounds``
adds the new sound effects to a running ``Audio`` object.
"""

from . import audio
from .audio import NOTE_NAMES, render_effect

# Chords by name, in a comfortable middle register.
CHORDS = {
    "C": "C4+E4+G4", "Cmaj7": "C4+E4+G4+B4", "Dm": "D4+F4+A4", "D": "D4+F#4+A4", "Em": "E3+G3+B3",
    "E": "E3+G#3+B3", "F": "F3+A3+C4", "Fmaj7": "F3+A3+C4+E4", "F#": "F#3+A#3+C#4", "G": "G3+B3+D4",
    "Gm": "G3+A#3+D4", "A": "A3+C#4+E4", "Am": "A3+C4+E4", "Am7": "A3+C4+E4+G4", "Bb": "A#3+D4+F4",
    "B": "B3+D#4+F#4", "Bm": "B3+D4+F#4", "C#m": "C#4+E4+G#4", "Eb": "D#4+G4+A#4", "C7": "C4+E4+A#4",
}


def shift(note, semitones):
    """Move a note such as "C4" up or down by a number of semitones."""
    pitch, octave = note[:-1], int(note[-1])
    index = NOTE_NAMES.index(pitch) + semitones
    return f"{NOTE_NAMES[index % 12]}{octave + index // 12}"


def root(chord, octave=2):
    """The lowest note of a chord, moved to the given octave for the bass."""
    note = CHORDS[chord].split("+")[0]
    return note[:-1] + str(octave)


def offbeat(chords):
    """Chords on the off-beats, one bar per chord."""
    return " ".join(f"-:.5 {CHORDS[c]}:.5 " * 4 for c in chords)


def held(chords, beats=4):
    """Chords held for a whole bar."""
    return " ".join(f"{CHORDS[c]}:{beats}" for c in chords)


def arpeggio(chords, step=0.5, octave=0):
    """Broken chords: the chord notes up and down in even steps, one bar per chord."""
    parts = []
    per_bar = int(4 / step)
    for chord in chords:
        notes = [shift(note, 12 * octave) for note in CHORDS[chord].split("+")]
        cycle = notes + notes[-2:0:-1]
        parts += [f"{cycle[index % len(cycle)]}:{step:g}" for index in range(per_bar)]
    return " ".join(parts)


def bass(chords, pattern):
    """
    A bass line: ``pattern`` is one bar with R (root), F (fifth) and O (octave).

    Example: "R:1 R:.5 F:.5 R:1 F:1".
    """
    parts = []
    for chord in chords:
        low = root(chord)
        names = {"R": low, "F": shift(low, 7), "O": shift(low, 12), "-": "-"}
        for entry in pattern.split():
            name, beats = entry.split(":")
            parts.append(f"{names[name]}:{beats}")
    return " ".join(parts)


def _track(tempo, chords, melody, instrument, melody_volume, extra_parts=(), drums=()):
    return {"tempo": tempo, "bars": len(chords), "parts": [(melody, instrument, melody_volume), *extra_parts], "drums": drums}


CAMPUS = ("C", "Am", "Dm", "G", "F", "G", "Em", "C")
ARCHIVE = ("Dm", "Bb", "C", "A", "Dm", "Gm", "A", "Dm")
DRAWER = ("Am", "Am", "F", "E", "Am", "Am", "F", "E")
ICE = ("E", "C#m", "A", "B", "E", "C#m", "A", "B")
CITY = ("Gm", "C", "Gm", "C", "Eb", "F", "Gm", "D")
VOLCANO = ("Em", "C", "D", "B", "Em", "C", "D", "B")
IMPULSE = ("Dm", "Dm", "Bb", "A", "Dm", "Dm", "Bb", "A")
FACTORY = ("Am", "F", "C", "G", "Am", "F", "C", "G")
SPACE = ("Fmaj7", "G", "Em", "Am", "Fmaj7", "G", "Em", "Am")
RULES = ("Bm", "G", "Em", "F#", "Bm", "G", "Em", "F#")
CASTLE = ("Dm", "A", "Bb", "Gm", "Dm", "C", "Bb", "A")
HACKULA = ("Dm", "Dm", "Bb", "A", "Gm", "Dm", "Eb", "A")
LAB = ("Cmaj7", "Am7", "Fmaj7", "G", "Cmaj7", "Am7", "Fmaj7", "G")

STORY_TRACKS = {
    # Old Campus: friendly and curious, in C major.
    "campus": _track(
        112, CAMPUS,
        "E4:1 G4:1 C5:1 G4:1 A4:1 C5:1 E5:2 D5:1 C5:1 A4:1 G4:1 E4:2 G4:2 "
        "F4:1 A4:1 C5:1 A4:1 G4:1 B4:1 D5:2 E5:1 D5:1 C5:1 B4:1 C5:3 -:1",
        "flute", 0.42,
        ((offbeat(CAMPUS), "keys", 0.12), (bass(CAMPUS, "R:1 R:.5 F:.5 R:1 F:1"), "bass", 0.45)),
        ("k-----k-s-------", "--h---h---h---h-"),
    ),
    # The Archive: dusty and mysterious, in D minor.
    "archive": _track(
        92, ARCHIVE,
        "D5:1.5 C5:.5 A4:2 D5:1 F5:1 E5:1 D5:1 C5:1.5 A#4:.5 A4:2 C#5:2 E5:2 "
        "F5:1.5 E5:.5 D5:2 A#4:1 D5:1 G5:2 E5:1 C#5:1 A4:1 E4:1 D4:3 -:1",
        "keys", 0.4,
        ((arpeggio(ARCHIVE), "marimba", 0.16), (held(ARCHIVE), "pad", 0.14), (bass(ARCHIVE, "R:2 F:2"), "bass", 0.4)),
        ("k-------k---s---",),
    ),
    # The File Drawer: tense and driving, in A minor.
    "boss_drawer": _track(
        150, DRAWER,
        ("A4:.5 A4:.5 C5:.5 A4:.5 E5:.5 A4:.5 D#5:.5 E5:.5 A4:.5 A4:.5 C5:.5 A4:.5 G5:.5 F5:.5 E5:.5 D5:.5 "
         "F4:.5 F4:.5 A4:.5 F4:.5 C5:.5 F4:.5 B4:.5 C5:.5 E4:.5 G#4:.5 B4:.5 E5:.5 D5:.5 B4:.5 G#4:.5 E4:.5 ") * 2,
        "keys", 0.38,
        ((bass(DRAWER, "R:.5 R:.5 O:.5 R:.5 R:.5 R:.5 F:.5 R:.5"), "bass", 0.5), (held(DRAWER), "pad", 0.12)),
        ("k-k-s-k-k-k-s-k-", "h-h-h-h-h-h-h-h-"),
    ),
    # Frost Peaks: clear and crystalline, in E major.
    "ice": _track(
        104, ICE,
        "B4:1 E5:1 B4:1 G#4:1 C#5:1 E5:1 C#5:2 A4:1 C#5:1 E5:1 C#5:1 B4:2 D#5:2 "
        "E5:1 B4:1 G#4:1 B4:1 C#5:1 G#4:1 E4:2 F#4:1 A4:1 C#5:1 E5:1 D#5:2 B4:2",
        "keys", 0.4,
        ((arpeggio(ICE, 0.5), "marimba", 0.14), (held(ICE), "pad", 0.14), (bass(ICE, "R:2 F:1 R:1"), "bass", 0.4)),
        ("k-------s-------", "--h---h---h---h-"),
    ),
    # Neon City: a funky groove, in G minor.
    "city": _track(
        116, CITY,
        "G4:.5 A#4:.5 -:.5 D5:.5 C5:1 A#4:1 A4:.5 C5:.5 E5:1 D5:.5 C5:.5 A4:1 "
        "G4:.5 A#4:.5 D5:.5 F5:.5 D5:1 -:1 E5:.5 D5:.5 C5:.5 A#4:.5 A4:2 "
        "G4:1 A#4:.5 D#5:.5 G5:1 F5:1 F5:.5 D#5:.5 D5:.5 C5:.5 A4:2 "
        "A#4:.5 D5:.5 G5:1 F5:.5 D5:.5 A#4:1 A4:1 F#4:1 D4:2",
        "flute", 0.4,
        ((offbeat(CITY), "keys", 0.12), (bass(CITY, "R:.75 R:.25 -:.5 F:.5 R:.5 O:.5 F:.5 R:.5"), "bass", 0.5)),
        ("k--k--s-k-k---s-", "h-hhh-hhh-hhh-hh"),
    ),
    # Volcano Fortress: fast and fiery, in E minor.
    "volcano": _track(
        138, VOLCANO,
        "E5:.5 D5:.5 B4:1 E5:.5 F#5:.5 G5:1 E5:.5 D5:.5 C5:1 G4:1 C5:1 "
        "D5:.5 C5:.5 A4:1 D5:.5 E5:.5 F#5:1 D#5:2 B4:2 "
        "G5:.5 F#5:.5 E5:1 B4:1 E5:1 G5:1 E5:.5 C5:.5 G4:2 "
        "A4:.5 B4:.5 D5:1 F#5:1 G5:1 F#5:1 D#5:1 B4:2",
        "flute", 0.4,
        ((offbeat(VOLCANO), "keys", 0.12), (bass(VOLCANO, "R:.5 R:.25 R:.25 R:.5 R:.25 R:.25 F:.5 R:.25 R:.25 R:.5 F:.5"), "bass", 0.5)),
        ("k-k-s---k-k-s-k-", "h-h-h-h-h-h-h-h-"),
    ),
    # Captain Impulse: aggressive stabs, in D minor.
    "boss_impulse": _track(
        160, IMPULSE,
        "D5:.5 -:.5 D5:.5 F5:.5 -:.5 E5:.5 D5:1 C5:.5 D5:.5 -:.5 A4:.5 C5:.5 D5:.5 F5:1 "
        "A#4:.5 -:.5 A#4:.5 D5:.5 -:.5 F5:.5 G5:1 G5:1 F5:.5 E5:.5 D5:1 C#5:1 "
        "D5:.5 -:.5 D5:.5 F5:.5 -:.5 E5:.5 D5:1 C5:.5 D5:.5 -:.5 A4:.5 C5:.5 D5:.5 F5:1 "
        "A#4:.5 -:.5 A#4:.5 D5:.5 -:.5 F5:.5 G5:1 G5:.5 F5:.5 E5:.5 D5:.5 C#5:1 A4:1",
        "keys", 0.4,
        ((bass(IMPULSE, "R:.5 R:.5 R:.5 O:.5 R:.5 R:.5 F:.5 O:.5"), "bass", 0.5), (held(IMPULSE), "pad", 0.12)),
        ("k-s-k-s-k-s-kks-", "h-h-h-h-h-h-h-h-"),
    ),
    # Clockwork Factory: mechanical and busy, in A minor.
    "factory": _track(
        120, FACTORY,
        "A4:2 C5:1 E5:1 F5:2 E5:1 C5:1 E5:2 G5:1 E5:1 D5:3 -:1 "
        "A4:1 B4:1 C5:1 E5:1 F5:1 G5:1 F5:1 E5:1 E5:1 C5:1 G4:1 C5:1 B4:3 -:1",
        "flute", 0.38,
        ((arpeggio(FACTORY, 0.25, -1), "marimba", 0.14), (bass(FACTORY, "R:1 R:1 F:1 R:1"), "bass", 0.45)),
        ("k---k-s-k---k-s-", "h-h-h-h-h-h-h-hh"),
    ),
    # Space Station: dreamy and floating, in F (Lydian).
    "space": _track(
        88, SPACE,
        "C5:2 E5:1 G5:1 B4:3 D5:1 G4:2 B4:1 E5:1 A4:4 "
        "C5:1 D5:1 E5:1 G5:1 F#5:2 D5:2 E5:1 B4:1 G4:2 A4:3 -:1",
        "keys", 0.36,
        ((held(SPACE), "pad", 0.18), (arpeggio(SPACE, 1.0), "marimba", 0.12), (bass(SPACE, "R:4"), "bass", 0.35)),
        ("k-------------k-",),
    ),
    # The Rule Keeper: quirky and unpredictable, in B minor.
    "boss_rules": _track(
        140, RULES,
        "B4:.5 D5:.5 F#5:.5 D5:.5 B4:.5 F#5:.5 B4:1 G5:.5 F#5:.5 E5:.5 D5:.5 B4:1 G4:1 "
        "E5:.5 G5:.5 E5:.5 B4:.5 G4:.5 B4:.5 E5:1 F#5:1 F5:.5 F#5:.5 C#5:1 A#4:1 "
        "B4:.5 D5:.5 F#5:.5 D5:.5 B4:.5 F#5:.5 B4:1 G5:.5 F#5:.5 E5:.5 D5:.5 B4:1 G4:1 "
        "E5:.5 G5:.5 E5:.5 B4:.5 G4:.5 B4:.5 E5:1 F#5:2 F#4:2",
        "keys", 0.4,
        ((bass(RULES, "R:.5 -:.5 R:.5 F:.5 -:.5 R:.5 O:1"), "bass", 0.5), (offbeat(RULES), "marimba", 0.12)),
        ("k--s--k-k--s--k-", "h-h-h-h-h-h-h-h-"),
    ),
    # Count Hackula's castle: gothic and creepy, in D minor.
    "castle": _track(
        100, CASTLE,
        "D5:1 A4:1 F4:1 D4:1 C#5:2 E5:2 F5:1 D5:1 A#4:1 F4:1 G4:3 -:1 "
        "A4:1 D5:1 F5:1 E5:1 E5:1 C5:1 G4:1 E4:1 F4:1 D4:1 A#4:2 C#5:3 -:1",
        "keys", 0.38,
        ((held(CASTLE), "pad", 0.2), (arpeggio(CASTLE, 0.5, -1), "marimba", 0.12), (bass(CASTLE, "R:2 F:1 R:1"), "bass", 0.42)),
        ("k-------k---s---",),
    ),
    # The final fight against Count Hackula: fast and dramatic.
    "boss_hackula": _track(
        156, HACKULA,
        "D5:.5 D5:.5 A4:.5 D5:.5 F5:.5 E5:.5 D5:.5 C#5:.5 D5:.5 D5:.5 A4:.5 D5:.5 G5:1 F5:1 "
        "F5:.5 E5:.5 D5:.5 A#4:.5 F4:1 A#4:1 E5:.5 D5:.5 C#5:.5 A4:.5 E4:1 C#5:1 "
        "D5:.5 A#4:.5 G4:.5 A#4:.5 D5:1 G5:1 F5:.5 E5:.5 D5:.5 A4:.5 F4:1 D5:1 "
        "D#5:.5 D5:.5 A#4:.5 G4:.5 D#4:1 G4:1 E5:.5 C#5:.5 A4:.5 E4:.5 A4:2",
        "keys", 0.4,
        ((held(HACKULA), "pad", 0.16), (bass(HACKULA, "R:.5 R:.5 O:.5 R:.5 R:.5 F:.5 O:.5 F:.5"), "bass", 0.5)),
        ("k-s-k-s-k-s-kks-", "h-h-h-h-h-h-h-h-"),
    ),
    # The experiments: calm and steady, the same in every condition.
    "lab": _track(
        72, LAB,
        arpeggio(LAB, 1.0),
        "marimba", 0.12,
        ((held(LAB), "pad", 0.18), (bass(LAB, "R:4"), "bass", 0.28)),
    ),
}


def register():
    """Add the tracks to ``audio.TRACKS``."""
    audio.TRACKS.update(STORY_TRACKS)


def make_story_effects():
    """Return the new sound effects as float sample arrays."""
    return {"whistle": render_effect(1180, 1040, 0.28, 0.3)}


def install_sounds(game_audio):
    """Add the new sound effects to a running ``Audio`` object."""
    if game_audio.enabled:
        from .config import SOUND_VOLUME

        for name, samples in make_story_effects().items():
            game_audio._effects[name] = game_audio._to_sound(samples, SOUND_VOLUME)
