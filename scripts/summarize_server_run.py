"""Render the actual server receipts into a compact Chinese run/budget report."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT/'reports'


def read(name):
    path = REPORTS/name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


budget = read('server_training_budget.json')
status = read('server_job_status.json') or {}
environment = read('server_environment.json') or {}
metrics = read('server_training.metrics.json')
initial = read('server_training_initial.metrics.json')
test = read('server_inference_smoke_test.json')
early = read('server_early_inference.json')
disk = read('server_disk_usage.json')
stage = {'completed':'已完成', 'training':'训练中', 'building_index':'索引构建中',
         'testing_holdout':'推理验证中', 'failed':'失败'}.get(status.get('stage'), status.get('stage','未读取'))
when = datetime.fromisoformat(status['updated_at']).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S') if status.get('updated_at') else '未知'
lines = ['# 服务器运行与预算报告', '', f'状态：**{stage}**。记录时点：{when}（北京时间）。', '',
         '远端项目：`/srv/ai-vocal-clone`；SSH 别名：`voice-gpu`。',
         f'GPU：{environment.get("gpu", "RTX PRO 6000 Blackwell 96GB")}。',
         f'Python {environment.get("python")} / Torch {environment.get("torch")} / CUDA {environment.get("cuda")}；CUDA 运算自检通过。',
         '主机物理内存 251GiB，但当前容器限制为 **32GiB 内存、32 核 CPU 配额**。', '',
         '## 数据与检查', '',
         '- 729 个原始 WAV 上传后逐一通过 SHA-256 校验，原始数据保持不变。',
         '- 训练为 462 条、64.58 分钟；留出《水星记》24 条、3.37 分钟；配对朗读排除。',
         '- 预处理生成 1169 个训练切片，RMVPE 和 HuBERT 提取全部成功。',
         '- 135 项离线依赖文件通过校验；环境依赖检查通过；官方预训练资源固定版本并已上传。', '',
         '## Batch 实测与预算', '',
         '| Batch | 稳定每轮秒数 | 显存峰值 GiB | 主机 PSS 峰值 GiB |',
         '|---:|---:|---:|---:|']
for item in budget['benchmarks']:
    if item.get('steady_epoch_seconds'):
        lines.append(f'| {item["batch_size"]} | {item["steady_epoch_seconds"]:.2f} | {item["peak_gpu_mib"]/1024:.2f} | {item.get("peak_host_pss_mib",0)/1024:.2f} |')
    else:
        lines.append(f'| {item["batch_size"]} | 失败，见日志 | — | — |')
lines += ['', '每个配置短跑 3 轮，后两轮中位数排除预热，期间不写大检查点。显存/内存为本项目训练进程及后代的采样峰值；PSS 不包括完整文件缓存。共享服务器上 batch 16 阶段存在其他 GPU 负载，表格不是严格控制负载的性能基准。', '',
          f'正式选择 **batch {budget["chosen_batch_size"]}**，目标 100 epoch，每 10 epoch 保存。',
          f'同配置从头训练 100 轮预算为 **{budget["estimated_training_hours_low"]*60:.1f}–{budget["estimated_training_hours_high"]*60:.1f} 分钟**，即 {budget["estimated_training_hours_low"]:.2f}–{budget["estimated_training_hours_high"]:.2f} GPU 小时；索引和推理另计。',
          f'项目磁盘占用约 {disk["bytes"]/1024**3:.1f}GiB，建议预留 40–50GB；容器内存按 32GB 预算。没有新增付费云资源，未提供现有服务器计费单价，因此不编造金额。' if disk else '部署初期磁盘占用约 27GB，建议预留 40–50GB；容器内存按 32GB 预算。没有新增付费云资源，未提供现有服务器计费单价，因此不编造金额。', '',
          '## 实际训练与测试', '',
          '前 10 轮使用 batch 16，保存检查点后用 batch 64 恢复；上游从 checkpoint 的 epoch 10 重跑该轮，再继续到目标轮次。']
if metrics and metrics.get('exit_code') == 0:
    seconds = metrics['elapsed_seconds'] + (initial['elapsed_seconds'] if initial else 0)
    lines += [f'两段正式训练实际累计耗时 **{seconds/60:.2f} 分钟**（含进程启动、模型读取及检查点保存，不含安装和短跑）。',
              f'恢复阶段本项目显存采样峰值 {metrics["peak_gpu_mib"]/1024:.2f}GiB，主机 PSS 采样峰值 {metrics.get("peak_host_pss_mib",0)/1024:.2f}GiB。']
else:
    lines += ['正式训练尚在进行，完成后的实际计时以 `server_training.metrics.json` 为准。']
if test:
    lines += [f'最终模型留出音频推理：输入 {test["input_seconds"]:.2f} 秒，输出 {test["output_seconds"]:.2f} 秒，采样率 {test["sample_rate"]}Hz；音频可读且数值有限。',
              '最终权重与 added 索引见远端 `models/gtsinger_zh_alto/`，最终推理音频见 `audio/output/server_public/`。']
elif early:
    lines += [f'第 10 轮模型已完成 CPU/无索引技术检查：输入 {early["input_seconds"]:.2f} 秒、输出 {early["output_seconds"]:.2f} 秒，{early["sample_rate"]}Hz。测试音频见 `audio/output/server_public_e10/`。']
lines += ['这些测试使用未进入训练的目标歌手片段，属于技术回归检查；尚未测量跨歌手转换质量或人工试听评分。', '',
          '## 查看服务器任务', '', '```bash', 'ssh voice-gpu', 'cd /srv/ai-vocal-clone',
          'cat reports/server_job_status.json', 'tail -n 20 reports/server_training.log', 'tmux list-sessions', '```', '',
          '数据仅用于当前私人验证。许可含非商业及额外条款，原文已保存；未公开数据、模型或音频。']
path = REPORTS/'server_training_budget.md'
path.write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
print(path)
