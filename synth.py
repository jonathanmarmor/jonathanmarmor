#!/usr/bin/env python2.7

import time
import random

import pyo


def setup():
    """Boot and start the pyo synthesis server"""
    server = pyo.Server().boot()
    server.start()
    return server


def play(piece, bpm):
    """Play music with the pyo synth.

    `piece` dictionary
    keys are instrument names
    values are lists of `pitch.Pitch` objects with raw_pitches
    and raw_duration properties.

    WARNING: It's assumed in this version that all instruments are in exact
    rhythmic unison

    """

    server = setup()

    quarter = 60.0 / bpm  # set quarter note duration in seconds

    reference_instrument = piece[piece.keys()[0]]
    num_notes = len(reference_instrument)

    init_vol = 0.00001
    attack = 0.0000001
    attack_vol = 0.21
    decay = 0.035
    sustain_vol = 0.17
    # sustain is duration - attack - decay - release
    release = 0.00001

    timbres = [
        pyo.SawTable(order=12).normalize(),
        pyo.SawTable(order=12).normalize(),
        pyo.SawTable(order=12).normalize(),
        pyo.SawTable(order=12).normalize(),
        pyo.SawTable(order=12).normalize(),
        pyo.SawTable(order=12).normalize()

        # pyo.SawTable(order=1).normalize(),
        # pyo.SawTable(order=20).normalize(),
        # pyo.SquareTable().normalize(),
        # pyo.SawTable(order=5).normalize(),
        # pyo.SawTable(order=16).normalize()
    ]

    synths = {}
    for instrument in piece:
        timbre = random.choice(timbres)
        synths[instrument] = pyo.Osc(table=timbre, freq=[60], mul=init_vol).out()

    for i in range(num_notes):
        duration = quarter * reference_instrument[i].raw_duration
        for instrument in piece:
            fs = [p.fq for p in piece[instrument][i].raw_pitches]
            synths[instrument].freq = fs
            synths[instrument].mul = init_vol
        time.sleep(attack)

        for instrument in piece:
            synths[instrument].mul = attack_vol
        time.sleep(decay)

        for instrument in piece:
            synths[instrument].mul = sustain_vol
        time.sleep(duration - attack - decay - release)

        for instrument in piece:
            synths[instrument].mul = init_vol
        time.sleep(release)

    teardown(server)


def teardown(server):
    server.stop()
    time.sleep(0.25)
    server.shutdown()
