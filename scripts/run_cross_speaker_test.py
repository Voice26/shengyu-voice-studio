"""Run the existing model on two unseen singers and export listening A/B files."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from math import gcd

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
RVC = ROOT / 'third_party/RVC-WebUI'
OUTPUT = ROOT / 'audio/output/cross_speaker_20261107'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(path):
    audio, rate = sf.read(str(path), dtype='float32', always_2d=True)
    assert len(audio) and np.isfinite(audio).all(), str(path)
    return dict(seconds=len(audio)/rate, sample_rate=rate,
                peak=float(np.max(np.abs(audio))), rms=float(np.sqrt(np.mean(audio.astype('float64')**2))),
                clipping_fraction=float(np.mean(np.abs(audio) >= 0.9995)), sha256=sha256(path))


def mono(path, rate=40000):
    audio, sr = sf.read(str(path), dtype='float32', always_2d=True)
    divisor = gcd(sr, rate)
    return resample_poly(audio.mean(axis=1), rate//divisor, sr//divisor).astype('float32')


def main():
    sources = json.loads((ROOT / 'reports/cross_speaker_sources.json').read_text(encoding='utf-8'))
    model = ROOT / 'models/gtsinger_zh_alto/gtsinger_zh_alto.pth'
    index = RVC / 'logs/gtsinger_zh_alto/added_IVF4777_Flat_nprobe_1_gtsinger_zh_alto_v2.index'
    assert model.is_file() and index.is_file()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONPATH':str(RVC), 'RVC_CUDA_GRAPH':'0', 'HF_HUB_OFFLINE':'1',
           'OMP_NUM_THREADS':'8', 'OPENBLAS_NUM_THREADS':'8', 'MKL_NUM_THREADS':'8',
           'PATH':str(ROOT/'.venv/bin')+':'+os.environ.get('PATH', '')}
    results = []
    for source in sources['sources']:
        original = ROOT / source['input']
        assert sha256(original) == source['sha256']
        converted = OUTPUT / f"{source['key']}_converted.wav"
        comparison = OUTPUT / f"{source['key']}_comparison.wav"
        log = ROOT / 'reports' / f"cross_speaker_{source['key']}.log"
        args = [str(ROOT/'.venv/bin/python'), '-m', 'infer.cli', '--model', str(model),
                '--input', str(original), '--output', str(converted), '--speaker-id', '0',
                '--pitch', '0', '--f0-method', 'rmvpe', '--index', str(index),
                '--index-rate', '0.75', '--protect', '0.33', '--rms-mix-rate', '1', '--overwrite']
        started = time.monotonic()
        with log.open('w', encoding='utf-8') as stream:
            subprocess.run(args, cwd=RVC, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
        elapsed = time.monotonic() - started
        original_stats, converted_stats = stats(original), stats(converted)
        assert converted_stats['sample_rate'] == 40000
        assert abs(original_stats['seconds']-converted_stats['seconds']) < 0.5
        assert converted_stats['rms'] > 0.0001
        a, b = mono(original), mono(converted)
        gains = [0.08/max(float(np.sqrt(np.mean(x.astype('float64')**2))), 1e-8) for x in (a, b)]
        joined = np.concatenate([a*gains[0], np.zeros(40000, dtype='float32'), b*gains[1]])
        limiter = min(1.0, 0.95/max(float(np.max(np.abs(joined))), 1e-8))
        sf.write(str(comparison), joined*limiter, 40000, subtype='PCM_16')
        result = dict(key=source['key'], source_speaker=source['speaker'], source_language=source['language'],
                      song=source['song'], target_speaker='ZH-Alto-1', pitch_semitones=0, index_rate=0.75,
                      f0_method='rmvpe', protect=0.33, rms_mix_rate=1, elapsed_seconds=elapsed,
                      input=source['input'], input_stats=original_stats,
                      converted=str(converted.relative_to(ROOT)), converted_stats=converted_stats,
                      comparison=str(comparison.relative_to(ROOT)), comparison_stats=stats(comparison),
                      comparison_layout='Original, 1 s silence, converted; equal RMS, common peak limiter',
                      listening_gains=gains, comparison_common_gain=limiter)
        results.append(result)
        print(json.dumps(result, ensure_ascii=True), flush=True)
    report = dict(status='completed', test_type='Two unseen source singers converted to the trained target singer',
                  model_sha256=sha256(model), index_sha256=sha256(index), results=results,
                  subjective_quality='Not evaluated by an audio-capable reviewer; listen to A/B files',
                  note='Female source sings English; this also tests cross-language generalization. Both tests preserve source pitch.')
    (ROOT / 'reports/cross_speaker_test.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
