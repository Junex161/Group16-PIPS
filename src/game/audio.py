"""Music and sound effects, synthesised in code (no audio files needed).

Every music track is a small arrangement of up to four parts that are played
at the same time: a lead melody, a bass line, a quiet arpeggio and drums. The
parts are written down below as lists of ``(note, beats)`` pairs and as drum
patterns. If the computer has no sound device the game simply stays silent.
"""

import math
import random
from array import array

import pygame

from .config import MUSIC_VOLUME, SOUND_VOLUME

SAMPLE_RATE = 22050
MAX_AMPLITUDE = 32767
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
REST = "-"
N_MUSIC_CHANNELS = 4
# Drum patterns have this many steps per bar (sixteenth notes in 4/4 time).
STEPS_PER_BAR = 16
BEATS_PER_BAR = 4


def note_frequency(name):
    """Return the frequency in Hz of a note such as "A4" or "F#5"."""
    pitch, octave = name[:-1], int(name[-1])
    if pitch not in NOTE_NAMES:
        raise ValueError(f"unknown note: {name}")
    semitones_from_a4 = NOTE_NAMES.index(pitch) - 9 + (octave - 4) * 12
    return 440.0 * 2 ** (semitones_from_a4 / 12)


def notes(text, beats):
    """Turn "E4 G4 -" into a list of notes that all last ``beats`` beats."""
    return [(name, beats) for name in text.split()]


def melody(text):
    """
    Turn "E4:1 G4:.5 -:2" into a list of ``(note, beats)`` pairs.

    Each entry is a note name (or "-" for a rest), a colon and its length in
    beats.
    """
    pairs = []
    for entry in text.split():
        name, beats = entry.split(":")
        pairs.append((name, float(beats)))
    return pairs


def transpose(note_list, octaves):
    """Shift all notes of a ``(note, beats)`` list by whole octaves."""
    return [
        (name if name == REST else f"{name[:-1]}{int(name[-1]) + octaves}", beats)
        for name, beats in note_list
    ]


def _arpeggio(chords, repeats, beats):
    """Repeat each chord pattern ``repeats`` times, one note every ``beats`` beats."""
    return [note for chord in chords for note in notes(chord, beats) * repeats]


# A part is (notes, wave, volume). Waves: "soft" (flute-like), "triangle"
# (round, for the bass) and "pulse" (a mellow chiptune sound).
TRACKS = {
    # Home screen: slow and calm.
    "title": {
        "tempo": 92,
        "parts": [
            (
                melody(
                    "E4:1 G4:1 C5:2  C5:1 B4:1 A4:2  A4:1 C5:1 F4:2  G4:1 A4:1 B4:2  "
                    "C5:1 G4:1 E4:2  A4:1 E4:1 C4:2  F4:1 A4:1 C5:1 A4:1  G4:3 -:1"
                ),
                "soft",
                0.42,
            ),
            (notes("C3 G3 A2 E3 F2 C3 G2 D3 C3 G3 A2 E3 F2 C3 G2 G2", 2), "triangle", 0.55),
            (_arpeggio(["C4 E4 G4 E4", "A3 C4 E4 C4", "F3 A3 C4 A3", "G3 B3 D4 B3"] * 2, 2, 0.5), "soft", 0.16),
        ],
        "drums": "",
    },
    # Level 1, meadow: fast and driving, in E minor.
    "meadow": {
        "tempo": 150,
        "parts": [
            (
                melody(
                    "E4:.5 G4:.5 B4:1 A4:.5 G4:.5 E4:1  G4:.5 E4:.5 C5:1 B4:.5 G4:.5 E4:1  "
                    "D4:.5 G4:.5 B4:1 D5:1 B4:1  A4:1 F#4:.5 A4:.5 D5:1.5 -:.5  "
                    "E4:.5 G4:.5 B4:.5 E5:.5 D5:1 B4:1  C5:.5 B4:.5 G4:1 E4:.5 G4:.5 C5:1  "
                    "B4:1 D5:1 G4:.5 B4:.5 D5:1  F#4:.5 A4:.5 D5:.5 F#5:.5 D5:1 A4:1"
                ),
                "pulse",
                0.34,
            ),
            (
                _arpeggio(["E2 E2 E3 E2 E2 E3 E2 E3", "C3 C3 C4 C3 C3 C4 C3 C4", "G2 G2 G3 G2 G2 G3 G2 G3", "D3 D3 D4 D3 D3 D4 D3 D4"] * 2, 1, 0.5),
                "triangle",
                0.62,
            ),
            (_arpeggio(["E4 G4 B4 G4", "C4 E4 G4 E4", "D4 G4 B4 G4", "D4 F#4 A4 F#4"] * 2, 4, 0.25), "soft", 0.13),
        ],
        "drums": "k-h-s-h-kkh-s-hh",
    },
    # Cave: slow, low and dark, in A minor.
    "cave": {
        "tempo": 100,
        "parts": [
            (
                melody(
                    "A3:.5 C4:.5 E4:.5 C4:.5 A3:.5 C4:.5 B3:.5 G#3:.5  A3:.5 C4:.5 E4:.5 A4:.5 G4:.5 E4:.5 C4:.5 B3:.5  "
                    "F3:.5 A3:.5 C4:.5 A3:.5 F3:.5 A3:.5 G3:.5 E3:.5  E3:1 G#3:1 B3:1 -:1  "
                    "A3:.5 E4:.5 A4:.5 E4:.5 C4:.5 E4:.5 B3:.5 E4:.5  A3:.5 C4:.5 E4:.5 A4:.5 B4:.5 A4:.5 E4:.5 C4:.5  "
                    "D4:.5 F4:.5 A4:.5 F4:.5 D4:.5 F4:.5 E4:.5 D4:.5  C4:1 B3:1 A3:1 -:1"
                ),
                "soft",
                0.4,
            ),
            (notes("A2 E3 A2 E3 A2 E3 A2 E3 F2 C3 F2 C3 E2 B2 E3 - A2 E3 A2 E3 A2 E3 A2 E3 D3 A3 D3 A3 A2 E3 A2 -", 1), "triangle", 0.6),
        ],
        "drums": "k-------h---k-h-",
    },
    # Sunset heights: bright and quick, in G major.
    "sunset": {
        "tempo": 144,
        "parts": [
            (
                melody(
                    "G4:.5 B4:.5 D5:1 B4:.5 G4:.5 D5:1  E4:.5 G4:.5 B4:1 G4:.5 E4:.5 B4:1  "
                    "C4:.5 E4:.5 G4:.5 C5:.5 E5:1 C5:1  D4:.5 F#4:.5 A4:.5 D5:.5 A4:1 F#4:1  "
                    "G4:.5 B4:.5 D5:.5 G5:.5 D5:1 B4:1  E4:.5 G4:.5 B4:.5 E5:.5 B4:1 G4:1  "
                    "C5:.5 B4:.5 A4:.5 G4:.5 A4:.5 B4:.5 C5:.5 D5:.5  G4:1 D5:1 G4:1 -:1"
                ),
                "pulse",
                0.32,
            ),
            (
                _arpeggio(["G2 G2 G3 G2 G2 G3 G2 G3", "E2 E2 E3 E2 E2 E3 E2 E3", "C3 C3 C4 C3 C3 C4 C3 C4", "D3 D3 D4 D3 D3 D4 D3 D4"] * 2, 1, 0.5),
                "triangle",
                0.6,
            ),
            (_arpeggio(["G3 B3 D4 B3", "E3 G3 B3 G3", "C4 E4 G4 E4", "D4 F#4 A4 F#4"] * 2, 2, 0.5), "soft", 0.14),
        ],
        "drums": "k-h-s-h-k-h-s-hh",
    },
}


def _cycle(frequency, amplitude, wave):
    """Return one period of a wave as a list of samples."""
    length = max(2, round(SAMPLE_RATE / frequency))
    phases = [index / length for index in range(length)]
    if wave == "triangle":
        values = [1 - 4 * abs(phase - 0.5) for phase in phases]
    elif wave == "soft":
        # A sine with two quiet overtones sounds like a flute or an organ.
        values = [
            (math.sin(2 * math.pi * p) + 0.3 * math.sin(4 * math.pi * p) + 0.12 * math.sin(6 * math.pi * p)) / 1.3
            for p in phases
        ]
    elif wave == "pulse":
        # A narrow square wave with rounded edges: chiptune, but not shrill.
        raw = [1.0 if phase < 0.3 else -0.6 for phase in phases]
        width = max(1, length // 8)
        values = [sum(raw[(index + offset) % length] for offset in range(-width, width + 1)) / (2 * width + 1) for index in range(length)]
    else:
        raise ValueError(f"unknown wave: {wave}")
    return [round(value * amplitude) for value in values]


def render_voice(note_list, tempo, wave="soft", volume=0.5):
    """
    Turn a list of notes into audio samples.

    Parameters
    ----------
    note_list : list of tuple
        ``(note name, beats)`` pairs; the name "-" is a rest.
    tempo : float
        Beats per minute.
    wave : str, optional
        "soft", "triangle" or "pulse".
    volume : float, optional
        Loudness from 0 to 1.

    Returns
    -------
    array.array
        Signed 16-bit mono samples at ``SAMPLE_RATE``.
    """
    samples = array("h")
    samples_per_beat = SAMPLE_RATE * 60 / tempo
    position = 0.0
    for name, beats in note_list:
        position += beats * samples_per_beat
        note_length = round(position) - len(samples)
        if name != REST:
            # The note fades out in steps and ends a little early, so that
            # repeated notes can be told apart.
            sounding = int(note_length * 0.88)
            frequency = note_frequency(name)
            for share, loudness in ((0.06, 0.6), (0.44, 1.0), (0.3, 0.7), (0.2, 0.4)):
                cycle = _cycle(frequency, volume * loudness * MAX_AMPLITUDE, wave)
                repeats = max(1, int(sounding * share / len(cycle)))
                samples.extend(cycle * repeats)
        missing = round(position) - len(samples)
        if missing > 0:
            samples.extend([0] * missing)
        else:
            del samples[round(position):]
    return samples


def render_drums(pattern, tempo, n_bars, volume=0.5):
    """
    Turn a one-bar drum pattern into audio samples.

    Parameters
    ----------
    pattern : str
        ``STEPS_PER_BAR`` characters: "k" kick drum, "s" snare, "h" hi-hat,
        "-" silence.
    tempo : float
        Beats per minute.
    n_bars : int
        Number of bars; the pattern is repeated.
    volume : float, optional
        Loudness from 0 to 1.

    Returns
    -------
    array.array
        Signed 16-bit mono samples at ``SAMPLE_RATE``.
    """
    if len(pattern) != STEPS_PER_BAR:
        raise ValueError(f"a drum pattern needs {STEPS_PER_BAR} steps")
    hits = {
        "k": render_sweep(130, 45, 0.13, volume, wave="sine"),
        "s": render_sweep(240, 160, 0.11, volume * 0.6, noise=0.85, seed=5),
        "h": render_sweep(900, 900, 0.035, volume * 0.22, noise=1.0, seed=6),
    }
    samples_per_step = SAMPLE_RATE * 60 / tempo * BEATS_PER_BAR / STEPS_PER_BAR
    n_steps = n_bars * STEPS_PER_BAR
    samples = array("h", [0]) * round(n_steps * samples_per_step)
    for step in range(n_steps):
        hit = hits.get(pattern[step % STEPS_PER_BAR])
        if hit:
            start = round(step * samples_per_step)
            end = min(start + len(hit), len(samples))
            samples[start:end] = hit[: end - start]
    return samples


def render_sweep(start_hz, end_hz, duration, volume=0.5, noise=0.0, seed=0, wave="square"):
    """
    Create a short tone that glides from one pitch to another.

    Parameters
    ----------
    start_hz, end_hz : float
        Pitch at the start and at the end.
    duration : float
        Length in seconds.
    volume : float, optional
        Loudness from 0 to 1; the tone fades out towards its end.
    noise : float, optional
        Share of random noise mixed in (0 = pure tone, 1 = only noise).
    seed : int, optional
        Seed of the noise, so that a sound is the same on every run.
    wave : str, optional
        "square" (bright) or "sine" (soft).

    Returns
    -------
    array.array
        Signed 16-bit mono samples at ``SAMPLE_RATE``.
    """
    rng = random.Random(seed)
    n_samples = int(SAMPLE_RATE * duration)
    samples = array("h")
    phase = 0.0
    for index in range(n_samples):
        share = index / n_samples
        phase += (start_hz + (end_hz - start_hz) * share) / SAMPLE_RATE
        if wave == "sine":
            tone = math.sin(2 * math.pi * phase)
        else:
            tone = 1.0 if phase % 1 < 0.5 else -1.0
        value = tone * (1 - noise) + rng.uniform(-1, 1) * noise
        samples.append(round(value * volume * (1 - share) * MAX_AMPLITUDE))
    return samples


def render_track(name):
    """
    Render all parts of a music track.

    Returns
    -------
    list of array.array
        One sample array per part (drums last); all have the same length.
    """
    track = TRACKS[name]
    tempo = track["tempo"]
    parts = [render_voice(note_list, tempo, wave, volume) for note_list, wave, volume in track["parts"]]
    if track["drums"]:
        n_beats = sum(beats for _, beats in track["parts"][0][0])
        parts.append(render_drums(track["drums"], tempo, round(n_beats / BEATS_PER_BAR)))
    return parts


def _join(*parts):
    """Play several sounds one after the other."""
    joined = array("h")
    for part in parts:
        joined.extend(part)
    return joined


def make_sound_effects():
    """Return a dict that maps effect names to audio samples."""
    return {
        "jump": render_sweep(260, 520, 0.12, 0.35, wave="sine"),
        "double_jump": render_sweep(390, 780, 0.12, 0.35, wave="sine"),
        "spark": _join(render_sweep(660, 660, 0.05, 0.3, wave="sine"), render_sweep(880, 880, 0.09, 0.3, wave="sine")),
        "stomp": render_sweep(320, 90, 0.14, 0.5),
        "punch": render_sweep(220, 80, 0.09, 0.6, noise=0.6, seed=1),
        "shoot": render_sweep(700, 180, 0.12, 0.4, noise=0.15, seed=7),
        "break": render_sweep(160, 60, 0.16, 0.6, noise=0.8, seed=2),
        "hurt": render_sweep(420, 120, 0.28, 0.5, noise=0.2, seed=3),
        "powerup": _join(*(render_sweep(f, f, 0.07, 0.35, wave="sine") for f in (392, 494, 587, 784))),
        "note": _join(*(render_sweep(f, f, 0.09, 0.35, wave="sine") for f in (523, 659, 784))),
        "checkpoint": _join(render_sweep(440, 440, 0.08, 0.35, wave="sine"), render_sweep(587, 587, 0.14, 0.35, wave="sine")),
        "fear": _join(render_sweep(1047, 1047, 0.18, 0.4, wave="sine"), render_sweep(140, 60, 0.3, 0.6, noise=0.5, seed=4)),
        "correct": _join(render_sweep(523, 523, 0.09, 0.35, wave="sine"), render_sweep(784, 784, 0.16, 0.35, wave="sine")),
        "wrong": _join(render_sweep(220, 220, 0.12, 0.4), render_sweep(165, 165, 0.22, 0.4)),
        "select": render_sweep(520, 520, 0.04, 0.3, wave="sine"),
        "win": _join(*(render_sweep(f, f, 0.11, 0.35, wave="sine") for f in (392, 494, 587, 784, 988))),
    }


class Audio:
    """
    Plays the music and the sound effects.

    All methods do nothing if no sound device is available, so the rest of
    the game never has to check.
    """

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.current_track = None
        self._music = {}
        self._effects = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            self._frequency, sample_format, self._n_channels = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(max(pygame.mixer.get_num_channels(), N_MUSIC_CHANNELS + 8))
            pygame.mixer.set_reserved(N_MUSIC_CHANNELS)
            self._music_channels = [pygame.mixer.Channel(index) for index in range(N_MUSIC_CHANNELS)]
            self.enabled = sample_format == -16
        except pygame.error:
            return
        if self.enabled:
            self._effects = {name: self._to_sound(samples, SOUND_VOLUME) for name, samples in make_sound_effects().items()}

    def _to_sound(self, samples, volume):
        """Convert mono samples at SAMPLE_RATE to a Sound in the mixer's format."""
        step = SAMPLE_RATE / self._frequency
        if step != 1 or self._n_channels != 1:
            n_frames = int(len(samples) / step)
            converted = array("h")
            for index in range(n_frames):
                converted.extend([samples[int(index * step)]] * self._n_channels)
            samples = converted
        sound = pygame.mixer.Sound(buffer=samples.tobytes())
        sound.set_volume(volume)
        return sound

    def play(self, effect):
        """Play a sound effect by name (see ``make_sound_effects``)."""
        if self.enabled and not self.muted:
            self._effects[effect].play()

    def play_music(self, track):
        """Loop a music track by name; does nothing if it is already playing."""
        if not self.enabled or track == self.current_track:
            return
        self.current_track = track
        if track not in self._music:
            self._music[track] = [self._to_sound(part, MUSIC_VOLUME) for part in render_track(track)]
        for channel in self._music_channels:
            channel.stop()
        for channel, part in zip(self._music_channels, self._music[track]):
            channel.play(part, loops=-1)
        if self.muted:
            self.pause_music()

    def pause_music(self):
        """Silence the music, for example during the flanker task."""
        if self.enabled:
            for channel in self._music_channels:
                channel.pause()

    def resume_music(self):
        """Continue the music after ``pause_music``."""
        if self.enabled and not self.muted:
            for channel in self._music_channels:
                channel.unpause()

    def toggle_mute(self):
        """Switch all sound off or on again; return True if now muted."""
        self.muted = not self.muted
        if self.muted:
            self.pause_music()
        else:
            self.resume_music()
        return self.muted
