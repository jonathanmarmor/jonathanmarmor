# Jonathan Marmor

A piece of music by Jonathan Marmor (1995–2000), for six instruments that can play the written pitches.

This branch preserves the composition algorithm, ports the working code to Python 3, and adds direct MIDI export and dry sampled audio rendering without LilyPond or pyo.

## Quick start

Python 3.12 was used for validation. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python render.py --midi-only
```

For audio, install FluidSynth and FFmpeg and obtain a General MIDI SF2 soundfont. The saved project checkpoint includes the exact TimGM6mb soundfont under `assets/TimGM6mb.sf2` with its license.

```sh
python render.py --soundfont ../assets/TimGM6mb.sf2
```

On Ubuntu, the audio dependencies used were `fluidsynth`, `ffmpeg`, and `timgm6mb-soundfont`. FluidSynth 2.3.4 was used. If the soundfont is installed at `/usr/share/sounds/sf2/TimGM6mb.sf2`, `python render.py` needs no soundfont argument.

The command produces note data (JSON), a standard six-track MIDI file plus tempo track, WAV, MP3, and render settings. `--midi-only` needs only Python dependencies. Use `--output PATH` to choose the output folder and `--name STEM` to name the outputs.

## Resume and change the composition

Edit `configs/six_parts.yaml`, then run:

```sh
python render.py --config configs/six_parts.yaml --soundfont ../assets/TimGM6mb.sf2
```

The initial six-part checkpoint uses the original six-note melody, 320 quarter-note beats per minute, six modulation steps, and both movements. Its target transposition is MIDI 66, with starting offsets −30, −18, −6, +6, +18, +30 semitones and rotations 0 through 5. The initial octave bands span C2 through C8 and converge toward the common register. The target was lowered from the three-part version's MIDI 74 to fit the six starting octave bands.

| Part | Instrument | Pan | MIDI program (zero-based) |
| --- | --- | --- | --- |
| 1 | Bassoon | 20L | 70 |
| 2 | Clean electric guitar | 60R | 27 |
| 3 | Clarinet | 100L | 71 |
| 4 | Harp | 100R | 46 |
| 5 | Flute | 60L | 73 |
| 6 | Piano | 20R | 0 |

Pan values in the config range from −100 (left) to +100 (right). MIDI program numbers are zero-based. Specify a named built-in melody (`original 6`, `original 5`, `another 5`) or a list of semitone offsets. The direct MIDI renderer requires resulting pitches to be integers from 0 through 127; it does not implement microtonal pitch bends. Keep the ensemble at 9 parts or fewer; this workflow is validated with six parts.

Audio is rendered one instrument at a time using FluidSynth. Reverb and chorus are disabled, and MIDI effects sends are zero. Each instrument is collapsed to mono before equal-power panning so hard left/right positions remain exact. Static gain balances RMS between parts; global gain prevents clipping. Natural instrument envelopes and release remain. There are no additional effects. Changing soundfonts or synth versions may change the sound. The MIDI stores instrument and pan choices, but its sound depends on the playback synth.

The current checkpoint has 2,651 notes per part, 2,099 quarter-note beats, and 393.5625 seconds of music. The audio includes three seconds for release (396.5625 seconds total).

## Validation

```sh
python -m doctest jonathanmarmor.py
python -m compileall -q .
python render.py --midi-only --output output/check
```

All 79 composition doctest examples pass. A pre-existing section E doctest was corrected to inspect the full phrase within each arch rather than treating nested lists as notes. No composition algorithm was changed. Integration validation reproduced the previously approved note JSON and MIDI bytes exactly, and exercised the full six-part audio render.

## Legacy notation and playback

The original configs and notation workflow remain. Run `python run.py CONFIG` from this directory for the LilyPond workflow; LilyPond remains an external dependency. That PDF/notation path was not exercised in this checkpoint. `synth.py` is the legacy optional pyo playback path and is not required or validated by the new renderer.
