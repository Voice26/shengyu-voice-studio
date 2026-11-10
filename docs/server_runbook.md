# RTX PRO 6000 服务器运行说明

## 部署位置与环境

- 示例 SSH 别名为 `voice-gpu`，部署时替换为本机配置的别名。
- 远端项目：`/srv/ai-vocal-clone`。
- GPU：NVIDIA RTX PRO 6000 Blackwell Workstation Edition，约 96GB 显存。
- 主机：251GiB 内存、128 个逻辑 CPU；当前 SSH 容器实际限额为 **32GiB 内存、32 核 CPU 配额**，`/dev/shm` 为 32GB。
- Python：项目 `.python/python` 中的独立 CPython 3.12；虚拟环境为项目 `.venv`。
- CUDA：Torch/Torchaudio `2.7.1+cu128`，匹配 Blackwell。实际安装版本见远端 `reports/server-requirements.lock.txt`。
- 官方 RVC 源码来自已固定 commit 的 `git archive`，没有向服务器上传本地 Git 凭据或私钥。

最终采用离线安装：在 Windows 本地按 Linux/Python 3.12 解析 135 项依赖，补下载缺失包后上传，复用服务器项目缓存中的完整 wheel。依赖清单为 `configs/server-offline-requirements.txt`，完整 URL/哈希锁为 `reports/pylock.server.toml`，安装文件在远端 `wheelhouse/`。GPU 环境使用 `scripts/server_bootstrap_offline.sh` 安装；不改变服务器全局代理或现有 Conda 环境。临时 SSH 下载转发已关闭。FFmpeg 使用项目环境内的 imageio-ffmpeg 二进制。

## 数据划分

- 原始 WAV 全部存放于 `data/raw/GTSinger`，以原始远端 SHA-256 验证上传结果。
- 留出整首《水星记》：24 条歌唱片段，202.23 秒。
- 训练：462 条歌唱片段，3874.77 秒（64.58 分钟）。
- 只训练 Control_Group、Breathy_Group，配对朗读不进入训练。
- 留出片段用于检查输出时长和音频格式。跨歌手测试使用另外两位歌手的录音，参数见[测试记录](../reports/cross_speaker_test.md)。

## 查看任务

```bash
ssh voice-gpu
cd /srv/ai-vocal-clone
cat reports/server_job_status.json
tail -n 30 reports/server_pipeline.log
tail -n 30 reports/server_training.log
nvidia-smi
tmux list-sessions
```

环境安装运行于 `rvc-setup` tmux 会话，实验运行于 `rvc-run`。日志存放在项目 reports 中，SSH 断开后任务继续。

## 流程与预算

`scripts/server_pipeline.py` 等待独立环境完成，检查 Matplotlib 兼容性，验证数据，检查已经上传的固定版本预训练资源，离线进行预处理、RMVPE 和 HuBERT 特征提取。

最终分别短跑 batch 16/32/64/128，各 3 epoch，保存间隔设为 100，排除预热并用后两轮中位数比较纯训练吞吐。显存统计只计算本项目训练子进程及其后代，主机内存统计使用进程树 PSS，排除无关任务。

实测选择 **batch 64**：每轮 8.36 秒，显存采样峰值 26.7GiB，主机 PSS 采样峰值 11.7GiB。batch 128 每轮 8.72 秒、显存约 47.5GiB，没有吞吐优势。完整 100 轮 GPU 训练预算为 14–19 分钟，随共享负载和检查点写盘有波动；索引与推理另计。

- 短跑结果：`reports/server_batch_benchmarks.json`。
- 100 epoch 时间预算：`reports/server_training_budget.json`，以稳定轮次耗时外推，并留 35% 余量；尚未完成短跑时不能作为实测结果。
- 正式训练日志：`reports/server_training.log`。
- 预处理和特征：RVC `logs/gtsinger_zh_alto/`。
- 最终权重与索引：项目 `models/gtsinger_zh_alto/` 备份，同时保留 RVC 原输出。
- 留出集输入/推理音频：`audio/output/server_public/`。

本轮正式训练目标为 100 epoch，batch 为 64，保存间隔 10 epoch，关闭训练集显存缓存。前 10 轮使用 batch 16，保存后重新测量纯训练吞吐，再从 epoch-10 检查点恢复为 batch 64。训练轮数与质量的关系还需试听；不同 batch 的同样 epoch 数不代表同样优化更新次数。

项目当前约占 27GB，建议预留 40–50GB 磁盘，容器内存按 32GB 预算。完整 100 轮约占用 0.23–0.31 GPU 小时。未提供现有服务器的计费单价，金额需用实测 GPU 小时乘以现有单价；没有创建额外付费云资源。

## 兼容性处理

上游 `train/utils.py` 使用 `FigureCanvasAgg.tostring_rgb()`，该接口在 Matplotlib 3.10 被移除；本项目在其官方允许范围内选择 `matplotlib>=3.8.2,<3.10`。固定上游源文件不作修改。

失败时先查看 job status 指向的阶段与对应日志，修复后重启流水线。已完成的特征阶段和成功的短跑记录可复用。不要同时启动两份正式训练，也不要在完成后重复启动同一个实验。
