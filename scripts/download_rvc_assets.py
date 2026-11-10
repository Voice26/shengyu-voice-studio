"""Fetch the exact official pretrained assets required for v2/F0/40k."""
import argparse
import os
import zipfile
from pathlib import Path

os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '120')
from huggingface_hub import hf_hub_download, snapshot_download

REVISION = 'e6d0c1a17da07c33557852f9dfa2bd44cc75737d'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='RVC-layout root directory')
    args = parser.parse_args()
    root = args.output.resolve()
    repo = 'lj1995/VoiceConversionWebUI'
    snapshot_download(repo, revision=REVISION, local_dir=root/'assets',
                      allow_patterns=['hubert_base/*', 'pretrained_v2/f0G40k.pth',
                                      'pretrained_v2/f0D40k.pth'], token=False, max_workers=3)
    hf_hub_download(repo, 'rmvpe.pt', revision=REVISION, local_dir=root/'assets/rmvpe', token=False)
    archive = hf_hub_download(repo, 'mute.zip', revision=REVISION, local_dir=root/'.model-downloads', token=False)
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            (root/'logs'/info.filename).resolve().relative_to((root/'logs').resolve())
        z.extractall(root/'logs')
    print(f'ASSETS_COMPLETED revision={REVISION} root={root}', flush=True)


if __name__ == '__main__':
    main()
