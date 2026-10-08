"""Checks for the agreed 21-figure random duration window."""
import random
import unittest
from pathlib import Path
import yaml
from jonathanmarmor import section_B_part, flatten
from notation import Note
from render import generate

class RhythmicLengtheningTests(unittest.TestCase):
    def test_exact_triangle_and_unchanged_pitches(self):
        seq = [Note(pitches=[p]) for p in [60,66,63,58,54,56]]
        old = section_B_part(seq,6/13,13)
        settings = dict(start_bar=3,bar_count=21,seed=20261008)
        new = section_B_part(seq,6/13,13,settings,random.Random('20261008:3'))
        expected = [0,0]+list(range(1,12))+list(range(10,0,-1))+[0]*68
        self.assertEqual(len(new),len(expected))
        for before,after,count in zip(old,new,expected):
            a=list(flatten(before));b=list(flatten(after))
            self.assertEqual([n.raw_pitches[0].ps for n in a],[n.raw_pitches[0].ps for n in b])
            changed=[(x,y) for x,y in zip(a,b) if x.raw_duration!=y.raw_duration]
            self.assertEqual(len(changed),count)
            self.assertTrue(all(x.raw_duration==.5 and y.raw_duration==1 for x,y in changed))
            self.assertEqual(sum(n.raw_duration for n in b),sum(n.raw_duration for n in a)+count*.5)

    def test_seed_reproducibility_and_independent_choices(self):
        seq=[Note(pitches=[p]) for p in range(6)]
        settings=dict(start_bar=3,bar_count=21,seed=20261008)
        def durations(part):
            return [n.raw_duration for n in flatten(section_B_part(seq,6/13,13,settings,random.Random(f'20261008:{part}')))]
        self.assertEqual(durations(1),durations(1))
        self.assertNotEqual(durations(1),durations(2))

    def test_all_parts_realign_and_second_movement_is_unchanged(self):
        root=Path(__file__).parent
        original=yaml.safe_load((root/'configs/six_parts_microtonal_thirteen_steps.yaml').read_text())
        changed=yaml.safe_load((root/'configs/six_parts_thirteen_steps_random_rhythm.yaml').read_text())
        baseline=generate(original);version=generate(changed)
        self.assertEqual(generate(original,True),generate(changed,True))
        totals=[]
        for before,after in zip(baseline['parts'],version['parts']):
            self.assertEqual([n[0] for n in before['notes']],[n[0] for n in after['notes']])
            delta=sum(n[1] for n in after['notes'])-sum(n[1] for n in before['notes'])
            self.assertEqual(delta,60.5)
            totals.append(sum(n[1] for n in after['notes']))
        self.assertEqual(len(set(totals)),1)

if __name__=='__main__': unittest.main()
