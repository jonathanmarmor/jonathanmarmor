'''Configuration for a realization of "Jonathan Marmor."'''

# The main melody.
# In the "central" transposition.

# Equal tempered, 12 notes to the octave
# melody = [ps + -6 for ps in [59, 65, 62, 57, 53, 55]]  # b f^ d a f g


# melody = [79, 85, 82, 77, 73, 75]

melody = [79, 82, 77, 73, 75]

# Harmonic series on G
# 9 A +4
# 7 F -31
# 5 D -14
# 3 B +2
# 1 G
# melody = [59.02, 64.69, 61.86, 57.04, 52.69, 55.0]

# Random melody in one octave
# melody = [55.34, 52.11, 60.68, 59.4, 57.52, 64.77]

# Number of times seq needs to be transposed from
# original transposition to reach central transposition
steps = 6

tempo_duration = 4
tempo_bpm = 200

subtitle = ''

# in score order top to bottom
instruments = [
    dict(
        full='Piano',
        short='pno',
        midi='acoustic grand',
        start=5,
        init_transposition=12 * 2.5,
        clef='treble'
    ),
    dict(
        full='Guitar 2',
        short='gtr2',
        midi='electric bass (pick)',
        start=3,
        init_transposition=12 * 1.5,
        clef='treble'
    ),
    dict(
        full='Violin 1',
        short='vln1',
        midi='violin',
        start=1,
        init_transposition=12 * 0.5,
        clef='treble'
    ),
    dict(
        full='Guitar 3',
        short='gtr3',
        midi='electric piano 1',
        start=2,
        init_transposition=12 * -0.5,
        clef='treble'
    ),
    dict(
        full='Violin 2',
        short='vln2',
        midi='violin',
        start=0,
        init_transposition=12 * -1.5,
        clef='treble'
    ),
    dict(
        full='6-string bass 2',
        short='bs2',
        midi='electric guitar (clean)',
        start=4,
        init_transposition=12 * -2.5,
        clef='bass'
    )
]

instruments_by_start = {i['start']:i for i in instruments}

instruments_by_short_name = {i['short']:i for i in instruments}

for i in instruments:
    i['interval'] = -(float(i['init_transposition']) / steps)

"""Some notes.

harmonics
f 7
a 9
f 7
b 5
d 3
g 1


f * 56

d   48
b   40
a   26
g   32
f   28

d   24
b   20
a * 18
g   16
f   14

d   12
b   10
a   9
g   8
f * 7

d   6
b * 5
a
g   4
f

d * 3
b
a
g   2
f

d
b
a
g * 1
f




f *.....
d .*....
b .....*
a ..*...
g ....*.
f ...*..

f ....*.
d .....*
b ...*..
a *.....
g ..*...
f .*....

f ...*..
d ....*.
b ..*...
a .....*
g .*....
f *.....

f .*....
d ..*...
b *.....
a ...*..
g .....*
f ....*.

f .....*
d *.....
b ....*.
a .*....
g ...*..
f ..*...

f ..*...
d ...*..
b .*....
a ....*.
g *.....
f .....*

"""
