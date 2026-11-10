"""Compact download snapshot without importing heavy dependencies."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
state_path = root / "reports/download_status.json"
if not state_path.exists():
    print(json.dumps({"status": "not_started"}))
else:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    result = {k: state[k] for k in ("status", "expected_wav_count", "expected_wav_bytes", "error") if k in state}
    manifest = root / "reports/download_manifest.json"
    if manifest.exists():
        files = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        complete = [f for f in files if f["path"].endswith(".wav")
                    and (Path(state["output"]) / f["path"]).is_file()
                    and (Path(state["output"]) / f["path"]).stat().st_size == f["size"]]
        result.update(completed_wav=len(complete), completed_bytes=sum(f["size"] for f in complete))
    print(json.dumps(result, ensure_ascii=False))
