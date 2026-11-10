"""Preview or copy a song-level split; original WAV files are never moved."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

import yaml

from download_gtsinger import ROOT, write_json


def build_split(rows, speaker, holdout):
    selected = [r for r in rows if r["speaker"] == speaker and r["training_candidate"] == "True"
                and r["group"] in ("Control_Group", "Breathy_Group")]
    if holdout not in {r["song"] for r in selected}:
        raise ValueError("Holdout song must be an audited singing candidate")
    output = []
    for row in selected:
        split = "holdout_reference" if row["song"] == holdout else "rvc_train"
        unique_name = hashlib.sha256(row["path"].encode("utf-8")).hexdigest() + ".wav"
        output.append(dict(source=row["path"], destination=f"{speaker}/{split}/{unique_name}",
                           song=row["song"], group=row["group"], speaker=speaker,
                           duration=float(row["duration"]), usage=split))
    return output


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--holdout-song")
    p.add_argument("--apply", action="store_true", help="Copy files after preview; default is dry-run")
    args = p.parse_args(argv)
    config = yaml.safe_load((ROOT / "configs/project.yaml").read_text(encoding="utf-8"))
    with (ROOT / "reports/gtsinger_file_manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    songs = sorted({r["song"] for r in rows if r["training_candidate"] == "True"
                    and r["speaker"] == config["target_speaker"]})
    holdout = args.holdout_song or config.get("holdout_song")
    if not holdout:
        print(json.dumps(dict(mode="preview", songs=songs, message="Choose --holdout-song before copying. Source speaker data has not been downloaded."), ensure_ascii=False, indent=2))
        return 0
    entries = build_split(rows, config["target_speaker"], holdout)
    stats = {usage: dict(files=sum(e["usage"] == usage for e in entries),
                        seconds=sum(e["duration"] for e in entries if e["usage"] == usage))
             for usage in ("rvc_train", "holdout_reference")}
    write_json(ROOT / "reports/dataset_split_preview.json", dict(holdout_song=holdout, stats=stats, files=entries))
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    if stats["rvc_train"]["seconds"] < 600:
        p.error("Less than 10 minutes of training singing remains; extend the dataset first")
    if args.apply:
        raw = (ROOT / "data/raw/GTSinger").resolve()
        processed = (ROOT / "data/processed").resolve()
        train_dir = processed / config["target_speaker"] / "rvc_train"
        intended = {Path(e["destination"]).name for e in entries if e["usage"] == "rvc_train"}
        if train_dir.exists() and any(f.is_file() and f.name not in intended for f in train_dir.iterdir()):
            p.error("Training directory contains files from another split; use a separate clean output directory")
        for e in entries:
            source, target = (raw / e["source"]).resolve(), (processed / e["destination"]).resolve()
            source.relative_to(raw)
            target.relative_to(processed)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                    raise RuntimeError(f"Refusing to overwrite different existing file: {target}")
            else:
                shutil.copy2(source, target)
        with (processed / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=list(entries[0]))
            writer.writeheader()
            writer.writerows(entries)
        print("Copied train/holdout split. Raw files are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
