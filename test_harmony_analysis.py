"""Checks for actual composition alignment and interpretable analysis invariants."""
import copy
from pathlib import Path
import unittest
import numpy as np
import yaml
from harmony_analysis import (annotations, stream_cache, assemble, roughness_table,
    cluster_features, harmonic_fit, palette_candidates, HARMONIC_STARTS, event_features)
from render import generate

class HarmonyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = yaml.safe_load((Path(__file__).parent/'configs/six_parts.yaml').read_text())
        cls.cache, cls.durations, cls.labels = stream_cache(cls.config)

    def test_annotations_match_all_events_and_first_transposition_introduction(self):
        self.assertEqual(len(self.labels), 2652)
        self.assertAlmostEqual(sum(self.durations), 2118.5)
        intros = [r for r in self.labels if r['introduction']]
        self.assertEqual(len(intros), 36)
        self.assertEqual(intros[0]['event'], 441+20)
        self.assertTrue(all(r['phrase']==6 and r['phrase_position']==5 for r in intros))
        self.assertEqual(sum(r['update']==1 for r in intros), 6)

    def test_cached_assignment_matches_direct_generation_and_preserves_opening_classes(self):
        cfg = copy.deepcopy(self.config)
        for part, start in zip(cfg['ensemble'], HARMONIC_STARTS): part['start'] = start
        direct = np.array([[n for n, d in p['notes']] for p in generate(cfg)['parts']]).T
        assembled = assemble(self.cache, HARMONIC_STARTS)
        np.testing.assert_array_equal(direct, assembled)
        original = assemble(self.cache, range(6))
        np.testing.assert_array_equal(np.sort(original[:441]%12, axis=1), np.sort(assembled[:441]%12, axis=1))
        np.testing.assert_array_equal(assembled[0], [38,57,66,84,88,96])

    def test_non_linear_fractional_schedule_retained(self):
        cfg = yaml.safe_load((Path(__file__).parent/'configs/six_parts_six_then_six_quadratic.yaml').read_text())
        cache, durations, labels = stream_cache(cfg)
        pitches = assemble(cache, HARMONIC_STARTS)
        self.assertEqual(len(labels), len(pitches))
        self.assertTrue(np.any(abs(pitches-np.rint(pitches)) > .001))

    def test_pure_tone_roughness_symmetry_unison_and_semitone(self):
        table = roughness_table('pure', 'pure', [60,61,72])
        np.testing.assert_allclose(table, table.T)
        self.assertEqual(table[0,0], 0)
        self.assertGreater(table[0,1], table[0,2])
        ab = roughness_table('rich', 'odd', [60,66,72])
        ba = roughness_table('odd', 'rich', [60,66,72])
        np.testing.assert_allclose(ab, ba.T)

    def test_isolated_cluster_and_unison_are_distinct(self):
        _, pop, unisons = cluster_features(np.array([[36,60,61,80,100,120],[60,61,62,63,64,65],[60]*6], float))
        self.assertGreater(pop[0], pop[1])
        self.assertEqual(pop[2], 0)
        self.assertEqual(unisons[2], 5)

    def test_harmonic_fit_order_invariance_and_deterministic_palettes(self):
        p = np.array([[38,57,66,84,88,96],[60,61,62,63,64,65]], float)
        np.testing.assert_allclose(harmonic_fit(p), harmonic_fit(p[:,::-1]))
        self.assertTrue(np.isfinite(harmonic_fit(p)).all())
        self.assertEqual(palette_candidates(), palette_candidates())
        self.assertEqual(len(set(palette_candidates())), 24)

    def test_matched_effect_removes_exact_new_increment_and_is_zero_without_it(self):
        pitches = assemble(self.cache, HARMONIC_STARTS)
        lookup = np.unique(np.round(np.concatenate(list(self.cache.values())), 10))
        deltas = np.tile(-np.array([p['init_transposition'] for p in self.config['ensemble']])/6, (6,1))
        features = event_features(pitches, self.durations, self.labels, ['rich']*6, {}, lookup, deltas)
        zero = event_features(pitches, self.durations, self.labels, ['rich']*6, {}, lookup, np.zeros_like(deltas))
        np.testing.assert_allclose(zero['transposition_roughness_effect'], 0)
        first = 461
        # The sixth note of the first full phrase is the first newly shifted note.
        core = [72,78,75,70,66,68]
        expected = [core[(start-1)%6]+p['init_transposition'] for start,p in zip(HARMONIC_STARTS,self.config['ensemble'])]
        np.testing.assert_allclose(pitches[first]-deltas[0], expected)
        self.assertGreater(np.max(abs(features['transposition_roughness_effect'])), 0)
        self.assertEqual(np.count_nonzero(features['transposition_roughness_effect'][:441]), 0)

if __name__=='__main__': unittest.main()
