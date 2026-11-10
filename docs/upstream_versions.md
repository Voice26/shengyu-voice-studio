# 上游版本与兼容性

- 官方仓库：https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- 默认分支：main；本轮固定 commit：`81eed5e8f68b6bed1789f682fe78cdd324495afc`。
- 随仓库分发的上游源码位于 `third_party/RVC-WebUI`。
- 软件许可：MIT，原文见上游 `LICENSE`。
- 数据环境：项目 `.venv` 使用 Python 3.10.15；锁定依赖见 `requirements-data.lock.txt`。
- RVC 环境：当前官方 README 指定 Python **3.12 x64**，推荐 Ubuntu 24.04。未在本机 3.10 环境中安装 RVC 大型依赖。
- NVIDIA 安装：按官方两阶段方案安装 Torch/Torchaudio 2.7.1（cu118 或 cu128），然后对应的 `requirments_*_py312.txt`。文件名确实拼作 `requirments`。
- 当前 HuBERT 使用 `assets/hubert_base/{config.json,preprocessor_config.json,pytorch_model.bin}`，不是旧教程中的单个 `hubert_base.pt`。

## 已核验入口

在 RVC 根目录运行以下命令，并将该目录加入 `PYTHONPATH`。实验名、输入路径和 batch size 按实际环境填写。

```text
python -m train.preprocess DATA_DIR 40000 2 logs/EXPERIMENT False 3.7
python -m train.dataset.extract_f0 cuda 1 0 0 logs/EXPERIMENT true
python -m train.dataset.extract_hubert_feature cuda:0 1 0 0 logs/EXPERIMENT v2 true
python -m train.train -e EXPERIMENT -sr 40k -f0 1 -bs 4 -g 0 -te 100 -se 5 -pg assets/pretrained_v2/f0G40k.pth -pd assets/pretrained_v2/f0D40k.pth -l 1 -c 0 -sw 1 -v v2
python -m train.train_index EXPERIMENT v2 assets/indices 2 single
python -m infer.cli --model MODEL.pth --input INPUT.wav --output OUTPUT.wav --pitch 0 --f0-method rmvpe --index INDEX.index --index-rate 0.75
```

40k/v2/F0/RMVPE 和 CUDA 均已在服务器运行验证。上面 batch size/epoch 为示例；服务器正式实测选择 batch 64、目标 100 epoch，详情见 `reports/server_training_budget.md`。Colab Notebook 尚未在 Colab 实测。

服务器首次运行发现直接 `python train/preprocess.py` 会使脚本目录优先进入 sys.path，误把 `train/train.py` 当成顶层 train 模块并触发循环导入。项目启动器和 Notebook 已统一为 `python -m ...`，保持参数与上游源码不变。Matplotlib 在官方范围内约束为 `<3.10`，兼容上游图像日志接口。

`config.json` 与 `filelist.txt` 的生成逻辑已核对 `webui.py` 1169–1300 附近：v2/40k 仍复用 `configs/v1/40k.json`；每条记录为 WAV、768维特征、粗 F0、连续 F0、ID 0 五字段，以 `|` 分隔，并加入两条官方 mute 记录。辅助脚本 `scripts/prepare_rvc_config.py` 实现此单歌手格式，缺失特征会报错。
