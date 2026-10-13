"""Music and sound effects, synthesised in code (no audio files needed).

The music is a simple chiptune: every track is a melody played with a square
wave and a bass line played with a triangle wave. Both are written down below
as lists of ``(note, beats)`` pairs. If the computer has no sound device the
game simply stays silent.
"""

import random
from array import array

import pygame

from .config import MUSIC_VOLUME, SOUND_VOLUME

SAMPLE_RATE = 22050
MAX_AMPLITUDE = 32767
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
REST = "-"


def note_frequency(name):
    """Return the frequency in Hz of a note such as "A4" or "F#5"."""
    pitch, octave = name[:-1], int(name[-1])
    if pitch not in NOTE_NAMES:
        raise ValueError(f"unknown note: {name}")
    semitones_from_a4 = NOTE_NAMES.index(pitch) - 9 + (octave - 4) * 12
    return 440.0 * 2 ** (semitones_from_a4 / 12)


def _eighths(text):
    """Turn "E5 G5 C6" into a list of eighth notes (half a beat each)."""
    return [(name, 0.5) for name in text.split()]


def _quarters(text):
    """Turn "C3 G3" into a list of quarter notes (one beat each)."""
    return [(name, 1.0) for name in text.split()]


# Each track: tempo in beats per minute, melody and bass of equal length.
TRACKS = {
    "meadow": {
        "tempo": 138,
        "melody": _eighths(
            "E5 G5 C6 G5 E5 G5 A5 G5  F5 A5 C6 A5 F5 A5 G5 E5  D5 F5 A5 F5 D5 F5 G5 B5"
        )
        + [("C6", 1.0), ("G5", 0.5), ("E5", 0.5), ("C5", 1.0), (REST, 1.0)]
        + _eighths("E5 G5 C6 E6 D6 C6 A5 G5  F5 A5 C6 F6 E6 C6 A5 F5  G5 B5 D6 G6 F6 D6 B5 G5")
        + [("C6", 1.5), ("E6", 0.5), ("C6", 1.0), (REST, 1.0)],
        "bass": _quarters(
            "C3 G3 C3 G3  F3 C4 F3 C4  D3 A3 G3 B3  C3 G3 C3 -  "
            "C3 G3 C3 G3  F3 C4 F3 C4  G3 D4 G3 D4  C3 G3 C4 -"
        ),
    },
    "cave": {
        "tempo": 100,
        "melody": _eighths(
            "A4 C5 E5 C5 A4 C5 B4 G#4  A4 C5 E5 A5 G5 E5 C5 B4  F4 A4 C5 A4 F4 A4 G4 E4"
        )
        + [("E4", 1.0), ("G#4", 1.0), ("B4", 1.0), (REST, 1.0)]
        + _eighths("A4 E5 A5 E5 C5 E5 B4 E5  A4 C5 E5 A5 B5 A5 E5 C5  D5 F5 A5 F5 D5 F5 E5 D5")
        + [("C5", 1.0), ("B4", 1.0), ("A4", 1.0), (REST, 1.0)],
        "bass": _quarters(
            "A2 E3 A2 E3  A2 E3 A2 E3  F2 C3 F2 C3  E2 B2 E3 -  "
            "A2 E3 A2 E3  A2 E3 A2 E3  D3 A3 D3 A3  A2 E3 A2 -"
        ),
    },
    "sunset": {
        "tempo": 150,
        "melody": _eighths(
            "G5 B5 D6 B5 G5 B5 D6 G6  E5 G5 B5 G5 E5 G5 B5 E6  C5 E5 G5 C6 E6 C6 G5 E5  "
            "D5 F#5 A5 D6 F#6 D6 A5 F#5  G5 B5 D6 G6 F#6 D6 B5 G5  E5 G5 B5 E6 D6 B5 G5 E5  "
            "C6 B5 A5 G5 A5 B5 C6 D6"
        )
        + [("G5", 1.0), ("D6", 1.0), ("G6", 1.0), (REST, 1.0)],
        "bass": _quarters(
            "G2 D3 G2 D3  E2 B2 E2 B2  C3 G3 C3 G3  D3 A3 D3 A3  "
            "G2 D3 G2 D3  E2 B2 E2 B2  C3 G3 D3 A3  G2 D3 G3 -"
        ),
    },
}


def _cycle(frequency, amplitude, wave):
    """Return one period of a square or triangle wave as a list of samples."""
    length = max(2, round(SAMPLE_RATE / frequency))
    amplitude = round(amplitude)
    if wave == "square":
        return [amplitude if index < length / 2 else -amplitude for index in range(length)]
    return [round(amplitude * (1 - 4 * abs(index / length - 0.5))) for index in range(length)]


def render_voice(notes, tempo, wave="square", volume=0.5):
    """
    Turn a list of notes into audio samples.

    Parameters
    ----------
    notes : list of tuple
        ``(note name, beats)`` pairs; the name "-" is a rest.
    tempo : float
        Beats per minute.
    wave : str, optional
        "square" (bright) or "triangle" (soft).
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
    for name, beats in notes:
        position += beats * samples_per_beat
        note_length = round(position) - len(samples)
        if name != REST:
            # The note fades out in steps and ends a little early, so that
            # repeated notes can be told apart.
            sounding = int(note_length * 0.85)
            frequency = note_frequency(name)
            for share, loudness in ((0.5, 1.0), (0.3, 0.7), (0.2, 0.45)):
                cycle = _cycle(frequency, volume * loudness * MAX_AMPLITUDE, wave)
                repeats = max(1, int(sounding * share / len(cycle)))
                samples.extend(cycle * repeats)
        missing = round(position) - len(samples)
        if missing > 0:
            samples.extend([0] * missing)
        else:
            del samples[round(position):]
    return samples


def render_sweep(start_hz, end_hz, duration, volume=0.5, noise=0.0, seed=0):
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
        tone = 1.0 if phase % 1 < 0.5 else -1.0
        value = tone * (1 - noise) + rng.uniform(-1, 1) * noise
        samples.append(round(value * volume * (1 - share) * MAX_AMPLITUDE))
    return samples


def _join(*parts):
    """Play several sounds one after the other."""
    joined = array("h")
    for part in parts:
        joined.extend(part)
    return joined


def make_sound_effects():
    """Return a dict that maps effect names to audio samples."""
    return {
        "jump": render_sweep(380, 760, 0.12, 0.4),
        "double_jump": render_sweep(560, 1120, 0.12, 0.4),
        "spark": _join(render_sweep(988, 988, 0.05, 0.35), render_sweep(1319, 1319, 0.09, 0.35)),
        "stomp": render_sweep(320, 90, 0.14, 0.5),
        "punch": render_sweep(220, 80, 0.09, 0.6, noise=0.6, seed=1),
        "break": render_sweep(160, 60, 0.16, 0.6, noise=0.8, seed=2),
        "hurt": render_sweep(520, 140, 0.28, 0.5, noise=0.2, seed=3),
        "powerup": _join(*(render_sweep(f, f, 0.07, 0.4) for f in (523, 659, 784, 1047))),
        "note": _join(*(render_sweep(f, f, 0.09, 0.4) for f in (784, 988, 1175))),
        "checkpoint": _join(render_sweep(659, 659, 0.08, 0.4), render_sweep(880, 880, 0.14, 0.4)),
        "fear": _join(render_sweep(1568, 1568, 0.18, 0.45), render_sweep(140, 60, 0.3, 0.6, noise=0.5, seed=4)),
        "correct": _join(render_sweep(660, 660, 0.09, 0.4), render_sweep(990, 990, 0.16, 0.4)),
        "wrong": _join(render_sweep(260, 260, 0.12, 0.4), render_sweep(180, 180, 0.22, 0.4)),
        "select": render_sweep(700, 700, 0.04, 0.3),
        "win": _join(*(render_sweep(f, f, 0.11, 0.4) for f in (523, 659, 784, 1047, 1319))),
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
            pygame.mixer.set_reserved(2)
            self._melody_channel = pygame.mixer.Channel(0)
            self._bass_channel = pygame.mixer.Channel(1)
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
            score = TRACKS[track]
            self._music[track] = (
                self._to_sound(render_voice(score["melody"], score["tempo"], "square", 0.5), MUSIC_VOLUME),
                self._to_sound(render_voice(score["bass"], score["tempo"], "triangle", 0.9), MUSIC_VOLUME),
            )
        melody, bass = self._music[track]
        self._melody_channel.play(melody, loops=-1)
        self._bass_channel.play(bass, loops=-1)
        if self.muted:
            self.pause_music()

    def pause_music(self):
        """Silence the music, for example during the flanker task."""
        if self.enabled:
            self._melody_channel.pause()
            self._bass_channel.pause()

    def resume_music(self):
        """Continue the music after ``pause_music``."""
        if self.enabled and not self.muted:
            self._melody_channel.unpause()
            self._bass_channel.unpause()

    def toggle_mute(self):
        """Switch all sound off or on again; return True if now muted."""
        self.muted = not self.muted
        if self.muted:
            self.pause_music()
        else:
            self.resume_music()
        return self.muted
