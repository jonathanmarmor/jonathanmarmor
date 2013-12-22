#!/usr/bin/env python2.7

import os
import json

from notation import Instrument, Movement, Piece
# import synth
from jonathanmarmor import make_music
import config


def run(play_synth, make_notation):
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

    insts = [i for i in config.instruments if i['short'] in ['vln1', 'vln2']]

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
