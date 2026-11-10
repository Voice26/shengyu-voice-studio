"""Check the Windows web client and its configured GPU worker without creating a conversion."""
import argparse
import json
import re
import shutil

from platform_app.server import ROOT, Studio, save_json


def configure_connection(path, config):
    print(f"当前 GPU 服务器：{config['ssh_host']}    项目目录：{config['remote_root']}")
    if input('沿用请按回车；更换服务器请输入 S 再回车：').strip().lower() != 's':
        return
    host = input(f"SSH 别名或 用户@主机 [{config['ssh_host']}]：").strip() or config['ssh_host']
    directory = input(f"Linux 项目绝对路径 [{config['remote_root']}]：").strip() or config['remote_root']
    if not re.fullmatch(r'(?:[\w.][\w.-]*@)?(?:[\w][\w.-]*|\[[0-9a-fA-F:]+\])', host):
        raise ValueError('SSH 地址格式有误。例如 voice-gpu 或 singer@myserver。')
    if not directory.startswith('/') or any(ord(char) < 32 for char in directory):
        raise ValueError('服务器目录需要以 / 开头，例如 /srv/ai-vocal-clone。')
    config.update(ssh_host=host, remote_root=directory.rstrip('/') or '/')
    save_json(path, config)
    print('连接设置已保存。已运行的网页服务需要停止并重新启动才能使用新设置。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--non-interactive', action='store_true')
    parser.add_argument('--skip-server-check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'configs/platform.json'
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    if not args.non_interactive:
        configure_connection(path, config)
    # Studio recovers interrupted jobs when it starts. Keep this probe away from live jobs.
    studio = Studio(config, ROOT / '.tools' / 'web-check')
    try:
        voices = studio.models()
        if voices:
            print('网页可选音色：' + '、'.join(v['name'] for v in voices))
        else:
            print('暂未发现可用音色。把下载的模型包解压到项目根目录，再刷新网页。')
            print('模型下载：https://github.com/Voice26/shengyu-voice-studio/releases/tag/v1.0.0')
        missing = [cmd for cmd in ('ssh', 'scp') if not shutil.which(cmd)]
        if missing:
            print('缺少 ' + '、'.join(missing) + '。要使用服务器换声，请在 Windows「可选功能」中安装 OpenSSH 客户端。')
        elif not args.skip_server_check:
            print(f"正在检查 {config['ssh_host']} 的 GPU 推理环境…", flush=True)
            status = studio.health()
            if status.get('ready'):
                print('GPU 服务器就绪：' + status.get('gpu', ''))
                remote = status.get('models', {})
                unavailable = [v['name'] for v in voices if not remote.get(v['id'])]
                if unavailable:
                    print('以下音色在服务器缺少权重或索引：' + '、'.join(unavailable))
            else:
                print('服务器尚未就绪：' + str(status.get('message', '连接失败')))
                print('网页可以启动。换声前请确认此电脑能通过 SSH 免密连接，且远端已部署 GPU 环境和权重。')
    finally:
        studio.queue.shutdown(wait=True)
    print(f"下一步：双击「启动换声平台.bat」，打开 http://127.0.0.1:{config['port']}/")


if __name__ == '__main__':
    try:
        main()
    except (OSError, KeyError, ValueError) as exc:
        raise SystemExit(f'配置读取或保存失败：{exc}')
