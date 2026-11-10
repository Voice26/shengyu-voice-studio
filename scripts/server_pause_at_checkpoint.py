"""Pause only this project's trainer after its requested checkpoint is saved."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--pid', type=int, required=True)
p.add_argument('--epoch', type=int, default=10)
args = p.parse_args()
command = Path(f'/proc/{args.pid}/cmdline').read_bytes()
assert b'train.train' in command and b'gtsinger_zh_alto' in command and str(root).encode() in command
checkpoint = root/'third_party/RVC-WebUI/logs/gtsinger_zh_alto'
deadline = time.monotonic() + 300
while time.monotonic() < deadline:
    text = (root/'reports/server_training.log').read_text(errors='replace')
    if f'Epoch: {args.epoch} ' in text and all((checkpoint/name).is_file() for name in ('G_2333333.pth', 'D_2333333.pth')):
        os.kill(args.pid, signal.SIGINT)
        result = dict(paused_pid=args.pid, checkpoint_epoch=args.epoch, reason='Refine batch timing without checkpoint I/O')
        (root/'reports/server_checkpoint_pause.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        break
    time.sleep(2)
else:
    raise TimeoutError('Checkpoint was not saved within five minutes; no process was stopped')
