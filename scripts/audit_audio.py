"""Read-only WAV audit for the downloaded single-speaker dataset."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

from download_gtsinger import ROOT, write_json

SINGING = {"Control_Group", "Breathy_Group"}
GROUPS = SINGING | {"Paired_Speech_Group"}


def identify(path, root):
    relative = path.relative_to(root).as_posix()
    parts = relative.split("/")
    valid = (len(parts) >= 6 and parts[0] == "Chinese"
             and parts[1] in ("ZH-Alto-1", "ZH-Tenor-1")
             and parts[2] == "Breathy" and parts[4] in GROUPS)
    return dict(path=relative, speaker=parts[1] if len(parts) > 1 else "",
                technique=parts[2] if len(parts) > 2 else "",
                song=parts[3] if len(parts) > 3 else "",
                group=parts[4] if valid else "unknown", path_valid=valid)


def audit_file(path, root):
    row = identify(path, root)
    row.update(readable=False, training_candidate=False, duration=0.0,
               sample_rate=0, channels=0, subtype="", peak=0.0, rms=0.0,
               near_clip_samples=0, silent_sample_ratio=0.0, flags="", error="")
    flags = []
    try:
        info = sf.info(str(path))
        count, squares, silent, clip, peak = 0, 0.0, 0, 0, 0.0
        for block in sf.blocks(str(path), blocksize=65536, dtype="float32", always_2d=True):
            if not np.isfinite(block).all():
                raise ValueError("Non-finite audio samples")
            absolute = np.abs(block)
            peak = max(peak, float(absolute.max(initial=0)))
            squares += float(np.sum(block.astype(np.float64) ** 2))
            count += block.size
            clip += int(np.count_nonzero(absolute >= 0.999))
            silent += int(np.count_nonzero(absolute < 1e-4))
        row.update(readable=True, duration=info.duration, sample_rate=info.samplerate,
                   channels=info.channels, subtype=info.subtype, peak=peak,
                   rms=float(np.sqrt(squares / max(count, 1))), near_clip_samples=clip,
                   silent_sample_ratio=silent / max(count, 1))
        if info.duration < 0.5:
            flags.append("too_short")
        if clip:
            flags.append("near_clipping")
        if row["rms"] < 1e-4:
            flags.append("very_low_rms")
        row["training_candidate"] = (row["path_valid"] and row["group"] in SINGING
                                     and info.duration >= 0.5 and row["rms"] >= 1e-4)
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        flags.append("unreadable")
    if not row["path_valid"]:
        flags.append("unexpected_path")
    if row["group"] == "Paired_Speech_Group":
        flags.append("speech_excluded")
    row["flags"] = ";".join(flags)
    return row


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "data/raw/GTSinger")
    args = p.parse_args(argv)
    rows = [audit_file(path, args.input) for path in sorted(args.input.rglob("*.wav"))]
    if not rows:
        p.error("No WAV files found")
    groups = defaultdict(lambda: dict(files=0, seconds=0.0))
    songs = defaultdict(lambda: dict(files=0, candidate_seconds=0.0))
    for row in rows:
        groups[row["group"]]["files"] += 1
        groups[row["group"]]["seconds"] += row["duration"]
        songs[row["song"]]["files"] += 1
        if row["training_candidate"]:
            songs[row["song"]]["candidate_seconds"] += row["duration"]
    summary = dict(wav_count=len(rows), total_seconds=sum(r["duration"] for r in rows),
                   candidate_count=sum(r["training_candidate"] for r in rows),
                   candidate_seconds=sum(r["duration"] for r in rows if r["training_candidate"]),
                   unreadable=sum(not r["readable"] for r in rows),
                   unexpected_paths=sum(not r["path_valid"] for r in rows),
                   flagged_count=sum(bool(r["flags"]) for r in rows),
                   sample_rates=dict(Counter(r["sample_rate"] for r in rows)),
                   channels=dict(Counter(r["channels"] for r in rows)),
                   subtypes=dict(Counter(r["subtype"] for r in rows)),
                   groups=dict(groups), songs=dict(songs))
    write_json(ROOT / "reports/gtsinger_audio_audit.json", summary)
    with (ROOT / "reports/gtsinger_file_manifest.csv").open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# GTSinger 音频审计", "", f"WAV：{len(rows)}；总时长：{summary['total_seconds']/60:.2f} 分钟。",
             f"可用歌唱候选：{summary['candidate_count']} 条，{summary['candidate_seconds']/60:.2f} 分钟。",
             f"不可读：{summary['unreadable']}；异常路径：{summary['unexpected_paths']}。", "",
             "| Group | 文件数 | 分钟 |", "|---|---:|---:|"]
    lines += [f"| {group} | {v['files']} | {v['seconds']/60:.2f} |" for group, v in groups.items()]
    lines += ["", "| 歌曲 | 文件数 | 歌唱候选分钟 |", "|---|---:|---:|"]
    lines += [f"| {song} | {v['files']} | {v['candidate_seconds']/60:.2f} |" for song, v in songs.items()]
    lines += ["", "Paired_Speech_Group 为朗读，全部排除训练。削波、静音等标记详见 CSV；原件未修改。",
              "静音比例是绝对幅度低于 1e-4 的样本比例。此审计不保证模型训练效果。"]
    (ROOT / "reports/gtsinger_audio_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("wav_count", "total_seconds", "candidate_count", "candidate_seconds", "unreadable", "unexpected_paths")}, ensure_ascii=False))
    return 1 if summary["unreadable"] or summary["unexpected_paths"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
