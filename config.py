'''Configuration for a realization of "Jonathan Marmor."'''

subtitle = ''
melody = 'original 6'
steps = 6
tempo_duration = 4
tempo_bpm = 380
second_movement = False

ensemble = [
    dict(
        type='violin',
        # init_transposition = 12 * 0.5,
    ),
    dict(
        type='violin',
        # init_transposition = 12 * -0.5,
    ),
    # dict(
    #     type='piano',
    #     # init_transposition = 12 * 1.5,
    # ),
    # dict(
    #     type='piano',
    #     # init_transposition = 12 * -1.5,
    #     clef = 'bass'
    # ),
    dict(type='viola'),
    dict(type='viola'),
    dict(type='cello'),
    dict(type='cello'),
]
