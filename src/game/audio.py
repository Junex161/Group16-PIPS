"""Music and sound effects, synthesised in code (no audio files needed).

Every track is a small arrangement of instruments (melody, chords, bass and
drums) that is written down below as text and rendered into one seamless
loop with NumPy. All notes fade in and out smoothly, which prevents clicks,
and a soft echo makes the result sound less dry. If the computer has no
sound device the game simply stays silent.
"""

import threading
from functools import lru_cache

import numpy as np
import pygame

from .config import MUSIC_VOLUME, SOUND_VOLUME

SAMPLE_RATE = 22050
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
REST = "-"
BEATS_PER_BAR = 4
STEPS_PER_BAR = 16

# Sound of each instrument: overtones (multiple, loudness), envelope in
# seconds (attack, decay, release) with the sustain level, and options.
INSTRUMENTS = {
    "keys": {"harmonics": ((1, 1.0), (2, 0.3), (3, 0.08)), "attack": 0.006, "decay": 0.6, "sustain": 0.2, "release": 0.25},
    "flute": {"harmonics": ((1, 1.0), (2, 0.12), (3, 0.04)), "attack": 0.04, "decay": 0.2, "sustain": 0.7, "release": 0.15, "vibrato": 5.0},
    "marimba": {"harmonics": ((1, 1.0), (4, 0.2)), "attack": 0.003, "decay": 0.35, "sustain": 0.0, "release": 0.08},
    "pad": {"harmonics": ((1, 1.0), (2, 0.15)), "attack": 0.4, "decay": 0.4, "sustain": 0.8, "release": 0.6, "detune": 0.004},
    "bass": {"harmonics": ((1, 1.0), (2, 0.35), (3, 0.1)), "attack": 0.01, "decay": 0.25, "sustain": 0.55, "release": 0.08},
}


def note_frequency(name):
    """Return the frequency in Hz of a note such as "A4" or "F#5"."""
    pitch, octave = name[:-1], int(name[-1])
    if pitch not in NOTE_NAMES:
        raise ValueError(f"unknown note: {name}")
    semitones_from_a4 = NOTE_NAMES.index(pitch) - 9 + (octave - 4) * 12
    return 440.0 * 2 ** (semitones_from_a4 / 12)


def parse(text):
    """
    Turn "E4:1 C4+E4+G4:2 -:1" into a list of ``(notes, beats)`` pairs.

    Each entry is one note, several notes joined by "+" (a chord) or "-" (a
    rest), followed by a colon and the length in beats.
    """
    events = []
    for entry in text.split():
        names, beats = entry.split(":")
        events.append(([] if names == REST else names.split("+"), float(beats)))
    return events


def total_beats(events):
    """Return the length of a parsed part in beats."""
    return sum(beats for _, beats in events)


def _envelope(n_samples, gate_samples, instrument):
    """Return the loudness curve of one note (0 to 1) as an array."""
    attack = max(1, int(instrument["attack"] * SAMPLE_RATE))
    decay = max(1, int(instrument["decay"] * SAMPLE_RATE))
    release = max(1, int(instrument["release"] * SAMPLE_RATE))
    sustain = instrument["sustain"]
    index = np.arange(n_samples)
    curve = np.where(
        index < attack,
        index / attack,
        sustain + (1 - sustain) * np.exp(-(index - attack) / decay),
    )
    # After the key is released, fade out smoothly to zero.
    after = np.clip((index - gate_samples) / release, 0, 1)
    return curve * (1 - after)


@lru_cache(maxsize=512)
def render_note(frequency, seconds, instrument_name, volume=1.0):
    """
    Synthesise one note including its fade-out.

    Parameters
    ----------
    frequency : float
        Pitch in Hz.
    seconds : float
        How long the note is held.
    instrument_name : str
        Key in ``INSTRUMENTS``.
    volume : float, optional
        Loudness from 0 to 1.

    Returns
    -------
    numpy.ndarray
        Float samples between -1 and 1 at ``SAMPLE_RATE`` (cached: do not
        change the array).
    """
    instrument = INSTRUMENTS[instrument_name]
    gate = int(seconds * SAMPLE_RATE)
    n_samples = gate + int(instrument["release"] * SAMPLE_RATE)
    time = np.arange(n_samples) / SAMPLE_RATE
    phase = 2 * np.pi * frequency * time
    if "vibrato" in instrument:
        phase += 0.12 * np.sin(2 * np.pi * instrument["vibrato"] * time) * np.clip(time / 0.3, 0, 1)
    wave = np.zeros(n_samples)
    for multiple, loudness in instrument["harmonics"]:
        wave += loudness * np.sin(multiple * phase)
        if "detune" in instrument:
            wave += loudness * np.sin(multiple * phase * (1 + instrument["detune"]))
    peak = sum(loudness for _, loudness in instrument["harmonics"]) * (2 if "detune" in instrument else 1)
    return volume * wave / peak * _envelope(n_samples, gate, instrument)


def add_wrapped(buffer, start, sound):
    """Add ``sound`` into ``buffer`` at ``start``; what sticks out wraps to the beginning."""
    n_samples = len(buffer)
    start %= n_samples
    first = min(len(sound), n_samples - start)
    buffer[start:start + first] += sound[:first]
    rest = sound[first:]
    while len(rest):
        chunk = rest[:n_samples]
        buffer[:len(chunk)] += chunk
        rest = rest[n_samples:]


def render_part(events, tempo, instrument_name, volume, n_samples):
    """
    Render a melody, chord or bass part into a loop of ``n_samples``.

    Notes that ring on past the end of the loop continue at its start, so
    the loop has no gap or click when it repeats.
    """
    buffer = np.zeros(n_samples)
    seconds_per_beat = 60 / tempo
    position = 0.0
    for names, beats in events:
        start = int(position * seconds_per_beat * SAMPLE_RATE)
        for name in names:
            note = render_note(note_frequency(name), beats * seconds_per_beat * 0.92, instrument_name, volume)
            add_wrapped(buffer, start, note)
        position += beats
    return buffer


def _noise(n_samples, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n_samples)


def _smooth(signal, width):
    """A simple low-pass filter: the moving average over ``width`` samples."""
    return np.convolve(signal, np.ones(width) / width, mode="same")


def make_drum_sounds(volume=1.0):
    """Return soft kick, snare and shaker sounds as float arrays."""
    kick_time = np.arange(int(0.25 * SAMPLE_RATE)) / SAMPLE_RATE
    kick_phase = 2 * np.pi * (50 * kick_time + 70 * (1 - np.exp(-kick_time * 30)) / 30)
    kick = np.sin(kick_phase) * np.exp(-kick_time * 14)
    snare_time = np.arange(int(0.18 * SAMPLE_RATE)) / SAMPLE_RATE
    snare = (0.7 * _smooth(_noise(len(snare_time), 1), 3) + 0.3 * np.sin(2 * np.pi * 190 * snare_time)) * np.exp(-snare_time * 22)
    shaker_noise = _noise(int(0.05 * SAMPLE_RATE), 2)
    shaker_time = np.arange(len(shaker_noise)) / SAMPLE_RATE
    shaker = (shaker_noise - _smooth(shaker_noise, 6)) * np.exp(-shaker_time * 70) * np.clip(shaker_time / 0.004, 0, 1)
    return {"k": 0.9 * volume * kick, "s": 0.45 * volume * snare, "h": 0.18 * volume * shaker}


def render_drums(patterns, tempo, n_bars, n_samples, volume=1.0):
    """
    Render drum patterns into a loop.

    Each pattern has ``STEPS_PER_BAR`` characters per bar: "k" kick,
    "s" snare, "h" shaker and "-" silence; it is repeated for every bar.
    """
    sounds = make_drum_sounds(volume)
    buffer = np.zeros(n_samples)
    samples_per_step = 60 / tempo * BEATS_PER_BAR / STEPS_PER_BAR * SAMPLE_RATE
    for pattern in patterns:
        if len(pattern) != STEPS_PER_BAR:
            raise ValueError(f"a drum pattern needs {STEPS_PER_BAR} steps")
        for step in range(n_bars * STEPS_PER_BAR):
            sound = sounds.get(pattern[step % STEPS_PER_BAR])
            if sound is not None:
                add_wrapped(buffer, int(step * samples_per_step), sound)
    return buffer


def add_echo(signal, tempo, feedback=0.28, repeats=3):
    """Add a soft echo every three sixteenth notes (wrapping around the loop)."""
    delay = int(60 / tempo * 0.75 * SAMPLE_RATE)
    result = signal.copy()
    for repeat in range(1, repeats + 1):
        result += np.roll(_smooth(signal, 4 * repeat), delay * repeat) * feedback**repeat
    return result


# A track: tempo, number of bars, parts (text, instrument, volume) and drums.
TRACKS = {
    # Home screen: slow and warm.
    "title": {
        "tempo": 84,
        "bars": 16,
        "parts": [
            (
                "E4:1 G4:1 B4:2 A4:1 G4:1 E4:2 F4:1 A4:1 C5:2 B4:1 A4:1 G4:2 "
                "E4:1 G4:1 C5:2 C5:1 B4:1 A4:2 F4:1 A4:1 D5:1 C5:1 B4:3 -:1 "
                "G4:1 E4:1 C4:2 A4:1 C5:1 E5:1 -:1 F4:1 E4:1 C4:2 D4:1 E4:1 G4:2 "
                "E4:1 D4:1 C4:2 A3:1 C4:1 E4:2 F4:1 E4:1 D4:1 F4:1 C4:3 -:1",
                "keys",
                0.55,
            ),
            (
                "C3+E3+G3+B3:4 A2+C3+E3+G3:4 F2+A2+C3+E3:4 G2+B2+D3+E3:4 "
                "C3+E3+G3+B3:4 A2+C3+E3+G3:4 D3+F3+A3+C4:4 G2+B2+D3+F3:4 " * 2,
                "pad",
                0.16,
            ),
            ("C2:2 G2:2 A1:2 E2:2 F1:2 C2:2 G1:2 D2:2 C2:2 G2:2 A1:2 E2:2 D2:2 A2:2 G1:2 G2:2 " * 2, "bass", 0.45),
        ],
        "drums": (),
    },
    # Level 1, meadow: bouncy and upbeat, in G major.
    "meadow": {
        "tempo": 116,
        "bars": 16,
        "parts": [
            (
                "B4:1 D5:.5 B4:.5 A4:1 G4:1 A4:1.5 F#4:.5 D4:1 F#4:1 G4:1 B4:.5 G4:.5 E4:1 G4:1 E4:2 -:1 D4:1 "
                "G4:.5 A4:.5 B4:1 D5:1 B4:1 A4:1 F#4:.5 A4:.5 D5:2 B4:1 A4:.5 G4:.5 E4:1 B4:1 C5:1 B4:.5 A4:.5 G4:2 "
                "D5:1.5 B4:.5 G4:1 B4:1 A4:1 D5:1 F#4:1 A4:1 G4:1.5 E4:.5 B4:1 G4:1 E4:1 G4:1 C5:1 E5:1 "
                "D5:1 B4:.5 D5:.5 G5:1 D5:1 F#5:1 E5:.5 D5:.5 A4:2 B4:1 G4:.5 B4:.5 E5:1 D5:1 C5:1 E5:1 D5:1 -:1",
                "flute",
                0.45,
            ),
            (
                "-:.5 G3+B3+D4:.5 -:.5 G3+B3+D4:.5 -:.5 G3+B3+D4:.5 -:.5 G3+B3+D4:.5 "
                "-:.5 F#3+A3+D4:.5 -:.5 F#3+A3+D4:.5 -:.5 F#3+A3+D4:.5 -:.5 F#3+A3+D4:.5 "
                "-:.5 G3+B3+E4:.5 -:.5 G3+B3+E4:.5 -:.5 G3+B3+E4:.5 -:.5 G3+B3+E4:.5 "
                "-:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 " * 4,
                "keys",
                0.12,
            ),
            (
                "G2:1 G2:.5 D3:.5 G2:1 D3:1 D2:1 D2:.5 A2:.5 D2:1 A2:1 "
                "E2:1 E2:.5 B2:.5 E2:1 B2:1 C2:1 C2:.5 G2:.5 C2:1 G2:1 " * 4,
                "bass",
                0.5,
            ),
        ],
        "drums": ("k---s---k-k-s---", "h-h-h-h-h-h-h-h-"),
    },
    # Professor Fin's Pond Challenge: calm and steady, so that it does not
    # distract; the same music plays in every condition of the task.
    "pond": {
        "tempo": 76,
        "bars": 8,
        "parts": [
            ("D3+F#3+A3:4 B2+D3+F#3:4 G2+B2+D3:4 A2+C#3+E3:4 " * 2, "pad", 0.2),
            (
                "D4:.5 F#4:.5 A4:.5 F#4:.5 D4:.5 F#4:.5 A4:.5 F#4:.5 B3:.5 D4:.5 F#4:.5 D4:.5 B3:.5 D4:.5 F#4:.5 D4:.5 "
                "G3:.5 B3:.5 D4:.5 B3:.5 G3:.5 B3:.5 D4:.5 B3:.5 A3:.5 C#4:.5 E4:.5 C#4:.5 A3:.5 C#4:.5 E4:.5 C#4:.5 " * 2,
                "marimba",
                0.12,
            ),
            ("D2:4 B1:4 G1:4 A1:4 " * 2, "bass", 0.3),
        ],
        "drums": (),
    },
    # Cave: slow and mysterious, in A minor.
    "cave": {
        "tempo": 90,
        "bars": 8,
        "parts": [
            ("E4:3 -:1 C4:2 A3:2 G4:3 -:1 D4:2 B3:2 E4:1 A4:1 C5:2 A4:3 -:1 G#4:2 B4:2 E4:4", "flute", 0.4),
            (
                "A3:.5 C4:.5 E4:.5 A4:.5 E4:.5 C4:.5 A3:.5 E4:.5 F3:.5 A3:.5 C4:.5 F4:.5 C4:.5 A3:.5 F3:.5 C4:.5 "
                "C4:.5 E4:.5 G4:.5 C5:.5 G4:.5 E4:.5 C4:.5 G4:.5 G3:.5 B3:.5 D4:.5 G4:.5 D4:.5 B3:.5 G3:.5 D4:.5 "
                "A3:.5 C4:.5 E4:.5 A4:.5 E4:.5 C4:.5 A3:.5 E4:.5 F3:.5 A3:.5 C4:.5 F4:.5 C4:.5 A3:.5 F3:.5 C4:.5 "
                "E3:.5 G#3:.5 B3:.5 E4:.5 B3:.5 G#3:.5 E3:.5 B3:.5 E3:.5 G#3:.5 B3:.5 E4:.5 B3:.5 G#3:.5 E3:.5 B3:.5",
                "marimba",
                0.22,
            ),
            ("A2+C3+E3:4 F2+A2+C3:4 C3+E3+G3:4 G2+B2+D3:4 A2+C3+E3:4 F2+A2+C3:4 E2+G#2+B2:4 E2+G#2+B2:4", "pad", 0.18),
            ("A1:4 F1:4 C2:4 G1:4 A1:4 F1:4 E1:4 E1:4", "bass", 0.45),
        ],
        "drums": ("k-------k-------", "--h---h---h---h-"),
    },
    # Whispering Woods: curious and a little mysterious, in E minor.
    "forest": {
        "tempo": 100,
        "bars": 8,
        "parts": [
            ("B4:1 G4:.5 E4:.5 G4:1 B4:1 C5:1.5 B4:.5 A4:2 A4:1 F#4:.5 D4:.5 F#4:1 A4:1 B4:3 -:1 "
             "E5:1 D5:.5 B4:.5 G4:1 B4:1 C5:1 E5:1 A4:2 D5:1 C5:.5 A4:.5 F#4:1 D4:1 E4:3 -:1", "flute", 0.4),
            ("E3:.5 G3:.5 B3:.5 G3:.5 E3:.5 G3:.5 B3:.5 G3:.5 C3:.5 E3:.5 G3:.5 E3:.5 C3:.5 E3:.5 G3:.5 E3:.5 "
             "D3:.5 F#3:.5 A3:.5 F#3:.5 D3:.5 F#3:.5 A3:.5 F#3:.5 E3:.5 G3:.5 B3:.5 G3:.5 E3:.5 G3:.5 B3:.5 G3:.5 " * 2, "marimba", 0.2),
            ("E2:2 B2:2 C2:2 G2:2 D2:2 A2:2 E2:2 B2:2 " * 2, "bass", 0.45),
        ],
        "drums": ("k-----k---s-----", "--h---h---h---h-"),
    },
    # Sky Bridge: airy and quick, in D major.
    "sky": {
        "tempo": 126,
        "bars": 8,
        "parts": [
            ("F#4:.5 A4:.5 D5:1 C#5:.5 A4:.5 E4:1 F#4:.5 B4:.5 D5:1 B4:1 A4:1 G4:.5 B4:.5 D5:1 E5:2 A4:2 F#4:2 "
             "F#5:1 E5:.5 D5:.5 A4:1 F#4:1 B4:1 D5:1 F#5:2 G5:1 F#5:.5 E5:.5 D5:1 B4:1 A4:3 -:1", "flute", 0.4),
            ("-:.5 D4+F#4+A4:.5 -:.5 D4+F#4+A4:.5 -:.5 C#4+E4+A4:.5 -:.5 C#4+E4+A4:.5 "
             "-:.5 B3+D4+F#4:.5 -:.5 B3+D4+F#4:.5 -:.5 B3+D4+G4:.5 -:.5 B3+D4+G4:.5 " * 4, "keys", 0.12),
            ("D2:1 D2:.5 A2:.5 A1:1 A2:1 B1:1 B1:.5 F#2:.5 G1:1 G2:1 " * 4, "bass", 0.5),
        ],
        "drums": ("k---s---k-k-s---", "h-h-h-h-h-h-h-h-"),
    },
    # Sunset heights: warm and lively, in F major.
    "sunset": {
        "tempo": 120,
        "bars": 16,
        "parts": [
            (
                "A4:1 C5:1 F5:1 C5:1 G4:1.5 E4:.5 C4:2 D4:1 F4:1 A4:1 D5:1 D5:1 C5:.5 A#4:.5 F4:2 "
                "A4:.5 A#4:.5 C5:1 A4:1 F4:1 G4:1 E4:1 C5:2 A4:1 F4:.5 A4:.5 D5:1 F5:1 E5:1 D5:1 C5:2 "
                "F5:1.5 E5:.5 C5:1 A4:1 E5:1 C5:1 G4:2 F4:1 A4:1 D5:1.5 C5:.5 A#4:1 A4:1 G4:1 F4:1 "
                "A4:1 C5:1 F5:2 E5:1 G5:1 C5:2 D5:1 F5:1 A4:1 D5:1 C5:3 -:1",
                "flute",
                0.42,
            ),
            (
                "-:.5 A3+C4+F4:.5 -:.5 A3+C4+F4:.5 -:.5 A3+C4+F4:.5 -:.5 A3+C4+F4:.5 "
                "-:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 -:.5 G3+C4+E4:.5 "
                "-:.5 A3+D4+F4:.5 -:.5 A3+D4+F4:.5 -:.5 A3+D4+F4:.5 -:.5 A3+D4+F4:.5 "
                "-:.5 A#3+D4+F4:.5 -:.5 A#3+D4+F4:.5 -:.5 A#3+D4+F4:.5 -:.5 A#3+D4+F4:.5 " * 4,
                "keys",
                0.12,
            ),
            (
                "F2:1 F2:.5 C3:.5 F2:1 C3:1 C2:1 C2:.5 G2:.5 C2:1 G2:1 "
                "D2:1 D2:.5 A2:.5 D2:1 A2:1 A#1:1 A#1:.5 F2:.5 A#1:1 F2:1 " * 4,
                "bass",
                0.5,
            ),
        ],
        "drums": ("k---s---k---s-k-", "h-h-h-h-h-h-h-h-"),
    },
}


def render_track(name):
    """
    Render a whole music track into one seamless loop.

    Returns
    -------
    numpy.ndarray
        Float samples between -1 and 1 at ``SAMPLE_RATE``.
    """
    track = TRACKS[name]
    tempo, n_bars = track["tempo"], track["bars"]
    n_samples = int(n_bars * BEATS_PER_BAR * 60 / tempo * SAMPLE_RATE)
    mix = np.zeros(n_samples)
    for text, instrument, volume in track["parts"]:
        events = parse(text)
        if abs(total_beats(events) - n_bars * BEATS_PER_BAR) > 1e-6:
            raise ValueError(f"a part of '{name}' does not last {n_bars} bars")
        mix += render_part(events, tempo, instrument, volume, n_samples)
    mix = add_echo(mix, tempo)
    if track["drums"]:
        mix += render_drums(track["drums"], tempo, n_bars, n_samples, 0.6)
    # Gentle limiting keeps loud moments from distorting.
    return np.tanh(1.3 * mix / max(1.0, np.abs(mix).max())) / np.tanh(1.3)


def render_effect(start_hz, end_hz, seconds, volume=0.5, noise=0.0, seed=0):
    """
    Create a short sound effect that glides from one pitch to another.

    The sound fades in and out, so it never clicks.

    Parameters
    ----------
    start_hz, end_hz : float
        Pitch at the start and at the end.
    seconds : float
        Length of the sound.
    volume : float, optional
        Loudness from 0 to 1.
    noise : float, optional
        Share of noise mixed in (0 = pure tone, 1 = only noise).
    seed : int, optional
        Seed of the noise.

    Returns
    -------
    numpy.ndarray
        Float samples between -1 and 1 at ``SAMPLE_RATE``.
    """
    n_samples = int(seconds * SAMPLE_RATE)
    time = np.arange(n_samples) / SAMPLE_RATE
    frequency = np.linspace(start_hz, end_hz, n_samples)
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    tone = 0.8 * np.sin(phase) + 0.2 * np.sin(2 * phase)
    sound = (1 - noise) * tone + noise * _smooth(_noise(n_samples, seed), 2)
    fade = np.minimum(np.clip(time / 0.005, 0, 1), np.exp(-time / (seconds * 0.45)))
    return volume * sound * fade


def _sequence(*parts):
    """Play several sounds one after the other."""
    return np.concatenate(parts)


def make_sound_effects():
    """Return a dict that maps effect names to float sample arrays."""
    notes = lambda *frequencies: _sequence(*(render_effect(f, f, 0.09, 0.4) for f in frequencies))  # noqa: E731
    return {
        "jump": render_effect(300, 520, 0.14, 0.35),
        "double_jump": render_effect(420, 700, 0.14, 0.35),
        "spark": notes(880, 1175),
        "stomp": render_effect(260, 90, 0.15, 0.5),
        "punch": render_effect(200, 80, 0.1, 0.55, noise=0.6, seed=1),
        "shoot": render_effect(620, 180, 0.14, 0.4, noise=0.15, seed=7),
        "break": render_effect(150, 60, 0.18, 0.55, noise=0.8, seed=2),
        "hurt": render_effect(400, 140, 0.3, 0.45, noise=0.2, seed=3),
        "powerup": notes(392, 494, 587, 784),
        "note": notes(523, 659, 784),
        "checkpoint": notes(440, 587),
        "fear": _sequence(render_effect(1047, 1000, 0.2, 0.35), render_effect(140, 60, 0.3, 0.5, noise=0.5, seed=4)),
        "correct": notes(523, 784),
        "wrong": _sequence(render_effect(220, 210, 0.14, 0.4), render_effect(165, 150, 0.24, 0.4)),
        "select": render_effect(520, 520, 0.05, 0.3),
        "firework": render_effect(900, 120, 0.5, 0.35, noise=0.55, seed=8),
        "win": notes(392, 494, 587, 784, 988),
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
            pygame.mixer.set_reserved(1)
            self._music_channel = pygame.mixer.Channel(0)
            self.enabled = sample_format == -16
        except pygame.error:
            return
        if self.enabled:
            self._effects = {name: self._to_sound(samples, SOUND_VOLUME) for name, samples in make_sound_effects().items()}
            # Render the music in the background, so that changing worlds
            # later never stutters and the game starts without waiting.
            threading.Thread(target=self._prepare_music, daemon=True).start()

    def _prepare_music(self):
        for name in TRACKS:
            if name in self._music:
                continue
            samples = render_track(name)
            try:
                self._music[name] = self._to_sound(samples, MUSIC_VOLUME)
            except pygame.error:
                return  # the game was closed while the music was rendering

    def _to_sound(self, samples, volume):
        """Convert float samples at SAMPLE_RATE to a Sound in the mixer's format."""
        if self._frequency != SAMPLE_RATE:
            n_frames = int(len(samples) * self._frequency / SAMPLE_RATE)
            samples = np.interp(np.linspace(0, len(samples) - 1, n_frames), np.arange(len(samples)), samples)
        frames = np.clip(samples * 32767, -32767, 32767).astype(np.int16)
        if self._n_channels > 1:
            frames = np.repeat(frames[:, None], self._n_channels, axis=1)
        sound = pygame.mixer.Sound(buffer=np.ascontiguousarray(frames).tobytes())
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
        if track not in self._music:  # not rendered in the background yet
            self._music[track] = self._to_sound(render_track(track), MUSIC_VOLUME)
        self._music_channel.play(self._music[track], loops=-1, fade_ms=400)
        if self.muted:
            self.pause_music()

    def pause_music(self):
        """Silence the music, for example during the flanker task."""
        if self.enabled:
            self._music_channel.pause()

    def resume_music(self):
        """Continue the music after ``pause_music``."""
        if self.enabled and not self.muted:
            self._music_channel.unpause()

    def toggle_mute(self):
        """Switch all sound off or on again; return True if now muted."""
        self.muted = not self.muted
        if self.muted:
            self.pause_music()
        else:
            self.resume_music()
        return self.muted
