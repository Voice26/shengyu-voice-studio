"""Fetch one pinned PyMSS vocal separator and verify its public file manifest."""
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
REPO = 'baicai1145/pymss'
REVISION = 'f02318ef92c43472777ed7aeeded3d2b29a68b58'
NAME = 'model_bs_roformer_ep_368_sdr_12.9628'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    from huggingface_hub import HfApi
    files = [f'vocal/vocal_extraction/{NAME}'+suffix for suffix in ('.ckpt', '.yaml')]
    entries = HfApi(token=False).get_paths_info(REPO, files, revision=REVISION, repo_type='model')
    folder = ROOT/'models/separation'
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for entry in entries:
        target = folder/Path(entry.path).name
        expected = entry.lfs.sha256 if entry.lfs else None
        valid = target.is_file() and target.stat().st_size == entry.size and (not expected or digest(target) == expected)
        if not valid:
            part = target.with_suffix(target.suffix+'.part')
            for attempt in range(4):
                offset = part.stat().st_size if part.is_file() else 0
                if offset == entry.size:
                    break
                if offset > entry.size:
                    raise ValueError('Partial download is larger than the expected file')
                try:
                    with requests.get(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{quote(entry.path, safe="/")}',
                                      headers={'Range':f'bytes={offset}-'} if offset else {},
                                      stream=True, timeout=(15, 120)) as response:
                        response.raise_for_status()
                        append = offset > 0 and response.status_code == 206
                        if append and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                            raise ValueError('Unexpected resume range')
                        received = offset if append else 0
                        print(f'{target.name}: starting at {received/1024/1024:.0f} MiB', flush=True)
                        with part.open('ab' if append else 'wb') as output:
                            for block in response.iter_content(4*1024*1024):
                                output.write(block)
                                received += len(block)
                                if received//(100*1024*1024) != (received-len(block))//(100*1024*1024):
                                    print(f'{target.name}: {received/1024/1024:.0f} MiB', flush=True)
                    break
                except requests.RequestException:
                    if attempt == 3:
                        raise
                    print('Connection interrupted; resuming existing bytes', flush=True)
                    time.sleep(1)
            if part.stat().st_size != entry.size or (expected and digest(part) != expected):
                raise ValueError('Model download verification failed')
            if not expected:
                data = part.read_bytes()
                blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                if blob != entry.blob_id:
                    raise ValueError('Model config Git blob mismatch')
            part.replace(target)
        records.append(dict(file=target.name, bytes=entry.size, sha256=digest(target), repo_path=entry.path))
        print(f'Verified {target.name}', flush=True)
    report = dict(repo_id=REPO, revision=REVISION, model_type='bs_roformer', files=records)
    (ROOT/'reports/separation_assets.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
