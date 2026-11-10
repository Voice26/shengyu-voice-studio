"""Decode -> optional vocal separation -> pitch analysis -> RVC -> optional remix."""
import argparse
import gc
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

def parameters(data):
    import math
    result = {}
    for key, default, low, high in [('pitch', 0, -12, 12), ('index_rate', .75, 0, 1),
                                   ('protect', .33, 0, .5), ('rms_mix_rate', 1, 0, 1)]:
        value = data.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'Invalid {key}')
        if key == 'pitch' and int(value) != value:
            raise ValueError('Pitch must be an integer')
        result[key] = int(value) if key == 'pitch' else float(value)
    cleanup = data.get('pause_cleanup', True)
    if not isinstance(cleanup, bool):
        raise ValueError('Invalid pause_cleanup')
    result['pause_cleanup'] = cleanup
    for name, default, choices in [('source_type', 'vocals', ('vocals', 'song')),
                                    ('pitch_mode', 'manual', ('manual', 'auto'))]:
        value = data.get(name, default)
        if value not in choices:
            raise ValueError(f'Invalid {name}')
        result[name] = value
    return result


def stage(value):
    print('__STUDIO_STAGE__'+json.dumps(dict(stage=value)), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--probe', action='store_true')
    p.add_argument('--job')
    args = p.parse_args()
    root = args.root.resolve()
    from voice_models import DEFAULT_MODEL, MODELS
    if args.probe:
        import torch
        models = {key: all((root/model[field]).is_file() for field in ('weight', 'index'))
                  for key, model in MODELS.items()}
        print(json.dumps(dict(ready=any(models.values()) and torch.cuda.is_available(), models=models,
                              gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)))
        return
    if not args.job or not re.fullmatch('[0-9a-f]{32}', args.job):
        raise ValueError('Invalid job ID')
    folder = root/'.incoming/platform'/args.job
    request = json.loads((folder/'request.json').read_text(encoding='utf-8'))
    settings = parameters(request['settings'])
    key = request['settings'].get('model_id', DEFAULT_MODEL)
    model = MODELS[key]
    if not all((root/model[field]).is_file() for field in ('weight', 'index')):
        raise FileNotFoundError('Selected target model or index is missing')
    settings['model_id'] = key
    extension = request['extension']
    if extension not in ('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus'):
        raise ValueError('Unsupported audio format')
    import imageio_ffmpeg
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from audio_preparation import applied_pitch, pitch_summary, remix
    from pause_cleanup import HEAD_PADDING_SECONDS, TAIL_PADDING_SECONDS, apply_cleanup, frame_rms, trim_padding

    started = time.monotonic()
    song = settings['source_type'] == 'song'
    decoded = folder/('original_44k.wav' if song else 'source.wav')
    decode_rate = 44100 if song else 40000
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-hide_banner', '-loglevel', 'error',
                    '-y', '-i', str(folder/('input'+extension)), '-vn', '-ac', '2' if song else '1',
                    '-ar', str(decode_rate), '-t', '601', '-c:a', 'pcm_f32le', str(decoded)],
                   check=True, timeout=90)
    info = sf.info(str(decoded))
    if not .2 <= info.duration <= 600:
        raise ValueError('Audio must be between 0.2 seconds and 10 minutes')
    separation_report = dict(enabled=False)
    extra_files = []
    sr = 40000
    voice_reference = None
    music = None
    if song:
        stage('separating')
        subprocess.run([str(root/'.venv/bin/python'), str(root/'scripts/separate_vocals.py'),
                        '--root', str(root), '--job', args.job], check=True, timeout=650)
        vocals, _ = sf.read(str(folder/'vocals_44k.wav'), dtype='float32', always_2d=True)
        instrumental, _ = sf.read(str(folder/'instrumental_44k.wav'), dtype='float32', always_2d=True)
        original, _ = sf.read(str(decoded), dtype='float32', always_2d=True)
        # Resample both stems with the same filter and timeline.
        voice_reference = resample_poly(vocals.mean(axis=1), 400, 441).astype('float32')
        music = resample_poly(instrumental, 400, 441, axis=0).astype('float32')
        original = resample_poly(original, 400, 441, axis=0).astype('float32')
        if len(voice_reference) != len(music) or len(music) != len(original):
            raise ValueError('Separation changed the audio timeline')
        a = voice_reference.copy()
        normalization = min(1., .98/max(float(np.max(np.abs(a))), 1e-8))
        a *= normalization
        sf.write(str(folder/'source.wav'), a, sr, subtype='PCM_16')
        sf.write(str(folder/'instrumental.wav'), music, sr, subtype='PCM_16')
        separation_report = json.loads((folder/'separation.json').read_text(encoding='utf-8'))
        separation_report.update(enabled=True, vocal_input_gain=normalization)
        extra_files = ['instrumental.wav']
    else:
        a, sr = sf.read(str(decoded), dtype='float32')
    source = folder/'source.wav'
    if float(np.max(np.abs(a))) < 1e-6:
        raise ValueError('No audible input audio')

    stage('analyzing')
    rvc = root/'third_party/RVC-WebUI'
    os.environ['RVC_CUDA_GRAPH'] = '0'
    sys.path.insert(0, str(rvc))
    from infer.rmvpe import RMVPE
    import torch
    pitch_model = RMVPE(str(rvc/'assets/rmvpe/rmvpe.pt'), is_half=False,
                        device='cuda' if torch.cuda.is_available() else 'cpu')
    raw_f0 = pitch_model.infer_from_audio(resample_poly(a, 2, 5).astype('float32'), thred=.03)
    np.save(str(folder/'source_voiced.npy'), raw_f0 > 0)
    del pitch_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    profile_file = (root/model['weight']).with_name('voice_profile.json')
    if profile_file.is_file():
        target = json.loads(profile_file.read_text(encoding='utf-8'))
        analysis = pitch_summary(raw_f0, target, frame_rms(a, sr)[0])
    else:
        analysis = dict(available=False, suggested_pitch=0, message='目标音区参考尚未准备，保持手动设置')
    shift = applied_pitch(settings, analysis)
    analysis.update(mode=settings['pitch_mode'], manual_adjustment=settings['pitch'], applied_pitch=shift)

    inference_input = source
    padded_inference = settings['pause_cleanup'] or song
    if padded_inference:
        inference_input = folder/'inference_input.wav'
        padded = np.pad(a, (round(sr*HEAD_PADDING_SECONDS), round(sr*TAIL_PADDING_SECONDS)))
        sf.write(str(inference_input), padded, sr, subtype='FLOAT')
    env = {**os.environ, 'PYTHONPATH':str(rvc), 'RVC_CUDA_GRAPH':'0', 'HF_HUB_OFFLINE':'1',
           'OMP_NUM_THREADS':'8', 'OPENBLAS_NUM_THREADS':'8', 'MKL_NUM_THREADS':'8',
           'PATH':str(root/'.venv/bin')+':'+os.environ.get('PATH', '')}
    raw_result = folder/'inference_raw.wav'
    stage('converting')
    command = [str(root/'.venv/bin/python'), '-m', 'infer.cli', '--model', str(root/model['weight']),
               '--input', str(inference_input), '--output', str(raw_result), '--speaker-id', '0',
               '--pitch', str(shift), '--f0-method', 'rmvpe', '--index', str(root/model['index']),
               '--index-rate', str(settings['index_rate']), '--protect', str(settings['protect']),
               '--rms-mix-rate', str(settings['rms_mix_rate']), '--overwrite']
    subprocess.run(command, cwd=rvc, env=env, check=True, timeout=720)
    b, rate = sf.read(str(raw_result), dtype='float32')
    if not np.isfinite(b).all() or len(b) == 0 or rate != sr:
        raise ValueError('Output audio failed validation')
    if padded_inference:
        b = trim_padding(b, len(a), sr)
    cleanup_report = dict(enabled=False)
    if settings['pause_cleanup']:
        sf.write(str(folder/'before_pause_cleanup.wav'), b, sr, subtype='PCM_16')
        b, cleanup_report = apply_cleanup(a, b, sr, voiced=raw_f0 > 0)
        cleanup_report.update(enabled=True, head_context_seconds=HEAD_PADDING_SECONDS,
                              tail_context_seconds=TAIL_PADDING_SECONDS)
    if abs(len(a)-len(b))/sr > .5:
        raise ValueError('Output duration failed validation')
    result = folder/'result.wav'
    sf.write(str(result), b, rate, subtype='PCM_16')
    if float(np.sqrt(np.mean(b.astype('float64')**2))) < 1e-6:
        raise ValueError('Output audio is silent; check the input recording')

    mixing_report = dict(enabled=False)
    if song:
        stage('mixing')
        mixed, mixing_report = remix(b, voice_reference, music)
        sf.write(str(folder/'mix.wav'), mixed, rate, subtype='PCM_16')
        mixing_report['enabled'] = True
        extra_files.append('mix.wav')
    matched = [x*(.08/max(float(np.sqrt(np.mean(x.astype('float64')**2))), 1e-8)) for x in (a, b)]
    comparison = np.concatenate([matched[0], np.zeros(sr, dtype='float32'), matched[1]])
    comparison *= min(1, .95/max(float(np.max(np.abs(comparison))), 1e-8))
    sf.write(str(folder/'comparison.wav'), comparison, sr, subtype='PCM_16')
    report = dict(sample_rate=rate, input_seconds=len(a)/sr, output_seconds=len(b)/rate,
                  elapsed_seconds=round(time.monotonic()-started, 2), peak=float(np.max(np.abs(b))),
                  clipping_fraction=float(np.mean(np.abs(b) >= .9995)), settings=settings,
                  pause_cleanup=cleanup_report, pitch_analysis=analysis, separation=separation_report,
                  mixing=mixing_report, extra_files=extra_files,
                  comparison='Source vocals, 1 s silence, converted vocals; matched RMS')
    (folder/'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
