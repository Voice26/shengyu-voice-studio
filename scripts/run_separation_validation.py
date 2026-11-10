"""Exercise the running local API and retain reproducible integration evidence."""
import argparse
import json
from pathlib import Path
import shutil
import time
from urllib.parse import quote

import numpy as np
import requests
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'audio/output/separation_tuning_20261107'
REPORT = ROOT/'reports/separation_validation.json'
API = 'http://127.0.0.1:7866'
HEADERS = {'X-Voice-Studio':'1'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=['public_song', 'public_male', 'personal_song'], required=True)
    args = parser.parse_args()
    settings = dict(source_type='song', pitch_mode='auto', pitch=0, index_rate=.75,
                    protect=.33, rms_mix_rate=1, pause_cleanup=True)
    if args.case == 'public_song':
        file = OUTPUT/'synthetic_song.wav'
        response = requests.post(API+'/api/uploads', data=file.read_bytes(),
            headers={**HEADERS, 'X-Filename':quote('验证用带伴奏歌曲.wav')}, timeout=60)
        response.raise_for_status()
        payload = dict(upload_id=response.json()['id'])
    elif args.case == 'public_male':
        settings['source_type'] = 'vocals'
        payload = dict(sample_id='male')
    else:
        # Explicitly authorized recording and the same destination host as the previous tuning.
        previous = json.loads((ROOT/'.platform/jobs/ef8fc0efc1da4315828839d5bbff0e4b/job.json').read_text(encoding='utf-8'))
        settings.update(previous['settings'])
        settings.update(source_type='song', pitch_mode='auto', pitch=0)
        payload = dict(upload_id=previous['input_url'].rsplit('/', 1)[-1])
    response = requests.post(API+'/api/jobs', json=dict(**payload, settings=settings), headers=HEADERS, timeout=15)
    response.raise_for_status()
    job = response.json()
    print(json.dumps(dict(case=args.case, job_id=job['id'])), flush=True)
    deadline = time.monotonic()+1850
    last = None
    while time.monotonic() < deadline:
        response = requests.get(API+'/api/jobs/'+job['id'], timeout=15)
        response.raise_for_status()
        job = response.json()
        if job['status'] != last:
            print(json.dumps(dict(status=job['status'], message=job['message']), ensure_ascii=False), flush=True)
            last = job['status']
        if last in ('completed', 'failed'):
            break
        time.sleep(2.5)
    if job['status'] != 'completed':
        raise RuntimeError(json.dumps(job, ensure_ascii=False))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    checks = {}
    for stem in ('source', 'result', 'instrumental', 'mix', 'comparison'):
        file = ROOT/'.platform/jobs'/job['id']/(stem+'.wav')
        if not file.is_file():
            continue
        out = OUTPUT/(args.case+'_'+stem+'.wav')
        shutil.copy2(file, out)
        audio, sr = sf.read(str(out), dtype='float32', always_2d=True)
        checks[stem] = dict(seconds=len(audio)/sr, frames=len(audio), channels=audio.shape[1],
                            sample_rate=sr, finite=bool(np.isfinite(audio).all()),
                            peak=float(np.max(np.abs(audio))), clipping_fraction=float(np.mean(np.abs(audio) >= .9995)))
        assert np.isfinite(audio).all() and sr == 40000
        assert checks[stem]['clipping_fraction'] == 0
    assert checks['source']['frames'] == checks['result']['frames']
    if settings['source_type'] == 'song':
        assert checks['mix']['frames'] == checks['source']['frames'] == checks['instrumental']['frames']
        assert checks['mix']['channels'] == checks['instrumental']['channels'] == 2
    report = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.is_file() else {}
    report[args.case] = dict(job_id=job['id'], elapsed_seconds=job['elapsed_seconds'],
                             settings=settings, report=job['report'], audio_checks=checks)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report[args.case], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
