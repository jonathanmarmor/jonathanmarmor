"""Bounded pitch/timbre exploration; scores are descriptors, not aesthetic verdicts.

Numerical work stays outside language-model context. No composition is modified.
"""
import argparse
import copy
import csv
import itertools
import json
from pathlib import Path

import numpy as np
import yaml

from notation import Note
from jonathanmarmor import (flatten, section_A_part, section_B_part,
                           section_C_part, section_D_part, section_E_part)
from render import generate

FAMILIES = {
    'pure': dict(partials=[1], amplitudes=[1], attack=.012, decay=None, release=.04),
    'warm': dict(partials=list(range(1, 7)), amplitudes=[1/h**2 for h in range(1, 7)],
                 attack=.025, decay=None, release=.12),
    'rich': dict(partials=list(range(1, 9)), amplitudes=[1/h for h in range(1, 9)],
                 attack=.012, decay=None, release=.08),
    'odd': dict(partials=[1, 3, 5, 7], amplitudes=[1, 1/3, 1/5, 1/7],
                attack=.02, decay=None, release=.1),
    'bell': dict(partials=[1, 2.71, 4.09, 5.43], amplitudes=[1, .5, .3, .2],
                 attack=.003, decay=.65, release=.4),
    'pluck': dict(partials=list(range(1, 9)), amplitudes=[1/h for h in range(1, 9)],
                  attack=.003, decay=.12, release=.04),
}
PAIRS = list(itertools.combinations(range(6), 2))
HARMONIC_STARTS = (5, 2, 0, 1, 3, 4)
BANDLIMIT_HZ = .45*44100


def annotations(config):
    """Reproduce rhythmic nesting to label every event; verify against generator."""
    seq = [Note(pitches=[p]) for p in [0, 2, 4, 6, 9, 12]]
    records = []
    figure = 0
    beat = 0.

    def add(section, phrases, stage=0, cycle=0, round_=0, update=0):
        nonlocal figure, beat
        figure += 1
        position = 0
        for phrase_no, phrase in enumerate(phrases, 1):
            for in_phrase, note in enumerate(phrase):
                records.append(dict(event=len(records), onset_beats=beat,
                    duration_beats=note.raw_duration, gate_beats=.94*note.raw_duration,
                    section=section, stage=stage, cycle=cycle, figure=figure,
                    phrase=phrase_no, phrase_position=in_phrase, figure_position=position,
                    round=round_, update=update,
                    introduction=(section == 'inward' and update > 0 and position == 20)))
                beat += note.raw_duration
                position += 1

    for section, groups in [('opening', section_A_part(seq))]:
        for stage, group in enumerate(groups, 1):
            for cycle, phrases in enumerate(group, 1): add(section, phrases, stage, cycle)
    for i, phrases in enumerate(section_B_part(seq, 0, config['steps'])):
        add('inward', phrases, round_=i//7+1, update=(i % 7 + 1 if i % 7 < 6 else 0))
    for stage, group in enumerate(section_C_part(seq), 1):
        for cycle, phrases in enumerate(group, 1): add('converged_contract', phrases, stage, cycle)
    if config.get('second_movement', True):
        pulses = [Note(pitches=[0]) for _ in range(32)]
        for note in pulses: note.raw_duration = 1
        add('pulses', [pulses])
        for stage, group in enumerate(section_D_part(seq), 1):
            for cycle, phrases in enumerate(group, 1): add('converged_expand', phrases, stage, cycle)
        for i, phrases in enumerate(section_E_part(seq, 0, config.get('progressive_final_contraction', False))):
            add('ending', phrases, stage=i+1, update=i+1)
    return records


def stream_cache(config):
    """Six cyclic assignments yield all 36 independent voice/start streams."""
    if len(config['ensemble']) != 6:
        raise ValueError('This pilot requires six voices and a six-note melody.')
    cache = {}
    durations = None
    for shift in range(6):
        variant = copy.deepcopy(config)
        for voice, part in enumerate(variant['ensemble']): part['start'] = (voice+shift) % 6
        music = generate(variant)
        for voice, part in enumerate(music['parts']):
            notes = np.asarray(part['notes'])
            if durations is None: durations = notes[:, 1]
            if not np.array_equal(notes[:, 1], durations):
                raise ValueError('Analysis requires rhythmically aligned monophonic voices.')
            cache[voice, (voice+shift) % 6] = notes[:, 0]
    labels = annotations(config)
    if len(labels) != len(durations) or not np.allclose([r['duration_beats'] for r in labels], durations):
        raise ValueError('Section annotations do not match the composition rhythm.')
    return cache, durations, labels


def assemble(cache, starts):
    if sorted(starts) != list(range(6)): raise ValueError('Starts must be a permutation of 0..5.')
    return np.column_stack([cache[v, s] for v, s in enumerate(starts)])


def roughness_table(a, b, pitches):
    """Sethares-style pairwise spectral interference, equal spectral RMS.

    Product amplitude weighting; self-voice terms excluded. This is a relative
    cross-voice proxy, not a complete consonance or binaural perception model.
    """
    x, y = FAMILIES[a], FAMILIES[b]
    f = 440 * 2**((np.asarray(pitches)-69)/12)
    fx = f[:, None] * np.array(x['partials'])
    fy = f[:, None] * np.array(y['partials'])
    ax = np.array(x['amplitudes']); ax = ax / np.linalg.norm(ax)
    ay = np.array(y['amplitudes']); ay = ay / np.linalg.norm(ay)
    f1 = fx[:, None, :, None]; f2 = fy[None, :, None, :]
    d = .24 * abs(f1-f2) / (.021*np.minimum(f1, f2)+19)
    kernel = np.exp(-3.5*d)-np.exp(-5.75*d)
    weights = ax[None, None, :, None] * ay[None, None, None, :]
    return np.sum(kernel * weights * (f1 < BANDLIMIT_HZ) * (f2 < BANDLIMIT_HZ), axis=(2, 3))


def harmonic_fit(pitches):
    """Register-aware partial fit with a stated high-partial complexity penalty.

    Fundamental candidates: bass down through two octaves in semitone steps.
    This heuristic uses continuous pitch inputs; it is not validated perception.
    """
    unique, inverse = np.unique(np.sort(pitches, axis=1), axis=0, return_inverse=True)
    roots = unique[:, :1] - np.arange(25)[None, :]
    ratios = 2**((unique[:, None, :]-roots[:, :, None])/12)
    h = np.maximum(1, np.rint(ratios))
    error = 1200*np.log2(ratios/h)
    rms = np.sqrt(np.mean(error**2, axis=2))
    complexity = np.mean(np.log2(h), axis=2)
    cost = rms + 12*complexity
    cost[np.max(h, axis=2) > 64] = np.inf
    best = np.argmin(cost, axis=1)
    return cost[np.arange(len(unique)), best][inverse]


def cluster_features(pitches):
    """Tight non-unison edges, with local isolation from neighboring notes."""
    ordered = np.sort(pitches, axis=1)
    gaps = np.diff(ordered, axis=1)
    tight = (gaps > 1e-8) & (gaps <= 2)
    isolation = np.full_like(gaps, 12.)
    isolation[:, 1:] = np.minimum(isolation[:, 1:], gaps[:, :-1])
    isolation[:, :-1] = np.minimum(isolation[:, :-1], gaps[:, 1:])
    # Not a perceptual salience probability: retain density and isolation separately.
    density = np.sum(tight*(3-gaps)/3, axis=1)
    pop = np.max(tight*(3-gaps)/3 * (1+np.minimum(isolation, 12)/12), axis=1)
    return density, pop, np.sum(gaps < 1e-8, axis=1)


def pc_fingerprint(pitches):
    """Soft circular 12-bin fingerprint; absolute fractional pitches also retained."""
    pc = pitches % 12
    low = np.floor(pc).astype(int)
    frac = pc-low
    out = np.zeros((len(pitches), 12))
    rows = np.arange(len(pitches))
    for voice in range(6):
        np.add.at(out, (rows, low[:, voice]), 1-frac[:, voice])
        np.add.at(out, (rows, (low[:, voice]+1) % 12), frac[:, voice])
    return out


def event_features(pitches, durations, labels, palette, tables, lookup, inward_deltas=None):
    indexes = np.searchsorted(lookup, np.round(pitches, 10))
    rough = np.zeros(len(pitches))
    pair_rough = []
    for a, b in PAIRS:
        key = (palette[a], palette[b])
        if key not in tables: tables[key] = roughness_table(*key, lookup)
        values = tables[key][indexes[:, a], indexes[:, b]]
        rough += values
        pair_rough.append(values)
    density, pop, unisons = cluster_features(pitches)
    harmonic = harmonic_fit(pitches)
    prev = np.vstack([pitches[:1], pitches[:-1]])
    voice_motion = np.mean(abs(pitches-prev), axis=1)
    fingerprint = pc_fingerprint(pitches)
    pc_change = np.sum(abs(fingerprint-np.vstack([fingerprint[:1], fingerprint[:-1]])), axis=1)/12
    cycle_departure = np.zeros(len(pitches))
    figure_starts = {}
    for i, r in enumerate(labels):
        figure_starts.setdefault(r['figure'], i)
        if r['section'] == 'inward' and r['figure']-1 in figure_starts:
            j = figure_starts[r['figure']-1]+r['figure_position']
            if j < figure_starts[r['figure']]:
                cycle_departure[i] = np.mean(abs(pitches[i]-pitches[j]))
    crossing = np.zeros(len(pitches))
    close = np.zeros(len(pitches))
    cluster_rough = np.zeros(len(pitches))
    for (a, b), values in zip(PAIRS, pair_rough):
        distance = abs(pitches[:, a]-pitches[:, b])
        close += (distance > 1e-8) & (distance <= 2)
        cluster_rough += values * ((distance > 1e-8) & (distance <= 2))
        crossing += ((pitches[:, a]-pitches[:, b])*(prev[:, a]-prev[:, b]) < -1e-8)
    transposition_effect = np.zeros(len(pitches))
    transposition_harmonic_effect = np.zeros(len(pitches))
    if inward_deltas is not None:
        intro = np.array([r['introduction'] for r in labels])
        rounds = np.array([r['round']-1 for r in labels])[intro]
        counterfactual = pitches[intro] - inward_deltas[rounds]
        cf_indexes = np.searchsorted(lookup, np.round(counterfactual, 10))
        cf_rough = np.zeros(len(counterfactual))
        for a, b in PAIRS:
            cf_rough += tables[palette[a], palette[b]][cf_indexes[:, a], cf_indexes[:, b]]
        transposition_effect[intro] = rough[intro] - cf_rough
        transposition_harmonic_effect[intro] = harmonic[intro] - harmonic_fit(counterfactual)
    return dict(roughness=rough, harmonic_fit_cost=harmonic, cluster_density=density,
        cluster_pop=pop, unisons=unisons, span=np.ptp(pitches, axis=1),
        voice_motion=voice_motion, pitch_class_change=pc_change,
        cycle_departure=cycle_departure, crossing=crossing, close_pairs=close,
        cluster_roughness=cluster_rough,
        roughness_jump=abs(np.diff(rough, prepend=rough[0])),
        transposition_roughness_effect=transposition_effect,
        transposition_harmonic_fit_effect=transposition_harmonic_effect)


def summarize(features, durations, labels):
    intro = np.array([r['introduction'] for r in labels])
    entry = intro & np.array([r['update'] == 1 for r in labels])
    avg = lambda key: float(np.average(features[key], weights=durations))
    maximum = lambda key, mask: float(np.max(features[key][mask], initial=0))
    return dict(mean_roughness=avg('roughness'), harmonic_fit_cost=avg('harmonic_fit_cost'),
        cluster_exposure=avg('cluster_density'), cluster_pop_peak=float(features['cluster_pop'].max()),
        mean_span=avg('span'), close_pair_exposure=avg('close_pairs'),
        crossings=int(np.sum(features['crossing'])),
        entry_roughness_jump=maximum('roughness_jump', entry),
        update_roughness_jump=maximum('roughness_jump', intro),
        entry_voice_motion=maximum('voice_motion', entry),
        entry_pitch_class_change=maximum('pitch_class_change', entry),
        entry_transposition_roughness_effect=float(np.max(abs(features['transposition_roughness_effect'][entry]), initial=0)),
        cycle_departure=maximum('cycle_departure', intro))


def write_csv(path, rows):
    if not rows: return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader(); writer.writerows(rows)


def palette_candidates(seed=1995):
    names = list(FAMILIES)
    palettes = [tuple([name]*6) for name in names]
    palettes += [tuple(names), tuple(reversed(names))]
    rng = np.random.default_rng(seed)
    while len(palettes) < 24:
        value = tuple(rng.choice(names, size=6))
        if value not in palettes: palettes.append(value)
    return palettes


def run(config, output):
    output.mkdir(parents=True, exist_ok=True)
    cache, durations, labels = stream_cache(config)
    lookup = np.unique(np.round(np.concatenate(list(cache.values())), 10))
    progress = np.asarray(config.get('inward_progress', np.linspace(0, 1, config['steps']+1)))
    deltas = -np.diff(progress)[:, None] * np.array([p['init_transposition'] for p in config['ensemble']])[None, :]
    tables = {}
    records = []
    for n, starts in enumerate(itertools.permutations(range(6))):
        pitches = assemble(cache, starts)
        record = dict(assignment=''.join(str(s+1) for s in starts), starts=list(starts))
        rich = event_features(pitches, durations, labels, ['rich']*6, tables, lookup, deltas)
        record.update(summarize(rich, durations, labels))
        for family in ['pure', 'warm']:
            rough = np.zeros(len(pitches)); key = (family, family)
            if key not in tables: tables[key] = roughness_table(*key, lookup)
            index = np.searchsorted(lookup, np.round(pitches, 10))
            for a, b in PAIRS: rough += tables[key][index[:, a], index[:, b]]
            record['mean_roughness_'+family] = float(np.average(rough, weights=durations))
        records.append(record)
        if n % 120 == 0: print(f'Screened {n+1}/720 assignments', flush=True)
    selected = []
    reasons = {}
    def choose(record, reason):
        key = record['assignment']
        reasons.setdefault(key, []).append(reason)
        if record not in selected: selected.append(record)
    for starts, reason in [(tuple(p['start'] for p in config['ensemble']), 'original'), (HARMONIC_STARTS, 'harmonic-series')]:
        choose(next(r for r in records if r['starts'] == list(starts)), reason)
    for metric, direction, reason in [('cluster_pop_peak', 1, 'isolated cluster peak'),
        ('entry_transposition_roughness_effect', 1, 'largest matched round-entry transposition effect'),
        ('cycle_departure', 1, 'largest cycle departure'),
        ('mean_roughness', -1, 'lowest rich-spectrum roughness'),
        ('mean_roughness', 1, 'highest rich-spectrum roughness')]:
        ordered = sorted(records, key=lambda r: direction*r[metric], reverse=True)
        # Ties are explicitly deterministic, not evidence of a unique optimum.
        choose(ordered[0], reason)
    metrics = ['mean_roughness', 'cluster_exposure', 'mean_span', 'harmonic_fit_cost',
               'entry_transposition_roughness_effect', 'cycle_departure', 'crossings']
    vectors = np.array([[r[k] for k in metrics] for r in records])
    vectors = (vectors-vectors.mean(axis=0))/np.maximum(vectors.std(axis=0), 1e-9)
    while len(selected) < 8:
        indexes = [records.index(r) for r in selected]
        distance = np.min(np.sum((vectors[:, None, :]-vectors[indexes][None, :, :])**2, axis=2), axis=1)
        choose(records[int(np.argmax(distance))], 'diverse descriptor profile')
    # All cheap passes are completed before the bounded timbre search.
    pilot = []; events = []; trajectories = []; pair_records = []
    palettes = palette_candidates()
    for record in selected:
        starts = record['starts']; pitches = assemble(cache, starts)
        ref = event_features(pitches, durations, labels, ['rich']*6, tables, lookup, deltas)
        for i, label in enumerate(labels):
            row = dict(assignment=record['assignment'], **label)
            row.update({f'pitch_{v+1}': float(p) for v, p in enumerate(pitches[i])})
            row.update({k: float(a[i]) for k, a in ref.items()})
            events.append(row)
        for section in dict.fromkeys(r['section'] for r in labels):
            rounds = sorted(set(r['round'] for r in labels if r['section'] == section))
            for round_ in rounds:
                mask = np.array([r['section'] == section and r['round'] == round_ for r in labels])
                trajectories.append(dict(assignment=record['assignment'], section=section, round=round_,
                    **{k: float(np.average(a[mask], weights=durations[mask])) for k, a in ref.items()}))
        for a, b in PAIRS:
            dist = abs(pitches[:, a]-pitches[:, b]); delta = np.diff(pitches, axis=0)
            pair_records.append(dict(assignment=record['assignment'], voice_a=a+1, voice_b=b+1,
                close_exposure=float(np.average((dist > 1e-8) & (dist <= 2), weights=durations)),
                unison_exposure=float(np.average(dist < 1e-8, weights=durations)),
                contrary_events=int(np.sum(delta[:, a]*delta[:, b] < 0)),
                crossings=int(np.sum((pitches[1:, a]-pitches[1:, b])*(pitches[:-1, a]-pitches[:-1, b]) < 0))))
        for palette_id, palette in enumerate(palettes):
            features = event_features(pitches, durations, labels, palette, tables, lookup, deltas)
            pilot.append(dict(assignment=record['assignment'], palette_id=palette_id,
                palette=list(palette), **summarize(features, durations, labels),
                cluster_roughness_share=float(np.sum(features['cluster_roughness']*durations)/max(1e-12, np.sum(features['roughness']*durations)))))
    write_csv(output/'assignments.csv', records)
    write_csv(output/'shortlist_events.csv', events)
    write_csv(output/'trajectories.csv', trajectories)
    write_csv(output/'voice_pairs.csv', pair_records)
    write_csv(output/'timbre_pilot.csv', pilot)
    for record in selected: record['selection_reasons'] = reasons[record['assignment']]
    report = dict(config=config, family_definitions=FAMILIES, seed=1995,
        assignment_count=len(records), event_count=len(labels), total_snapshots=len(records)*len(labels),
        shortlist=selected, palettes=[list(p) for p in palettes], timbre_pilot=pilot,
        limitations=['Shock, cluster pop, and harmonic fit are explicit heuristics, not validated perceptual ratings.',
            'Spectral scores are static, equal-RMS, cross-voice measures; envelope/release effects are auditioned but not included in these scores.',
            'No prediction of stereo listening or artistic quality. Pans are preserved in audio.',
            'No tonal-familiarity model or perceptually validated composite-melody detector in this first pass.',
            'Timbre search samples 24 palettes; it does not optimize or enumerate the whole timbre space.'])
    (output/'analysis.json').write_text(json.dumps(report, indent=2))
    # Preserve inputs for every selected assignment as ordinary renderer configurations.
    for record in selected:
        cfg = copy.deepcopy(config)
        for part, start in zip(cfg['ensemble'], record['starts']): part['start'] = start
        (output/f"assignment_{record['assignment']}.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(json.dumps(dict(assignments=len(records), shortlist=[r['assignment'] for r in selected],
                         timbre_cases=len(pilot), output=str(output.resolve())), indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).parent/'configs/six_parts.yaml')
    parser.add_argument('--output', type=Path, default=Path('output/harmony'))
    args = parser.parse_args()
    run(yaml.safe_load(args.config.read_text()), args.output)
