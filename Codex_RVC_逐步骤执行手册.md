# AI 歌声克隆项目：Codex 逐步骤执行手册

> 版本：2026-11-06\
> 目标：先用公开中文歌声数据集跑通 RVC，再用本人声音训练独立模型。\
> 使用方式：**每次只复制一个"Codex 指令块"给
> Codex。完成当前步骤并验收后，再复制下一步。不要一次性把全部指令交给
> Codex。**

------------------------------------------------------------------------

## 0. 项目目标与执行边界

### 0.1 最终目标

完成两轮相互独立的实验：

-   **实验 A：公开数据集验证。** 使用 GTSinger 中一位中文歌手的歌声训练
    RVC 模型，完成数据筛选、预处理、训练、索引构建、推理和效果检查。
-   **实验 B：个人声音训练。** 使用本人录制的清唱音频，沿用实验 A
    验证过的流程，训练另一套个人声音模型。

最终形成：

1.  可复现的数据下载与预处理脚本。
2.  可在 Google Colab GPU 上执行的 RVC 训练 Notebook。
3.  公开数据集模型和个人模型的独立权重、索引及实验记录。
4.  推理结果和对比音频。
5.  项目技术文档与 GitHub 展示材料。

### 0.2 技术路线

-   公开数据集：GTSinger，官方 Hugging Face 仓库为 `GTSinger/GTSinger`。
-   首轮中文数据目录：`Chinese/ZH-Alto-1/Breathy/` 或
    `Chinese/ZH-Tenor-1/Breathy/`。
-   模型：RVC 官方 `Retrieval-based-Voice-Conversion-WebUI`。
-   训练环境：Google Colab GPU；本地 Codex
    主要负责创建、检查和维护代码、脚本及 Notebook。
-   训练方案：单歌手、RVC v2、启用 F0、优先
    RMVPE、40kHz；具体参数必须以所固定的 RVC 版本和实际 GPU 显存为准。
-   音频处理：Python、SoundFile/FFmpeg；如需人声分离，再使用 RVC
    官方支持的分离工具或独立 UVR/Demucs 流程。

### 0.3 重要纠正与数据结构

本手册统一使用官方数据仓库
`GTSinger/GTSinger`。不要使用未经核实的镜像仓库 ID。

当前公开页面可确认：

-   `Chinese/ZH-Alto-1/` 目录约 5.15GB。
-   `Chinese/ZH-Alto-1/Breathy/` 目录约 734MB。
-   `Breathy/` 下按歌曲分目录；歌曲目录内可见
    `Breathy_Group`、`Control_Group`、`Paired_Speech_Group`。
-   首轮训练只考虑歌唱数据：`Control_Group` 与
    `Breathy_Group`；排除朗读数据 `Paired_Speech_Group`。
-   代码必须递归扫描实际文件，不得假定所有音频都恰好位于固定的两层目录。

数据入口： - GTSinger
数据集主页：https://huggingface.co/datasets/GTSinger/GTSinger -
ZH-Alto-1
目录：https://huggingface.co/datasets/GTSinger/GTSinger/tree/main/Chinese/ZH-Alto-1 -
ZH-Alto-1/Breathy
目录：https://huggingface.co/datasets/GTSinger/GTSinger/tree/main/Chinese/ZH-Alto-1/Breathy -
数据集许可：https://huggingface.co/datasets/GTSinger/GTSinger/blob/main/dataset_license.md

**许可注意：** 数据集页面标注 CC BY-NC-SA
4.0，许可文件还包含额外的责任承担、版权音频副本及代表雇主签署等条款。公开可下载不等于可以不受限制地训练、发布模型或传播生成音频。开始下载前必须阅读并保存许可文件；如果无法确认这些额外条款是否适用于个人学生项目，先暂停并由用户确认/联系数据集维护者。不得将数据集原始音频、由其训练的模型权重或受版权保护的歌曲音频自动上传到公开
GitHub。

### 0.4 Codex 的工作边界

Codex 可以在项目工作区内创建脚本、配置、文档和
Notebook，也可以运行本地测试。**不要假设 Codex 已经登录用户的 Hugging
Face、Google Drive 或 Colab。** 需要登录、同意许可、选择 GPU、挂载
Drive、下载大文件、启动云端训练、公开发布或推送 GitHub
时，必须先向用户说明并等待确认。

所有步骤遵循：

1.  一次只做当前步骤，不提前实施后续步骤。
2.  先检查现有项目，再修改；不要覆盖用户已有文件。
3.  不得删除原始数据、模型、日志或用户文件。
4.  不得把 Token、密码、Cookie、密钥写进代码或日志。
5.  不得把
    `data/raw/`、`data/processed/`、`models/`、录音原件、缓存或大文件提交到
    Git。
6.  不得在未确认许可前下载/处理受限数据。
7.  命令、参数、文件路径必须以实际检出的 RVC 版本为准；不能凭印象编造
    CLI 参数。
8.  每一步结束后报告：做了什么、改了哪些文件、运行了哪些检查、结果如何、尚存问题、下一步需要用户做什么。等待用户确认再继续。

------------------------------------------------------------------------

## 1. 建议的项目目录

项目目录建议命名为 `ai-vocal-clone`：

``` text
ai-vocal-clone/
├── README.md
├── .gitignore
├── configs/
│   └── project.yaml
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   ├── processed/
│   │   └── .gitkeep
│   └── personal/
│       └── .gitkeep
├── models/
│   └── .gitkeep
├── audio/
│   ├── input/
│   │   └── .gitkeep
│   └── output/
│       └── .gitkeep
├── notebooks/
│   └── .gitkeep
├── scripts/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
├── docs/
│   ├── implementation_plan.md
│   ├── dataset_and_license.md
│   └── experiment_log.md
└── third_party/
    └── .gitkeep
```

说明：

-   `third_party/` 中的 RVC
    上游代码只用于本地检查，不要复制进项目发布目录；也可以直接 clone
    到项目外部。
-   `data/raw/` 保存下载的原始公开数据。
-   `data/processed/` 保存整理后的 RVC 训练集。
-   `data/personal/` 保存本人录音及处理结果。
-   `models/` 保存 `.pth`、`.index` 和训练检查点。
-   `audio/output/` 保存推理结果和对比音频。
-   上述数据、模型和个人录音默认不进入 Git。

------------------------------------------------------------------------

# 2. Codex 执行步骤

## 步骤 0：初始化项目并检查工作区

**目的：** 让 Codex
先理解任务、检查当前工作区并建立项目骨架，不下载数据、不安装大型依赖、不启动训练。

### 复制给 Codex 的指令

``` text
你现在负责协助我实施“AI 歌声克隆项目”。请先阅读我提供的《AI 歌声克隆项目：Codex 逐步骤执行手册》，严格按步骤执行。

本轮只执行“步骤 0：初始化项目并检查工作区”，不要提前做后续步骤。

要求：
1. 先检查当前工作区路径、已有文件、Git 状态和 Python 环境。
2. 如果工作区已有项目文件，不要覆盖或删除；先说明现状，再选择安全的项目子目录。
3. 创建本手册第 1 节所示的项目目录骨架。
4. 创建 configs/project.yaml，至少包含：
   - dataset_repo: GTSinger/GTSinger
   - target_speaker: ZH-Alto-1
   - source_speaker: ZH-Tenor-1
   - technique_dir: Breathy
   - include_groups: [Control_Group, Breathy_Group]
   - exclude_groups: [Paired_Speech_Group]
   - sample_rate: 40000
   - model_version: v2
   - use_f0: true
   - f0_method: rmvpe
   - experiment_public: gtsinger_zh_alto
   - experiment_personal: my_voice
   - holdout_song: null
5. 创建 .gitignore，排除 data/raw、data/processed、data/personal、models、音频大文件、缓存、.env、Token 和临时日志。
6. 创建 docs/implementation_plan.md，记录本项目的阶段、依赖关系和验收目标。
7. 创建 docs/experiment_log.md 空白实验记录模板。
8. 创建 docs/dataset_and_license.md，写入官方数据集和许可链接，并标注“使用前必须阅读许可文件”。
9. 不要下载数据，不要安装 RVC，不要运行 GPU 任务，不要执行 git push。
10. 运行必要的目录/配置检查，确认 YAML 可解析。

如果我没有明确指定目标歌手，暂时保留配置中的 ZH-Alto-1 作为默认值，并在报告中提醒我可以改为 ZH-Tenor-1。不要擅自推断我的性别或音域。

完成后停止，报告文件清单、检查结果和需要我确认的事项。
```

### 验收标准

-   项目目录骨架存在。
-   `configs/project.yaml` 可解析。
-   `.gitignore` 不会忽略 README、脚本、Notebook 和文档。
-   没有下载大文件、覆盖原文件或推送 Git。

**完成后：** 检查 Codex 报告，确认目录和默认歌手，再进入步骤 1。

------------------------------------------------------------------------

## 步骤 1：核验并固定上游 RVC 版本

**目的：** 使用 RVC 官方代码和官方 CLI 文档，避免使用不明来源的 Colab
Notebook 或过时命令。

官方仓库：
https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

官方中文 CLI 文档：
https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/cn/cli.md

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 1：核验并固定上游 RVC 版本”。

要求：
1. 检查 RVC 官方仓库：
   https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
2. 检查官方中文 CLI 文档：
   https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/cn/cli.md
3. 如果当前环境可以访问 GitHub，获取官方仓库当前 commit hash、默认分支、许可证文件、Python 版本要求、依赖安装方式。
4. 将官方仓库 clone 到项目外部目录，或 clone 到已被 .gitignore 排除的 third_party/RVC-WebUI。不要修改上游代码。
5. 记录 commit hash，生成 docs/upstream_versions.md。
6. 检查以下脚本/入口是否存在，并记录其真实参数与调用方式：
   - train/preprocess.py
   - train/dataset/extract_f0.py
   - train/dataset/extract_hubert_feature.py
   - train/train.py
   - train/train_index.py
   - infer/cli.py
7. 对训练参数，不要只抄网上示例。尽可能结合当前 commit 的官方文档和脚本 --help/参数解析代码核验。
8. 特别确认：40kHz、v2、F0、RMVPE、GPU 训练、模型保存、索引生成、推理 CLI 的实际支持情况。
9. 如果官方 CLI 需要 config.json 或 filelist.txt，查明官方 WebUI 如何生成它们；不要自行猜测文件格式。
10. 如果官方仓库当前版本与本手册假设不一致，列出差异并提出调整建议，不要擅自更换成第三方实现。

本轮不要训练模型，不要下载预训练权重，不要启动大规模安装。

完成后停止，报告固定的 commit hash、环境要求、核验过的命令入口和未解决问题。
```

### 验收标准

-   `docs/upstream_versions.md` 记录了可复现的 commit hash。
-   已确认实际 CLI 参数，而不是凭记忆填写。
-   已确认 `config.json` 和 `filelist.txt` 的生成方式。
-   没有修改 RVC 上游代码。

------------------------------------------------------------------------

## 步骤 2：创建 GTSinger 数据集下载脚本

**目的：** 只下载一个中文歌手的 `Breathy` 子目录，不下载整个 54GB
数据集。

### 重要设置

-   仓库：`GTSinger/GTSinger`
-   默认歌手：`ZH-Alto-1`
-   可选歌手：`ZH-Tenor-1`
-   下载路径：`Chinese/<目标歌手>/Breathy/`
-   许可文件：`dataset_license.md`
-   Hugging Face
    官方下载工具文档：https://huggingface.co/docs/huggingface_hub/guides/download

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 2：创建 GTSinger 数据集下载脚本”，不要开始模型训练。

要求：
1. 创建 scripts/download_gtsinger.py。
2. 使用 Hugging Face 官方 huggingface_hub.snapshot_download。
3. repo_id 必须是 GTSinger/GTSinger，repo_type 必须是 dataset。
4. 从 configs/project.yaml 读取 target_speaker。
5. 只允许下载：
   Chinese/<target_speaker>/Breathy/**/*.wav
   dataset_license.md
   数据集 README/元信息（如果仓库中存在）。
6. 默认下载目录为 data/raw/GTSinger。
7. 支持命令行参数：
   --speaker ZH-Alto-1 或 ZH-Tenor-1
   --output
   --revision
   --dry-run（如果底层 API 不支持真正 dry-run，就只列出配置和预期范围，不得假装完成远端文件清单验证）
8. 脚本应打印仓库 ID、revision、歌手、下载范围、输出目录。
9. 下载结束后输出文件数量、总字节数和目录结构摘要。
10. 不要把 Hugging Face Token 写入脚本。公开数据优先匿名下载；如遇权限错误，再提示我在本地安全登录。
11. 添加异常处理、断点续传说明和清晰日志。
12. 编写最小单元测试，测试参数解析和下载范围生成；测试不得真正下载数百 MB 数据。
13. 更新 requirements-data.txt，列出脚本所需依赖及合理版本范围。
14. 不要在本轮自动开始实际下载；先生成脚本并运行 --help、静态检查和单元测试。

完成后停止，告诉我如何执行实际下载，并提醒我先阅读 dataset_license.md。
```

### 用户需要手动确认

运行脚本前，先打开并阅读：

https://huggingface.co/datasets/GTSinger/GTSinger/blob/main/dataset_license.md

如果许可文件中的额外条款不适用于你的个人项目，先不要继续下载和训练，联系数据集维护者确认。

### 验收标准

-   下载脚本只匹配一个目标歌手的 `Breathy` 子目录。
-   不会下载其他歌手或整个仓库。
-   许可文件会保存到本地。
-   `--help` 和单元测试通过。

### 用户实际运行命令示例

``` bash
python scripts/download_gtsinger.py --speaker ZH-Alto-1
```

如需男高音数据：

``` bash
python scripts/download_gtsinger.py --speaker ZH-Tenor-1
```

------------------------------------------------------------------------

## 步骤 3：审计下载数据并生成数据质量报告

**目的：** 先了解实际数据结构和音频质量，再决定训练集如何组织。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 3：审计 GTSinger 数据”，不要移动、删除或覆盖原始音频。

要求：
1. 创建 scripts/audit_audio.py。
2. 递归扫描 data/raw/GTSinger 下的 WAV 文件。
3. 从路径识别歌手、演唱技巧目录、歌曲名和 Group 名称；路径结构不符合预期的文件放入异常清单，不要直接丢弃。
4. 统计：
   - WAV 文件总数
   - 每首歌曲文件数
   - 每个 Group 文件数
   - 总时长和分组时长
   - 采样率分布
   - 声道数分布
   - 位深（如果可读取）
   - 无法读取/损坏文件
   - 时长过短的文件
   - 峰值接近削波的文件
   - 静音或极低 RMS 文件
5. 训练候选组只标记 Control_Group 和 Breathy_Group。
6. Paired_Speech_Group 标记为 speech_excluded，不得进入歌声训练集。
7. 不要因为文件名或路径异常而自动删除文件。
8. 生成：
   reports/gtsinger_audio_audit.json
   reports/gtsinger_audio_audit.md
   reports/gtsinger_file_manifest.csv
9. 报告必须给出可用歌声总时长，并明确这是审计结果，不是模型训练质量保证。
10. 使用 soundfile 等轻量工具；如需 librosa，先说明安装成本和版本兼容性。
11. 为审计逻辑编写小型测试，测试数据使用临时生成的短 WAV，不使用真实数据集文件。

运行审计后停止。不要自动创建训练集，也不要改动原始数据。
```

### 验收标准

-   报告能列出歌曲、Group、文件数量和总时长。
-   朗读数据已单独标记。
-   损坏文件和异常路径有记录。
-   原始数据未被修改。

------------------------------------------------------------------------

## 步骤 4：按歌曲划分训练集与留出测试集

**目的：**
避免同一首歌的片段同时出现在训练集和测试集中，降低数据泄漏风险。

### 划分原则

-   目标歌手：用于训练目标音色。
-   训练数据：仅 `Control_Group` 和 `Breathy_Group`。
-   留出数据：至少选择一首完整歌曲，从该歌曲中排除所有目标歌手训练片段。
-   朗读数据：全部排除。
-   源歌手：选择另一位歌手，准备未进入目标模型训练的输入歌声。
-   如果目标歌手和源歌手存在同名歌曲，优先选择共同歌曲作为测试曲目；如果没有共同歌曲，必须在报告中说明，不能伪造同曲对比。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 4：整理 RVC 单说话人训练集与留出测试集”。

要求：
1. 创建 scripts/prepare_gtsinger_dataset.py。
2. 输入使用步骤 3 生成的文件清单和 data/raw/GTSinger。
3. 目标歌手从 configs/project.yaml 读取。
4. 只允许使用 Control_Group 和 Breathy_Group。
5. 排除 Paired_Speech_Group。
6. 按歌曲整体划分训练集和留出测试集，不能按单个音频片段随机拆分。
7. 如果 holdout_song 未设置：
   - 列出所有可选歌曲；
   - 优先检查源歌手是否有同名歌曲；
   - 选择一首文件质量正常、时长足够的共同歌曲作为建议留出曲目；
   - 先把建议写入报告并等待我确认，不要直接覆盖配置。
8. 如果我指定了 holdout_song，则该歌曲下目标歌手的所有 Group 音频都不得进入训练集。
9. 输出目录：
   data/processed/<target_speaker>/rvc_train/
   data/processed/<target_speaker>/holdout_reference/
   data/processed/<source_speaker>/source_test/
10. RVC 单说话人训练目录必须是平铺结构：音频文件直接位于 rvc_train 目录第一层。
11. 文件名必须唯一；不要只用歌曲名导致覆盖。
12. 生成 manifest.csv，记录原始路径、目标路径、歌手、歌曲、Group、时长、用途（train/holdout/source）。
13. 默认采用复制而不是移动；不得修改 data/raw 中的文件。
14. 不要擅自做降噪、变速、变调或音高修正。保留原始音频，由 RVC 预处理流程负责采样率转换和切片。
15. 输出数据集统计报告，至少包含训练时长、留出时长、源音频时长、文件数和歌曲数。
16. 如果训练候选有效时长不足 10 分钟，发出警告并停止后续训练准备，先让我决定是否扩展其他技巧目录。
17. 添加测试，验证朗读组排除、按歌曲留出、文件名唯一和原始数据不变。

先运行脚本的 dry-run/预览模式。将拟选歌曲和统计报告给我确认，不要立即复制全部文件。
```

### 验收标准

-   训练目录只有一个目标歌手。
-   `rvc_train/` 是平铺目录。
-   `Paired_Speech_Group` 不在训练集。
-   留出歌曲没有任何片段混入训练集。
-   原始文件没有被移动或修改。

------------------------------------------------------------------------

## 步骤 5：生成 RVC Colab 训练 Notebook

**目的：** 让 Codex 创建一个可在 Google Colab GPU 上逐单元格运行的
Notebook。Codex 负责生成 Notebook；真正的 GPU 训练由用户在 Colab
中启动。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 5：生成 RVC Colab 训练 Notebook”，不要在本地启动训练。

要求：
1. 创建 notebooks/rvc_public_dataset_training.ipynb。
2. 使用步骤 1 固定的 RVC 官方 commit，不要直接追随不固定的 main 分支。
3. Notebook 必须在 Google Colab 中运行，包含：
   - GPU 检查与 nvidia-smi
   - 用户手动挂载 Google Drive
   - 检查 Drive 中的训练数据目录
   - 克隆/检出固定 commit 的 RVC 官方仓库
   - 按该 commit 的官方说明安装依赖
   - 下载/检查 RVC 所需预训练权重、HuBERT 和 RMVPE 文件
   - 检查数据目录、音频数量、训练时长
   - RVC 数据预处理
   - F0 提取（优先 CUDA + RMVPE）
   - HuBERT 特征提取（v2）
   - 生成或验证 config.json 和 filelist.txt
   - 训练模型
   - 生成 FAISS added index
   - 保存模型、索引、配置、日志到 Google Drive
4. 所有 RVC 命令必须根据固定 commit 的官方 CLI 文档和脚本参数核验。不得照抄未经验证的博客命令。
5. 如果 CLI 不会自动生成 config.json/filelist.txt：
   - 检查官方 WebUI 的一键训练逻辑；
   - 复用官方逻辑或使用官方 WebUI 生成；
   - 训练前检查文件格式与字段数量；
   - 不允许凭猜测手写一个“看起来正确”的 filelist。
6. 首轮配置建议：
   - sample rate：40k
   - version：v2
   - F0：开启
   - F0 method：rmvpe
   - epochs：先设 200，保存间隔以官方支持参数为准
   - batch size：根据 Colab 实际 GPU 显存选择；T4 显存不足时自动提示降低到 4 或更小，不得反复 OOM
   - 单说话人模式
7. 训练目录使用 data/processed/<target_speaker>/rvc_train，不得使用 holdout_reference 或 source_test。
8. Notebook 每个阶段都要有路径检查、文件数检查和失败即停止的断言。
9. Notebook 必须支持从 Google Drive 恢复训练输入和保存结果，避免 Colab 断开后数据丢失。
10. 不要在 Notebook 中写入任何账号 Token 或密码。
11. Notebook 开头写清楚：哪些单元格会下载大文件、哪些单元格会消耗 GPU、哪些单元格需要用户手动确认。
12. 同时创建 docs/colab_training_guide.md，逐单元格说明用途和预期产物。
13. 为 Notebook 做 JSON 结构检查，确保可以被 nbformat 读取。
14. 不要声称 Notebook 已经在真实 Colab GPU 上验证，除非确实运行过并提供运行记录。

完成后停止，告诉我 Notebook 路径、运行前需要上传到 Drive 的目录结构、尚未在 Colab 实测的事项。
```

### 用户需要手动完成

1.  打开 Google Colab：https://colab.research.google.com/
2.  上传或打开 `notebooks/rvc_public_dataset_training.ipynb`。
3.  选择 GPU 运行时。
4.  按 Notebook 提示挂载自己的 Google Drive。
5.  检查路径和许可确认后，再逐单元格运行。

### 验收标准

-   Notebook 能被 `nbformat` 正常读取。
-   每个阶段有输入检查和输出检查。
-   训练、索引、模型保存步骤均与固定 RVC commit 匹配。
-   未实测的部分明确标注"待 Colab 实测"。

------------------------------------------------------------------------

## 步骤 6：完成公开数据集模型训练

**目的：** 在 Colab 中真实完成训练并保存可推理模型。

### 复制给 Codex 的指令

``` text
本轮执行“步骤 6：公开数据集模型训练前检查与故障排查准备”。

注意：你不能假设自己能访问我的 Colab 会话。先检查 Notebook 和文档，不要伪造训练已完成。

要求：
1. 检查 notebooks/rvc_public_dataset_training.ipynb 的所有路径、命令、参数和断言。
2. 对照 docs/upstream_versions.md 中固定的 RVC commit。
3. 检查训练数据只来自目标歌手训练集。
4. 检查训练集和 holdout_reference 没有交叉。
5. 检查 F0、HuBERT、config.json、filelist.txt 的预期产物路径。
6. 检查模型保存位置、索引保存位置和 Google Drive 备份逻辑。
7. 创建 docs/training_troubleshooting.md，至少包含：
   - GPU 不可用
   - CUDA OOM
   - 依赖安装失败
   - F0 提取失败
   - HuBERT 特征提取失败
   - config/filelist 缺失或格式错误
   - 训练中断与恢复
   - 索引生成失败
8. 创建训练完成验收脚本 scripts/verify_rvc_artifacts.py，检查模型文件、索引文件、配置和训练日志是否存在、大小是否合理、是否能读取基本元数据。
9. 不要自动删除旧 checkpoint，不要覆盖已有模型。
10. 不要把模型文件上传到 Git。
11. 完成后给我一份“在 Colab 中执行步骤清单”，我会手动运行训练。

我在 Colab 实际完成训练后，会把日志或错误信息提供给你。届时你只根据实际日志排查，不得编造训练结果。
```

### 用户在 Colab 中的实际验收

训练结束后确认：

-   训练日志显示正常完成。
-   `.pth` 模型文件已保存到 Drive。
-   `.index` 文件已生成。
-   模型、索引、配置、训练日志都能在 Drive 中找到。
-   没有把测试歌曲放入训练集。

------------------------------------------------------------------------

## 步骤 7：生成推理脚本并完成公开数据集转换

**目的：** 使用另一位歌手的中文歌声作为输入，转换成目标歌手音色。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 7：创建 RVC 推理脚本和测试流程”。

要求：
1. 根据步骤 1 固定的 RVC commit 和官方 CLI 文档，核验 infer/cli.py 的真实参数。
2. 创建 scripts/run_inference.py，封装官方推理命令；不要复制或重写 RVC 模型推理算法。
3. 输入文件来自 data/processed/<source_speaker>/source_test/。
4. 模型来自 Google Drive 中保存的公开数据集模型。
5. 输出保存到 audio/output/public_model/。
6. 支持输入单个 WAV 文件，也支持输入目录。
7. 参数至少包括 model、input、output、index、index_rate、pitch、f0_method、protect、rms_mix_rate。
8. 如果索引不存在，必须明确报错；不能在 index_rate > 0 时悄悄假装使用了索引。
9. 第一次推理先使用 pitch=0、f0_method=rmvpe；索引比例使用官方默认或 0.75 起步，后续再做参数对照。
10. 不要默认对输入音频做变调、降噪或速度调整。
11. 记录模型路径、索引路径、输入文件、推理参数、输出文件和运行时间。
12. 创建一份小型参数实验表，允许比较 index_rate 0、0.5、0.75；只有在用户确认后才批量运行多组实验。
13. 创建 scripts/verify_audio_output.py，检查输出文件是否可读取、时长是否合理、是否有静音/削波异常。
14. 不得把他人声音转换结果用于冒充本人或暗示获得了该歌手授权。
15. 本轮先完成脚本和测试；实际推理等待我提供 Colab 模型文件或运行环境。

完成后停止。
```

### 效果检查

准备以下音频：

-   `source_vocal.wav`：源歌手的输入人声。
-   `ai_public_model.wav`：公开数据集模型生成的转换音频。
-   `target_reference.wav`：目标歌手的真实演唱参考（优先选择留出的同曲录音）。

注意：目标参考音频必须来自留出集，不得是训练片段。若不能取得同曲参考，应在实验报告中注明比较条件不完全一致。

------------------------------------------------------------------------

## 步骤 8：制作公开数据集实验报告

**目的：** 把模型训练和推理变成可复现的实验记录，而不是只保留一段音频。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 8：整理公开数据集实验报告”。

要求：
1. 读取实际存在的训练日志、模型配置、数据审计报告、推理参数和输出文件。
2. 创建 reports/public_dataset_experiment.md。
3. 报告必须包含：
   - 数据集名称、官方地址、目标歌手
   - 使用的 Group 和排除的 Group
   - 数据总时长、训练时长、留出时长
   - 数据筛选规则
   - RVC 仓库 commit hash
   - Python/PyTorch/CUDA/GPU 环境
   - 采样率、模型版本、F0、RMVPE、epoch、batch size
   - 模型和索引文件位置（只写相对路径，不嵌入大文件）
   - 推理输入、推理参数和输出路径
   - 音频质量检查结果
   - 人工试听评价
   - 失败案例和已知限制
4. 不得编造 AUC、相似度分数或训练指标；没有测量就写“未测量”。
5. 区分客观检查（时长、采样率、文件可读性）和主观试听评价。
6. 生成一张可填写的 1-5 分主观评价表，评价音色接近度、清晰度、自然度、旋律保留和稳定性。
7. 报告中加入数据许可和音乐版权提醒。
8. 所有结论必须来自真实文件、日志或用户试听反馈。

完成后停止，并列出报告中仍缺少的实测数据。
```

------------------------------------------------------------------------

## 步骤 9：准备并审计本人声音数据

**目的：**
用本人声音训练独立模型。不要把公开歌手数据和个人声音混在一个单说话人模型里。

### 录音建议

-   只录制本人声音，或明确获得录音者授权。
-   建议录制 15--30
    分钟干净清唱作为初始实验目标；实际可用时长以审计结果为准。
-   选择 2--4 首歌曲，覆盖不同音高和演唱方式。
-   尽量无伴奏、无混响、无背景噪声。
-   保存 WAV 原件，不要只保存 MP3。
-   不要把个人原始录音提交到公开 GitHub。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 9：创建个人声音数据审计与整理流程”。

要求：
1. 创建 scripts/audit_personal_voice.py。
2. 输入目录为 data/personal/raw/，没有目录就创建说明文件，不要虚构录音。
3. 递归扫描本人提供的 WAV 音频。
4. 检查时长、采样率、声道数、可读性、峰值、RMS、静音比例和削波情况。
5. 输出 reports/personal_voice_audit.json、CSV 和 Markdown 报告。
6. 不要自动删除、降噪、变调、压缩或覆盖原始录音。
7. 创建 scripts/prepare_personal_dataset.py，将通过质量检查的文件复制到 data/personal/rvc_train/，文件名唯一，保持单层平铺目录。
8. 训练前检查有效时长；如果有效时长不足 10 分钟，先警告并等待我补录或确认，不要自动开始训练。
9. 个人数据与 GTSinger 数据完全分开。
10. .gitignore 必须排除 data/personal/ 下所有录音。
11. 创建 docs/personal_voice_recording_guide.md，列出录音环境、设备、文件格式和质量检查建议。

本轮只创建工具并审计实际存在的文件。没有录音时明确报告“等待用户录音”。
```

### 验收标准

-   本人原始录音保持不变。
-   个人训练目录与公开数据集训练目录完全独立。
-   有效时长和音频质量有报告。
-   未经本人确认，不开始个人模型训练。

------------------------------------------------------------------------

## 步骤 10：复用 RVC 流程训练个人声音模型

**目的：** 使用与公开数据集实验相同的 RVC
版本和主要训练设置，训练个人模型，方便比较。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 10：准备个人声音模型训练”。

要求：
1. 复用步骤 5 的 RVC Colab Notebook 结构，创建 notebooks/rvc_personal_voice_training.ipynb。
2. 使用与公开数据集实验相同的 RVC commit、模型版本、采样率和 F0 方法，除非实际数据或显存要求必须调整。
3. 训练数据只能来自 data/personal/rvc_train/。
4. 实验名使用 my_voice，输出目录与 gtsinger 公开数据集实验分开。
5. 不得把 GTSinger 数据加入个人模型训练目录。
6. 训练前检查个人数据时长、文件数量、损坏文件和数据路径。
7. 训练参数必须根据固定 RVC 版本的官方文档和实际 GPU 显存核验。
8. 保存个人模型、索引、配置和训练日志到 Google Drive 的独立目录。
9. Notebook 不得包含任何账号密钥。
10. 不要声称训练成功；只有我在 Colab 实际运行并提供日志后，才能更新实验状态。

完成后停止，提供 Notebook 使用说明和训练前检查清单。
```

------------------------------------------------------------------------

## 步骤 11：个人模型推理与三方对比

**目的：** 验证模型是否能够把输入歌声转换为本人音色。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 11：个人模型推理与对比音频制作”。

要求：
1. 使用步骤 10 训练的 my_voice 模型和对应索引。
2. 输入音频必须是本人有权使用的歌曲人声，或已取得许可的素材。
3. 创建个人模型推理配置，输出到 audio/output/personal_model/。
4. 录制/导入本人真实演唱参考音频，放在 data/personal/reference/，不得覆盖原件。
5. 对比音频必须尽可能使用同一首歌、同一段落：
   - source_vocal：源人声
   - ai_my_voice：个人模型转换结果
   - ground_truth：本人真实演唱
6. 如需拼接对比音频，先对副本进行响度匹配，不要修改原始文件。
7. 生成 comparison_personal.wav 或 comparison_personal.mp3。
8. 创建 reports/personal_voice_experiment.md，记录数据、训练配置、推理参数、文件路径和人工试听评价。
9. 不得把“声音像本人”写成未经验证的客观结论；需要人工试听并注明评价者和评价方法。
10. 不得公开个人录音或模型权重，除非我明确确认。

完成后停止，列出待我试听和确认的内容。
```

------------------------------------------------------------------------

## 步骤 12：项目文档、GitHub 和最终验收

**目的：**
将项目整理为可复现的作品集，但不自动公开敏感数据或受许可限制的文件。

### 复制给 Codex 的指令

``` text
本轮只执行“步骤 12：项目文档整理与发布前检查”。

要求：
1. 更新 README.md，包含：
   - 项目背景和目标
   - RVC 技术路线
   - GTSinger 数据来源与许可说明
   - 数据预处理流程
   - 模型训练流程
   - 推理流程
   - 实验结果与局限
   - 环境配置和复现步骤
   - 个人声音实验说明
2. 创建 docs/system_architecture.md 和一张项目流程图。
3. README 中区分“公开数据集实验”和“个人声音实验”。
4. 只引用实际完成的实验结果；未完成的部分标注 TODO 或待验证。
5. 检查 .gitignore，确保以下内容不会被提交：
   - 原始数据集
   - 处理后的训练数据
   - 个人录音
   - .pth 模型权重
   - .index 文件
   - Colab 缓存
   - Token、密码和其他密钥
   - 未获授权的歌曲音频
6. 生成发布前检查报告 reports/release_checklist.md。
7. 检查数据集许可、第三方软件许可和音乐版权说明是否完整。
8. 不要自动 git add、git commit、git push，不要创建公开仓库，不要发布 Notion 页面。
9. 如发现可能泄露隐私或版权风险的文件，列出路径并停止发布。
10. 最后给出项目完成情况、尚未完成事项和可公开展示的材料清单。

完成后停止，等待我确认是否发布。
```

------------------------------------------------------------------------

# 3. 项目最终验收清单

## A. 公开数据集实验

-   [ ] 已确认 GTSinger 数据集许可适用于当前用途。
-   [ ] 已下载一个中文歌手的数据。
-   [ ] 已完成数据结构和音频质量审计。
-   [ ] 已按歌曲划分训练集和留出集。
-   [ ] 已排除 Paired_Speech_Group。
-   [ ] 已生成 RVC 单说话人平铺训练目录。
-   [ ] 已固定 RVC 官方仓库 commit。
-   [ ] 已完成 Colab GPU 环境检查。
-   [ ] 已完成数据预处理、F0、HuBERT 特征提取。
-   [ ] 已训练模型并生成索引。
-   [ ] 已完成至少一段中文歌声转换。
-   [ ] 已保存模型、索引、参数和日志。
-   [ ] 已完成实验报告和试听记录。

## B. 个人声音实验

-   [ ] 已录制本人清唱音频。
-   [ ] 已完成音频质量审计。
-   [ ] 已独立整理个人训练目录。
-   [ ] 已使用相同 RVC 版本训练个人模型。
-   [ ] 已生成个人模型索引。
-   [ ] 已完成个人声音转换。
-   [ ] 已制作 AI 版本与本人真唱对比音频。
-   [ ] 已完成个人实验报告。

## C. 工程与展示

-   [ ] 项目代码和配置可以复现。
-   [ ] README 与流程图完整。
-   [ ] 实验结果均有真实文件或日志支持。
-   [ ] 原始数据、个人录音和模型权重未误提交。
-   [ ] 数据许可和音乐版权说明完整。
-   [ ] 发布前检查通过。
-   [ ] GitHub/Notion 发布经过用户明确确认。

------------------------------------------------------------------------

# 4. 常用官方资料

1.  GTSinger 数据集主页\
    https://huggingface.co/datasets/GTSinger/GTSinger

2.  GTSinger 中文女中音目录\
    https://huggingface.co/datasets/GTSinger/GTSinger/tree/main/Chinese/ZH-Alto-1

3.  GTSinger 中文男高音目录\
    https://huggingface.co/datasets/GTSinger/GTSinger/tree/main/Chinese/ZH-Tenor-1

4.  GTSinger 数据集许可\
    https://huggingface.co/datasets/GTSinger/GTSinger/blob/main/dataset_license.md

5.  Hugging Face Hub 下载文档\
    https://huggingface.co/docs/huggingface_hub/guides/download

6.  RVC 官方 GitHub\
    https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

7.  RVC 官方中文 CLI 训练与推理文档\
    https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI/blob/main/docs/cn/cli.md

8.  Google Colab\
    https://colab.research.google.com/

------------------------------------------------------------------------

## 5. 使用时最重要的规则

**不要把本手册全部内容一次性粘贴给 Codex。**

正确做法：

1.  先粘贴步骤 0。
2.  检查 Codex 的输出。
3.  确认无误后，再粘贴步骤 1。
4.  每完成一个步骤，都检查生成的文件和验收结果。
5.  需要下载数据、同意许可、使用 GPU、上传文件或公开发布时，亲自确认。
6.  遇到错误，把完整错误日志交给
    Codex，让它只修复当前步骤，不要让它跳过错误继续执行。

项目的核心顺序是：

**公开数据准备 → 数据审计与筛选 → RVC 环境 → 公开模型训练 → 推理验证 →
个人声音训练 → 效果对比 → 工程化展示。**
