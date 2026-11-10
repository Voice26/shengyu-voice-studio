"""Summarize existing target training F0 without changing data or weights."""
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--experiment', default='gtsinger_zh_alto')
    p.add_argument('--speaker', default='ZH-Alto-1')
    args = p.parse_args()
    root = args.root.resolve()
    files = sorted((root/'third_party/RVC-WebUI/logs'/args.experiment/'2b-f0nsf').glob('*.npy'))
    if not files:
        raise FileNotFoundError('Target pitch features were not found')
    values = np.concatenate([np.load(path).reshape(-1)[::5] for path in files])
    values = values[np.isfinite(values) & (values >= 50) & (values <= 1100)]
    low, mid, high = np.percentile(values, [10, 50, 90])
    report = dict(speaker=args.speaker, p10_hz=round(float(low), 1), median_hz=round(float(mid), 1),
                  p90_hz=round(float(high), 1), files=len(files),
                  source='Existing target training F0 features, includes interpolated pitch; only a range reference')
    file = root/'models'/args.experiment/'voice_profile.json'
    file.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
