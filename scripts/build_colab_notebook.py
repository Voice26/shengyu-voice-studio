"""Build the project Colab notebook with only Python standard-library tools."""
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(source):
    cells.append(dict(cell_type="markdown", metadata={}, source=dedent(source).strip() + "\n"))


def code(source):
    cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=dedent(source).strip() + "\n"))


md("""
# GTSinger 单歌手 RVC 训练框架（Colab）
环境要求为 Python 3.12 和 CUDA GPU。按顺序执行单元格，先检查运行时和数据划分，再开始训练。

1. 本地下载完成并审计后，运行 `scripts/prepare_gtsinger_dataset.py --holdout-song 歌名 --apply`。
2. 将 `data/processed/`、`scripts/prepare_rvc_config.py`、本 Notebook 上传到自己的 Google Drive `ai-vocal-clone/` 中。
3. 在 Colab 选择 GPU，确认 Python 3.12。先执行环境、数据检查，再逐步执行预处理和训练。

数据集为 CC BY-NC-SA 4.0 并附额外条款，使用前阅读 `docs/dataset_license.md`。默认实验仅本地/私人验证，不公开模型和音频。
""")
code("""
import os, sys, json, subprocess, shutil, csv
from pathlib import Path
assert sys.version_info[:2] == (3, 12), '固定 RVC 版本要求 Python 3.12；请切换兼容的 Colab 运行时后再继续。'
subprocess.run(['nvidia-smi'], check=True)
from google.colab import drive
drive.mount('/content/drive')

PROJECT = Path('/content/drive/MyDrive/ai-vocal-clone')
SPEAKER = 'ZH-Alto-1'
EXP = 'gtsinger_zh_alto'
RVC = Path('/content/RVC-WebUI')
TRAIN = Path('/content/rvc_training')
SAVE = PROJECT / 'models' / EXP
COMMIT = '81eed5e8f68b6bed1789f682fe78cdd324495afc'
MODEL_REVISION = 'e6d0c1a17da07c33557852f9dfa2bd44cc75737d'
CUDA_FLAVOR = 'cu118'  # T4/L4/A100 常用；Blackwell/RTX50 系改为 cu128，并检查驱动。
BATCH_SIZE = 4  # 初始值；显存不足改 2 或 1，禁止开启显存缓存。
EPOCHS = 100
SAVE_EVERY = 5
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['RVC_CUDA_GRAPH'] = '0'  # Keep variable-length graph caches out of 16GB Colab GPUs.

def run(*args):
    subprocess.run([str(x) for x in args], cwd=RVC, check=True,
                   env={**os.environ, 'PYTHONPATH': str(RVC)})
""")
md("## 固定官方源码与安装依赖\n此单元格需要网络并安装大型 GPU 依赖，只在 Colab 中手动运行。采用官方两阶段方案。")
code("""
if not RVC.exists():
    subprocess.run(['git', 'clone', 'https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git', str(RVC)], check=True)
run('git', 'checkout', '--detach', COMMIT)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=RVC, text=True).strip() == COMMIT
assert CUDA_FLAVOR in ('cu118', 'cu128')
run('apt-get', 'update', '-qq')
run('apt-get', 'install', '-y', '-qq', 'ffmpeg', 'libsndfile1', 'libportaudio2')
run(sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools<81', 'wheel')
run(sys.executable, '-m', 'pip', 'install', f'torch==2.7.1+{CUDA_FLAVOR}',
    f'torchaudio==2.7.1+{CUDA_FLAVOR}', '--index-url', f'https://download.pytorch.org/whl/{CUDA_FLAVOR}',
    '--extra-index-url', 'https://pypi.org/simple')
# 仅生成依赖副本替换下载源，不改上游文件或包版本。
requirements = (RVC / f'requirments_{CUDA_FLAVOR}_py312.txt').read_text()
requirements = requirements.replace('https://mirrors.pku.edu.cn/pypi/simple', 'https://pypi.org/simple')
Path('/content/rvc-requirements.txt').write_text(requirements)
Path('/content/rvc-constraints.txt').write_text(chr(10).join([
    f'torch==2.7.1+{CUDA_FLAVOR}', f'torchaudio==2.7.1+{CUDA_FLAVOR}', 'matplotlib>=3.8.2,<3.10']))
run(sys.executable, '-m', 'pip', 'install', '-r', '/content/rvc-requirements.txt', '-c', '/content/rvc-constraints.txt')
run(sys.executable, '-m', 'pip', 'check')
""")
code("""
# GPU 检查在独立子进程中执行，避免 Notebook 内核保留旧 Torch 模块。
run(sys.executable, '-c', "import torch; print(torch.__version__, torch.version.cuda); assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory / 2**30)")
SAVE.mkdir(parents=True, exist_ok=True)
environment = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
(SAVE / 'environment.txt').write_text(environment)
""")
md("## 检查并复制单歌手训练集\n只使用本地脚本已生成的平铺训练集，不从原始数据直接训练。留出歌曲、朗读组不得混入。")
code("""
import soundfile as sf
source = PROJECT / 'data/processed' / SPEAKER / 'rvc_train'
manifest_path = PROJECT / 'data/processed/manifest.csv'
assert source.is_dir() and manifest_path.is_file(), '请先上传处理后的训练目录及 manifest.csv'
with manifest_path.open(encoding='utf-8-sig', newline='') as f:
    manifest = list(csv.DictReader(f))
selected = [r for r in manifest if r['usage'] == 'rvc_train']
assert selected and all(r['speaker'] == SPEAKER and r['group'] in ('Control_Group', 'Breathy_Group') for r in selected)
holdout_songs = {r['song'] for r in manifest if r['usage'] == 'holdout_reference'}
assert holdout_songs and not (holdout_songs & {r['song'] for r in selected})
files = sorted(source.glob('*.wav'))
expected = {Path(r['destination']).name for r in selected}
assert {p.name for p in files} == expected, '训练文件与清单不一致'
minutes = sum(sf.info(str(p)).duration for p in files) / 60
assert minutes >= 10, f'有效歌唱只有 {minutes:.2f} 分钟，需要补充数据'
TRAIN.mkdir(exist_ok=True)
assert not ({p.name for p in TRAIN.iterdir()} - expected), 'Colab 训练目录有旧数据；请使用新的运行时'
for p in files:
    shutil.copy2(p, TRAIN / p.name)
print('文件数:', len(files), '分钟:', minutes, '留出歌曲:', sorted(holdout_songs))
(SAVE / 'dataset_manifest.csv').write_bytes(manifest_path.read_bytes())
""")
md("## 获取官方预训练资源\n本机只准备了数据；本单元格在 Colab 下载 HuBERT、RMVPE、40k v2 预训练 G/D 和 mute。")
code("""
run(sys.executable, '-m', 'pip', 'install', 'huggingface_hub>=0.34,<1.0')
from huggingface_hub import snapshot_download, hf_hub_download
model_repo = 'lj1995/VoiceConversionWebUI'
snapshot_download(model_repo, revision=MODEL_REVISION, local_dir=RVC/'assets',
                  allow_patterns=['hubert_base/*', 'pretrained_v2/f0G40k.pth', 'pretrained_v2/f0D40k.pth'], token=False)
hf_hub_download(model_repo, 'rmvpe.pt', revision=MODEL_REVISION, local_dir=RVC/'assets/rmvpe', token=False)
archive = hf_hub_download(model_repo, 'mute.zip', revision=MODEL_REVISION, local_dir='/content/model-downloads', token=False)
import zipfile
with zipfile.ZipFile(archive) as z:
    base = (RVC/'logs').resolve()
    for entry in z.infolist():
        (base / entry.filename).resolve().relative_to(base)
    z.extractall(base)
for path in ('assets/hubert_base/config.json', 'assets/hubert_base/preprocessor_config.json',
             'assets/hubert_base/pytorch_model.bin', 'assets/rmvpe/rmvpe.pt',
             'assets/pretrained_v2/f0G40k.pth', 'assets/pretrained_v2/f0D40k.pth'):
    assert (RVC/path).is_file(), path
""")
md("## 预处理 → RMVPE F0 → HuBERT v2\n以下每个单元格应成功完成后再执行下一个。")
code("""
EXP_DIR = RVC / 'logs' / EXP
EXP_DIR.mkdir(parents=True, exist_ok=True)
for directory in ('assets/weights', 'assets/indices'):
    (RVC/directory).mkdir(parents=True, exist_ok=True)
run(sys.executable, '-m', 'train.preprocess', TRAIN, '40000', '2', EXP_DIR, 'False', '3.7')
assert list((EXP_DIR/'0_gt_wavs').glob('*.wav'))
""")
code("run(sys.executable, '-m', 'train.dataset.extract_f0', 'cuda', '1', '0', '0', EXP_DIR, 'true')")
code("run(sys.executable, '-m', 'train.dataset.extract_hubert_feature', 'cuda:0', '1', '0', '0', EXP_DIR, 'v2', 'true')")
code("""
helper = PROJECT / 'scripts/prepare_rvc_config.py'
assert helper.is_file(), '请上传 prepare_rvc_config.py'
run(sys.executable, helper, '--rvc-dir', RVC, '--experiment', EXP)
params = dict(commit=COMMIT, model_revision=MODEL_REVISION, speaker=SPEAKER,
              sample_rate=40000, version='v2', f0=True, f0_method='rmvpe',
              batch_size=BATCH_SIZE, epochs=EPOCHS, save_every=SAVE_EVERY)
(SAVE/'run_parameters.json').write_text(json.dumps(params, indent=2))
""")
md("## 训练与保存\n此单元格会实际启动 GPU 训练。可先把 EPOCHS 设为 5 检查能否跑通，再调整。显存不足时先降低 BATCH_SIZE。中断后大检查点保留在运行时 logs；下方备份会复制到 Drive。")
code("""
def backup():
    for p in EXP_DIR.rglob('*'):
        if p.is_file() and (p.suffix in ('.pth', '.index', '.json', '.txt', '.log') or p.name.startswith('events')):
            dest = SAVE/'logs'/p.relative_to(EXP_DIR)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    for p in (RVC/'assets/weights').glob(f'{EXP}*.pth'):
        shutil.copy2(p, SAVE/p.name)

try:
    run(sys.executable, '-m', 'train.train', '-e', EXP, '-sr', '40k', '-f0', '1',
        '-bs', str(BATCH_SIZE), '-g', '0', '-te', str(EPOCHS), '-se', str(SAVE_EVERY),
        '-pg', 'assets/pretrained_v2/f0G40k.pth', '-pd', 'assets/pretrained_v2/f0D40k.pth',
        '-l', '1', '-c', '0', '-sw', '1', '-v', 'v2')
finally:
    backup()
""")
code("""
run(sys.executable, '-m', 'train.train_index', EXP, 'v2', 'assets/indices', '2', 'single')
backup()
weights = list(SAVE.glob('*.pth'))
indices = list((SAVE/'logs').glob('added_*.index'))
assert weights and indices, '权重或 added 索引缺失，请检查训练日志'
print('实际生成的权重:', [p.name for p in weights])
print('实际生成的索引:', [p.name for p in indices])
print('保存目录:', SAVE)
""")
md("""
训练后可用 `python -m infer.cli --help` 查看推理参数，用有权使用的其他歌手录音测试音色转换。
Colab 重启后会清空 `/content`。续训前，从 Drive 的 `models/<实验名>/logs/` 恢复检查点和配置，再准备同一训练集的特征。此 Notebook 的续训流程尚未在 Colab 实测。
""")

notebook = dict(nbformat=4, nbformat_minor=5, cells=cells,
                metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3"),
                              language_info=dict(name="python", version="3.12"),
                              accelerator="GPU", colab=dict(provenance=[])))
for index, cell in enumerate(cells):
    cell["id"] = f"rvc-{index:02d}"
    if cell["cell_type"] == "code":
        compile(cell["source"], f"cell-{index}", "exec")
path = ROOT / "notebooks/rvc_public_dataset_training.ipynb"
path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"Generated and syntax-checked {len(cells)} cells: {path}")
