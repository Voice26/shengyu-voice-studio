"""Objective reconstruction checks and a volume-matched listening comparison."""
import json
import os
from pathlib import Path
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'audio/output/server_public'


def mono(path, rate):
    audio, original_rate = sf.read(str(path), dtype='float32', always_2d=True)
    audio = audio.mean(axis=1)
    divisor = gcd(rate, original_rate)
    return resample_poly(audio, rate//divisor, original_rate//divisor).astype('float32')


def stats(path):
    audio, rate = sf.read(str(path), dtype='float32')
    return dict(seconds=len(audio)/rate, sample_rate=rate,
                peak=float(np.max(np.abs(audio))), rms=float(np.sqrt(np.mean(audio.astype('float64')**2))),
                clipping_fraction=float(np.mean(np.abs(audio) >= 0.9995)))


def envelope(audio):
    padded = np.pad(audio, (160, 320))
    return np.array([np.sqrt(np.mean(padded[start:start+320]**2))
                     for start in range(0, len(audio), 160)])


def aligned(a, b, lag):
    offset_a, offset_b = max(lag, 0), max(-lag, 0)
    length = min(len(a)-offset_a, len(b)-offset_b)
    return a[offset_a:offset_a+length], b[offset_b:offset_b+length]


reference = OUTPUT/'holdout_input.wav'
converted = OUTPUT/'holdout_converted.wav'
a, b = mono(reference, 16000), mono(converted, 16000)
ea, eb = envelope(a), envelope(b)
correlations = []
for lag in range(-20, 21):
    x, y = aligned(ea, eb, lag)
    correlations.append((float(np.corrcoef(x, y)[0, 1]), lag))
correlation, lag = max(correlations)

os.environ['RVC_CUDA_GRAPH'] = '0'
from infer.rmvpe import RMVPE
pitch = RMVPE(str(ROOT/'third_party/RVC-WebUI/assets/rmvpe/rmvpe.pt'), is_half=False, device='cuda')
pa = pitch.infer_from_audio(a, thred=0.03)
pb = pitch.infer_from_audio(b, thred=0.03)
pa, pb = aligned(pa, pb, lag)
both = (pa > 0) & (pb > 0)
cents = 1200 * np.log2(pb[both] / pa[both])
result = dict(test_type='Held-out target singer reconstruction; not a speaker similarity score',
              reference=stats(reference), converted=stats(converted),
              alignment_frames_10ms=lag, envelope_correlation=correlation,
              jointly_voiced_frames=int(both.sum()),
              voiced_unvoiced_agreement=float(np.mean((pa > 0) == (pb > 0))),
              median_abs_pitch_cents=float(np.median(np.abs(cents))),
              p90_abs_pitch_cents=float(np.percentile(np.abs(cents), 90)),
              pitch_within_50_cents_fraction=float(np.mean(np.abs(cents) <= 50)),
              pitch_over_100_cents_fraction=float(np.mean(np.abs(cents) > 100)),
              median_signed_pitch_cents=float(np.median(cents)),
              subjective_listening='Not performed by an audio-capable reviewer',
              cross_speaker_conversion='Not tested')
result['output_rms_difference_db'] = float(20*np.log10(result['converted']['rms']/result['reference']['rms']))
(ROOT/'reports/server_audio_quality.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))

# Listening copy only. Original source and converted WAVs remain unchanged.
clips = []
for path in (reference, converted):
    audio = mono(path, 40000)
    audio = audio * (0.08 / max(float(np.sqrt(np.mean(audio**2))), 1e-8))
    clips.append(audio)
comparison = np.concatenate([clips[0], np.zeros(28000, dtype='float32'), clips[1]])
if np.max(np.abs(comparison)) > 0.95:
    comparison *= 0.95/np.max(np.abs(comparison))
sf.write(str(OUTPUT/'comparison_original_then_converted.wav'), comparison, 40000, subtype='PCM_16')
print(json.dumps(result, ensure_ascii=False, indent=2))
