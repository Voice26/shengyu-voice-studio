"""Stop only the optional batch-128 probe if container working memory gets high."""
import json
import os
from pathlib import Path
import signal
import time

root = Path(__file__).resolve().parents[1]
deadline = time.monotonic() + 300
while time.monotonic() < deadline:
    state = json.loads((root/'reports/server_job_status.json').read_text())
    if state['stage'] != 'benchmarking':
        break
    memory = dict(line.split() for line in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())
    working = sum(int(memory.get(k, 0)) for k in ('anon', 'shmem', 'kernel'))
    if working > 27 * 1024**3:
        for entry in Path('/proc').iterdir():
            if entry.name.isdigit():
                try:
                    command = (entry/'cmdline').read_bytes()
                    if b'bench_compute_b128' in command and b'train.train' in command and str(root/'.venv/bin/python').encode() in command:
                        os.kill(int(entry.name), signal.SIGINT)
                        result = dict(stopped_optional_batch=128, working_memory_bytes=working, reason='Protect 32GiB container memory limit')
                        (root/'reports/server_memory_guard.json').write_text(json.dumps(result, indent=2))
                        print(json.dumps(result), flush=True)
                        raise SystemExit(0)
                except (OSError, ProcessLookupError):
                    pass
    time.sleep(0.5)
