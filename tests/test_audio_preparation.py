"""Meaningful pitch-range and stereo-remix checks, independent of GPU inference."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audio_preparation import applied_pitch, pitch_summary, remix

TARGET = dict(p10_hz=188.6, median_hz=263.3, p90_hz=369.8)


class AudioPreparationTest(unittest.TestCase):
    def test_low_voice_gets_octave_and_overlapping_voice_keeps_key(self):
        low = pitch_summary(np.linspace(100, 165, 300), TARGET)
        self.assertEqual(low['suggested_pitch'], 12)
        overlap = pitch_summary(np.linspace(200, 340, 300), TARGET)
        self.assertEqual(overlap['suggested_pitch'], 0)
        high = pitch_summary(np.linspace(520, 800, 300), TARGET)
        self.assertEqual(high['suggested_pitch'], -12)

    def test_unvoiced_and_quiet_frames_do_not_drive_suggestion(self):
        values = np.r_[np.zeros(100), np.full(200, 250.), np.full(100, 100.)]
        energy = np.r_[np.ones(300), np.full(100, .001)]
        result = pitch_summary(values, TARGET, energy)
        self.assertEqual(result['median_hz'], 250)
        self.assertEqual(result['voiced_seconds'], 2)
        insufficient = pitch_summary([0, np.nan, 120, 9999], TARGET)
        self.assertFalse(insufficient['available'])
        self.assertEqual(insufficient['suggested_pitch'], 0)

    def test_manual_adjustment_and_bounds(self):
        analysis = dict(suggested_pitch=12)
        self.assertEqual(applied_pitch(dict(pitch=0, pitch_mode='auto'), analysis), 12)
        self.assertEqual(applied_pitch(dict(pitch=-1, pitch_mode='auto'), analysis), 11)
        self.assertEqual(applied_pitch(dict(pitch=3, pitch_mode='auto'), analysis), 12)
        self.assertEqual(applied_pitch(dict(pitch=-2, pitch_mode='manual'), analysis), -2)

    def test_remix_retains_stereo_and_matches_original_vocal_level(self):
        t = np.arange(4000)/40000
        original = (.1*np.sin(2*np.pi*230*t)).astype('float32')
        music = np.column_stack([.04*np.sin(2*np.pi*100*t), .05*np.sin(2*np.pi*150*t)])
        mixed, report = remix(original*2, original, music)
        self.assertEqual(mixed.shape, (4000, 2))
        self.assertAlmostEqual(report['vocal_gain'], .5, places=6)
        np.testing.assert_allclose(mixed, music+original[:, None], atol=2e-8)
        # The center vocal leaves the original left/right accompaniment difference intact.
        np.testing.assert_allclose(mixed[:, 0]-mixed[:, 1], music[:, 0]-music[:, 1], atol=3e-8)

    def test_loud_mix_uses_common_headroom_without_clipping(self):
        voice = np.full(100, .8, dtype='float32')
        mixed, report = remix(voice, voice, np.full((100, 2), .8))
        self.assertLess(report['common_gain'], 1)
        self.assertLessEqual(float(np.max(np.abs(mixed))), .980001)
        self.assertTrue(np.isfinite(mixed).all())

    def test_invalid_timeline_and_nonfinite_stems_are_rejected(self):
        for voice, reference, music in [(np.ones(10), np.ones(9), np.ones((10, 2))),
                                        (np.full(10, np.nan), np.ones(10), np.ones((10, 2)))]:
            with self.assertRaises(ValueError):
                remix(voice, reference, music)


if __name__ == '__main__':
    unittest.main()
