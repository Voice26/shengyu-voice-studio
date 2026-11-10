# 男声与女声跨歌手换声测试

日期：2026-11-07（北京时间）。状态：两组 GPU 推理完成，音频已回传本地并验证 SHA-256。

## 输入与结果

| 测试 | 源歌手 | 曲目 | 输入秒数 | 输出秒数 | 音量匹配对比秒数 |
|---|---|---|---:|---:|---:|
| 男声 | ZH-Tenor-1，中文男高音 | 平凡的一天 | 18.620 | 18.600 | 38.220 |
| 女声 | EN-Alto-1，英文女低音 | Safe and Sound | 24.213 | 24.200 | 49.413 |

两位源歌手均不同于训练目标 `ZH-Alto-1`，没有进入目标模型训练。每组从 Control_Group 下载前两段完整乐句，乐句之间添加 0.25 秒静音；总计只下载 4 个 WAV，约 6.10MB，没有下载完整歌手数据集。

数据来自 [GTSinger/GTSinger](https://huggingface.co/datasets/GTSinger/GTSinger)，固定 revision `4426c862beed558b7e1cb8a4dce7e8c0c83bb208`。原始文件逐一验证远端 LFS SHA-256。来源、路径、时长和哈希见 `cross_speaker_sources.json`。

## 转换配置

- 服务器：`voice-gpu:/srv/ai-vocal-clone`，CUDA GPU 推理，float16。
- 使用现有 100 epoch 模型 `models/gtsinger_zh_alto/gtsinger_zh_alto.pth`，未重新训练。
- 使用现有 `added_IVF4777_Flat_nprobe_1_gtsinger_zh_alto_v2.index`，服务器原始位置为 `third_party/RVC-WebUI/logs/gtsinger_zh_alto/`。
- 目标 speaker ID 0，RMVPE，index rate 0.75，protect 0.33，RMS mix rate 1。
- 两组均保留输入原调，pitch shift 为 0；男声没有自动提高八度。
- 输出均为单声道 40kHz WAV。

## 试听文件

输入原声：

- `audio/input/cross_speaker/male_zh_tenor_1.wav`
- `audio/input/cross_speaker/female_en_alto_1.wav`

转换结果：

- `audio/output/cross_speaker_20261107/male_zh_tenor_1_converted.wav`
- `audio/output/cross_speaker_20261107/female_en_alto_1_converted.wav`

音量匹配对比：

- `audio/output/cross_speaker_20261107/male_zh_tenor_1_comparison.wav`
- `audio/output/cross_speaker_20261107/female_en_alto_1_comparison.wav`

每个对比文件均为：**原声 → 1 秒静音 → 转换结果**。原声和转换音按相同 RMS 匹配音量，并应用共同峰值限制；单独的原声/转换文件保持原电平。

## 已验证与待评价

两组 CLI 均报告 Success，使用 cuda:0；输出可读、非空、数值有限，与输入时长差均小于 0.03 秒。输出峰值分别为 0.7051 和 0.7500，无数字削波。回传后全部输入、输出和对比文件哈希一致；本地模型及索引哈希与服务器使用的文件一致。

音色相似度、自然度和咬字尚未做主观评分。两组使用不同歌曲和语言，比较时需要考虑这些差异。

完整参数与数值见 `cross_speaker_test.json`，原始推理日志见 `cross_speaker_male_zh_tenor_1.log` 和 `cross_speaker_female_en_alto_1.log`。

## 复现

本地准备少量测试输入：

```powershell
.\.venv\Scripts\python.exe scripts/prepare_cross_speaker_samples.py
```

将两段输入、`reports/cross_speaker_sources.json`、`scripts/run_cross_speaker_test.py` 同步到服务器对应项目路径后：

```bash
cd /srv/ai-vocal-clone
.venv/bin/python scripts/run_cross_speaker_test.py
```

