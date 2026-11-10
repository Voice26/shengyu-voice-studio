#!/usr/bin/env bash
set -euo pipefail
PROJECT=/srv/ai-vocal-clone
cd "$PROJECT"
export PYTHONUNBUFFERED=1
export HTTPS_PROXY=http://127.0.0.1:18791
export HTTP_PROXY=$HTTPS_PROXY
export https_proxy=$HTTPS_PROXY
export http_proxy=$HTTPS_PROXY
export PIP_INDEX_URL=https://pypi.org/simple
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_CACHE_DIR="$PROJECT/.cache/pip"
export UV_CACHE_DIR="$PROJECT/.cache/uv"
mkdir -p .python third_party/RVC-WebUI data/raw reports models audio/output
if [ ! -x .python/python/bin/python3.12 ]; then
  tar -xf .incoming/python312-linux.tar.gz -C .python
fi
if [ ! -x .venv/bin/python ]; then
  .python/python/bin/python3.12 -m venv .venv
fi
PY="$PROJECT/.venv/bin/python"
"$PY" -m pip install --upgrade pip 'setuptools<81' wheel uv
"$PY" -m pip install 'torch==2.7.1+cu128' 'torchaudio==2.7.1+cu128' --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple
"$PY" -c 'from pathlib import Path; s=Path("third_party/RVC-WebUI/requirments_cu128_py312.txt").read_text(); Path("reports/server-requirements.txt").write_text(s.replace("https://mirrors.pku.edu.cn/pypi/simple", "https://pypi.org/simple"))'
"$PY" -m pip install -r reports/server-requirements.txt 'huggingface_hub>=0.34,<1.0' imageio-ffmpeg
FFMPEG=$("$PY" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
ln -sfn "$FFMPEG" .venv/bin/ffmpeg
"$PY" -m pip check
"$PY" -m pip freeze > reports/server-requirements.lock.txt
"$PY" -c 'import torch, json, platform; assert torch.cuda.is_available(); a=torch.randn((1024,1024),device="cuda"); b=a@a; torch.cuda.synchronize(); x={"python":platform.python_version(),"torch":torch.__version__,"cuda":torch.version.cuda,"available":True,"gpu":torch.cuda.get_device_name(0),"vram_bytes":torch.cuda.get_device_properties(0).total_memory,"capability":torch.cuda.get_device_capability(0),"matmul_passed":True}; print(json.dumps(x))' > reports/server_environment.json
echo SETUP_COMPLETED
