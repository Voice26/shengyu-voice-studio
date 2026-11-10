#!/usr/bin/env bash
set -euo pipefail
PROJECT=/srv/ai-vocal-clone
cd "$PROJECT"
export PYTHONUNBUFFERED=1
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_CACHE_DIR="$PROJECT/.cache/pip"
export TMPDIR="$PROJECT/.cache/tmp"
mkdir -p "$TMPDIR"
PY="$PROJECT/.venv/bin/python"
"$PY" -m pip install --no-index --find-links "$PROJECT/wheelhouse" --no-build-isolation -r configs/server-offline-requirements.txt
FFMPEG=$("$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
ln -sfn "$FFMPEG" .venv/bin/ffmpeg
"$PY" -m pip check
"$PY" -m pip freeze > reports/server-requirements.lock.txt
"$PY" -c 'import torch,json,platform; assert torch.cuda.is_available(); a=torch.randn((1024,1024),device="cuda"); b=a@a; torch.cuda.synchronize(); x={"python":platform.python_version(),"torch":torch.__version__,"cuda":torch.version.cuda,"available":True,"gpu":torch.cuda.get_device_name(0),"vram_bytes":torch.cuda.get_device_properties(0).total_memory,"capability":torch.cuda.get_device_capability(0),"matmul_passed":True}; print(json.dumps(x))' > reports/server_environment.json
echo SETUP_COMPLETED_OFFLINE
