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
        # tmp
        init_transposition = 12 * 0.5,
    ),
    dict(
        type='violin',
        # tmp
        init_transposition = 12 * -1.5,
    ),
    dict(
        type='piano',
        # tmp
        init_transposition = 12 * -0.5,
    ),
    dict(
        type='piano',
        # tmp
        init_transposition = 12 * -3.5,
        clef = 'bass'
    )
]
