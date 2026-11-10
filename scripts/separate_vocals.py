"""Run a pinned, local BS-RoFormer in its own process to release GPU memory."""
import argparse
import json
from pathlib import Path
import re
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--job', required=True)
    args = p.parse_args()
    if not re.fullmatch('[0-9a-f]{32}', args.job):
        raise ValueError('Invalid job')
    root = args.root.resolve()
    folder = root/'.incoming/platform'/args.job
    separate(root, folder)


def separate(root, folder):
    import numpy as np
    import soundfile as sf
    from pymss import MSSeparator
    name = 'model_bs_roformer_ep_368_sdr_12.9628'
    weights = root/'models/separation'/(name+'.ckpt')
    config = root/'models/separation'/(name+'.yaml')
    if not weights.is_file() or not config.is_file():
        raise FileNotFoundError('Vocal separation model is not installed')
    mix, rate = sf.read(str(folder/'original_44k.wav'), dtype='float32', always_2d=True)
    if rate != 44100 or mix.shape[1] != 2:
        raise ValueError('Separator expects 44.1 kHz stereo')
    started = time.monotonic()
    with MSSeparator(model_type='bs_roformer', model_path=str(weights), config_path=str(config),
                     device='cuda', device_ids=[0], output_format='wav', store_dirs={}, use_tta=False,
                     inference_params=dict(batch_size=1, chunk_size=352800, overlap_size=264600,
                                           standardize=False, normalize=False, use_amp=True,
                                           cuda_attention_backend='default')) as separator:
        result = separator.separate(mix.T, pbar=False)
    stems = {key.lower(): np.asarray(value, dtype='float32') for key, value in result.items()}
    if 'vocals' not in stems:
        raise ValueError('Separator did not return vocals')
    vocals = stems['vocals']
    if vocals.ndim == 2 and vocals.shape[0] <= 2:
        vocals = vocals.T
    if vocals.shape != mix.shape or not np.isfinite(vocals).all():
        raise ValueError('Separated stems changed the audio timeline')
    # Define accompaniment as the exact residual, preserving alignment and level.
    instrumental = mix-vocals
    sf.write(str(folder/'vocals_44k.wav'), vocals, rate, subtype='FLOAT')
    sf.write(str(folder/'instrumental_44k.wav'), instrumental, rate, subtype='FLOAT')
    report = dict(model=name, sample_rate=rate, seconds=len(mix)/rate,
                  elapsed_seconds=round(time.monotonic()-started, 2),
                  reconstruction_max_error=float(np.max(np.abs(mix-(vocals+instrumental)))))
    (folder/'separation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
