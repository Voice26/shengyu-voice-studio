"""Loopback-only, no-login UI and serial SSH conversion queue. No new packages."""
import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import logging
import math
import mimetypes
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlsplit
import uuid
import webbrowser
from scripts.voice_models import DEFAULT_MODEL, MODELS

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).parent/'static'
EXTENSIONS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus'}
ACTIVE = {'queued', 'uploading', 'separating', 'analyzing', 'converting', 'mixing', 'downloading'}
SAMPLES = {
    'male': dict(name='男声 · 平凡的一天', subtitle='中文 / ZH-Tenor-1', path='audio/input/cross_speaker/male_zh_tenor_1.wav'),
    'female': dict(name='女声 · Safe and Sound', subtitle='英文 / EN-Alto-1', path='audio/input/cross_speaker/female_en_alto_1.wav'),
    'target': dict(name='目标女声 · 水星记', subtitle='真实录音 / ZH-Alto-1', path='audio/output/server_public/holdout_input.wav'),
}


class APIError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def validate_settings(data):
    if not isinstance(data, dict):
        raise APIError('换声参数格式不正确')
    model_id = data.get('model_id', DEFAULT_MODEL)
    if not isinstance(model_id, str) or model_id not in MODELS:
        raise APIError('找不到选定的目标音色')
    output = dict(model_id=model_id)
    for key, default, low, high in [('pitch', 0, -12, 12), ('index_rate', .75, 0, 1),
                                   ('protect', .33, 0, .5), ('rms_mix_rate', 1, 0, 1)]:
        value = data.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
            raise APIError('换声参数超出允许范围：'+key)
        if key == 'pitch' and int(value) != value:
            raise APIError('音高需要填写整数半音')
        output[key] = int(value) if key == 'pitch' else float(value)
    cleanup = data.get('pause_cleanup', True)
    if not isinstance(cleanup, bool):
        raise APIError('静音优化开关格式不正确')
    output['pause_cleanup'] = cleanup
    for name, default, choices in [('source_type', 'vocals', ('vocals', 'song')),
                                   ('pitch_mode', 'manual', ('manual', 'auto'))]:
        value = data.get(name, default)
        if value not in choices:
            raise APIError('不支持的处理选项：'+name)
        output[name] = value
    return output


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{32}', value)


def audio_info(path):
    import soundfile as sf
    try:
        info = sf.info(str(path))
        return dict(seconds=info.duration, sample_rate=info.samplerate, channels=info.channels)
    except (RuntimeError, ValueError):
        return dict(seconds=None, sample_rate=None, channels=None)


class Studio:
    def __init__(self, config, state_dir=None):
        self.config = config
        self.state_dir = Path(state_dir or ROOT/'.platform')
        self.uploads_dir = self.state_dir/'uploads'
        self.jobs_dir = self.state_dir/'jobs'
        for folder in (self.uploads_dir, self.jobs_dir):
            folder.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.queue = ThreadPoolExecutor(max_workers=1, thread_name_prefix='conversion')
        self.jobs = {}
        for file in self.jobs_dir.glob('*/job.json'):
            try:
                item = json.loads(file.read_text(encoding='utf-8'))
                if not valid_id(item.get('id')):
                    continue
                if item['status'] in ACTIVE:
                    item.update(status='failed', message='上次服务关闭时任务中断，请重新转换', updated_at=now())
                    save_json(file, item)
                self.jobs[item['id']] = item
            except (ValueError, KeyError, OSError):
                logging.exception('Cannot restore job %s', file)
        self.health_lock = threading.Lock()
        self.health_cache = None
        self.health_at = 0

    def ssh(self, command, timeout=30, log=None):
        return self.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                         '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
                         self.config['ssh_host'], command], timeout=timeout, log=log)

    def run(self, args, timeout=120, log=None):
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
                                encoding='utf-8', errors='replace',
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if log:
            with log.open('a', encoding='utf-8') as stream:
                stream.write(result.stdout+'\n')
        if result.returncode:
            raise RuntimeError(result.stdout.strip()[-3000:] or f'进程退出：{result.returncode}')
        return result.stdout

    def health(self, refresh=False):
        with self.health_lock:
            if self.health_cache and not refresh and time.monotonic()-self.health_at < 30:
                return self.health_cache
            root = self.config['remote_root']
            command = shlex.join([root+'/.venv/bin/python', root+'/scripts/platform_worker.py', '--root', root, '--probe'])
            try:
                result = json.loads(self.ssh(command, timeout=30).strip().splitlines()[-1])
                result['message'] = 'GPU 已连接' if result['ready'] else '服务器模型、索引或 GPU 尚未就绪'
            except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError):
                result = dict(ready=False, gpu=None, message='无法连接服务器，请检查网络和 SSH 免密连接')
            result.update(host=self.config['ssh_host'], checked_at=now())
            self.health_cache, self.health_at = result, time.monotonic()
            return result

    def samples(self):
        return [dict(id=key, name=value['name'], subtitle=value['subtitle'], url='/api/audio/sample/'+key,
                     **audio_info(ROOT/value['path'])) for key, value in SAMPLES.items() if (ROOT/value['path']).is_file()]

    def models(self):
        models = []
        for key, model in MODELS.items():
            reference = ROOT/model['reference']
            if not (ROOT/model['weight']).is_file():
                continue
            models.append(dict(id=key, name=model['name'], speaker=model['speaker'], description=model['description'],
                               epochs=model['epochs'], sample_rate=40000, reference_title=model['reference_title'],
                               reference_url='/api/audio/reference/'+key if reference.is_file() else None,
                               reference_seconds=audio_info(reference)['seconds'] if reference.is_file() else 0,
                               pitch_analysis=(ROOT/model['weight']).with_name('voice_profile.json').is_file()))
        return models

    def public_job(self, item):
        output = dict(item)
        if item['status'] == 'completed':
            output['result_url'] = '/api/audio/job/'+item['id']+'/result'
            output['comparison_url'] = '/api/audio/job/'+item['id']+'/comparison'
            output['source_url'] = '/api/audio/job/'+item['id']+'/source'
            for stem in ('instrumental', 'mix'):
                if (self.jobs_dir/item['id']/(stem+'.wav')).is_file():
                    output[stem+'_url'] = '/api/audio/job/'+item['id']+'/'+stem
        return output

    def list_jobs(self):
        with self.lock:
            return [self.public_job(item) for item in sorted(self.jobs.values(), key=lambda x:x['created_at'], reverse=True)[:50]]

    def change_job(self, job_id, **changes):
        with self.lock:
            self.jobs[job_id].update(**changes, updated_at=now())
            save_json(self.jobs_dir/job_id/'job.json', self.jobs[job_id])

    def run_worker(self, command, job_id, log, timeout):
        args = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
                self.config['ssh_host'], command]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   encoding='utf-8', errors='replace', bufsize=1,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        tail = deque(maxlen=30)
        messages = dict(separating='正在分离人声与伴奏', analyzing='正在分析人声音区',
                        converting='正在生成目标人声', mixing='正在合成新的人声与原伴奏')
        def consume():
            with log.open('a', encoding='utf-8') as stream:
                for line in process.stdout:
                    stream.write(line)
                    stream.flush()
                    tail.append(line)
                    if line.startswith('__STUDIO_STAGE__'):
                        try:
                            stage = json.loads(line[len('__STUDIO_STAGE__'):])['stage']
                            if stage in messages:
                                self.change_job(job_id, status=stage, message=messages[stage])
                        except (ValueError, KeyError):
                            pass
        reader = threading.Thread(target=consume, daemon=True)
        reader.start()
        try:
            result = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        finally:
            reader.join(timeout=5)
            if not reader.is_alive():
                process.stdout.close()
        if result:
            raise RuntimeError(''.join(tail)[-3500:] or '服务器处理失败')

    def source(self, data):
        if data.get('sample_id') in ('male', 'female'):
            key = data['sample_id']
            sample = SAMPLES[key]
            file = ROOT/sample['path']
            if not file.is_file():
                raise APIError('示例音频不存在', 404)
            return file, sample['name'], '/api/audio/sample/'+key
        upload_id = data.get('upload_id')
        if not valid_id(upload_id):
            raise APIError('请先上传音频或选择示例')
        metadata = self.uploads_dir/(upload_id+'.json')
        if not metadata.is_file():
            raise APIError('上传记录不存在，请重新上传', 404)
        info = json.loads(metadata.read_text(encoding='utf-8'))
        file = self.uploads_dir/(upload_id+info['extension'])
        if not file.is_file():
            raise APIError('上传的音频不存在', 404)
        return file, info['name'], '/api/audio/upload/'+upload_id

    def create_job(self, data):
        settings = validate_settings(data.get('settings', {}))
        model_id = settings['model_id']
        if not any(model['id'] == model_id for model in self.models()):
            raise APIError('该目标音色暂未就绪', 409)
        file, name, url = self.source(data)
        job_id = uuid.uuid4().hex
        with self.lock:
            if sum(job['status'] in ACTIVE for job in self.jobs.values()) >= 3:
                raise APIError('当前已有 3 个任务，请稍后再试', 429)
            folder = self.jobs_dir/job_id
            folder.mkdir()
            # Snapshot the chosen source so queued jobs are independent of future selections.
            shutil.copy2(file, folder/('input'+file.suffix.lower()))
            item = dict(id=job_id, name=name, status='queued', message='等待转换', created_at=now(),
                        updated_at=now(), settings=settings, input_url=url, extension=file.suffix.lower(),
                        input_info=audio_info(file), model_name=MODELS[model_id]['name'])
            self.jobs[job_id] = item
            save_json(folder/'job.json', item)
            save_json(folder/'request.json', dict(extension=item['extension'], settings=settings))
        self.queue.submit(self.convert, job_id)
        return self.public_job(item)

    def convert(self, job_id):
        folder = self.jobs_dir/job_id
        log = folder/'process.log'
        root, host = self.config['remote_root'], self.config['ssh_host']
        remote = root+'/.incoming/platform/'+job_id
        started = time.monotonic()
        try:
            self.change_job(job_id, status='uploading', message='正在发送音频到 GPU 服务器')
            self.ssh(shlex.join(['mkdir', '-p', remote]), log=log)
            self.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                      str(ROOT/'scripts/platform_worker.py'), str(ROOT/'scripts/pause_cleanup.py'),
                      str(ROOT/'scripts/audio_preparation.py'), str(ROOT/'scripts/separate_vocals.py'), str(ROOT/'scripts/voice_models.py'),
                      host+':'+root+'/scripts/'], log=log)
            self.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                      str(folder/('input'+self.jobs[job_id]['extension'])), str(folder/'request.json'), host+':'+remote+'/'], log=log)
            self.change_job(job_id, status='uploading', message='正在解码音频并准备处理')
            limit = self.config['job_timeout_seconds']
            command = shlex.join(['timeout', '-k', '10', str(limit-20), root+'/.venv/bin/python',
                                  root+'/scripts/platform_worker.py', '--root', root, '--job', job_id])
            self.run_worker(command, job_id, log, timeout=limit)
            self.change_job(job_id, status='downloading', message='正在回传音频并制作试听结果')
            names = ['result.wav', 'source.wav', 'comparison.wav', 'result.json']
            self.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                      *[host+':'+remote+'/'+name for name in names], str(folder)], timeout=600, log=log)
            import numpy as np
            import soundfile as sf
            for name in names[:3]:
                audio, rate = sf.read(str(folder/name), dtype='float32')
                if not len(audio) or rate != 40000 or not np.isfinite(audio).all():
                    raise ValueError('生成的音频校验失败')
            report = json.loads((folder/'result.json').read_text(encoding='utf-8'))
            if report['settings']['model_id'] != self.jobs[job_id]['settings']['model_id']:
                raise ValueError('返回结果与任务选定的音色不一致')
            extras = report.get('extra_files', [])
            if not isinstance(extras, list) or not set(extras) <= {'instrumental.wav', 'mix.wav'}:
                raise ValueError('Invalid output artifact list')
            if extras:
                self.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                          *[host+':'+remote+'/'+name for name in extras], str(folder)], timeout=600, log=log)
                for name in extras:
                    audio, rate = sf.read(str(folder/name), dtype='float32', always_2d=True)
                    if not len(audio) or rate != 40000 or audio.shape[1] != 2 or not np.isfinite(audio).all():
                        raise ValueError('分离或混音音频校验失败')
            self.change_job(job_id, status='completed', message='转换完成', report=report,
                            elapsed_seconds=round(time.monotonic()-started, 1))
        except Exception as error:
            logging.exception('Job %s failed', job_id)
            with log.open('a', encoding='utf-8') as stream:
                stream.write(str(error)+'\n')
            if isinstance(error, subprocess.TimeoutExpired):
                message = '任务超时，请尝试较短的音频或稍后重试'
            elif any(x in str(error).lower() for x in ('permission denied', 'connection', 'timed out', 'no route')):
                message = '服务器连接失败，请检查网络和 SSH 免密连接后重试'
            elif 'Audio must be' in str(error):
                message = '音频时长需在 0.2 秒到 10 分钟之间'
            else:
                message = '音频转换失败，请确认文件可正常播放；详情可查看任务日志'
            self.change_job(job_id, status='failed', message=message, elapsed_seconds=round(time.monotonic()-started, 1))


class Handler(BaseHTTPRequestHandler):
    server_version = 'VoiceStudio/1.0'
    sys_version = ''

    @property
    def studio(self):
        return self.server.studio

    def log_message(self, format, *args):
        logging.info('%s %s', self.client_address[0], format % args)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def allowed_request(self, write=False):
        host = self.headers.get('Host', '')
        port = self.server.server_port
        if host not in (f'localhost:{port}', f'127.0.0.1:{port}'):
            raise APIError('仅支持本机访问', 403)
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{port}', f'http://localhost:{port}'):
            raise APIError('不允许来自其他页面的请求', 403)
        if self.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise APIError('不允许跨站请求', 403)
        if write and self.headers.get('X-Voice-Studio') != '1':
            raise APIError('请求缺少本地页面标识', 403)

    def json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise APIError('需要 JSON 请求')
        length = int(self.headers.get('Content-Length', '0'))
        if not 0 < length <= 16384:
            raise APIError('请求大小不正确')
        try:
            result = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            raise APIError('JSON 请求格式不正确')
        if not isinstance(result, dict):
            raise APIError('请求格式不正确')
        return result

    def send_file(self, path, download=False):
        if not path.is_file():
            raise APIError('文件不存在', 404)
        size = path.stat().st_size
        start, end, code = 0, size-1, 200
        range_header = self.headers.get('Range')
        if range_header:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
            if not match or not any(match.groups()):
                raise APIError('无效的音频范围', 416)
            first, last = match.groups()
            if first:
                start, end = int(first), min(int(last), end) if last else end
            else:
                start = max(0, size-int(last))
            if start > end or start >= size:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(end-start+1))
        self.send_header('Accept-Ranges', 'bytes')
        if code == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        if download:
            self.send_header('Content-Disposition', "attachment; filename*=UTF-8''"+quote(path.name))
        self.end_headers()
        if self.command != 'HEAD':
            with path.open('rb') as stream:
                stream.seek(start)
                remaining = end-start+1
                while remaining:
                    block = stream.read(min(65536, remaining))
                    if not block:
                        break
                    self.wfile.write(block)
                    remaining -= len(block)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            self.allowed_request()
            url = urlsplit(self.path)
            path = unquote(url.path)
            query = parse_qs(url.query)
            if path == '/api/bootstrap':
                models = self.studio.models()
                legacy_model = next((model for model in models if model['id'] == DEFAULT_MODEL), None)
                return self.json(dict(model=legacy_model, models=models, default_model_id=DEFAULT_MODEL,
                                      samples=self.studio.samples(), jobs=self.studio.list_jobs(),
                                      capabilities=dict(separation=(ROOT/'models/separation/model_bs_roformer_ep_368_sdr_12.9628.ckpt').is_file(),
                                                        pitch_analysis=(ROOT/'models/gtsinger_zh_alto/voice_profile.json').is_file()),
                                      limits=dict(max_mb=self.studio.config['max_upload_mb'], max_seconds=self.studio.config['max_audio_seconds']),
                                      execution=dict(mode='ssh', host=self.studio.config['ssh_host'])))
            if path == '/api/health':
                return self.json(self.studio.health(refresh=query.get('refresh') == ['1']))
            if path == '/api/jobs':
                return self.json(dict(jobs=self.studio.list_jobs()))
            match = re.fullmatch(r'/api/jobs/([0-9a-f]{32})(/log)?', path)
            if match:
                with self.studio.lock:
                    item = self.studio.jobs.get(match[1])
                    if not item:
                        raise APIError('任务不存在', 404)
                    if match[2]:
                        file = self.studio.jobs_dir/match[1]/'process.log'
                        return self.json(dict(log=file.read_text(encoding='utf-8')[-10000:] if file.exists() else '暂无日志'))
                    return self.json(self.studio.public_job(item))
            match = re.fullmatch(r'/api/audio/sample/(male|female|target)', path)
            if match:
                return self.send_file(ROOT/SAMPLES[match[1]]['path'], 'download' in query)
            match = re.fullmatch(r'/api/audio/reference/([A-Za-z0-9_-]+)', path)
            if match and match[1] in MODELS:
                return self.send_file(ROOT/MODELS[match[1]]['reference'], 'download' in query)
            match = re.fullmatch(r'/api/audio/upload/([0-9a-f]{32})', path)
            if match:
                file, _, _ = self.studio.source(dict(upload_id=match[1]))
                return self.send_file(file, 'download' in query)
            match = re.fullmatch(r'/api/audio/job/([0-9a-f]{32})/(result|comparison|source|instrumental|mix)', path)
            if match:
                item = self.studio.jobs.get(match[1])
                if not item or item['status'] != 'completed':
                    raise APIError('音频尚未生成', 404)
                return self.send_file(self.studio.jobs_dir/match[1]/(match[2]+'.wav'), 'download' in query)
            if path in ('/', '/history', '/history/'):
                return self.send_file(STATIC/'index.html')
            files = {'/app.js':'app.js', '/style.css':'style.css', '/favicon.svg':'favicon.svg'}
            if path in files:
                return self.send_file(STATIC/files[path])
            raise APIError('页面不存在', 404)
        except APIError as error:
            self.json(dict(error=str(error)), error.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            logging.exception('GET failed')
            self.json(dict(error='读取失败，请刷新重试'), 500)

    def do_POST(self):
        try:
            self.allowed_request(write=True)
            path = urlsplit(self.path).path
            if path == '/api/jobs':
                return self.json(self.studio.create_job(self.read_json()), 202)
            if path == '/api/uploads':
                return self.upload()
            raise APIError('接口不存在', 404)
        except APIError as error:
            self.close_connection = True
            self.json(dict(error=str(error)), error.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            self.close_connection = True
            logging.exception('POST failed')
            self.json(dict(error='操作失败，请重试'), 500)

    def upload(self):
        maximum = self.studio.config['max_upload_mb']*1024*1024
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise APIError('文件大小不正确')
        if not 0 < size <= maximum:
            raise APIError(f'请选择小于 {self.studio.config["max_upload_mb"]}MB 的音频', 413)
        raw_name = unquote(self.headers.get('X-Filename', 'audio.wav'))
        name = re.sub(r'[\x00-\x1f\x7f]', '', raw_name.replace('\\', '/').rsplit('/', 1)[-1])[:180]
        extension = Path(name).suffix.lower()
        if extension not in EXTENSIONS:
            raise APIError('不支持这个文件格式，请使用 WAV、MP3、FLAC、M4A 或 OGG')
        upload_id = uuid.uuid4().hex
        file = self.studio.uploads_dir/(upload_id+extension)
        self.connection.settimeout(60)
        try:
            with file.open('xb') as stream:
                remaining = size
                while remaining:
                    block = self.rfile.read(min(65536, remaining))
                    if not block:
                        raise APIError('文件上传不完整，请重试')
                    stream.write(block)
                    remaining -= len(block)
            info = audio_info(file)
            if info['seconds'] is None and extension in ('.wav', '.flac', '.ogg'):
                raise APIError('无法读取这个音频，请检查文件是否损坏')
            if info['seconds'] is not None and not .2 <= info['seconds'] <= self.studio.config['max_audio_seconds']:
                raise APIError('音频时长需在 0.2 秒到 10 分钟之间')
            record = dict(id=upload_id, name=name, extension=extension, bytes=size, **info, created_at=now())
            save_json(self.studio.uploads_dir/(upload_id+'.json'), record)
        except Exception:
            file.unlink(missing_ok=True)
            raise
        self.json(dict(**record, url='/api/audio/upload/'+upload_id), 201)


def create_server(config, state_dir=None, port=None):
    server = ThreadingHTTPServer(('127.0.0.1', config['port'] if port is None else port), Handler)
    server.daemon_threads = True
    server.studio = Studio(config, state_dir)
    return server


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    config = json.loads((ROOT/'configs/platform.json').read_text(encoding='utf-8'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        server = create_server(config, port=args.port)
    except OSError:
        print('启动失败：端口可能已被使用。请打开现有页面，或使用 --port 更换端口。', flush=True)
        raise SystemExit(1)
    url = f'http://127.0.0.1:{server.server_port}'
    save_json(server.studio.state_dir/'server.json', dict(pid=os.getpid(), port=server.server_port,
                                                        root=str(ROOT), started_at=now()))
    print('Voice Studio ready: '+url, flush=True)
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=.3)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.studio.queue.shutdown(wait=True)


if __name__ == '__main__':
    main()
