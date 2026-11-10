"""Download Linux/Python 3.12 packages locally from a platform-resolved lock."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import unquote, urlparse

import requests
try:
    import tomllib as tomli
except ModuleNotFoundError:
    import tomli
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'reports/.tmp/server-wheelhouse'
OUTPUT.mkdir(parents=True, exist_ok=True)


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def download(item):
    if item['available_on_server']:
        return 'server-cache', item['filename']
    path = OUTPUT / item['filename']
    if path.is_file() and path.stat().st_size == item['size'] and digest(path) == item['sha256']:
        return 'local-cache', item['filename']
    partial = path.with_suffix(path.suffix + '.part')
    for attempt in range(6):
        try:
            existing = partial.stat().st_size if partial.exists() else 0
            if existing >= item['size']:
                if existing == item['size'] and digest(partial) == item['sha256']:
                    partial.replace(path)
                    return 'downloaded', item['filename']
                partial.write_bytes(b'')
                existing = 0
            headers = {'Range': f'bytes={existing}-'} if existing else {}
            with requests.get(item['url'], headers=headers, stream=True, timeout=(15, 60)) as response:
                response.raise_for_status()
                mode = 'ab' if existing and response.status_code == 206 else 'wb'
                with partial.open(mode) as target:
                    for block in response.iter_content(1024 * 1024):
                        if block:
                            target.write(block)
            if partial.stat().st_size != item['size'] or digest(partial) != item['sha256']:
                raise RuntimeError('Size or SHA-256 mismatch')
            partial.replace(path)
            return 'downloaded', item['filename']
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(2 ** attempt, 15))


def main():
    lock = tomli.loads((ROOT / 'reports/pylock.server.toml').read_text(encoding='utf-8'))
    cached = json.loads((ROOT / 'reports/server_cached_wheels.json').read_text(encoding='utf-8'))
    remote_hashes = {x['sha256'] for x in cached}
    remote_sizes = {x['sha256']: x['bytes'] for x in cached}
    platforms = [f'manylinux_2_{v}_x86_64' for v in range(35, 4, -1)]
    platforms += ['manylinux2014_x86_64', 'manylinux2010_x86_64', 'manylinux1_x86_64', 'linux_x86_64']
    tags = list(cpython_tags((3, 12), abis=['cp312'], platforms=platforms))
    tags += list(compatible_tags((3, 12), interpreter='cp312', platforms=platforms))
    order = {tag: index for index, tag in reversed(list(enumerate(tags)))}
    items, requirements = [], []
    for package in lock['packages']:
        choices = []
        for wheel in package.get('wheels', []):
            filename = unquote(Path(urlparse(wheel['url']).path).name)
            wheel_tags = parse_wheel_filename(filename)[3]
            scores = [order[tag] for tag in wheel_tags if tag in order]
            if scores:
                choices.append((min(scores), wheel, filename))
        if choices:
            _, artifact, filename = min(choices, key=lambda x: x[0])
        else:
            artifact = package.get('sdist')
            if not artifact:
                raise RuntimeError(f'No Linux/Python 3.12 artifact for {package["name"]}')
            filename = unquote(Path(urlparse(artifact['url']).path).name)
        if Path(filename).name != filename:
            raise RuntimeError('Unsafe artifact filename')
        checksum = artifact['hashes']['sha256']
        size = artifact.get('size') or remote_sizes.get(checksum)
        if not size:
            response = requests.get(f'https://pypi.org/pypi/{package["name"]}/{package["version"]}/json', timeout=30)
            response.raise_for_status()
            match = next((x for x in response.json()['urls'] if x['digests']['sha256'] == checksum), None)
            if match:
                size = match['size']
                artifact = {**artifact, 'url': match['url']}
            else:
                response = requests.head(artifact['url'], allow_redirects=True, timeout=30)
                response.raise_for_status()
                size = int(response.headers['Content-Length'])
        item = dict(name=package['name'], version=package['version'], filename=filename,
                    url=artifact['url'], size=size, sha256=checksum,
                    available_on_server=checksum in remote_hashes)
        items.append(item)
        requirements.append(f'{package["name"]}=={package["version"]}')
    (ROOT/'configs/server-offline-requirements.txt').write_text('\n'.join(requirements)+'\n')
    (ROOT/'reports/server_offline_download_manifest.json').write_text(json.dumps(items, indent=2))
    print(json.dumps(dict(packages=len(items), reuse_server_packages=sum(x['available_on_server'] for x in items),
          local_download_bytes=sum(x['size'] for x in items if not x['available_on_server']))), flush=True)
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, item): item for item in items}
        for future in concurrent.futures.as_completed(futures):
            try:
                status, filename = future.result()
                print(f'{status}: {filename}', flush=True)
            except Exception as exc:
                item = futures[future]
                failures.append(dict(filename=item['filename'], error=str(exc)))
    state = dict(status='failed' if failures else 'completed', packages=len(items), failures=failures)
    (ROOT/'reports/server_offline_download_status.json').write_text(json.dumps(state, indent=2))
    print(json.dumps(state), flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
