"""Verify seven-step convergence and pitch-bent MIDI export."""
import math
import struct
import tempfile
import unittest
from pathlib import Path
import yaml
from jonathanmarmor import transitions, section_A_part, flatten
from notation import Note
from render import generate, render


def midi_messages(path):
    data = path.read_bytes()
    pos = 14
    result = []
    while pos < len(data):
        size = struct.unpack('>I', data[pos+4:pos+8])[0]
        track = data[pos+8:pos+8+size]
        pos += 8+size
        cursor = 0
        def vlq():
            nonlocal cursor
            value = 0
            while True:
                b = track[cursor]; cursor += 1
                value = (value << 7) | (b & 127)
                if b < 128: return value
        messages = []
        while cursor < len(track):
            vlq()
            status = track[cursor]; cursor += 1
            if status == 255:
                cursor += 1
                size = vlq(); cursor += size
            else:
                size = 1 if status & 240 in (192,208) else 2
                messages.append((status, list(track[cursor:cursor+size])))
                cursor += size
        result.append(messages)
    return result


class MicrotonalTests(unittest.TestCase):
    def test_all_voices_converge_in_seven_equal_rounds(self):
        for offset in [-30,-18,-6,6,18,30]:
            initial = [Note(pitches=[p+offset]) for p in [72,78,75,70,66,68]]
            stages = transitions(initial, -offset/7, 7)
            for round_index in range(1,8):
                complete = stages[round_index*7-1]
                actual = sorted(n.raw_pitches[0].ps for n in complete)
                expected = sorted(n.raw_pitches[0].ps-offset*round_index/7 for n in initial)
                for a,b in zip(actual,expected): self.assertAlmostEqual(a,b)
            for note in stages[-1]:
                self.assertAlmostEqual(note.raw_pitches[0].ps, round(note.raw_pitches[0].ps))

    def test_export_preserves_fractional_pitch_and_resets_bend(self):
        pitches = [60,60+6/7,61,60-6/7]
        music = dict(bpm=320,parts=[dict(name='Clarinet',program=71,pan=-100,notes=[[p,1] for p in pitches])])
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)/'micro'
            render(music,base,False,Path('unused.sf2'))
            messages = midi_messages(base.with_suffix('.mid'))[1]
        controls = [(data[0],data[1]) for status,data in messages if status == 176]
        self.assertIn((6,2),controls)
        self.assertIn((38,0),controls)
        bend = 8192; actual = []
        for status,data in messages:
            if status == 224: bend = data[0]+128*data[1]
            if status == 144: actual.append(data[0]+(bend-8192)*2/8192)
        self.assertEqual(len(actual),len(pitches))
        for a,b in zip(actual,pitches): self.assertLess(abs(a-b)*100,0.013)
        self.assertEqual(actual[2],61)

    def test_opening_and_second_movement_rhythm_are_preserved(self):
        root = Path(__file__).parent
        old = generate(yaml.safe_load((root/'configs/six_parts.yaml').read_text()))
        cfg = yaml.safe_load((root/'configs/six_parts_microtonal_seven_steps.yaml').read_text())
        new = generate(cfg)
        opening_count = len(list(flatten(section_A_part([Note(pitches=[p]) for p in range(6)]))))
        second = generate(cfg,from_pulses=True)
        for a,b,c in zip(old['parts'],new['parts'],second['parts']):
            self.assertEqual(a['notes'][:opening_count],b['notes'][:opening_count])
            self.assertEqual([n[1] for n in a['notes'][-len(c['notes']):]],
                             [n[1] for n in c['notes']])
            self.assertTrue(all(math.isclose(p,round(p),abs_tol=1e-9) for p,_ in c['notes']))

if __name__ == '__main__': unittest.main()
