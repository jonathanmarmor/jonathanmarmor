#!/usr/bin/env python2.7

import sys
import os
import random
import yaml
import json
from collections import Counter

from notation import Instrument, Movement, Piece
from jonathanmarmor import make_music
# import synth


# Some default melodies
default_melodies = {
    'original 6': [6, 12, 9, 4, 0, 2],
    'original 5': [6, 12, 9, 4, 0],
    # Harmonic series on G
    # 9 A +4
    # 7 F -31
    # 5 D -14
    # 3 B +2
    # 1 G
    'spectral': [59.02, 64.69, 61.86, 57.04, 52.69, 55.0],
    'random': [random.uniform(0.0, 12.0) for _ in range(6)]
}


def load_config(config):
    known_instruments = yaml.load(open('known_instruments.yaml', 'r'))

    melody = config['melody']
    if melody in default_melodies:
        melody = default_melodies[melody]
    if not melody:
        melody = default_melodies['original 6']
    melody = [float(n) for n in melody]

    if 0 not in melody:
        lowest = min(melody)
        melody = [n - lowest for n in melody]

    # find interval covered by melody
    melody_interval = max(melody)

    # evaluate registers
    ensemble = config['ensemble']
    for i in ensemble:
        i['range'] = set(range(int(known_instruments[i['type']]['lowest']), int(known_instruments[i['type']]['highest'] + 1)))
    a = ensemble[0]['range']
    shared_range =  a.intersection(*[i['range'] for i in ensemble[1:]])

    # If the target_transposition isn't defined in the config pick one randomly
    # in the ensemble's shared range
    target_transposition = config.get('target_transposition')
    if not target_transposition:
        # find all possible transpositions of the melody that all instruments can play in unison
        if melody_interval > len(shared_range):
            raise Exception("These instruments don't have a shared register large enough to accommodate the melody.")
        target_transposition = random.choice(list(shared_range)[:-int(melody_interval)])
    melody = [n + target_transposition for n in melody]

    # target_lowest = min(melody)
    # target_highest = max(melody)

    # # Find all possible starting transpositions for all instruments
    # # To make this easy, first implement with only tritone transpositions and octaves of that
    # transposition_options = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    # transposition_options = [t * 12 for t in transposition_options]

    # # figure out which instruments can play which transpositions
    # # then assign a transposition per instrument
    # init_transposition_opts = {}
    # for i in ensemble:
    #     for trans in transposition_options:
    #         if target_lowest + trans in i['range'] and target_highest + trans in i['range']:







    # Set instrument ordinals (eg, violin 1, violin 2)
    counter = Counter()
    for i in ensemble:
        counter[i['type']] += 1
        i['ordinal'] = counter[i['type']]
    for i in ensemble:
        if counter[i['type']] == 1:
            del i['ordinal']

    # TODO in the future, need to be able to have more than one inst starting on the same position
    starts = random.sample(range(len(melody)), len(ensemble))


    # Flesh out instrument configs from defaults
    instruments = []
    for c, i in enumerate(ensemble):
        type_ = known_instruments[i['type']]
        ordinal = i.get('ordinal')

        start = i.get('start')
        if start is None:
            start = starts[c]

        init_transposition = i.get('init_transposition')
        # if init_transposition is None:
        #     init_transposition = init_transpositions[c]

        inst = dict(
            full = '{} {}'.format(type_['full'], ordinal) if ordinal else type_['full'],
            short = '{}{}'.format(type_['short'], ordinal) if ordinal else type_['short'],
            midi = i.get('midi') or type_['midi'],

            start = start,
            init_transposition = init_transposition,

            clef = i.get('clef') or type_['clef'],
            notation = i.get('notation') or type_['notation'],
            transpose_from_middle_c = i.get('transpose_from_middle_c') or type_['transpose_from_middle_c']
        )
        instruments.append(inst)



    instruments_by_start = {i['start']:i for i in instruments}

    steps = config['steps']
    for i in instruments:
        i['interval'] = -(float(i['init_transposition']) / steps)


    return melody, instruments, instruments_by_start, steps


def write_json(music, path):
    new = {}
    for inst in music:
        new[inst] = {
            'synth': 2,
            'notes': []
        }
        for note in music[inst]:
            new[inst]['notes'].append([note.raw_pitches[0].ps, note.raw_duration])
    s = json.dumps(new)
    f = open('{}/jonathanmarmor.json'.format(path), 'w')
    f.write(s)
    f.close()


# def synthesize(music, bpm):
#     synth.play(music, bpm)


def notate(music, instruments, subtitle, tempo_duration, tempo_bpm, parts=False,
    midi=True, score=True, yaml=False, ly=True, pdf=True, json=True):
    piece = Piece()
    piece.title = '\\"Jonathan Marmor\\"'
    piece.filename = 'jonathanmarmor'
    piece.composer = 'Jonathan Marmor'
    piece.emsis_number = '06-004 S'

    mv = Movement()
    mv.number = 1
    mv.folder = 'mv{}'.format(mv.number)
    mv.title = subtitle
    mv.tempo_duration = tempo_duration
    mv.tempo_bpm = tempo_bpm
    mv.instruments = []

    for i in instruments:
        inst = Instrument()
        inst.name = i['full']
        inst.musician = i['full']
        inst.short_name = i['short']
        inst.midi_name = i['midi']
        inst.clef = i['clef']
        inst.transpose_from_middle_c = i['transpose_from_middle_c']
        inst.notation = music[i['short']]
        mv.instruments.append(inst)

    piece.movements = [mv]

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'output')
    if not os.path.exists(path):
        os.mkdir(path)

    target = piece.write(path, yaml=yaml, ly=ly, pdf=pdf, midi=midi,
        parts=parts, score=score)

    if json:
        write_json(music, target['target'])


def main(config_path='configs/default.yaml'):
    config = yaml.load(open(config_path, 'r'))
    melody, instruments, instruments_by_start, steps = load_config(config)

    music = make_music(melody, instruments, instruments_by_start, steps, config['second_movement'])

    if config.get('play_synth'):
        synthesize(music, tempo_bpm)

    if config.get('make_notation', True):
        notate(
            music,
            instruments,
            config.get('subtitle', ''),
            config['tempo_duration'],
            config['tempo_bpm'],
            parts=config.get('parts', False),
            midi=config.get('midi', True),
            score=config.get('score', True),
            yaml=config.get('yaml', False),
            ly=config.get('ly', True),
            pdf=config.get('pdf', True),
            json=config.get('json', True)
        )


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main()
