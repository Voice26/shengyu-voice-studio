"""Train an isolated 40 kHz RVC v2 voice from a directory of single-singer WAVs."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment')
    parser.add_argument('source', type=Path)
    parser.add_argument('--separate', action='append', default=[], help='WAV basename to separate before training')
    parser.add_argument('--epochs', type=int, default=80)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.experiment) or args.epochs < 1:
        parser.error('Invalid experiment name or epoch count')
    inputs = sorted(args.source.resolve().glob('*.wav'))
    if not inputs or set(args.separate) - {p.name for p in inputs}:
        parser.error('Check input directory and mixture filenames')
    root = Path(__file__).resolve().parents[1]
    rvc = root/'third_party/RVC-WebUI'
    exp = rvc/'logs'/args.experiment
    out = root/'models'/args.experiment
    work = root/'data/processed'/args.experiment
    if any(p.exists() for p in (exp, work, out, rvc/'assets/weights'/(args.experiment+'.pth'))):
        raise FileExistsError('Use a fresh experiment name to preserve existing artifacts')
    exp.mkdir()
    train = work/'train'
    train.mkdir(parents=True)
    out.mkdir()
    os.environ.update(HF_HUB_OFFLINE='1', PYTHONUNBUFFERED='1', PYTHONPATH=str(rvc),
                      PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'],
                      OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8',
                      NUMBA_NUM_THREADS='8', MPLBACKEND='Agg')

    def run(*command):
        print('Running', *command, flush=True)
        subprocess.run([sys.executable, *map(str, command)], cwd=rvc, check=True)

    records = []
    for i, path in enumerate(inputs):
        y, rate = sf.read(path, dtype='float32')
        if rate != 40000 or y.ndim != 1 or not np.isfinite(y).all():
            raise ValueError(f'Expected finite 40 kHz mono audio: {path.name}')
        record = dict(file=path.name, seconds=len(y)/rate, separated=path.name in args.separate)
        if record['separated']:
            from separate_vocals import separate
            stems = work/f'stems_{i:02d}'
            stems.mkdir()
            stereo = np.repeat(resample_poly(y, 441, 400)[:, None], 2, axis=1)
            sf.write(stems/'original_44k.wav', stereo, 44100, subtype='FLOAT')
            del stereo
            separate(root, stems)
            vocals, _ = sf.read(stems/'vocals_44k.wav', dtype='float32')
            y = resample_poly(vocals.mean(axis=1), 400, 441)[:len(y)]
            y *= min(1., .98/max(float(np.max(np.abs(y))), 1e-8))
        if i == 0:
            # Keep a continuous, active 12 s phrase for the reference player. Exclude
            # the whole phrase and a one-second buffer on each side from training.
            length = 12 * rate
            starts = range(rate*3, len(y)-length-rate*3, rate)
            if not starts:
                raise ValueError('First recording is too short to reserve a reference')
            start = max(starts, key=lambda n: np.mean(y[n:n+length:40]**2))
            sf.write(out/'reference.wav', y[start:start+length], rate, subtype='PCM_16')
            sf.write(train/'00_a.wav', y[:start-rate], rate, subtype='PCM_16')
            sf.write(train/'00_b.wav', y[start+length+rate:], rate, subtype='PCM_16')
            record.update(reference_start=start/rate, reference_seconds=12, excluded_seconds=14)
        else:
            sf.write(train/f'{i:02d}.wav', y, rate, subtype='PCM_16')
        records.append(record)
    run('-m', 'train.preprocess', train, 40000, 4, exp, 'False', '3.7')
    run('-m', 'train.dataset.extract_f0', 'cuda', 1, 0, 0, exp, 'true')
    run('-m', 'train.dataset.extract_hubert_feature', 'cuda:0', 1, 0, 0, exp, 'v2', 'true')
    run(root/'scripts/prepare_rvc_config.py', '--rvc-dir', rvc, '--experiment', args.experiment)
    run('-m', 'train.train', '-e', args.experiment, '-sr', '40k', '-f0', 1, '-bs', 8, '-g', 0,
        '-te', args.epochs, '-se', args.epochs, '-pg', 'assets/pretrained_v2/f0G40k.pth',
        '-pd', 'assets/pretrained_v2/f0D40k.pth', '-l', 1, '-c', 0, '-sw', 0, '-v', 'v2')
    run('-m', 'train.train_index', args.experiment, 'v2', 'assets/indices', 8, 'single')
    index, = exp.glob('added_*.index')
    shutil.copy2(index, out/'voice.index')
    shutil.copy2(rvc/'assets/weights'/(args.experiment+'.pth'), out/(args.experiment+'.pth'))
    run(root/'scripts/build_target_voice_profile.py', '--root', root, '--experiment', args.experiment,
        '--speaker', args.experiment)
    report = dict(experiment=args.experiment, inputs=records, epochs=args.epochs, batch_size=8,
                  sample_rate=40000, training_segments=len(list((exp/'0_gt_wavs').glob('*.wav'))),
                  index=index.name)
    (out/'training.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Completed', args.experiment, flush=True)


if __name__ == '__main__':
    main()
