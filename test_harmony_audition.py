import unittest
import numpy as np
from harmony_audition import note_signal, render_windows

class AuditionTests(unittest.TestCase):
    def test_natural_release_and_envelope_difference(self):
        age=np.arange(44100)/44100
        rich=note_signal(60,age,.5,'rich',44100)
        pluck=note_signal(60,age,.5,'pluck',44100)
        self.assertTrue(np.isfinite(rich).all())
        self.assertTrue(np.all(rich[age>=.59]==0))
        self.assertGreater(np.mean(rich[(age>.3)&(age<.45)]**2), np.mean(pluck[(age>.3)&(age<.45)]**2)*20)

    def test_hard_pan_and_mid_note_excerpt_preserve_signal(self):
        pitches=np.array([[60]*6],float); durations=np.array([4.])
        config=dict(tempo_bpm=60,ensemble=[dict(pan=-100) for _ in range(6)])
        audio=render_windows(pitches,durations,config,['warm']*6,[(1,2,'mid note')],sample_rate=8000)
        self.assertGreater(np.max(abs(audio[:,0])),.01)
        self.assertEqual(np.max(abs(audio[:,1])),0)
        self.assertTrue(np.isfinite(audio).all())

if __name__=='__main__':unittest.main()
