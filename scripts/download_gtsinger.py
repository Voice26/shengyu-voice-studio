"""Download one pinned GTSinger Breathy subset, anonymously and resumably."""
import argparse
import hashlib
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEAKERS = ("ZH-Alto-1", "ZH-Tenor-1")


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--speaker", choices=SPEAKERS)
    p.add_argument("--output", type=Path, default=ROOT / "data/raw/GTSinger")
    p.add_argument("--revision", help="Defaults to the pinned commit in project.yaml")
    p.add_argument("--dry-run", action="store_true", help="Offline configuration preview; does not verify remote files")
    p.add_argument("--workers", type=int, default=4)
    return p


def prefix_for(speaker):
    if speaker not in SPEAKERS:
        raise ValueError("Unsupported speaker")
    return f"Chinese/{speaker}/Breathy/"


def is_allowed(path, speaker):
    from pathlib import PurePosixPath
    parts = PurePosixPath(path).parts
    return (".." not in parts and path.startswith(prefix_for(speaker))
            and path.endswith(".wav"))


def main(argv=None):
    args = parser().parse_args(argv)
    import yaml
    config = yaml.safe_load((ROOT / "configs/project.yaml").read_text(encoding="utf-8"))
    speaker = args.speaker or config["target_speaker"]
    revision = args.revision or config["dataset_revision"]
    prefix = prefix_for(speaker)
    if args.workers < 1 or args.workers > 16:
        raise ValueError("workers must be between 1 and 16")
    output = args.output.resolve()
    state = dict(repo_id="GTSinger/GTSinger", revision=revision, speaker=speaker,
                 scope=prefix + "**/*.wav", output=str(output), started_at=now())
    print(json.dumps(state, ensure_ascii=False, indent=2), flush=True)
    if args.dry_run:
        print("Offline preview only; remote count and size have NOT been verified.")
        return 0
    # HTTP transfers avoid optional Xet binary installation and can resume partial files.
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    from huggingface_hub.hf_api import RepoFile
    status_path = ROOT / "reports/download_status.json"
    state["status"] = "listing"
    write_json(status_path, state)
    try:
        api = HfApi(token=False)
        revision = api.dataset_info("GTSinger/GTSinger", revision=revision).sha
        state["revision"] = revision
        # Fetch and retain the actual license before downloading audio.
        hf_hub_download("GTSinger/GTSinger", "dataset_license.md", repo_type="dataset",
                        revision=revision, local_dir=output, token=False)
        files = [f for f in api.list_repo_tree("GTSinger/GTSinger", repo_type="dataset",
                 revision=revision, path_in_repo=prefix.rstrip("/"), recursive=True)
                 if isinstance(f, RepoFile) and is_allowed(f.path, speaker)]
        if not files:
            raise RuntimeError("No matching WAV files found; refusing to report success")
        metadata = [f for f in api.list_repo_tree("GTSinger/GTSinger", repo_type="dataset",
                    revision=revision, recursive=False)
                    if isinstance(f, RepoFile) and (f.path == "dataset_license.md"
                       or f.path.lower().startswith("readme") and f.path.lower().endswith(".md"))]
        entries = [dict(path=f.path, size=f.size, blob_id=f.blob_id,
                        sha256=f.lfs.get("sha256") if f.lfs else None) for f in files + metadata]
        write_json(ROOT / "reports/download_manifest.json", dict(**state, files=entries))
        state.update(status="downloading", expected_wav_count=len(files),
                     expected_wav_bytes=sum(f.size for f in files))
        write_json(status_path, state)
        print(f"Verified scope: {len(files)} WAV, {state['expected_wav_bytes']:,} bytes", flush=True)
        # Small Git-backed metadata uses the official raw endpoint. A Hub HEAD
        # request for README can stall even when the audio transfers succeed.
        import requests
        for f in metadata:
            target = output / f.path
            data = target.read_bytes() if target.is_file() else b""
            def blob_id(payload):
                return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            if len(data) != f.size or blob_id(data) != f.blob_id:
                response = requests.get(
                    f"https://huggingface.co/datasets/GTSinger/GTSinger/raw/{revision}/{f.path}",
                    timeout=(10, 30))
                response.raise_for_status()
                data = response.content
                if len(data) != f.size or blob_id(data) != f.blob_id:
                    raise RuntimeError(f"Metadata content mismatch: {f.path}")
                temp = target.with_suffix(target.suffix + ".tmp")
                temp.write_bytes(data)
                temp.replace(target)
        pending, invalid = [], []
        for f in files:
            local = output / f.path
            if not local.is_file():
                pending.append(f.path)
            elif local.stat().st_size != f.size:
                invalid.append(f.path)
            elif f.lfs and f.lfs.get("sha256"):
                digest = hashlib.sha256()
                with local.open("rb") as audio:
                    for block in iter(lambda: audio.read(1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != f.lfs["sha256"]:
                    invalid.append(f.path)
        print(f"Already verified: {len(files)-len(pending)-len(invalid)}; pending download: {len(pending)}; invalid existing: {len(invalid)}", flush=True)
        if pending:
            snapshot_download(repo_id="GTSinger/GTSinger", repo_type="dataset", revision=revision,
                              local_dir=output, allow_patterns=pending,
                              max_workers=args.workers, token=False)
        if invalid:
            snapshot_download(repo_id="GTSinger/GTSinger", repo_type="dataset", revision=revision,
                              local_dir=output, allow_patterns=invalid,
                              max_workers=args.workers, token=False, force_download=True)
        bad = [f.path for f in files + metadata if not (output / f.path).is_file()
               or (output / f.path).stat().st_size != f.size]
        if bad:
            raise RuntimeError(f"Missing or size-mismatched files: {bad[:10]}")
        state.update(status="completed", completed_at=now(), wav_count=len(files),
                     wav_bytes=sum((output / f.path).stat().st_size for f in files),
                     verification="All expected WAV paths and sizes match remote manifest")
        write_json(status_path, state)
        print(json.dumps(state, ensure_ascii=False, indent=2), flush=True)
        return 0
    except Exception as exc:
        state.update(status="failed", error=f"{type(exc).__name__}: {exc}", ended_at=now())
        write_json(status_path, state)
        traceback.print_exc()
        print("Retry the same command to resume. For permission errors use local hf auth login; never put tokens in code.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
