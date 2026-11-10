# 实验记录

## 2026-11-06：框架与数据准备

- 目标：ZH-Alto-1，Breathy，RVC v2 / F0 / RMVPE / 40kHz。
- 上游与数据版本：见 `upstream_versions.md` 和 `configs/project.yaml`。
- 数据下载完成：729 个 WAV，712,461,378 字节，20 首歌曲；已有 WAV 逐一通过远端 SHA-256 核验，README 通过 Git blob 核验。
- 音频审计：82.46 分钟总时长；歌唱候选 486 条、67.95 分钟；朗读排除 243 条、14.51 分钟；不可读 0，异常路径 0。
- 工具检查：4 项单元测试通过；数据依赖无冲突；Notebook 18 个单元格中 11 个代码单元格语法通过。尚未划定留出歌曲或复制训练集。
- 下载收尾：原始 Hub README 元数据请求停滞，改用同一固定版本官方 raw 文件并校验；续传改为先校验本地文件，避免完整音频重复请求。
- 数据审计：见 `reports/gtsinger_audio_audit.md`。
- GPU 训练：未执行。
- 模型、索引、推理结果：尚未生成。

## 后续训练填写模板

- 日期 / 操作者：
- GPU / 显存 / Python / Torch / CUDA：
- 训练集 / 留出歌曲 / 有效分钟：
- RVC commit / epoch / batch size：
- 权重 / 索引 / 日志位置：
- 推理输入 / 参数 / 输出位置：
- 主观试听 / 失败案例：

## 2026-11-06：RTX PRO 6000 服务器实验完成

- 位置：`voice-gpu:/srv/ai-vocal-clone`，独立 Python 3.12.16 / Torch 2.7.1+cu128 / CUDA 12.8。
- 容器实际配额：32GiB 内存、32 核 CPU；主机物理内存 251GiB，GPU 为 96GB RTX PRO 6000 Blackwell。
- 在线依赖下载因 SSH 通道重置失败，已回收项目缓存约 3.02GB，在本地补齐后离线安装；135 项安装文件全部通过哈希检查，临时转发已关闭。
- 留出《水星记》24 条、202.23 秒；训练 462 条、3874.77 秒；训练切片 1169 个，RMVPE/HuBERT 全部成功。
- 纯计算短测 batch 16/32/64/128，正式选择 batch 64；首段先训练到 epoch 10，保存后恢复并到达 epoch 100。
- 两段正式训练累计 18.30 分钟，最终阶段显存采样峰值 26.99GiB，主机 PSS 采样峰值 12.52GiB。
- 索引：768 维、186332 向量，`added_IVF4777_Flat_nprobe_1_gtsinger_zh_alto_v2.index`。
- 最终 GPU 推理检查通过：留出目标歌手输入 13.58 秒、输出 13.56 秒，40000Hz，峰值 0.6299，输出可读且数值有限。
- 最终权重和索引已同步至本地 `models/gtsinger_zh_alto/`；音频在 `audio/output/server_public/`。
- 本次仅验证训练/推理技术链路，跨歌手音色转换和人工试听评价未测量；个人声音实验未执行。
- 完整环境、预算和哈希记录见 `reports/server_training_budget.md`、`server-requirements.lock.txt`、`server_artifact_manifest.json`。

## 2026-11-07：男声和女声跨歌手转换完成

- 使用现有 100 epoch 模型，目标音色仍为 ZH-Alto-1，没有重新训练。
- 男声来源 ZH-Tenor-1《平凡的一天》，输入 18.620 秒，输出 18.600 秒。
- 女声来源 EN-Alto-1《Safe and Sound》，输入 24.213 秒，输出 24.200 秒；这一组同时涉及跨语言泛化。
- 两组均为原调 pitch 0、RMVPE、index rate 0.75、protect 0.33、RMS mix rate 1；服务器 cuda:0 / float16 推理成功。
- 共下载 4 个公开原始 WAV，逐一通过固定 revision 的 LFS SHA-256 校验；未加入目标歌手训练集。
- 原声在 `audio/input/cross_speaker/`，转换和音量匹配对比在 `audio/output/cross_speaker_20261107/`。对比顺序为原声、1 秒静音、转换音。
- 两组输出均可读、数值有限、无数字削波；回传后验证全部音频哈希，以及本地/服务器模型和索引一致。
- 技术测试完成；音色相似度、自然度与咬字等待主观试听。完整结果见 `reports/cross_speaker_test.md` 和 `reports/cross_speaker_test.json`。
