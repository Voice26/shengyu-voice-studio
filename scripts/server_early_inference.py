"""CPU smoke test of the saved epoch-10 model on an unseen target-song clip."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
import soundfile as sf

root = Path(__file__).resolve().parents[1]
rvc = root/'third_party/RVC-WebUI'
python = root/'.venv/bin/python'
models = sorted((root/'models/gtsinger_zh_alto').glob('gtsinger_zh_alto_e10_*.pth'))
assert models, 'Epoch-10 checkpoint has not been saved'
references = list((root/'data/processed/ZH-Alto-1/holdout_reference').glob('*.wav'))
reference = max(references, key=lambda p: sf.info(str(p)).duration)
output = root/'audio/output/server_public_e10'
output.mkdir(parents=True, exist_ok=True)
shutil.copy2(reference, output/'holdout_input.wav')
env = {**os.environ, 'CUDA_VISIBLE_DEVICES':'', 'RVC_CUDA_GRAPH':'0',
       'PYTHONPATH':str(rvc), 'PATH':str(python.parent)+':'+os.environ.get('PATH',''),
       'HF_HUB_OFFLINE':'1', 'OMP_NUM_THREADS':'8', 'OPENBLAS_NUM_THREADS':'8', 'MKL_NUM_THREADS':'8'}
subprocess.run([str(python), '-m', 'infer.cli', '--model', str(models[-1]),
                '--input', str(output/'holdout_input.wav'), '--output', str(output/'holdout_converted.wav'),
                '--index-rate', '0', '--pitch', '0', '--f0-method', 'rmvpe', '--overwrite'],
               cwd=rvc, env=env, check=True)
waveform, rate = sf.read(str(output/'holdout_converted.wav'))
assert np.isfinite(waveform).all() and len(waveform) > 0
result = dict(status='passed', epoch=10, device='cpu', index_rate=0,
              test_type='Held-out target-song technical reconstruction; cross-speaker quality not evaluated',
              reference=str(reference.relative_to(root)), input_seconds=sf.info(str(reference)).duration,
              output_seconds=len(waveform)/rate, sample_rate=rate, peak=float(np.max(np.abs(waveform))),
              subjective_quality='Not evaluated; requires listening', output=str(output.relative_to(root)))
(root/'reports/server_early_inference.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False))
