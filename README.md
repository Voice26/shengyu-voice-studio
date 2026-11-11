# Shengyu · Singing Voice Conversion Studio

**English** · [简体中文](README.zh-CN.md)

Shengyu (声屿) converts a singing voice into a selected target timbre using RVC. It supports both isolated vocals and songs with accompaniment. For a full song, the system separates the vocals, converts them, and mixes the generated voice with the original backing track.

The browser interface supports **English and Simplified Chinese**, with upload, voice selection, pitch adjustment, playback, downloads and a dedicated recent-results page. Processing runs on the configured GPU server.

## Using the interface

1. Upload a song or vocal recording, or select one of the prepared examples.
2. Choose **Song with backing track** for audio containing instruments, or **Vocals only** for dry vocals.
3. Select a target voice. Automatic vocal-range matching and pause cleanup are enabled by default when supported by the selected model.
4. Select **Convert voice**, then listen to the source, converted vocals, loudness-matched comparison and full mix where available.

Use **中文 / English** in the upper-right corner to switch languages. The browser remembers the selection. Append `?lang=en` or `?lang=zh` to a studio URL to open a specific language directly. The interface accepts audio up to 80 MB and 10 minutes per file.

For an existing shared deployment, open the address provided by its administrator. A private deployment may require a connection to the administrator's VPN. The browser handles uploads, playback and downloads while the server processes the audio.

## Project pipelines

### Training

![Shengyu training pipeline](docs/images/train.png)

The training pipeline produces a target-voice model, retrieval index and vocal-range profile.

1. Prepare recordings from GTSinger or the target singer. Separate accompaniment from recordings that contain music.
2. Reserve reference or held-out recordings, then prepare training slices in the model's 40 kHz mono format.
3. Extract fundamental frequency with **RMVPE** and 768-dimensional content features with **HuBERT**.
4. Fine-tune the **RVC v2** generator and discriminator on the prepared target vocals.
5. Build the **FAISS retrieval index** from the extracted features and compute a target vocal-range profile.
6. Export the `.pth` weights, `.index` file and `voice_profile.json` for inference.

### Testing and inference

![Shengyu testing and inference pipeline](docs/images/test.png)

1. Decode the uploaded audio. For songs with accompaniment, use **BS-RoFormer** to separate vocals and retain the backing track.
2. Estimate source pitch with **RMVPE**. Optional range matching compares it with the target profile and suggests an octave shift, with manual adjustment available.
3. Extract **HuBERT** content features, blend them with features retrieved from the target index, and generate the target vocals with **RVC**.
4. Remove inference padding and reduce noise around pauses and vocal onsets using the source timing.
5. Export converted vocals and a loudness-matched comparison. For full songs, match vocal levels and produce a mix with the original backing track.

Vocal-range matching uses measured pitch. Audio quality depends on the source recording, separation quality, target training data and conversion settings.

## Model downloads

Download the required model packages and extract them into the project root. Each archive contains its own `models/` directory structure. [Model releases](https://github.com/Voice26/shengyu-voice-studio/releases/tag/v1.0.0)

| Package | Contents |
| --- | --- |
| `personal_20261110.zip` | Personal voice v2, trained on six recordings for 80 epochs. Includes weights, retrieval index and vocal-range profile. |
| `personal_20261109.zip` | Personal voice v1, trained on three recordings for 80 epochs. Includes weights, retrieval index and vocal-range profile. |
| `gtsinger_zh_alto.zip` | GTSinger Chinese female voice, trained for 100 epochs. Includes weights, retrieval index and profile. |
| `separation.zip` | BS-RoFormer weights and configuration for songs with accompaniment. |

Use `SHA256SUMS.txt` to verify downloaded archives. The model manifest records individual file sizes and SHA-256 hashes. Personal training recordings are excluded from the distribution. To add your own reference preview, place a short recording at `reference.wav` in the corresponding voice-model directory. [Model file manifest](MODEL-FILES.json)

## Windows setup

The Windows launcher runs the web interface locally and uses SSH to invoke inference on a configured GPU server.

1. Download the project ZIP and extract it into a writable folder on Windows x64. [Download source](https://github.com/Voice26/shengyu-voice-studio/archive/refs/heads/main.zip)
2. Run `配置换声环境.bat` to configure the environment. It reuses the project Python environment where available. On a new computer, it downloads and verifies a portable Python runtime and the web audio dependencies.
3. Follow the setup prompts to select an SSH host and remote Linux project directory. The GPU server needs RVC, the base resources and the selected voice models. The local computer needs SSH key authentication to that server.
4. Run `启动换声平台.bat`, then open `http://127.0.0.1:7866/?lang=en`.
5. Run `停止换声平台.bat` when finished.

To move the project, copy or extract the complete folder and run environment setup again in its new location. Detailed operational notes are available in Chinese. [Server setup](docs/server_runbook.md) · [Studio guide](docs/platform_runbook.md)

## Training records and data sources

The implementation notes cover held-out songs, feature extraction and personal-voice training. The cross-singer report records settings and results for two public dry-vocal examples. [Training notes](docs/implementation_plan.md) · [Cross-singer tests](reports/cross_speaker_test.md)

Public examples are drawn from GTSinger. Dataset use is subject to its licence and additional terms. [GTSinger dataset](https://huggingface.co/datasets/GTSinger/GTSinger) · [Dataset licence notes](docs/dataset_license.md)

The bundled RVC implementation retains its upstream licence. The separation asset manifest records the BS-RoFormer sources, versions and hashes. [RVC implementation](third_party/RVC-WebUI) · [RVC licence](third_party/RVC-WebUI/LICENSE) · [Separation assets](reports/separation_assets.json)
