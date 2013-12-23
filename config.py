'''Configuration for a realization of "Jonathan Marmor."'''

melody = None

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
