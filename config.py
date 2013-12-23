'''Configuration for a realization of "Jonathan Marmor."'''

subtitle = ''
melody = 'original 5'
steps = 5
tempo_duration = 4
tempo_bpm = 380
second_movement = False

ensemble = [
    dict(
        type='violin',
        ordinal=1,

        # tmp
        start = 1,  # Or should this be randomly assigned?  Or should some optimal solution be calculated?
        init_transposition = 12 * 0.5,  # this should be calculated

    ),
    dict(
        type='violin',
        ordinal=2,

        # tmp
        start = 2,
        init_transposition = 12 * -1.5,

    )
]

# instruments = [
#     dict(
#         full = 'Violin 1',
#         short = 'vln1',
#         midi = 'violin',
#         start = 1,  # Or should this be randomly assigned?  Or should some optimal solution be calculated?
#         init_transposition = 12 * 0.5,  # this should be calculated
#         clef = 'treble',
#         notation = 'standard'
#     ),
#     dict(
#         full = 'Violin 2',
#         short = 'vln2',
#         midi = 'violin',
#         start = 2,  # Or should this be randomly assigned?  Or should some optimal solution be calculated?
#         init_transposition = 12 * -1.5,  # this should be calculated
#         clef = 'treble',
#         notation = 'standard'
#     )
# ]
