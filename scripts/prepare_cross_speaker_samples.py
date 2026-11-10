"""Download two small, pinned GTSinger excerpts for conversion, not training."""
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import quote

import numpy as np
import requests
import soundfile as sf
import yaml

ROOT = Path(__file__).resolve().parents[1]
REVISION = yaml.safe_load((ROOT / 'configs/project.yaml').read_text(encoding='utf-8'))['dataset_revision']
REPO = 'GTSinger/GTSinger'
PLANS = [
    dict(key='male_zh_tenor_1', speaker='ZH-Tenor-1', language='Chinese',
         voice='male tenor', song='平凡的一天'),
    dict(key='female_en_alto_1', speaker='EN-Alto-1', language='English',
         voice='female alto', song='safe and sound'),
]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    session = requests.Session()
    sources = []
    for plan in PLANS:
        assert plan['speaker'] != 'ZH-Alto-1'
        group = f"{plan['language']}/{plan['speaker']}/Breathy/{plan['song']}/Control_Group"
        listing = session.get(f'https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/{quote(group, safe="/")}', timeout=(10, 40))
        listing.raise_for_status()
        assert not listing.links.get('next'), 'Unexpected paginated sample directory'
        wavs = sorted((f for f in listing.json() if f['type'] == 'file' and f['path'].endswith('.wav')), key=lambda f: f['path'])
        assert wavs, group
        pieces, entries, seconds, rate = [], [], 0.0, None
        for entry in wavs[:4]:
            relative = entry['path']
            expected = entry['lfs']['oid']
            target = ROOT / 'data/raw/GTSinger' / relative
            target.resolve().relative_to((ROOT / 'data/raw/GTSinger').resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            valid = target.exists() and target.stat().st_size == entry['size'] and digest(target) == expected
            if not valid:
                for attempt in range(3):
                    try:
                        part = target.with_suffix('.wav.part')
                        with session.get(f'https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{quote(relative, safe="/")}', stream=True, timeout=(15, 90)) as response:
                            response.raise_for_status()
                            with part.open('wb') as output:
                                for chunk in response.iter_content(1024 * 1024):
                                    output.write(chunk)
                        if part.stat().st_size != entry['size'] or digest(part) != expected:
                            raise ValueError(f'Hash or size mismatch: {relative}')
                        part.replace(target)
                        break
                    except (requests.RequestException, ValueError):
                        if attempt == 2:
                            raise
                        time.sleep(2)
            audio, current_rate = sf.read(str(target), dtype='float32', always_2d=True)
            assert np.isfinite(audio).all() and len(audio) > 0
            if rate is None:
                rate = current_rate
            assert rate == current_rate
            if pieces:
                pieces.append(np.zeros(round(rate * 0.25), dtype='float32'))
            pieces.append(audio.mean(axis=1))
            duration = len(audio) / rate
            seconds += duration
            entries.append(dict(repo_path=relative, bytes=entry['size'], sha256=expected, seconds=duration))
            print(json.dumps(dict(speaker=plan['speaker'], downloaded=relative, seconds=duration), ensure_ascii=True), flush=True)
            if seconds >= 18:
                break
        combined = np.concatenate(pieces)
        dest = ROOT / 'audio/input/cross_speaker' / f"{plan['key']}.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(dest), combined, rate, subtype='PCM_24')
        sources.append(dict(**plan, input=str(dest.relative_to(ROOT)).replace('\\', '/'),
                            sample_rate=rate, seconds=len(combined)/rate, sha256=digest(dest),
                            assembly='Whole numbered phrases in order, with 0.25 s silence between phrases; no trimming or pitch shift',
                            files=entries))
    manifest = dict(repo_id=REPO, revision=REVISION, purpose='Cross-speaker inference only; no training data or model changes',
                    target_speaker='ZH-Alto-1', sources=sources)
    (ROOT / 'reports/cross_speaker_sources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    main()
