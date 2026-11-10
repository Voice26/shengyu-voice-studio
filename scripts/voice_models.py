"""Allowlisted conversion targets used by the loopback studio and the GPU worker."""
DEFAULT_MODEL = 'gtsinger_zh_alto'
MODELS = {
    'personal_20261110': dict(
        name='我的音色 · 第二版', speaker='个人录音', description='6 段录音训练', epochs=80,
        weight='models/personal_20261110/personal_20261110.pth',
        index='models/personal_20261110/voice.index',
        reference='models/personal_20261110/reference.wav', reference_title='群青 · 留出的原声片段'),
    'personal_20261109': dict(
        name='我的音色', speaker='个人录音', description='个人歌声 · 第一版', epochs=80,
        weight='models/personal_20261109/personal_20261109.pth',
        index='models/personal_20261109/voice.index',
        reference='models/personal_20261109/reference.wav', reference_title='群青 · 留出的原声片段'),
    DEFAULT_MODEL: dict(
        name='清柔女声', speaker='ZH-Alto-1', description='中文女声 · GTSinger', epochs=100,
        weight='models/gtsinger_zh_alto/gtsinger_zh_alto.pth',
        index='models/gtsinger_zh_alto/added_IVF4777_Flat_nprobe_1_gtsinger_zh_alto_v2.index',
        reference='audio/output/server_public/holdout_input.wav', reference_title='水星记 · 原声片段'),
}
