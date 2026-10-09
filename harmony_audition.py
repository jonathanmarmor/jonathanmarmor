"""Render controlled dry additive timbre comparisons and a readable analysis report.

Requires FFmpeg for MP3. Plotting is optional and requires matplotlib.
"""
import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import wave

import numpy as np
from harmony_analysis import FAMILIES, PAIRS, assemble, stream_cache, write_csv


def note_signal(pitch, age, gate, family, sample_rate):
    """Continuous note age permits excerpts starting in the middle of notes."""
    definition = FAMILIES[family]
    amplitudes = np.array(definition['amplitudes'], float)
    amplitudes /= np.linalg.norm(amplitudes)
    frequencies = 440*2**((pitch-69)/12)*np.array(definition['partials'])
    signal = np.zeros(len(age))
    for frequency, amplitude in zip(frequencies, amplitudes):
        if frequency < .45*sample_rate:
            signal += amplitude*np.sin(2*np.pi*frequency*age)
    attack = np.sin(np.minimum(1, np.maximum(0, age)/definition['attack'])*np.pi/2)**2
    envelope = attack
    if definition['decay'] is not None: envelope = envelope*np.exp(-age/definition['decay'])
    release_age = np.maximum(0, age-gate)
    envelope = envelope*np.exp(-6*release_age/definition['release'])
    envelope[(age < 0) | (release_age >= definition['release'])] = 0
    return signal*envelope


def render_windows(pitches, durations, config, palette, windows, sample_rate=44100):
    """Same score excerpts and pans for all cases. No audio effects."""
    seconds = durations*60/config['tempo_bpm']
    onsets = np.cumsum(np.r_[0, seconds[:-1]])
    segments = []
    for start, end, _ in windows:
        mix = np.zeros((round((end-start+.5)*sample_rate), 2))
        for voice, family in enumerate(palette):
            definition = FAMILIES[family]
            pan = config['ensemble'][voice]['pan']/100
            gains = np.array([math.cos((pan+1)*math.pi/4), math.sin((pan+1)*math.pi/4)])
            if pan == -1: gains[1] = 0
            if pan == 1: gains[0] = 0
            for i, onset in enumerate(onsets):
                gate = .94*seconds[i]
                if onset >= end or onset+gate+definition['release'] <= start: continue
                # End excerpt-held notes at the cut and retain their natural release.
                gate = min(gate, end-onset)
                left = max(0, round((onset-start)*sample_rate))
                right = min(len(mix), round((onset+gate+definition['release']-start)*sample_rate))
                if right <= left: continue
                age = (np.arange(left, right)/sample_rate + start-onset)
                tone = note_signal(pitches[i, voice], age, gate, family, sample_rate)
                mix[left:right] += .06*tone[:, None]*gains[None, :]
        # Prevent an excerpt cut through a held tone from creating a false accent.
        splice = min(len(mix), round(.005*sample_rate))
        if splice: mix[:splice] *= np.linspace(0, 1, splice)[:, None]
        segments.append(mix)
        segments.append(np.zeros((round(.75*sample_rate), 2)))
    return np.concatenate(segments[:-1])


def make_report(analysis, directory, cases, windows):
    rows = analysis['shortlist']
    report = ['# Starting pitches and timbres: first exploration', '',
        f"Screened **{analysis['assignment_count']} assignments**, **{analysis['total_snapshots']:,} chord snapshots**, and **{len(analysis['timbre_pilot'])} pitch/palette cases** (eight representatives × 24 palettes).",
        '', 'Assignment IDs use melody positions 1–6 in instrument order: bassoon, guitar, clarinet, harp, flute, piano. Position 1 is F♯, 2 upper C, 3 A, 4 E, 5 lower C, 6 D. The two Cs remain distinct melody positions.', '',
        '## Representative assignments', '',
        '| Assignment | Why included | Mean roughness | Matched entry effect | Cluster exposure |',
        '|---|---|---:|---:|---:|']
    for r in rows:
        report.append(f"| {r['assignment']} | {', '.join(r['selection_reasons'])} | {r['mean_roughness']:.3f} | {r['entry_transposition_roughness_effect']:.3f} | {r['cluster_exposure']:.3f} |")
    original = next(r for r in rows if 'original' in r['selection_reasons'])
    harmonic = next(r for r in rows if 'harmonic-series' in r['selection_reasons'])
    shock = max(rows, key=lambda r:r['entry_transposition_roughness_effect'])
    report += ['', '## What the first pass found', '',
        f"- The largest matched entry effect is represented by **{shock['assignment']}**, at {shock['entry_transposition_roughness_effect']:.3f} relative units, versus {original['entry_transposition_roughness_effect']:.3f} for the original. This measures a change in spectral roughness, not a listener's surprise rating.",
        f"- The harmonic-series assignment **{harmonic['assignment']}** averages {harmonic['mean_roughness']:.3f} rich-spectrum roughness versus {original['mean_roughness']:.3f} for the original. A harmonic-series opening does not guarantee the lowest roughness over the whole piece.",
        '- Isolated-cluster peak scores have many ties. They are more useful together with cluster exposure, location, and transitions than as a unique winner criterion.',
        '- Pitch-class collections remain invariant throughout the opening when starts are permuted; the absolute voicing and sound-to-pitch mapping change. This shortcut does not apply generally during unequal inward transpositions.',
        '- Static spectral roughness treats rich and plucked sounds identically because their partials are identical. Their different envelopes are audible in the comparison clips; temporal overlap modeling is the next analysis step.',
        '', '## Controlled listening comparisons', '',
        'Every clip contains the same three score windows, separated by silence. All use the existing six pans, equal reference spectral RMS per voice, one shared output gain, 94% written note gates, and the documented natural envelopes. There is no reverb, chorus, compression, or other effect. These are controlled synthetic sound families, not recommendations for final orchestration.', '',
        '| Clip | Assignment | Families, low to high instrument slot |', '|---|---|---|']
    for case in cases: report.append(f"| [{case['name']}.mp3]({case['name']}.mp3) | {case['assignment']} | {', '.join(case['palette'])} |")
    report += ['', '| Score window | Full-piece start | Full-piece end |', '|---|---:|---:|']
    for start, end, label in windows: report.append(f'| {label} | {start:.2f} s | {end:.2f} s |')
    report += ['', '### Timbre comparisons for the same harmonic-series assignment', '',
        '| Clip/palette | Mean roughness | Matched entry effect |', '|---|---:|---:|']
    for case in cases:
        if case['assignment'] != harmonic['assignment']: continue
        result = next(r for r in analysis['timbre_pilot'] if r['assignment']==case['assignment'] and r['palette']==case['palette'])
        report.append(f"| {case['name']} | {result['mean_roughness']:.3f} | {result['entry_transposition_roughness_effect']:.3f} |")
    with (directory/'transposition_events.csv').open() as handle:
        entries = [r for r in csv.DictReader(handle) if r['assignment']==shock['assignment'] and r['update']=='1']
    strongest = max(entries, key=lambda r:abs(float(r['transposition_roughness_effect'])))
    direction = 'reduction' if float(strongest['transposition_roughness_effect']) < 0 else 'increase'
    report += ['', f"For {shock['assignment']}, the largest matched entry change occurs in round {strongest['round']} and is a **{direction} in roughness**. A sudden release can be as consequential as a sudden increase in tension. These comparisons are counterfactual transposition effects, not measurements of a listener's emotional response.",
        '', 'A 5 ms edit-entry envelope prevents clicks when a montage starts inside a held note. High partials above 19,845 Hz are omitted in both analysis and audio; reference RMS normalization precedes that band limit.']
    report += ['', '## Definitions and boundaries', '',
        '- **Matched transposition effect:** at the first sounding of each newly transposed pitch, compare the actual chord with the same chord minus only that new inward increment. Signed event values and absolute round-entry peaks are retained. This controls for the ongoing melodic figure.',
        '- **Immediate jump:** compare the new sounding chord with its predecessor. This includes melodic and transposition changes.',
        '- **Cycle departure:** mean absolute per-voice pitch difference against the previous figure at the same event position. This is a transparent repetition proxy, not a learned expectation model.',
        '- **Cluster density:** sum weighted non-unison gaps of at most two semitones. **Cluster pop proxy:** tightness weighted by separation from neighboring notes; not a probability of salience. Unisons are counted separately.',
        '- **Harmonic fit:** nearest integer partials 1–64, candidate fundamentals from the bass down two octaves in semitone steps; RMS cents error plus 12 times mean log₂(partial). This deliberately penalizes fitting arbitrary high partials. It is an exploratory register-aware descriptor.',
        '- **Roughness:** Sethares-style frequency-distance kernel with product amplitude weights and equal spectral RMS. Cross-voice terms only; no same-voice inharmonic roughness, envelope overlap, masking, or binaural model. Absolute units are not perceptual ratings.',
        '- **Emergent-line candidates:** pairwise close/unison exposure, contrary-motion events, and crossings are exported for all 15 pairs. This first pass does not claim to identify perceptually heard composite melodies.',
        '', '## Files and reproducibility', '',
        '- `assignments.csv`: all 720 assignments; whole-piece symbolic and three reference-spectrum summaries.',
        '- `shortlist_events.csv`: pitches, durations, section/phrase/update labels and all event features for eight representatives.',
        '- `initial_chords.csv`: six full-theme cyclic starting chords per representative.',
        '- `transposition_events.csv`: every individual inward update and its matched comparison.',
        '- `ending_phrases.csv`: exposure-weighted features for every slowed ending phrase, including the added last note.',
        '- `trajectories.csv`, `voice_pairs.csv`, `timbre_pilot.csv`: section/round trajectories, pair interactions, and 192 palette cases.',
        '- `analysis.json`, `audition_settings.json`, and selected YAML configs: complete inputs, definitions, deterministic seed, clip windows, and shared gain.',
        '', '## Next bounded step', '',
        'Listen for whether the predicted transition changes and isolated clusters are salient. Record preferences among the controlled palettes. Then model envelope-weighted sounding overlap on these passages, refine repetition-based expectation and composite contours, and map promising spectra/envelopes to actual instruments. Keep the full score event representation continuous for future microtonal schedules.',
        '', '## Research basis', '',
        'Sethares (1993), Local Consonance and the Relationship Between Timbre and Scale: https://sethares.engr.wisc.edu/papers/consance.html',
        'Harrison & Pearce (2020), Simultaneous consonance in music perception and composition: https://cms.mus.cam.ac.uk/publications/harrison-pearce-simultaneous-consonance/', '']
    (directory/'REPORT.md').write_text('\n'.join(report))


def detail_tables(directory):
    with (directory/'shortlist_events.csv').open() as handle: rows = list(csv.DictReader(handle))
    initial = [r for r in rows if r['section']=='opening' and r['stage']=='6' and r['figure_position']=='0']
    transitions = [r for r in rows if r['introduction']=='True']
    write_csv(directory/'initial_chords.csv', initial)
    write_csv(directory/'transposition_events.csv', transitions)
    phrases = {}
    for r in rows:
        if r['section'] != 'ending': continue
        key = (r['assignment'], r['stage'], r['phrase'])
        phrases.setdefault(key, []).append(r)
    features = ['roughness', 'harmonic_fit_cost', 'cluster_density', 'cluster_pop', 'span', 'close_pairs']
    results = []
    for (assignment, figure, phrase), group in phrases.items():
        durations = np.array([float(r['duration_beats']) for r in group])
        results.append(dict(assignment=assignment, ending_figure=figure, phrase=phrase,
            start_beats=float(group[0]['onset_beats']), duration_beats=float(durations.sum()),
            **{k:float(np.average([float(r[k]) for r in group], weights=durations)) for k in features}))
    write_csv(directory/'ending_phrases.csv', results)


def plot_report(analysis, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = analysis['shortlist']
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), constrained_layout=True)
    for ax, metric, title in zip(axes,
        ['mean_roughness', 'entry_transposition_roughness_effect', 'cluster_exposure'],
        ['Whole-piece rich-spectrum roughness', 'Largest matched round-entry effect', 'Duration-weighted cluster density']):
        ax.barh([r['assignment'] for r in rows], [r[metric] for r in rows], color='#307a86')
        ax.invert_yaxis(); ax.set_title(title, fontsize=10); ax.set_xlabel('Relative descriptor units')
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Different assignments produce different profiles — no combined quality score', fontsize=13)
    fig.savefig(directory/'assignment_profiles.png', dpi=150)
    plt.close(fig)


def run(directory, plots=False):
    analysis = json.loads((directory/'analysis.json').read_text())
    config = analysis['config']
    cache, durations, labels = stream_cache(config)
    harmonic = next(r for r in analysis['shortlist'] if 'harmonic-series' in r['selection_reasons'])
    original = next(r for r in analysis['shortlist'] if 'original' in r['selection_reasons'])
    shock = max(analysis['shortlist'], key=lambda r:r['entry_transposition_roughness_effect'])
    # A fixed first-round entry, a late round entry, and the final contraction.
    seconds = np.cumsum(np.r_[0, durations[:-1]])*60/config['tempo_bpm']
    entry_events = [r['event'] for r in labels if r['introduction'] and r['update']==1]
    final_phrase = next(r['event'] for r in labels if r['section']=='ending' and r['stage']==6 and r['phrase']==7)
    with (directory/'shortlist_events.csv').open() as handle:
        candidates = [r for r in csv.DictReader(handle) if r['assignment']==shock['assignment'] and r['introduction']=='True' and r['update']=='1']
    strongest = max(candidates, key=lambda r:abs(float(r['transposition_roughness_effect'])))
    shock_event = int(strongest['event'])
    windows = [(max(0, seconds[shock_event]-3), seconds[shock_event]+7, f"largest matched entry candidate, round {strongest['round']}"),
               (seconds[entry_events[-2]]-3, seconds[entry_events[-2]]+7, 'penultimate inward round, first changed pitch'),
               (seconds[final_phrase]-1, float(np.sum(durations)*60/config['tempo_bpm']), 'final contracting phrases through the extra last note')]
    mixed = [r for r in analysis['timbre_pilot'] if r['assignment']==harmonic['assignment'] and len(set(r['palette']))>=3]
    low = min(mixed, key=lambda r:r['mean_roughness'])
    change = max(mixed, key=lambda r:r['entry_transposition_roughness_effect'])
    cases = [dict(name='01_original_rich', assignment=original['assignment'], starts=original['starts'], palette=['rich']*6),
             dict(name='02_harmonic_rich', assignment=harmonic['assignment'], starts=harmonic['starts'], palette=['rich']*6),
             dict(name='03_transposition_contrast_rich', assignment=shock['assignment'], starts=shock['starts'], palette=['rich']*6),
             dict(name='04_harmonic_mixed_low_roughness', assignment=harmonic['assignment'], starts=harmonic['starts'], palette=low['palette']),
             dict(name='05_harmonic_mixed_entry_contrast', assignment=harmonic['assignment'], starts=harmonic['starts'], palette=change['palette'])]
    audio = [render_windows(assemble(cache, case['starts']), durations, config, case['palette'], windows) for case in cases]
    peak = max(float(abs(a).max()) for a in audio)
    gain = min(1., .85/max(peak, 1e-12))
    for case, samples in zip(cases, audio):
        samples = samples*gain
        assert np.isfinite(samples).all() and abs(samples).max() <= .850001
        case['seconds'] = len(samples)/44100
        path = directory/(case['name']+'.wav')
        with wave.open(str(path), 'wb') as handle:
            handle.setnchannels(2); handle.setsampwidth(2); handle.setframerate(44100)
            handle.writeframes((samples*32767).astype('<i2').tobytes())
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(path),'-c:a','libmp3lame','-b:a','192k',str(path.with_suffix('.mp3'))], check=True)
    (directory/'audition_settings.json').write_text(json.dumps(dict(cases=cases, windows=windows,
        sample_rate=44100, shared_gain=gain, effects=[], normalization='equal reference spectral RMS; one shared gain across all clips',
        montage_gap_seconds=.75, edit_entry_envelope_seconds=.005,
        natural_release_tail_seconds=.5, family_definitions=FAMILIES), indent=2))
    detail_tables(directory)
    make_report(analysis, directory, cases, windows)
    if plots: plot_report(analysis, directory)
    print(json.dumps(dict(clips=cases, windows=windows, peak=peak, shared_gain=gain), indent=2))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--plots', action='store_true', help='Optional matplotlib descriptor chart.')
    args = parser.parse_args()
    run(args.directory, args.plots)
