"""Objective check against the known dry voice; not a subjective quality score."""
import json
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'audio/output/separation_tuning_20261107'


def reference_40k(path):
    x, sr = sf.read(str(path), dtype='float64', always_2d=True)
    x = x.mean(axis=1)
    n = round(len(x)*40000/sr)
    # Fourier resampling of this deterministic fixture, including the even Nyquist bin.
    spectrum = np.fft.rfft(x)
    keep = min(len(x), n)
    selected = spectrum[:keep//2+1].copy()
    if keep % 2 == 0:
        selected[-1] *= 2 if n < len(x) else .5
    return np.fft.irfft(selected, n=n)*(n/len(x))


def si_sdr(estimate, reference):
    n = min(len(estimate), len(reference))
    estimate = estimate[:n]-np.mean(estimate[:n])
    reference = reference[:n]-np.mean(reference[:n])
    projected = reference*(np.dot(estimate, reference)/np.dot(reference, reference))
    return float(10*np.log10(np.sum(projected**2)/max(np.sum((estimate-projected)**2), 1e-16)))


def main():
    truth = reference_40k(FOLDER/'known_vocals.wav')
    mixture = reference_40k(FOLDER/'synthetic_song.wav')
    extracted, _ = sf.read(str(FOLDER/'public_song_source.wav'), dtype='float64')
    n = min(len(extracted), len(truth))
    hop = 400
    frames = n//hop
    energy = np.sqrt(np.mean(truth[:frames*hop].reshape(frames, hop)**2, axis=1))
    quiet = energy < max(float(np.percentile(energy, 95))*.015, 1e-6)
    mask = np.repeat(quiet, hop)
    before = np.sqrt(np.mean(mixture[:len(mask)][mask]**2))
    after = np.sqrt(np.mean(extracted[:len(mask)][mask]**2))
    report = dict(input_si_sdr_db=round(si_sdr(mixture, truth), 2),
                  extracted_si_sdr_db=round(si_sdr(extracted, truth), 2),
                  quiet_seconds=float(np.sum(mask)/40000),
                  quiet_energy_reduction_db=round(float(20*np.log10(max(before, 1e-12)/max(after, 1e-12))), 2),
                  limitation='One public dry voice plus synthetic accompaniment; not a score for arbitrary real songs or voice similarity')
    file = ROOT/'reports/separation_validation.json'
    whole = json.loads(file.read_text(encoding='utf-8'))
    whole['known_fixture_metrics'] = report
    file.write_text(json.dumps(whole, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
