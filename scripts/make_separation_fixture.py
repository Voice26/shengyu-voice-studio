"""Add a known synthetic accompaniment to a public dry voice for integration QA."""
from pathlib import Path
import json
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT/'audio/input/cross_speaker/female_en_alto_1.wav'
    vocal, rate = sf.read(str(source), dtype='float32', always_2d=True)
    vocal = vocal.mean(axis=1)
    t = np.arange(len(vocal), dtype=np.float64)/rate
    beat = t % .5
    bar = (t//2).astype(int) % 4
    roots = np.array([130.8128, 110., 87.3071, 97.9989])[bar]
    phase = np.cumsum(2*np.pi*roots/rate)
    # A bass line, sustained triads, stereo overtones and soft percussion.
    envelope = (1-np.exp(-beat*35))*np.exp(-beat*3)
    bass = .06*np.sin(phase*.5)*envelope
    chord = sum(np.sin(phase*ratio)/3 for ratio in (1, 2**(4/12), 1.5))*.075
    rng = np.random.default_rng(41)
    hats = rng.standard_normal(len(t))*.018*np.exp(-(t % .25)*70)
    kick = .055*np.sin(2*np.pi*(48*beat+2*(1-np.exp(-beat*25))))*np.exp(-beat*18)
    music = np.column_stack([bass+chord+kick+hats, bass+chord*.9+kick-hats])
    scale = .85/max(float(np.max(np.abs(music+vocal[:, None]))), .85)
    folder = ROOT/'audio/output/separation_tuning_20261107'
    folder.mkdir(parents=True, exist_ok=True)
    for name, audio in [('synthetic_song', music+vocal[:, None]),
                        ('known_vocals', vocal), ('known_instrumental', music)]:
        sf.write(str(folder/(name+'.wav')), audio*scale, rate, subtype='PCM_16')
    (folder/'fixture.json').write_text(json.dumps(dict(source=str(source), rate=rate,
        seconds=len(vocal)/rate, scale=scale, accompaniment='Deterministic synthetic chords, bass and percussion'), indent=2), encoding='utf-8')
    print(json.dumps(dict(folder=str(folder), seconds=len(vocal)/rate, rate=rate)))


if __name__ == '__main__':
    main()
