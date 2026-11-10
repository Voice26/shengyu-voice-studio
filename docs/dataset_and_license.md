# GTSinger 数据来源

公开目标音色使用 GTSinger 的 `Chinese/ZH-Alto-1/Breathy/` 子集，固定数据版本为 `4426c862beed558b7e1cb8a4dce7e8c0c83bb208`。[GTSinger 项目](https://huggingface.co/datasets/GTSinger/GTSinger)

训练使用 `Control_Group` 和 `Breathy_Group` 的歌唱片段，排除 `Paired_Speech_Group` 的朗读片段。工作台中的中文男声示例来自 `ZH-Tenor-1`，英文女声示例来自 `EN-Alto-1`，两位歌手均仅用于跨歌手推理测试。[测试记录](../reports/cross_speaker_test.md)

该版本的数据许可列出 CC BY-NC-SA 4.0（署名、非商业、相同方式共享），另含责任承担与论文引用等条款。具体条件见[随仓库保存的许可原文](dataset_license.md)和[固定数据版本的上游许可](https://huggingface.co/datasets/GTSinger/GTSinger/blob/4426c862beed558b7e1cb8a4dce7e8c0c83bb208/dataset_license.md)。
