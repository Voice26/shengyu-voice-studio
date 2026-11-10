"""Verify and record the completed private server experiment artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess

import faiss
import torch

root = Path(__file__).resolve().parents[1]
reports = root/'reports'
status = json.loads((reports/'server_job_status.json').read_text())
assert status['stage'] == 'completed', status
model = Path(status['model'])
index_path = Path(status['index'])
output = Path(status['output'])
for path in (model, index_path, output):
    path.resolve().relative_to(root.resolve())
metadata = torch.load(model, map_location='cpu', weights_only=True)
assert metadata['version'] == 'v2' and int(metadata['f0']) == 1
index = faiss.read_index(str(index_path))
assert index.d == 768 and index.ntotal > 0
files = [model, index_path, output/'holdout_input.wav', output/'holdout_converted.wav',
         root/'third_party/RVC-WebUI/logs/gtsinger_zh_alto/config.json']
entries = []
for path in files:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024), b''):
            digest.update(block)
    entries.append(dict(path=str(path.relative_to(root)), filename=path.name,
                        bytes=path.stat().st_size, sha256=digest.hexdigest()))
result = dict(status='verified', model_version=metadata['version'], use_f0=metadata['f0'],
              sample_rate=metadata['config'][-1], trained_speaker_id=0,
              index_dimensions=index.d, index_vectors=index.ntotal, artifacts=entries)
(reports/'server_artifact_manifest.json').write_text(json.dumps(result, indent=2))
used = int(subprocess.check_output(['du', '-sb', str(root)], text=True).split()[0])
(reports/'server_disk_usage.json').write_text(json.dumps(dict(bytes=used), indent=2))
subprocess.run([str(root/'.venv/bin/python'), str(root/'scripts/summarize_server_run.py')], check=True)
print(json.dumps(result, indent=2))
