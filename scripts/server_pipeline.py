"""Run the pinned RVC experiment on the authorized Linux GPU server."""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RVC = ROOT / 'third_party/RVC-WebUI'
PY = ROOT / '.venv/bin/python'
REPORTS = ROOT / 'reports'
EXP = 'gtsinger_zh_alto'
MODEL_REVISION = 'e6d0c1a17da07c33557852f9dfa2bd44cc75737d'
ENV = {**os.environ, 'PATH': str(PY.parent) + ':' + os.environ.get('PATH', ''),
       'PYTHONPATH': str(RVC), 'PYTHONUNBUFFERED': '1', 'CUDA_VISIBLE_DEVICES': '0',
       'OMP_NUM_THREADS': '8', 'OPENBLAS_NUM_THREADS': '8', 'MKL_NUM_THREADS': '8',
       'NUMBA_NUM_THREADS': '8', 'MPLBACKEND': 'Agg', 'HF_HUB_DISABLE_XET': '1',
       'HF_HOME': str(ROOT / '.cache/huggingface'), 'HF_HUB_DOWNLOAD_TIMEOUT': '120',
       'HTTPS_PROXY': 'http://127.0.0.1:18791', 'HTTP_PROXY': 'http://127.0.0.1:18791',
       'https_proxy': 'http://127.0.0.1:18791', 'http_proxy': 'http://127.0.0.1:18791',
       'NO_PROXY': 'localhost,127.0.0.1', 'TMPDIR': str(ROOT / '.cache/tmp')}
(ROOT / '.cache/tmp').mkdir(parents=True, exist_ok=True)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def state(stage, **extra):
    value = dict(stage=stage, updated_at=datetime.now(timezone.utc).isoformat(), **extra)
    save(REPORTS / 'server_job_status.json', value)
    print(json.dumps(value, ensure_ascii=False), flush=True)


def run(name, args, cwd=RVC, allow_failure=False):
    log_path = REPORTS / f'{name}.log'
    samples, stop = [], threading.Event()
    process = None
    def belongs_to_job(pid):
        seen = set()
        while pid > 1 and pid not in seen:
            if pid == process.pid:
                return True
            seen.add(pid)
            try:
                status = Path(f'/proc/{pid}/status').read_text()
                pid = int(next(line.split()[1] for line in status.splitlines() if line.startswith('PPid:')))
            except (OSError, StopIteration, ValueError):
                return False
        return False
    def sample():
        while not stop.is_set():
            try:
                card = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True, timeout=5)
                card_memory, utilization = [float(x.strip()) for x in card.strip().split(',')]
                text = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True, timeout=5)
                memory, pids = 0, {process.pid}
                for line in text.splitlines():
                    pid, used = line.split(',')
                    pid = int(pid)
                    if belongs_to_job(pid):
                        memory += float(used)
                        pids.add(pid)
                pss_kib = 0
                for pid in pids:
                    try:
                        status = Path(f'/proc/{pid}/smaps_rollup').read_text()
                        pss_kib += int(next(line.split()[1] for line in status.splitlines() if line.startswith('Pss:')))
                    except (OSError, StopIteration, ValueError):
                        pass
                samples.append((memory, utilization, pss_kib/1024, card_memory))
            except Exception:
                pass
            stop.wait(1)
    started = time.monotonic()
    with log_path.open('w', encoding='utf-8') as log:
        process = subprocess.Popen([str(x) for x in args], cwd=cwd, env=ENV, stdout=log, stderr=subprocess.STDOUT)
        monitor = threading.Thread(target=sample, daemon=True)
        monitor.start()
        process.wait()
    stop.set()
    monitor.join(timeout=6)
    result = dict(name=name, exit_code=process.returncode, elapsed_seconds=time.monotonic()-started,
                  peak_gpu_mib=max((s[0] for s in samples), default=0),
                  peak_host_pss_mib=max((s[2] for s in samples), default=0),
                  peak_card_total_mib=max((s[3] for s in samples), default=0),
                  gpu_memory_scope='Training subprocess and descendants, excludes unrelated jobs',
                  mean_gpu_utilization=statistics.mean(s[1] for s in samples) if samples else 0,
                  log=str(log_path.relative_to(ROOT)))
    save(REPORTS / f'{name}.metrics.json', result)
    if process.returncode and not allow_failure:
        raise RuntimeError(f'{name} failed ({process.returncode}); see {log_path}')
    return result


def train_args(experiment, batch, epochs, save_every, small):
    return [PY, '-m', 'train.train', '-e', experiment, '-sr', '40k', '-f0', '1',
            '-bs', batch, '-g', '0', '-te', epochs, '-se', save_every,
            '-pg', 'assets/pretrained_v2/f0G40k.pth', '-pd', 'assets/pretrained_v2/f0D40k.pth',
            '-l', '1', '-c', '0', '-sw', small, '-v', 'v2']


def epoch_times(text):
    durations = []
    for value in re.findall(r'====>[^\n]*?\((\d+:\d+:\d+(?:\.\d+)?)\)', text):
        hour, minute, second = map(float, value.split(':'))
        durations.append(hour * 3600 + minute * 60 + second)
    return durations


def prepare_assets():
    required = ['assets/hubert_base/config.json', 'assets/hubert_base/preprocessor_config.json',
                'assets/hubert_base/pytorch_model.bin', 'assets/rmvpe/rmvpe.pt',
                'assets/pretrained_v2/f0G40k.pth', 'assets/pretrained_v2/f0D40k.pth',
                'logs/mute/0_gt_wavs/mute40k.wav', 'logs/mute/3_feature768/mute.npy',
                'logs/mute/2a_f0/mute.wav.npy', 'logs/mute/2b-f0nsf/mute.wav.npy']
    missing = [name for name in required if not (RVC/name).is_file()]
    if missing:
        raise FileNotFoundError(f'Upload the locally downloaded official assets first: {missing}')
    ENV['HF_HUB_OFFLINE'] = '1'
    for name in ('HTTPS_PROXY', 'HTTP_PROXY', 'https_proxy', 'http_proxy'):
        ENV.pop(name, None)
    save(REPORTS/'server_assets_verification.json', dict(revision=MODEL_REVISION, files=required, offline=True))


def backup():
    destination = ROOT / 'models' / EXP
    destination.mkdir(parents=True, exist_ok=True)
    for file in (RVC / 'logs' / EXP).rglob('*'):
        if file.is_file() and (file.suffix in ('.pth', '.index', '.json', '.txt', '.log') or file.name.startswith('events')):
            target = destination / 'logs' / file.relative_to(RVC / 'logs' / EXP)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
    for file in (RVC / 'assets/weights').glob(f'{EXP}*.pth'):
        shutil.copy2(file, destination / file.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batches', type=int, nargs='+', default=[16, 32, 64, 128])
    parser.add_argument('--benchmark-only', action='store_true')
    args = parser.parse_args()
    state('waiting_for_environment')
    while not (REPORTS / 'server_environment.json').exists():
        active = subprocess.run(['tmux', 'has-session', '-t', 'rvc-setup'], capture_output=True).returncode == 0
        if not active:
            raise RuntimeError('Environment setup stopped before completion; check server_setup.log')
        time.sleep(10)
    state('compatibility_check')
    # Upstream logging uses FigureCanvasAgg.tostring_rgb, removed in 3.10.
    run('server_compatibility', [PY, '-c', "from importlib.metadata import version; from packaging.version import Version; assert Version(version('matplotlib')) < Version('3.10'); assert version('torch') == '2.7.1+cu128'; assert version('torchaudio') == '2.7.1+cu128'; print('Pinned compatibility checks passed')"], cwd=ROOT)
    run('server_pip_check', [PY, '-m', 'pip', 'check'], cwd=ROOT)
    with (REPORTS / 'server-requirements.lock.txt').open('w') as file:
        subprocess.run([PY, '-m', 'pip', 'freeze'], stdout=file, env=ENV, check=True)
    state('verifying_data')
    manifest = json.loads((REPORTS / 'download_manifest.json').read_text(encoding='utf-8'))
    verified = 0
    for entry in manifest['files']:
        path = ROOT / 'data/raw/GTSinger' / entry['path']
        if not path.is_file() or path.stat().st_size != entry['size']:
            raise RuntimeError(f'Missing or size mismatch after transfer: {entry["path"]}')
        if entry.get('sha256'):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != entry['sha256']:
                raise RuntimeError(f'Transfer SHA-256 mismatch: {entry["path"]}')
            verified += 1
    save(REPORTS / 'server_transfer_verification.json', dict(verified_wav_sha256=verified))
    run('server_prepare_data', [PY, ROOT / 'scripts/prepare_gtsinger_dataset.py', '--apply'], cwd=ROOT)
    state('downloading_pretrained_assets')
    prepare_assets()
    state('preprocessing')
    for directory in ('assets/weights', 'assets/indices', 'logs'):
        (RVC/directory).mkdir(parents=True, exist_ok=True)
    experiment = RVC / 'logs' / EXP
    experiment.mkdir(parents=True, exist_ok=True)
    train = ROOT / 'data/processed/ZH-Alto-1/rvc_train'
    marker = REPORTS / 'server_features_completed.json'
    if not marker.exists():
        run('server_preprocess', [PY, '-m', 'train.preprocess', train, 40000, 8, experiment, 'False', '3.7'])
        state('extracting_rmvpe')
        run('server_f0', [PY, '-m', 'train.dataset.extract_f0', 'cuda', 1, 0, 0, experiment, 'true'])
        state('extracting_hubert')
        run('server_features', [PY, '-m', 'train.dataset.extract_hubert_feature', 'cuda:0', 1, 0, 0, experiment, 'v2', 'true'])
        run('server_prepare_config', [PY, ROOT/'scripts/prepare_rvc_config.py', '--rvc-dir', RVC, '--experiment', EXP])
        save(marker, dict(experiment=EXP, wav_count=len(list((experiment/'0_gt_wavs').glob('*.wav')))))
    results = []
    for batch in args.batches:
        state('benchmarking', batch_size=batch)
        name = f'bench_compute_b{batch}'
        folder = RVC/'logs'/name
        folder.mkdir(exist_ok=True)
        for filename in ('config.json', 'filelist.txt'):
            shutil.copy2(experiment/filename, folder/filename)
        metrics_path = REPORTS/f'{name}.metrics.json'
        if metrics_path.exists():
            result = json.loads(metrics_path.read_text())
        else:
            result = run(name, train_args(name, batch, 3, 100, 0), allow_failure=True)
        text = (REPORTS/f'{name}.log').read_text(errors='replace')
        result.update(batch_size=batch, epoch_seconds=epoch_times(text))
        if result['exit_code'] == 0 and result['epoch_seconds']:
            result['steady_epoch_seconds'] = statistics.median(result['epoch_seconds'][1:] or result['epoch_seconds'])
            result['timing_scope'] = 'Median warm epochs, no large checkpoint writes during the benchmark'
        results.append(result)
        save(REPORTS/'server_batch_benchmarks.json', results)
    valid = [x for x in results if x.get('steady_epoch_seconds') and x['peak_gpu_mib'] < 82000]
    if not valid:
        raise RuntimeError('No benchmark succeeded; inspect bench_gtsinger logs')
    fastest = min(valid, key=lambda x: x['steady_epoch_seconds'])
    # Choose the smaller batch within 10% of best time to preserve more updates.
    chosen = min((x for x in valid if x['steady_epoch_seconds'] <= fastest['steady_epoch_seconds'] * 1.1), key=lambda x:x['batch_size'])
    budget = dict(epochs=args.epochs, chosen_batch_size=chosen['batch_size'],
                  measured_epoch_seconds=chosen['steady_epoch_seconds'],
                  peak_gpu_mib=chosen['peak_gpu_mib'],
                  peak_host_pss_mib=chosen.get('peak_host_pss_mib'),
                  estimated_training_hours_low=chosen['steady_epoch_seconds']*args.epochs/3600,
                  estimated_training_hours_high=chosen['steady_epoch_seconds']*args.epochs/3600*1.35,
                  monetary_cost='User-owned server; no hourly price supplied. No paid cloud resource created.',
                  benchmarks=results)
    save(REPORTS/'server_training_budget.json', budget)
    if args.benchmark_only:
        state('benchmarks_completed', **{k:v for k,v in budget.items() if k!='benchmarks'})
        return
    state('training', **{k:v for k,v in budget.items() if k!='benchmarks'})
    try:
        run('server_training', train_args(EXP, chosen['batch_size'], args.epochs, 10, 1))
    finally:
        backup()
    state('building_index')
    run('server_index', [PY, '-m', 'train.train_index', EXP, 'v2', 'assets/indices', 8, 'single'])
    backup()
    state('testing_holdout')
    # Technical smoke test on unseen target audio; this is not a cross-speaker quality claim.
    import soundfile as sf
    candidates = sorted((ROOT/'data/processed/ZH-Alto-1/holdout_reference').glob('*.wav'))
    reference = max(candidates, key=lambda x: sf.info(str(x)).duration)
    output = ROOT/'audio/output/server_public'
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(reference, output/'holdout_input.wav')
    model = RVC/'assets/weights'/f'{EXP}.pth'
    indices = list(experiment.glob('added_*.index'))
    if not model.is_file() or not indices:
        raise RuntimeError('Final model or index is missing')
    run('server_inference', [PY, '-m', 'infer.cli', '--model', model, '--input', output/'holdout_input.wav',
                            '--output', output/'holdout_converted.wav', '--pitch', 0, '--f0-method', 'rmvpe',
                            '--index', indices[0], '--index-rate', 0.75, '--overwrite'])
    source_info = sf.info(str(output/'holdout_input.wav'))
    result_info = sf.info(str(output/'holdout_converted.wav'))
    import numpy as np
    waveform, rate = sf.read(str(output/'holdout_converted.wav'))
    assert np.isfinite(waveform).all() and result_info.duration > 0
    save(REPORTS/'server_inference_smoke_test.json', dict(test_type='heldout-target technical reconstruction',
         reference=str(reference.relative_to(ROOT)), input_seconds=source_info.duration,
         output_seconds=result_info.duration, sample_rate=rate, peak=float(np.max(np.abs(waveform))),
         subjective_quality='Not evaluated; needs listening', cross_speaker_conversion='Not evaluated'))
    state('completed', model=str(model), index=str(indices[0]), output=str(output))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        import traceback
        traceback.print_exc()
        state('failed', error=f'{type(exc).__name__}: {exc}')
        sys.exit(1)
