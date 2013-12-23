#!/usr/bin/env python2.7

import os
import json
import random
from collections import Counter

from notation import Instrument, Movement, Piece
# import synth
from jonathanmarmor import make_music
from known_instruments import known_instruments
import config


# Some default melodies
default_melodies = {
    'original 6': [79, 85, 82, 77, 73, 75],
    'original 5': [79, 82, 77, 73, 75],
    # Harmonic series on G
    # 9 A +4
    # 7 F -31
    # 5 D -14
    # 3 B +2
    # 1 G
    'spectral': [59.02, 64.69, 61.86, 57.04, 52.69, 55.0],
    'random': [random.uniform(73.0, 85.0) for _ in range(6)]
}


def load_config():
    if config.melody in default_melodies:
        config.melody = default_melodies[config.melody]
    if not config.melody:
        config.melody = default_melodies['original 6']
    config.melody = [float(n) for n in config.melody]

    # evaluate registers

    for i in config.ensemble:
        i['range'] = set(range(int(known_instruments[i['type']]['lowest']), int(known_instruments[i['type']]['highest'] + 1)))

    # find the range shared by all instruments
    a = config.ensemble[0]['range']
    shared_range = a.intersection(*[i['range'] for i in config.ensemble[1:]])

    # find interval covered by melody
    lowest = min(config.melody)
    highest = max(config.melody)
    melody_interval = highest - lowest

    # find all possible transpositions of the melody that all instruments can play in unison
    shared_range_lowest = min(shared_range)
    shared_range_highest = max(shared_range)
    shared_range_interval = shared_range_highest - shared_range_lowest
    if shared_range_interval < melody_interval:
        raise Exception("These instruments don't have a shared register large enough to accommodate the melody.")
    wiggle_room = shared_range_interval - melody_interval

    # pick one
    melody_transposition = random.choice(range(int(wiggle_room)))

    new_melody_lowest = shared_range_lowest + melody_transposition
    diff = lowest - new_melody_lowest

    config.melody = [p + diff for p in config.melody]

    print config.melody






    # Find all possible starting transpositions for all instruments
    # To make this easy, first implement with only tritone transpositions and octaves of that






    # Set instrument ordinals (eg, violin 1, violin 2)
    counter = Counter()
    for i in config.ensemble:
        counter[i['type']] += 1
        i['ordinal'] = counter[i['type']]
    for i in config.ensemble:
        if counter[i['type']] == 1:
            del i['ordinal']

    # TODO in the future, need to be able to have more than one inst starting on the same position
    starts = random.sample(range(len(config.melody)), len(config.ensemble))

    # Flesh out instrument configs from defaults
    config.instruments = []
    for c, i in enumerate(config.ensemble):
        type_ = known_instruments[i['type']]
        ordinal = i.get('ordinal')

        inst = dict(
            full = '{} {}'.format(type_['full'], ordinal) if ordinal else type_['full'],
            short = '{}{}'.format(type_['short'], ordinal) if ordinal else type_['short'],
            midi = i.get('midi') or type_['midi'],

            # tmp
            start = starts[c],
            init_transposition = i['init_transposition'],

            clef = i.get('clef') or type_['clef'],
            notation = i.get('notation') or type_['notation']
        )
        config.instruments.append(inst)



    config.instruments_by_start = {i['start']:i for i in config.instruments}

    config.instruments_by_short_name = {i['short']:i for i in config.instruments}

    for i in config.instruments:
        i['interval'] = -(float(i['init_transposition']) / config.steps)

        print i['interval']


def run(play_synth, make_notation):
    load_config()

    music = make_music(config)

    # if play_synth:
    #     synthesize(music, config.tempo_bpm)

    if make_notation:
        notate(music)


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


def notate(music):
    piece = Piece()
    piece.title = '\\"Jonathan Marmor\\"'
    piece.filename = 'jonathanmarmor'
    piece.composer = 'Jonathan Marmor'
    piece.emsis_number = '06-004 S'

    mv = Movement()
    mv.number = 1
    mv.folder = 'mv{}'.format(mv.number)
    mv.title = config.subtitle
    mv.tempo_duration = config.tempo_duration
    mv.tempo_bpm = config.tempo_bpm
    mv.instruments = []

    insts = [i for i in config.instruments]

    for i in insts:
        inst = Instrument()
        inst.name = i['full']
        inst.musician = i['full']
        inst.short_name = i['short']
        inst.midi_name = i['midi']

        # @todo: Automatically figure out the clef and transposition
        # based on instrument and content
        inst.clef = i['clef']
        inst.transpose_from_middle_c = 'c'

        inst.notation = music[i['short']]

        mv.instruments.append(inst)

    piece.movements = [mv]

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'output')
    if not os.path.exists(path):
        os.mkdir(path)

    target = piece.write(path, yaml=False, ly=True, pdf=True, midi=True,
        parts=False, score=True)

    write_json(music, target['target'])


if __name__ == '__main__':
    # import argparse
    # parser = argparse.ArgumentParser()

    # parser.add_argument('-s', '--synth',
    #     action='store_true', dest='play_synth', default=True)
    # parser.add_argument('-n', '--notate',
    #     action='store_true', dest='make_notation', default=False)
    # args = parser.parse_args()

    # run(args.synth, args.notate)

    # run(play_synth=True, make_notation=False)
    run(play_synth=False, make_notation=True)
