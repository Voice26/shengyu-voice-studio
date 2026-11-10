"""Recover completed project pip-cache wheels for an offline installation."""
import hashlib
import json
import os
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
destination = root / 'wheelhouse'
destination.mkdir(exist_ok=True)
entries = []
for path in (root / '.cache/pip').rglob('*.body'):
    try:
        with path.open('rb') as source:
            if source.read(4) != b'PK\x03\x04':
                continue
        with zipfile.ZipFile(path) as wheel:
            metadata = next(n for n in wheel.namelist() if n.endswith('.dist-info/WHEEL'))
            tag = next(line[5:] for line in wheel.read(metadata).decode().splitlines() if line.startswith('Tag: '))
            stem = metadata.split('/')[0].removesuffix('.dist-info')
            filename = f'{stem}-{tag}.whl'
        target = destination / filename
        if not target.exists():
            os.link(path, target)
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for block in iter(lambda: source.read(1024*1024), b''):
                digest.update(block)
        entries.append(dict(filename=filename, bytes=path.stat().st_size, sha256=digest.hexdigest()))
    except (OSError, zipfile.BadZipFile, StopIteration):
        continue
(root/'reports/server_cached_wheels.json').write_text(json.dumps(entries, indent=2))
print(json.dumps(dict(recovered_wheels=len(entries), recovered_bytes=sum(x['bytes'] for x in entries))))
