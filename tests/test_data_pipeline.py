import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from download_gtsinger import is_allowed, parser
from audit_audio import audit_file
from prepare_gtsinger_dataset import build_split
from prepare_rvc_config import main as prepare_rvc


class DataPipelineTest(unittest.TestCase):
    def test_download_boundary(self):
        self.assertTrue(is_allowed("Chinese/ZH-Alto-1/Breathy/song/Control_Group/a.wav", "ZH-Alto-1"))
        for path in ("Chinese/ZH-Tenor-1/Breathy/song/a.wav", "Chinese/ZH-Alto-1/Glissando/a.wav",
                     "Chinese/ZH-Alto-1/Breathy/../a.wav", "Chinese/ZH-Alto-1/Breathy/a.json"):
            self.assertFalse(is_allowed(path, "ZH-Alto-1"))
        self.assertTrue(parser().parse_args(["--dry-run"]).dry_run)

    def test_audit_excludes_speech_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "Chinese/ZH-Alto-1/Breathy/song/Paired_Speech_Group/test.wav"
            path.parent.mkdir(parents=True)
            sf.write(path, np.sin(np.arange(16000) * 0.1) * 0.2, 16000)
            before = hashlib.sha256(path.read_bytes()).digest()
            row = audit_file(path, root)
            self.assertTrue(row["readable"])
            self.assertFalse(row["training_candidate"])
            self.assertIn("speech_excluded", row["flags"])
            self.assertEqual(before, hashlib.sha256(path.read_bytes()).digest())

    def test_split_keeps_whole_song_out_and_unique_names(self):
        rows = [dict(path=f"song{i}/{group}/same.wav", speaker="ZH-Alto-1", song=f"song{i}",
                     group=group, training_candidate="True", duration="20")
                for i in (1, 2) for group in ("Control_Group", "Breathy_Group", "Paired_Speech_Group")]
        entries = build_split(rows, "ZH-Alto-1", "song1")
        self.assertEqual(len(entries), 4)
        self.assertEqual(len({e["destination"] for e in entries}), 4)
        self.assertTrue(all(e["song"] != "song1" for e in entries if e["usage"] == "rvc_train"))

    def test_rvc_40k_v2_uses_official_config_and_five_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = ['logs/demo/0_gt_wavs/0_0.wav', 'logs/demo/3_feature768/0_0.npy',
                     'logs/demo/2a_f0/0_0.wav.npy', 'logs/demo/2b-f0nsf/0_0.wav.npy',
                     'logs/mute/0_gt_wavs/mute40k.wav', 'logs/mute/3_feature768/mute.npy',
                     'logs/mute/2a_f0/mute.wav.npy', 'logs/mute/2b-f0nsf/mute.wav.npy']
            for name in files:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            config = root / 'configs/v1/40k.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'data': {'sampling_rate': 40000}}))
            prepare_rvc(['--rvc-dir', str(root), '--experiment', 'demo'])
            records = (root / 'logs/demo/filelist.txt').read_text().splitlines()
            self.assertEqual(len(records), 3)
            self.assertTrue(all(len(line.split('|')) == 5 for line in records))
            self.assertEqual(json.loads((root / 'logs/demo/config.json').read_text())['data']['sampling_rate'], 40000)


if __name__ == "__main__":
    unittest.main()
