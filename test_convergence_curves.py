"""Checks for one ordinary round followed by six remaining rounds."""
import unittest
from pathlib import Path
import yaml
from jonathanmarmor import transitions
from notation import Note
from render import generate

class ConvergenceCurveTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).parent/'configs'
        self.equal=yaml.safe_load((root/'six_parts_six_then_six_equal.yaml').read_text())
        self.curve=yaml.safe_load((root/'six_parts_six_then_six_quadratic.yaml').read_text())

    def test_anchors_equal_remaining_steps_and_decreasing_curve_steps(self):
        for config in [self.equal,self.curve]:
            values=config['inward_progress']
            self.assertEqual(len(values),8)
            self.assertAlmostEqual(values[0],0)
            self.assertAlmostEqual(values[1],1/6)
            self.assertAlmostEqual(values[-1],1)
        equal=self.equal['inward_progress'];curve=self.curve['inward_progress']
        for a,b in zip(equal[1:],equal[2:]): self.assertAlmostEqual((b-a)*600,500/6)
        self.assertTrue(all(curve[i]>equal[i] for i in range(2,7)))
        jumps=[600*(b-a) for a,b in zip(curve,curve[1:])]
        self.assertAlmostEqual(jumps[0],100)
        self.assertTrue(all(a>b for a,b in zip(jumps,jumps[1:])))

    def test_first_round_matches_six_step_version_and_all_voices_converge(self):
        for offset in [-30,-18,-6,6,18,30]:
            seq=[Note(pitches=[p+offset]) for p in [72,78,75,70,66,68]]
            old=transitions(seq,-offset/6,6)
            for config in [self.equal,self.curve]:
                progress=config['inward_progress']
                intervals=[-offset*(b-a) for a,b in zip(progress,progress[1:])]
                new=transitions(seq,0,7,intervals)
                for before,after in zip(old[:7],new[:7]):
                    for a,b in zip(before,after):self.assertAlmostEqual(a.raw_pitches[0].ps,b.raw_pitches[0].ps)
                for a,b in zip(sorted(n.raw_pitches[0].ps for n in new[-1]),sorted([72,78,75,70,66,68])):self.assertAlmostEqual(a,b)

    def test_variants_share_rhythm_and_second_movement(self):
        a=generate(self.equal);b=generate(self.curve)
        for x,y in zip(a['parts'],b['parts']):self.assertEqual([n[1] for n in x['notes']],[n[1] for n in y['notes']])
        a=generate(self.equal,True);b=generate(self.curve,True)
        for x,y in zip(a['parts'],b['parts']):
            for (p,d),(q,e) in zip(x['notes'],y['notes']):
                self.assertAlmostEqual(p,q)
                self.assertEqual(d,e)

if __name__=='__main__':unittest.main()
