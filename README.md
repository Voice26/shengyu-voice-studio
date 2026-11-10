# 声屿 · 本地歌声转换工作台

此版本包含可视化换声工作台、训练与推理脚本和固定版本的上游 RVC 源码。项目源码和四组权重可从本仓库的 [v1.0.0 Release](https://github.com/Voice26/shengyu-voice-studio/releases/tag/v1.0.0) 下载。先解压 shengyu-source.zip，再把四个模型压缩包解压到同一个项目根目录，每个包自带 models/ 路径。SHA256SUMS.txt 用于核对下载文件，MODEL-FILES.json 列出解压后的权重及索引。

两版个人音色均保留 80 轮权重和配套索引，第二版使用六段训练录音。公开目标为 GTSinger 中文女声。网页的个人原声预览可选，如需启用，把自有短录音放回对应 models/personal_*/reference.wav。公开试听片段来自 GTSinger，许可与来源见 docs/dataset_and_license.md。伴奏分离模型的来源、版本与哈希见 reports/separation_assets.json。

在 Windows 上用 Python 3.10 建立 .venv，安装 requirements-data.lock.txt 中的依赖。在 GPU 服务器部署 RVC 环境并下载基础资源（HuBERT、RMVPE 等），把项目和解压后的 models/ 同步到服务器，然后填写 configs/platform.json 中的 SSH 别名和项目路径。运行“启动换声平台.bat”打开页面。历史记录位于 /history。安装步骤见 docs/platform_runbook.md 和 docs/server_runbook.md。

以下为项目的开发记录，其中的训练数据、以往的任务结果与运行报告按原工作区路径引用。

# AI 歌声克隆小项目

使用 RVC v2 训练公开歌手和个人录音两个独立的目标音色。公开歌手实验已完成服务器部署、100 epoch GPU 训练、索引构建、留出音频推理，以及男声/女声两组跨歌手转换；训练结果见 `reports/server_training_budget.md`，新转换样例见 `reports/cross_speaker_test.md`。

本次数据已下载完成：729 个 WAV，712,461,378 字节（约 712 MB），20 首歌曲。只读审计：总计 82.46 分钟，可用歌唱候选 486 条、67.95 分钟，配对朗读 243 条、14.51 分钟；不可读文件和异常路径均为 0。

## 本地可视化换声平台

双击项目根目录的 **`启动换声平台.bat`**，浏览器将打开 **http://127.0.0.1:7866**。无需登录，页面只接受本机访问；页面与任务记录在本地，转换时通过已配置的 `voice-gpu` SSH 连接调用服务器 GPU。

页面可选“我的音色 · 第二版”（6 段录音）、“我的音色”（第一版，3 段录音）或公开歌手“清柔女声”。可以试听原声参考，上传音频或用男女声示例转换，调整音高与音色融合，下载 WAV，并在历史记录中对比试听。两版个人模型、索引和训练记录分别在 `models/personal_20261110/` 和 `models/personal_20261109/`。单文件最大 80 MB、最长 10 分钟。

带伴奏输入请选择“带伴奏歌曲”：先用 BS-RoFormer 分离人声，再换声并与原伴奏回混；结果区提供分离后人声、原伴奏、转换人声和带伴奏整曲试听。默认“自动适配目标音区”按实际人声音高建议原调或上下八度，可手动调整。它分析音区，不按性别固定变调；干声和示例可直接转换。资源版本与哈希见 `reports/separation_assets.json`。

默认开启“静音与起音优化”，通过头尾缓冲和原声引导的渐变衰减降低停顿杂音，并保护轻声及人声边界；可以取消勾选作对照。已用公开样例与经用户授权的约 101 秒录音验证，后者识别出的停顿区能量下降约 27dB，时长保持不变。短对比音频在 `audio/output/pause_tuning_20261107/`。

也可以运行 `powershell -ExecutionPolicy Bypass -File .\start_platform.ps1`；结束后使用 `停止换声平台.bat`。输入、输出和任务记录保存在 `.platform/`，默认不进入 Git。详见 `docs/platform_runbook.md`。

## 已准备的框架

- 官方 RVC 源码：`third_party/RVC-WebUI`，固定 commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`。
- 项目配置：`configs/project.yaml`，默认 `ZH-Alto-1`，v2 / F0 / RMVPE / 40kHz。
- 本地独立数据环境：`.venv`（Python 3.10）；服务器 RVC 环境为独立 Python 3.12 / Torch 2.7.1+cu128。
- 工具：限定范围下载、下载监控、音频审计、按歌曲留出/平铺复制、RVC 配置生成。
- Colab Notebook：`notebooks/rvc_public_dataset_training.ipynb`，已检查语法，尚未在 Colab 实测。
- 版本和许可：`docs/upstream_versions.md`、`docs/dataset_and_license.md`。

## RTX PRO 6000 服务器

SSH 别名为 `voice-gpu`，项目位于 `/srv/ai-vocal-clone`。使用 96GB Blackwell GPU，当前容器实际限制为 32GB 内存、32 核 CPU 配额。Linux 依赖与官方预训练资源已通过本地下载后上传，完成离线安装。

已留出整首《水星记》：训练 462 条、64.58 分钟，留出 24 条、3.37 分钟。训练切片、RMVPE 和 HuBERT 均完成 1169/1169。实测选择 batch 64，每轮约 8.36 秒，完整 100 轮预算约 14–19 分钟，另计索引和推理；显存峰值约 26.7GiB，训练进程树 PSS 峰值约 11.7GiB。

操作说明见 `docs/server_runbook.md`；实测明细见 `reports/server_training_budget.md`。第 10 轮模型已完成留出歌曲无索引技术检查，音频在 `audio/output/server_public_e10/`；这不代表已测量跨歌手转换质量。

最终模型和 added 索引已同步到本地 `models/gtsinger_zh_alto/`，最终测试输入与输出位于 `audio/output/server_public/`，实际两段正式训练累计 18.30 分钟。最终训练显存采样峰值 26.99GiB、主机 PSS 采样峰值 12.52GiB，服务器项目约占 29.2GiB。文件校验清单见 `reports/server_artifact_manifest.json`。人工试听尚未评分。

## 本地使用（PowerShell）

在本项目根目录执行；无需激活环境：

```powershell
# 查询现有下载状态
.\.venv\Scripts\python.exe scripts/download_progress.py

# 下载/断点续传（默认 ZH-Alto-1，仅 Breathy 子目录）
.\.venv\Scripts\python.exe scripts/download_gtsinger.py

# 或后台下载，日志在 reports/download.*.log
.\scripts\start_download.ps1

# 下载后只读审计
.\.venv\Scripts\python.exe scripts/audit_audio.py

# 列出歌曲，默认只预览
.\.venv\Scripts\python.exe scripts/prepare_gtsinger_dataset.py

# 指定一整首歌留出；先预览，确认后添加 --apply 复制文件
.\.venv\Scripts\python.exe scripts/prepare_gtsinger_dataset.py --holdout-song '歌曲名'
.\.venv\Scripts\python.exe scripts/prepare_gtsinger_dataset.py --holdout-song '歌曲名' --apply
```

原始训练数据位于 `data/raw/GTSinger/Chinese/ZH-Alto-1/Breathy/`，包含歌唱和配对朗读。训练准备只选 `Control_Group`、`Breathy_Group`，排除 `Paired_Speech_Group`；不改原件。2026-11-07 另下载 `ZH-Tenor-1` 男声和 `EN-Alto-1` 女声各两段歌唱片段，仅用于跨歌手推理，没有混入训练。

下载清单和精确字节数见 `reports/download_manifest.json`；最终成功状态见 `reports/download_status.json`。状态 `completed` 表示全部预期 WAV 文件已下载且大小匹配。失败时重跑相同命令即可续传；不要同时启动多个下载进程。

## 在另一台电脑重建数据环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements-data.lock.txt
```

`requirements-data.txt` 给出版本范围，lock 文件为本次实际安装版本。RVC 大型 GPU 依赖没有安装到此环境。

## Colab 训练

先在本地确定留出歌曲并生成训练集，再把 `data/processed/`、`scripts/prepare_rvc_config.py` 和 Notebook 上传到 Google Drive 的 `ai-vocal-clone/`。

在 [Google Colab](https://colab.research.google.com/) 打开 Notebook，选择 GPU，逐单元格执行。Notebook 包含版本检查、官方依赖、固定版本预训练资源、数据预处理、RMVPE、HuBERT、配置、训练、索引与 Drive 保存。默认 batch size 4、100 epoch 仅为初始参数，实际显存不足时降低 batch size。没有 GPU 实测结果时不能视为训练成功。

## 后续工作

1. 人工试听已完成的男声/女声跨歌手对比，音频位于 `audio/output/cross_speaker_20261107/`；每组为原声、1 秒静音、转换音，已匹配音量。
2. 根据试听比较音色、自然度和咬字，再调整推理参数；当前两组均保持原调，英文女声也涉及跨语言转换，尚无主观评分。
3. 个人录音放入 `data/personal/`，另建 `my_voice` 实验；不混入公开歌手训练集。

原始数据、个人录音、处理数据、模型和音频默认被 `.gitignore` 排除；本项目未自动发布或推送。

## 数据许可

数据来自 [GTSinger/GTSinger](https://huggingface.co/datasets/GTSinger/GTSinger)，许可为 **CC BY-NC-SA 4.0，并附额外条款**。原文已保存于 `docs/dataset_license.md`。当前只准备本地验证；收费交付或商业使用须先确认授权。软件 MIT 许可和数据/音乐版权是不同事项。
