""""Jonathan Marmor" by Jonathan Marmor (1995-2000)

For any six instruments that can play the written pitches.

"""

import collections

from notation import Note


def copy_note(old):
    """Create a new note with the same pitches as the old note.

    >>> n = Note(pitches=[61])
    >>> new = copy_note(n)
    >>> [p.ps for p in new.raw_pitches]
    [61]

    """
    return Note(pitches=[p.ps for p in old.raw_pitches])


def copy_notes(old):
    """Create a list of new notes with the same pitches as the list of old notes.

    >>> old = [Note(pitches=[61]), Note(pitches=[63]), Note(pitches=[65])]
    >>> new = copy_notes(old)
    >>> [n.raw_pitches[0].ps for n in new]
    [61, 63, 65]

    """
    return [copy_note(n) for n in old]


def transpose(seq, diff):
    """

    >>> pitches = [61, 63, 65]
    >>> old = [Note(pitches=[p]) for p in pitches]
    >>> new = transpose(old, -3)
    >>> [n.raw_pitches[0].ps for n in new]
    [58, 60, 62]

    """
    transposed = []
    for n in seq:
        new = Note(pitches=[p.ps + diff for p in n.raw_pitches])
        transposed.append(new)
    return transposed


def turn(seq):
    """Return a list of new notes with the last pitch of `seq` first.

    >>> pitches = [61, 63, 65]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = turn(seq)
    >>> [n.raw_pitches[0].ps for n in result]
    [65, 61, 63]

    """

    new = copy_notes(seq)
    last = new.pop(-1)
    new.insert(0, last)
    return new


def turn_n(seq, n):
    """Return a list of new notes with with `seq` rotated so it starts on index `n`.

    >>> pitches = range(6)
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = turn_n(seq, 3)
    >>> [n.raw_pitches[0].ps for n in result]
    [3, 4, 5, 0, 1, 2]

    """

    new = copy_notes(seq)
    return new[n:] + new[:n]


def full_turn(seq):
    """

    >>> pitches = [61, 63, 65]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = full_turn(seq)
    >>> [[n.raw_pitches[0].ps for n in sub] for sub in result]
    [[61, 63, 65], [65, 61, 63], [63, 65, 61]]

    """
    result = []
    temp = copy_notes(seq)
    for counter in range(len(seq)):
        result.append(temp)
        temp = turn(temp)
    return result


def grow(seq):
    """

    >>> pitches = [61, 63, 65, 66]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = grow(seq)
    >>> [[n.raw_pitches[0].ps for n in sub] for sub in result]
    [[61], [61, 63], [61, 63, 65], [61, 63, 65, 66]]

    """
    result = []
    len_seq = len(seq)
    for x in range(len_seq):
        part = [copy_note(n) for n in seq[:x + 1]]
        result.append(part)
    return result


def shrink(seq):
    """

    >>> pitches = [61, 63, 65, 66]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = shrink(seq)
    >>> [[n.raw_pitches[0].ps for n in sub] for sub in result]
    [[63, 65, 66], [65, 66], [66]]

    """
    result = []
    len_seq = len(seq)
    for x in range(len_seq - 1):
        part = [copy_note(n) for n in seq[x + 1:]]
        result.append(part)
    return result


def shrink_2(seq):
    """

    >>> pitches = [1, 2, 3, 4]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = shrink_2(seq)
    >>> [[n.raw_pitches[0].ps for n in sub] for sub in result]
    [[1, 2, 3], [1, 2], [1]]

    """
    result = []
    for x in range(len(seq) - 1, 0, -1):
        result.append([copy_note(n) for n in seq[:x]])
    return result


def arch(seq, short=.5, long=1, long_2=None):
    """

    >>> pitches = [61, 63, 65, 66]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = arch(seq, .5, 1)
    >>> [[n.raw_pitches[0].ps for n in sub] for sub in result]
    [[61], [61, 63], [61, 63, 65], [61, 63, 65, 66], [63, 65, 66], [65, 66], [66]]

    >>> [[n.duration for n in sub] for sub in result]
    [['4'], ['8', '4'], ['8', '8', '4'], ['8', '8', '8', '4'], ['8', '8', '4'], ['8', '4'], ['4']]

    >>> [[n.beam for n in sub] for sub in result]
    [[None], [None, None], ['start', 'stop', None], ['start', None, 'stop', None], ['start', 'stop', None], [None, None], [None]]

    >>> [n.bar for n in flatten(result)]
    [1, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

    """
    a = grow(seq)
    b = shrink(seq)
    result = a + b

    # Set durations
    if not long_2:
        [set_durations(phrase, short, long) for phrase in result]
    else:
        [set_durations(phrase, short, long) for phrase in a]
        last(a).raw_duration = long_2
        [set_durations(phrase, long, long_2) for phrase in b]

    # Set beams
    if short < 1:
        if not long_2:
            [set_beams(phrase) for phrase in result]
        else:
            [set_beams(phrase) for phrase in a]

    # Set single barlines
    first(result).bar = 1
    return result


def set_durations(phrase, short, long):
    """Set durations on a list of notes

    >>> phrase = [Note(), Note(), Note(), Note()]
    >>> set_durations(phrase, .5, 1)
    >>> [n.duration for n in phrase]
    ['8', '8', '8', '4']

    """
    for note in phrase:
        note.raw_duration = short
    phrase[-1].raw_duration = long


def set_beams(phrase):
    """Set beams on a list of notes

    >>> phrase = [Note(), Note(), Note(), Note()]
    >>> set_beams(phrase)
    >>> [n.beam for n in phrase]
    ['start', None, 'stop', None]

    >>> phrase = [Note(), Note()]
    >>> set_beams(phrase)
    >>> [n.beam for n in phrase]
    [None, None]

    """
    if len(phrase) > 2:
        phrase[0].beam = 'start'
        phrase[-2].beam = 'stop'


def first(l):
    """Get the first item from nested lists

    >>> first([[[1, 2], [3, 4], 5], [6, [7, 8], 9], 10, [11, 12]])
    1

    """
    if isinstance(l[0], collections.Iterable) \
        and not isinstance(l[0], basestring):
        return first(l[0])
    else:
        return l[0]


def last(l):
    """Get the last item from nested lists

    >>> last([[[1, 2], [3, 4], 5], [6, [7, 8], 9], 10, [11, 12]])
    12

    """
    if isinstance(l[-1], collections.Iterable) \
        and not isinstance(l[-1], basestring):
        return last(l[-1])
    else:
        return l[-1]


def flatten(l):
    """Flatten arbitrarily nested lists

    >>> nested = [[[1, 2, 3], [4, 5], 6], 7, [8, [9, 10], [11, 12]], [[13], [14]]]
    >>> list(flatten(nested))
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

    """
    for el in l:
        if isinstance(el, collections.Iterable) \
            and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def section_A_part(seq):
    """
    for sequence: [A, B, C, D]

    A

    A AB B
    B BA A

    A AB ABC BC C
    C CA CAB AB B
    B BC BCA CA A

    A AB ABC ABCD BCD CD D
    D DA DAB DABC ABC BC C
    C CD CDA CDAB DAB AB B
    B BC BCD BCDA CDA DA A

    >>> pitches = [61, 63, 65]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = section_A_part(seq)
    >>> [n.raw_pitches[0].ps for n in flatten(result)]
    [61, 61, 61, 63, 63, 63, 63, 61, 61, 61, 61, 63, 61, 63, 65, 63, 65, 65, 65, 65, 61, 65, 61, 63, 61, 63, 63, 63, 63, 65, 63, 65, 61, 65, 61, 61]

    >>> [n.bar_type for n in flatten(result)]
    ['||', '||', '|', '|', '|', '|', '|', '|', '|', '||', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|']

    """
    section = []
    for g in grow(seq):
        subsection = []
        for t in full_turn(g):
            subsection.append(arch(t))
        first(subsection).bar_type = '||'
        section.append(subsection)
    return section


def one_transition(seq, interval):
    """
    >>> pitches = [1, 2, 3]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = one_transition(seq, 5)
    >>> [[n.raw_pitches[0].ps for n in notes] for notes in result]
    [[1, 2, 8], [8, 1, 7], [7, 8, 6]]

    """
    out = []
    len_seq = len(seq)
    for x in range(len_seq):
        old_last_ps = seq[-1].raw_pitches[0].ps
        new_last_ps = old_last_ps + interval
        new_seq = [copy_note(n) for n in seq[:-1]]
        new_seq.append(Note(pitches=[new_last_ps]))
        out.append(new_seq)
        seq = turn(new_seq)
    return out


def transitions(seq, interval, steps):
    """
    >>> pitches = [1, 2, 3]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = transitions(seq, 5, 5)
    >>> [[n.raw_pitches[0].ps for n in notes] for notes in result]
    [[1, 2, 8], [8, 1, 7], [7, 8, 6], [6, 7, 8], [8, 6, 12], [12, 8, 11], [11, 12, 13], [13, 11, 12], [12, 13, 16], [16, 12, 18], [18, 16, 17], [17, 18, 16], [16, 17, 23], [23, 16, 22], [22, 23, 21], [21, 22, 23], [23, 21, 27], [27, 23, 26], [26, 27, 28], [28, 26, 27]]

    """
    out = []
    for x in range(steps):
        out.extend(one_transition(seq, interval))
        # Turn an extra time
        out.append(turn(out[-1]))
        seq = turn(out[-1])
    return out


def section_B_part(seq, interval, steps):
    seqs = transitions(seq, interval, steps)
    out = []
    for i, seq in enumerate(seqs):
        new = arch(seq)
        if i % (len(seq) + 1) == 0:
            first(new).bar_type = '||'
        out.append(new)
    return out


def section_C_part(seq):
    """Shrink

    >>> pitches = [1, 2, 3, 4]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = section_C_part(seq)
    >>> [n.raw_pitches[0].ps for n in flatten(result)]
    [1, 1, 2, 1, 2, 3, 2, 3, 3, 3, 3, 1, 3, 1, 2, 1, 2, 2, 2, 2, 3, 2, 3, 1, 3, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1]

    # 123456 612345 561234 456123 345612 234561
    # 12345 51234 45123 34512 23451
    # 1234 2341 3412 2341
    # 123 312 213
    # 12 21
    # 1

    """
    section = []
    for g in shrink_2(seq):
        subsection = []
        for t in full_turn(g):
            subsection.append(arch(t))
        first(subsection).bar_type = '||'
        section.append(subsection)
    return section


def section_D_part(seq):
    """
    >>> pitches = [61, 63, 65]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = section_D_part(seq)
    >>> [n.raw_pitches[0].ps for n in flatten(result)]
    [61, 61, 61, 63, 63, 63, 63, 61, 61]

    """

    section = []
    for g in grow(seq)[:-1]:
        subsection = []
        for t in full_turn(g):
            subsection.append(arch(t))
        first(subsection).bar_type = '||'
        section.append(subsection)
    return section


def section_E_part(seq, interval):
    """
    >>> pitches = [1, 2, 3, 4, 5, 6]
    >>> seq = [Note(pitches=[p]) for p in pitches]
    >>> result = section_E_part(seq, 30)
    >>> [[n.raw_pitches[0].ps for n in notes] for notes in result]
    [[1, 2, 3, 4, 5, 36], [36, 1, 2, 3, 4, 35], [35, 36, 1, 2, 3, 34], [34, 35, 36, 1, 2, 33], [33, 34, 35, 36, 1, 32], [32, 33, 34, 35, 36, 31]]


    """
    out = []
    seqs = one_transition(seq, interval)

    durs = [d / 2.0 for d in range(1, 9)]

    for i, seq in enumerate(seqs):
        new = arch(seq, durs[i], durs[i + 1], durs[i + 2])
        out.append(new)
    return out


def make_music(melody, instruments, instruments_by_start, steps, second_movement=True):
    config_melody = melody[:]

    parts = {}
    for i in instruments:
        parts[i['short']] = []

    melody = [Note(pitches=[p]) for p in config_melody]
    # turns = full_turn(melody)

    for instrument in instruments:
        t = turn_n(melody, instrument['start'])
        seq = transpose(t, instrument['init_transposition'])

        # Grow
        parts[instrument['short']].extend(list(flatten(section_A_part(seq))))

        # Modulate in
        parts[instrument['short']].extend(
            list(flatten(section_B_part(seq, instrument['interval'], steps)))
        )

        # Shrink
        end = sum(range(len(seq)))
        start = end + len(seq)

        prev_seq = parts[instrument['short']][-start:-end]
        prev_seq = turn(prev_seq)
        parts[instrument['short']].extend(list(flatten(section_C_part(prev_seq))))

        if second_movement:
            # Pulse
            last_note = parts[instrument['short']][-1]
            pulse = [Note(pitches=[last_note.raw_pitches[0].ps])] * 32
            for n in pulse:
                n.raw_duration = 1
            parts[instrument['short']].extend(pulse)

            # Grow
            last_pitch = parts[instrument['short']][-1].raw_pitches[0].ps
            index = config_melody.index(round(last_pitch, 2))
            new_melody = config_melody[index:] + config_melody[:index]
            new_seq = [Note(pitches=[p]) for p in new_melody]
            parts[instrument['short']].extend(list(flatten(section_D_part(new_seq))))

            # Slow, Modulate out
            parts[instrument['short']].extend(list(flatten(section_E_part(new_seq, instrument['init_transposition']))))

    return parts


if __name__ == '__main__':
    import doctest
    doctest.testmod()
