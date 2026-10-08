"""Regression checks for the approved ending and pulse-based excerpt."""
import unittest
from pathlib import Path
import yaml
from jonathanmarmor import section_E_part, flatten
from notation import Note
from render import generate

class EndingTests(unittest.TestCase):
    def setUp(self):
        self.seq = [Note(pitches=[p]) for p in range(1, 7)]

    def test_final_bar_matches_approved_duration_table(self):
        last_bar = section_E_part(self.seq, 30, True)[-1]
        expected = [[7], [6,7], [6,6,7], [6,6,6,7], [6,6,6,6,7],
                    [6,6,6,6,6,8], [7,7,7,7,9], [8,8,8,10],
                    [9,9,11], [10,12], [13], [14]]
        self.assertEqual([[n.raw_duration*2 for n in phrase] for phrase in last_bar], expected)
        notes = list(flatten(last_bar))
        self.assertEqual(notes[-1].raw_pitches[0].ps, notes[-2].raw_pitches[0].ps)

    def test_earlier_bars_and_expansion_are_unchanged(self):
        old = section_E_part(self.seq, 30)
        new = section_E_part(self.seq, 30, True)
        def signature(section):
            return [(n.raw_pitches[0].ps, n.raw_duration) for n in flatten(section)]
        self.assertEqual(signature(old[:-1]), signature(new[:-1]))
        self.assertEqual(signature(old[-1][:6]), signature(new[-1][:6]))

    def test_excerpt_starts_at_pulses_and_contains_full_ending(self):
        config = yaml.safe_load((Path(__file__).parent/'configs/six_parts.yaml').read_text())
        full = generate(config)
        prefix = generate(dict(config, second_movement=False))
        excerpt = generate(config, from_pulses=True)
        for whole, first, part in zip(full['parts'], prefix['parts'], excerpt['parts']):
            self.assertEqual(part['notes'], whole['notes'][len(first['notes']):])
            self.assertEqual([n[1] for n in part['notes'][:32]], [1]*32)
            self.assertEqual(len({n[0] for n in part['notes'][:32]}), 1)
            self.assertEqual([n[1] for n in part['notes'][-2:]], [6.5,7])

if __name__ == '__main__':
    unittest.main()
