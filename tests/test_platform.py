"""Local platform boundaries and durable job state; no server/GPU required."""
import http.client
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import subprocess
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_app.server import APIError, Studio, create_server, save_json, validate_settings

CONFIG = dict(port=0, ssh_host='voice-gpu', remote_root='/srv/ai-vocal-clone',
              max_upload_mb=1, max_audio_seconds=600, job_timeout_seconds=900)


class PlatformTest(unittest.TestCase):
    def setUp(self):
        self.test_area = Path(__file__).resolve().parents[1]/'.platform/test-tmp'
        self.test_area.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.test_area)
        self.root = Path(self.temp.name)
        self.server = create_server(CONFIG, self.root, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        wave = io.BytesIO()
        sf.write(wave, np.sin(np.arange(16000)*.1)*.2, 16000, format='WAV', subtype='PCM_16')
        self.audio = wave.getvalue()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.server.studio.queue.shutdown(wait=True)
        self.root.resolve().relative_to(self.test_area.resolve())
        self.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        connection.close()
        return result

    def upload(self, name='test.wav', body=None):
        status, _, data = self.request('POST', '/api/uploads', self.audio if body is None else body,
                                       {'X-Voice-Studio':'1','X-Filename':name})
        return status, json.loads(data)

    def test_history_page_is_directly_addressable(self):
        for path in ('/history', '/history/'):
            status, headers, data = self.request('GET', path)
            self.assertEqual(status, 200)
            self.assertIn('text/html', headers['Content-Type'])
            self.assertIn(b'id="historyHeading"', data)

    def test_rejects_cross_site_posts_and_host_spoofing(self):
        for headers in ({}, {'X-Voice-Studio':'1','Origin':'https://other.example'},
                        {'X-Voice-Studio':'1','Host':'other.example'},
                        {'X-Voice-Studio':'1','Sec-Fetch-Site':'cross-site'}):
            status, _, _ = self.request('POST', '/api/jobs', '{}', headers)
            self.assertEqual(status, 403)

    def test_upload_audio_range_and_download_preserve_bytes(self):
        status, record = self.upload()
        self.assertEqual(status, 201)
        self.assertEqual(record['seconds'], 1)
        status, headers, data = self.request('GET', record['url'], headers={'Range':'bytes=0-43'})
        self.assertEqual((status, len(data)), (206, 44))
        self.assertEqual(data, self.audio[:44])
        self.assertEqual(headers['Content-Range'], f'bytes 0-43/{len(self.audio)}')
        status, headers, data = self.request('GET', record['url']+'?download=1')
        self.assertEqual(status, 200)
        self.assertEqual(data, self.audio)
        self.assertIn('attachment', headers['Content-Disposition'])
        status, _, _ = self.request('GET', record['url'], headers={'Range':'bytes=999999-'})
        self.assertEqual(status, 416)

    def test_rejects_corrupt_disguised_oversize_and_long_uploads(self):
        for name, body in [('audio.wav', b'not audio'), ('script.exe', self.audio)]:
            status, _ = self.upload(name, body)
            self.assertIn(status, (400, 413))
        status, _, _ = self.request('POST', '/api/uploads', b'',
                                    {'X-Voice-Studio':'1', 'X-Filename':'large.wav', 'Content-Length':str(1024*1024+1)})
        self.assertEqual(status, 413)
        self.assertEqual(list((self.root/'uploads').iterdir()), [])
        with patch('platform_app.server.audio_info', return_value=dict(seconds=601, sample_rate=16000, channels=1)):
            status, _ = self.upload()
            self.assertEqual(status, 400)

    def test_safe_upload_names_and_no_arbitrary_file_access(self):
        status, record = self.upload('../../outside.wav')
        self.assertEqual(status, 201)
        self.assertEqual(record['name'], 'outside.wav')
        self.assertFalse((self.root/'outside.wav').exists())
        for path in ('/configs/platform.json', '/%2e%2e/README.md', '/api/audio/upload/../../README.md'):
            status, _, _ = self.request('GET', path)
            self.assertEqual(status, 404)

    def test_parameter_validation_blocks_shell_text_nan_and_invalid_ranges(self):
        for setting in [dict(pitch='0; echo bad'), dict(pitch=True), dict(pitch=1.1), dict(pitch=13),
                        dict(index_rate=float('nan')),dict(protect=.6),dict(rms_mix_rate=-.1)]:
            with self.assertRaises(APIError):
                validate_settings(setting)
        self.assertEqual(validate_settings({})['index_rate'], .75)
        self.assertTrue(validate_settings({})['pause_cleanup'])
        self.assertFalse(validate_settings(dict(pause_cleanup=False))['pause_cleanup'])
        with self.assertRaises(APIError):
            validate_settings(dict(pause_cleanup='false'))

    def test_job_snapshots_input_and_persists_failure(self):
        _, uploaded = self.upload()
        def fail_job(job_id):
            self.server.studio.change_job(job_id, status='failed', message='Test failure')
        with patch.object(self.server.studio, 'convert', side_effect=fail_job):
            job = self.server.studio.create_job(dict(upload_id=uploaded['id'], settings=dict(pitch=2)))
            self.server.studio.queue.shutdown(wait=True)
        folder = self.root/'jobs'/job['id']
        self.assertEqual((folder/'input.wav').read_bytes(), self.audio)
        saved = json.loads((folder/'job.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['status'], 'failed')
        self.assertEqual(saved['settings']['pitch'], 2)

    def test_model_selection_is_allowlisted_and_snapshotted(self):
        self.assertEqual(validate_settings({})['model_id'], 'gtsinger_zh_alto')
        for unknown in ('missing', [], None):
            with self.assertRaises(APIError):
                validate_settings({'model_id': unknown})
        studio = self.server.studio
        key = 'personal_20261109'
        with patch.object(studio, 'models', return_value=[dict(id=key)]), patch.object(studio, 'convert'):
            job = studio.create_job(dict(sample_id='male', settings=dict(model_id=key)))
            studio.queue.shutdown(wait=True)
        request = json.loads((self.root/'jobs'/job['id']/'request.json').read_text(encoding='utf-8'))
        self.assertEqual(request['settings']['model_id'], key)
        self.assertEqual(job['model_name'], '我的音色')

    def test_restarts_mark_interrupted_jobs_failed(self):
        job_id = 'a'*32
        save_json(self.root/'jobs'/job_id/'job.json', dict(id=job_id, status='converting', created_at='2026-01-01'))
        studio = Studio(CONFIG, self.root)
        self.assertEqual(studio.jobs[job_id]['status'], 'failed')
        studio.queue.shutdown(wait=True)

    def test_new_modes_validate_and_optional_stems_are_playable(self):
        self.assertEqual(validate_settings({})['source_type'], 'vocals')
        self.assertEqual(validate_settings({})['pitch_mode'], 'manual')
        valid = validate_settings(dict(source_type='song', pitch_mode='auto'))
        self.assertEqual((valid['source_type'], valid['pitch_mode']), ('song', 'auto'))
        for bad in (dict(source_type='command'), dict(pitch_mode='female')):
            with self.assertRaises(APIError):
                validate_settings(bad)
        studio = self.server.studio
        job_id = 'b'*32
        folder = studio.jobs_dir/job_id
        folder.mkdir()
        studio.jobs[job_id] = dict(id=job_id, status='completed')
        for stem in ('instrumental', 'mix'):
            (folder/(stem+'.wav')).write_bytes(self.audio)
            url = studio.public_job(studio.jobs[job_id])[stem+'_url']
            status, _, data = self.request('GET', url, headers={'Range':'bytes=0-43'})
            self.assertEqual((status, data), (206, self.audio[:44]))
        studio.jobs[job_id]['status'] = 'mixing'
        status, _, _ = self.request('GET', f'/api/audio/job/{job_id}/mix')
        self.assertEqual(status, 404)

    def test_worker_streams_only_known_stages_and_preserves_logs(self):
        studio = self.server.studio
        job_id = 'c'*32
        studio.jobs[job_id] = dict(id=job_id, status='uploading')
        folder = studio.jobs_dir/job_id
        folder.mkdir()
        log = folder/'process.log'
        real_popen = subprocess.Popen
        code = "print('ordinary log'); print('__STUDIO_STAGE__{\"stage\":\"separating\"}'); print('__STUDIO_STAGE__{\"stage\":\"bogus\"}'); print('__STUDIO_STAGE__{\"stage\":\"mixing\"}')"
        def local_worker(args, **kwargs):
            return real_popen([sys.executable, '-c', code], **kwargs)
        with patch('platform_app.server.subprocess.Popen', side_effect=local_worker):
            studio.run_worker('unused', job_id, log, timeout=5)
        self.assertEqual(studio.jobs[job_id]['status'], 'mixing')
        self.assertIn('原伴奏', studio.jobs[job_id]['message'])
        self.assertIn('ordinary log', log.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
