# 音色训练流程

公开目标音色使用 GTSinger 中文歌手 `ZH-Alto-1`。个人音色使用各自独立的实验目录。三者都采用 RVC v2、40 kHz 和 RMVPE 音高提取。

## 准备公开数据

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe scripts/download_gtsinger.py
.\.venv\Scripts\python.exe scripts/audit_audio.py
.\.venv\Scripts\python.exe scripts/prepare_gtsinger_dataset.py --holdout-song 水星记 --apply
```

准备脚本只选择 `Control_Group` 和 `Breathy_Group` 的歌唱录音。按整首歌划分，避免同一首歌的不同乐句同时进入训练与评估。《水星记》留出 24 段，训练集包含其余 462 段，约 64.58 分钟。

## 训练与导出

1. 用 RVC 切分训练录音并重采样，提取 RMVPE 音高和 HuBERT 768 维特征。
2. 生成 `config.json` 和训练文件清单，训练目标音色。公开模型训练了 100 轮；两版个人模型各训练了 80 轮。
3. 导出推理权重并为该音色的特征构建检索索引。部署时，权重和索引必须来自同一个实验。

公开模型的 GPU 命令见[上游版本与命令](upstream_versions.md)，实测耗时见[训练报告](../reports/server_training_budget.md)。另有 [Colab Notebook](../notebooks/rvc_public_dataset_training.ipynb)，用于在 Google Drive 保存训练产物。

训练个人音色时，将同一演唱者的 WAV 放在一个目录，在部署了 RVC 的 GPU 服务器运行：

```bash
.venv/bin/python scripts/train_personal_voice.py my_voice /path/to/recordings --epochs 80
```

目录内有带伴奏的录音时，可按文件名添加 `--separate '歌曲.wav'`；多个文件分别指定。为新实验使用独立名称，输出位于 `models/<实验名>/`。
