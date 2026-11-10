import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from pause_cleanup import apply_cleanup, pause_envelope, trim_padding


class PauseCleanupTest(unittest.TestCase):
    rate = 16000

    def tone(self, duration, amplitude=.15):
        return (amplitude*np.sin(np.arange(round(duration*self.rate))*2*np.pi*220/self.rate)).astype('float32')

    def test_attenuates_leading_and_middle_silence_without_shortening(self):
        tone = self.tone(1)
        source = np.r_[np.zeros(self.rate),tone,np.zeros(self.rate),tone,np.zeros(self.rate)].astype('float32')
        converted = source + self.tone(5, .01)
        result, report = apply_cleanup(source, converted, self.rate)
        self.assertEqual(len(result), len(source))
        self.assertTrue(np.isfinite(result).all())
        self.assertLess(np.sqrt(np.mean(result[:self.rate//2]**2)), .0003)
        self.assertLess(np.sqrt(np.mean(result[round(2.4*self.rate):round(2.6*self.rate)]**2)), .0003)
        np.testing.assert_array_equal(result[self.rate:2*self.rate], converted[self.rate:2*self.rate])
        self.assertGreater(report['pause_reduction_db'], 20)

    def test_quiet_voiced_note_and_unvoiced_boundaries_are_protected(self):
        source = np.r_[self.tone(1),self.tone(1,.0002),self.tone(1)]
        voiced = np.ones(301, dtype=bool)
        gain, _ = pause_envelope(source, self.rate, voiced)
        np.testing.assert_array_equal(gain, np.ones_like(gain))
        source = np.r_[np.zeros(self.rate),self.tone(1),np.zeros(self.rate)].astype('float32')
        voiced = np.zeros(300, dtype=bool); voiced[100:200] = True
        gain, _ = pause_envelope(source, self.rate, voiced)
        self.assertEqual(float(gain[round(.9*self.rate)]), 1)
        self.assertEqual(float(gain[round(2.15*self.rate)]), 1)

    def test_short_syllable_gap_stays_unchanged(self):
        source = np.r_[self.tone(1),np.zeros(round(.1*self.rate)),self.tone(1)].astype('float32')
        gain, _ = pause_envelope(source, self.rate)
        np.testing.assert_array_equal(gain, np.ones_like(gain))

    def test_preserves_first_and_last_sung_samples_after_context_crop(self):
        source = self.tone(1)
        padded = np.r_[np.zeros(round(.4*self.rate)), source, np.zeros(round(.5*self.rate))]
        result = trim_padding(padded, len(source), self.rate)
        np.testing.assert_array_equal(result, source)
        with self.assertRaises(ValueError):
            trim_padding(source, len(source), self.rate)

    def test_fades_do_not_add_discontinuities_or_amplification(self):
        source = np.r_[self.tone(1),np.zeros(self.rate),self.tone(1)].astype('float32')
        gain, _ = pause_envelope(source, self.rate)
        self.assertGreaterEqual(float(gain.min()), 0)
        self.assertLessEqual(float(gain.max()), 1)
        self.assertLess(float(np.max(np.abs(np.diff(gain)))), .002)

    def test_rejects_invalid_audio_and_mismatched_timeline(self):
        for audio in (np.array([]),np.array([np.nan])):
            with self.assertRaises(ValueError):
                pause_envelope(audio, self.rate)
        with self.assertRaises(ValueError):
            apply_cleanup(np.zeros(10), np.zeros(9), self.rate)


if __name__ == '__main__':
    unittest.main()
