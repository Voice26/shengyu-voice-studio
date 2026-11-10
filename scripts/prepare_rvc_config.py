"""Prepare verified single-speaker v2/F0/40k inputs for the pinned RVC CLI.

Mirrors upstream webui.py's filelist and v1/40k config selection, without
importing the WebUI or any GPU dependency.
"""
import argparse
import json
import random
import re
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rvc-dir", required=True, type=Path)
    parser.add_argument("--experiment", required=True)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.experiment):
        parser.error("Experiment must contain only letters, numbers, underscores or hyphens")
    root = args.rvc_dir.resolve()
    exp = root / "logs" / args.experiment
    wavs = {p.stem for p in (exp / "0_gt_wavs").glob("*.wav")}
    if not wavs:
        parser.error("No preprocessed WAV files")
    records = []
    for name in sorted(wavs):
        paths = [exp / "0_gt_wavs" / f"{name}.wav", exp / "3_feature768" / f"{name}.npy",
                 exp / "2a_f0" / f"{name}.wav.npy", exp / "2b-f0nsf" / f"{name}.wav.npy"]
        missing = [str(p) for p in paths if not p.is_file()]
        if missing:
            raise FileNotFoundError(f"Incomplete F0/features: {missing}")
        records.append("|".join([p.as_posix() for p in paths] + ["0"]))
    mute = root / "logs/mute"
    mute_paths = [mute / "0_gt_wavs/mute40k.wav", mute / "3_feature768/mute.npy",
                  mute / "2a_f0/mute.wav.npy", mute / "2b-f0nsf/mute.wav.npy"]
    if not all(p.is_file() for p in mute_paths):
        raise FileNotFoundError("Download and extract the official mute.zip into logs first")
    records.extend(["|".join([p.as_posix() for p in mute_paths] + ["0"])] * 2)
    random.Random(1234).shuffle(records)
    config_path = exp / "config.json"
    # Upstream uses v1/40k.json even for v2; configs/v2/40k.json does not exist.
    config = json.loads((config_path if config_path.exists() else root / "configs/v1/40k.json").read_text(encoding="utf-8"))
    if config["data"]["sampling_rate"] != 40000:
        raise ValueError("Existing experiment config is not 40kHz")
    config.pop("speaker_info", None)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp / "filelist.txt").write_text("\n".join(records), encoding="utf-8")
    print(f"Prepared {len(wavs)} audio records + 2 official mute records: {exp}")


if __name__ == "__main__":
    main()
