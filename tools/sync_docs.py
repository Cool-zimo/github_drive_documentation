#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档同步脚本：github_drive_documentation → Github_Drive-Documentation

两个文档仓库需要同时维护，内容必须一致。
在旧仓库的每个页面顶部自动加一条迁移横幅，引导用户去新地址。

单向同步（新 → 旧），冲突时强制覆盖。

用法：
    export GITHUB_TOKEN=xxx
    python3 sync_docs.py              # 同步并加横幅
    python3 sync_docs.py --dry-run    # 只看要改什么，不实际提交
    python3 sync_docs.py --rollback   # 回滚到上一次同步前
    python3 sync_docs.py --rollback <sha>
    python3 sync_docs.py --history    # 查看可回滚的历史点

回滚机制：
    每次同步前会把目标仓库 main 的当前状态压到 BACKUP_BRANCH，
    并在本地 .sync_rollback.json 记录回滚点。
    所以强制覆盖是安全的 —— 随时能退回同步前。
"""
import json
import base64
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

SRC = 'github_drive_documentation'
DST = 'Github_Drive-Documentation'
OWNER = 'Cool-zimo'

# 同步前的快照分支（每次覆盖，只保留最近一次完整状态）
BACKUP_BRANCH = 'sync-backup'
# 本地回滚点记录
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.sync_rollback.json')
# 最多保留多少个历史回滚点
MAX_HISTORY = 10

NEW_URL = 'https://cool-zimo.github.io/github_drive_documentation/'
NEW_REPO = 'https://github.com/Cool-zimo/github_drive_documentation'

TK = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
if not TK:
    sys.exit('需要 GITHUB_TOKEN 环境变量')

DRY = '--dry-run' in sys.argv


def api(path, method='GET', body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request('https://api.github.com' + path, data=data, method=method)
    for k, v in [('Authorization', f'Bearer {TK}'),
                 ('Accept', 'application/vnd.github+json'),
                 ('Content-Type', 'application/json'),
                 ('User-Agent', 'docs-sync')]:
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode('utf-8', 'ignore')
    except Exception as e:
        return 0, str(e)


def get_file(repo, path):
    c, d = api(f'/repos/{OWNER}/{repo}/contents/{path}')
    if c != 200 or not isinstance(d, dict):
        return None, None
    return base64.b64decode(d['content']).decode('utf-8'), d['sha']


def put_file(repo, path, content, sha=None, msg=None, retries=3):
    """
    写入文件。强制覆盖语义：
      - 不带 sha 时是创建/覆盖
      - 带 sha 但过期（409）→ 重取最新 sha 再写，最多重试 retries 次
    这样并发写入或文件被外部改过也能写成功，不会卡在冲突上。
    """
    for attempt in range(retries):
        body = {'message': msg or f'docs: 同步 {path}',
                'content': base64.b64encode(content.encode('utf-8')).decode()}
        if sha:
            body['sha'] = sha
        c, err = api(f'/repos/{OWNER}/{repo}/contents/{path}', 'PUT', body)
        if c in (200, 201):
            return True
        # 409 = sha 不匹配（文件被改过）或没有 sha 但文件已存在
        if c == 409 or (c == 422 and 'sha' in str(err).lower()):
            _, fresh = get_file(repo, path)
            if fresh:
                sha = fresh          # 用最新 sha 重试 → 强制覆盖
                time.sleep(0.3)
                continue
        if c == 404 and sha:
            # 记录里带了 sha 但文件其实不存在（被删了）→ 去掉 sha 重建
            sha = None
            continue
        break
    print(f'    写入失败 HTTP {c}: {str(err)[:80]}')
    return False


def put_file_raw(repo, path, b64content, sha=None, msg=None, retries=3):
    """写入已经是 base64 的内容（用于二进制资源，避免解码再编码）"""
    for attempt in range(retries):
        body = {'message': msg or f'docs: 同步 {path}', 'content': b64content}
        if sha:
            body['sha'] = sha
        c, err = api(f'/repos/{OWNER}/{repo}/contents/{path}', 'PUT', body)
        if c in (200, 201):
            return True
        if c == 409 or (c == 422 and 'sha' in str(err).lower()):
            _, fresh = get_file(repo, path)
            if fresh:
                sha = fresh
                time.sleep(0.3)
                continue
        if c == 404 and sha:
            sha = None
            continue
        break
    print(f'    写入失败 HTTP {c}: {str(err)[:80]}')
    return False


def list_files(repo):
    c, t = api(f'/repos/{OWNER}/{repo}/git/trees/main?recursive=1')
    if c != 200:
        sys.exit(f'无法列出 {repo}: HTTP {c}')
    return [x for x in t['tree'] if x['type'] == 'blob']


# ---------- 回滚 ----------

def get_ref(repo, branch):
    c, d = api(f'/repos/{OWNER}/{repo}/git/ref/heads/{branch}')
    if c == 200 and isinstance(d, dict):
        return d['object']['sha']
    return None


def set_ref(repo, branch, sha):
    """
    强制把分支指向某个 commit（存在则 PATCH，不存在则 POST）

    注意 force=True 是必须的：回滚是把分支往回退，
    属于非快进更新。GitHub 的 PATCH ref 默认 force=false，
    非快进会被拒绝（422），表现为"回滚失败"。
    """
    c, _ = api(f'/repos/{OWNER}/{repo}/git/refs/heads/{branch}', 'PATCH',
               {'sha': sha, 'force': True})
    if c == 200:
        return True
    c, _ = api(f'/repos/{OWNER}/{repo}/git/refs', 'POST',
               {'ref': f'refs/heads/{branch}', 'sha': sha})
    return c in (200, 201)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            return json.load(open(STATE_FILE, encoding='utf-8'))
        except Exception:
            pass
    return {'points': []}


def save_state(state):
    state['points'] = state['points'][-MAX_HISTORY:]
    json.dump(state, open(STATE_FILE, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


def record_rollback_point(sha, note='', kind='pre-sync'):
    """
    记录一个可回滚的点。
    kind: 'pre-sync'（同步前，--rollback 默认回到这里）
          'pre-rollback'（回滚前，防止回滚错了回不去）
    """
    state = load_state()
    state['points'].append({
        'sha': sha,
        'kind': kind,
        'time': datetime.now().isoformat(timespec='seconds'),
        'note': note
    })
    save_state(state)


def do_rollback(target_sha=None):
    """把 DST 的 main 重置到指定 commit"""
    state = load_state()
    points = state.get('points', [])

    if target_sha is None:
        # 优先级：本地 [同步前] 记录 → 备份分支。
        # 备份分支在 CI 里尤其重要：Actions 每次都是全新环境，
        # 本地 .sync_rollback.json 不会留存，靠分支才能跨运行回滚。
        pre = [x for x in points if x.get('kind') == 'pre-sync']
        if pre:
            p = pre[-1]
        else:
            bc = get_ref(DST, BACKUP_BRANCH)
            if not bc:
                sys.exit('没有可用的回滚点（本地无记录，备份分支也不存在）')
            p = {'sha': bc, 'time': '?', 'note': f'{BACKUP_BRANCH} 分支（上次同步前）'}
        target_sha = p['sha']
    else:
        p = next((x for x in points if x['sha'].startswith(target_sha)), None)
        if not p:
            # 允许直接传完整的、不在记录里的 sha
            p = {'sha': target_sha, 'time': '?', 'note': '手动指定'}

    # 先确认这个 commit 真的存在
    c, d = api(f'/repos/{OWNER}/{DST}/commits/{target_sha}')
    if c != 200:
        sys.exit(f'commit 不存在: {target_sha} (HTTP {c})')

    cur = get_ref(DST, 'main')
    if cur == target_sha:
        print(f'main 已指向 {target_sha[:8]}，无需回滚')
        return

    # 回滚前也留个快照，防止回滚错了回不去
    if cur:
        set_ref(DST, BACKUP_BRANCH, cur)
        record_rollback_point(cur, f'回滚到 {target_sha[:8]} 之前的状态', 'pre-rollback')

    if not set_ref(DST, 'main', target_sha):
        sys.exit('回滚失败：无法更新 main')

    c, _ = api(f'/repos/{OWNER}/{DST}/pages/builds', 'POST')
    print(f'✓ 已回滚 {DST} 的 main')
    print(f'   回滚到: {target_sha[:8]}  ({p.get("time")})')
    if p.get('note'):
        print(f'   说明:   {p["note"]}')
    if cur:
        print(f'   （回滚前状态已存到 {BACKUP_BRANCH}: {cur[:8]}）')
    print(f'   Pages 重建 HTTP {c}')


def list_commits(repo, branch, limit=10):
    c, d = api(f'/repos/{OWNER}/{repo}/commits?sha={branch}&per_page={limit}')
    if c != 200 or not isinstance(d, list):
        return []
    return [{
        'sha': x['sha'],
        'time': (x['commit']['author']['date'] or '').replace('T', ' ').replace('Z', ''),
        'note': x['commit']['message'].split('\n')[0]
    } for x in d]


def do_history():
    state = load_state()
    points = state.get('points', [])
    cur = get_ref(DST, 'main')

    if points:
        print(f'本地记录（{DST}）：\n')
        for i, p in enumerate(reversed(points), 1):
            mark = ' ← 当前' if p['sha'] == cur else ''
            kind = {'pre-sync': '[同步前]', 'pre-rollback': '[回滚前]'}.get(
                p.get('kind'), '')
            print(f'  {i:2}. {p["sha"][:8]}  {p["time"]}  {kind} {p.get("note","")}{mark}')

    bc = get_ref(DST, BACKUP_BRANCH)
    print(f'\n备份分支 {BACKUP_BRANCH}: {bc[:8] if bc else "（不存在）"}')

    # git 历史是最终的回滚依据 —— 本地记录会随环境丢失，git 不会
    print(f'\n{BACKUP_BRANCH} 分支历史（上次同步前的状态，可直接 --rollback）：\n')
    for c in list_commits(DST, BACKUP_BRANCH, 8):
        print(f'  {c["sha"][:8]}  {c["time"][:19]}  {c["note"][:56]}')

    print(f'\nmain 分支最近提交：\n')
    for c in list_commits(DST, 'main', 8):
        mark = ' ← 当前' if c['sha'] == cur else ''
        print(f'  {c["sha"][:8]}  {c["time"][:19]}  {c["note"][:56]}{mark}')

    print(f'\n  --rollback           = 回到最近的 [同步前] 点（本地无记录时用备份分支）')
    print(f'  --rollback <sha>     = 回到指定 commit（可从上面的历史里挑）')


def snapshot_before_sync():
    """同步前把 main 当前状态压到备份分支，并记录回滚点"""
    cur = get_ref(DST, 'main')
    if not cur:
        print('  ! 无法读取 main，跳过快照')
        return False
    ok = set_ref(DST, BACKUP_BRANCH, cur)
    if ok:
        record_rollback_point(cur, '同步前的状态')
        print(f'  快照 {BACKUP_BRANCH} ← {cur[:8]}（可回滚）')
    else:
        print('  ! 快照失败（继续同步，但无法回滚到此刻）')
    return ok


# ---------- 迁移横幅 ----------

# 用 HTML 注释做标记：GitHub 渲染时忽略，删除时可精确定位，
# 保证"去掉横幅后 == 原文"，同步比对不会出现假差异
MARK_S = '<!-- MIGRATION-BANNER-START -->'
MARK_E = '<!-- MIGRATION-BANNER-END -->'

BANNER_HOME = MARK_S + """
<br>

> # ⚠️ 本文档已迁移
>
> **新地址：{url}**
>
> 本仓库仅作镜像保留，**不再单独更新**。所有新内容都在上面这个地址。
> 请更新你的收藏夹 👆
>
> [👉 前往新文档]({url}) · [📦 新仓库]({repo})

<br>

---

""".format(url=NEW_URL, repo=NEW_REPO) + MARK_E + "\n\n"

BANNER_PAGE = MARK_S + """
> ⚠️ **本文档已迁移到 [{url}]({url})** —— 本页为旧镜像，不再单独更新。

""".format(url=NEW_URL) + MARK_E + "\n\n"


def strip_old_banner(text):
    """按标记整块删除旧横幅，保证能还原成原文"""
    while MARK_S in text and MARK_E in text:
        i = text.index(MARK_S)
        j = text.index(MARK_E) + len(MARK_E)
        # 吃掉标记后的连续换行，然后直接拼接。
        # 不能额外补 '\n' —— 横幅块自带结尾换行，
        # 补了就会多出空行，导致同步比对出现假差异。
        k = j
        while k < len(text) and text[k] == '\n':
            k += 1
        text = text[:i] + text[k:]
    return text


def add_banner(path, text):
    text = strip_old_banner(text)
    if path == 'README.md':
        return BANNER_HOME + text.lstrip('\n')
    lines = text.split('\n')
    if lines and lines[0].startswith('# '):
        # 插到一级标题之后。通常空一行保持 Markdown 结构；
        # 若原文标题紧贴正文（非标准写法），则只换一行，避免改变原结构
        sep = '\n\n' if (len(lines) < 2 or not lines[1].strip()) else '\n'
        return lines[0] + sep + BANNER_PAGE + '\n'.join(lines[1:]).lstrip('\n')
    return BANNER_PAGE + text


def main():
    # 先处理子命令
    if '--history' in sys.argv:
        do_history()
        return
    if '--rollback' in sys.argv:
        idx = sys.argv.index('--rollback')
        sha = sys.argv[idx + 1] if len(sys.argv) > idx + 1 \
            and not sys.argv[idx + 1].startswith('--') else None
        do_rollback(sha)
        return

    print(f'同步 {SRC} → {DST}（强制覆盖）\n')
    files = list_files(SRC)
    md_files = [x for x in files if x['path'].endswith('.md')]

    changed = []
    same = []

    for f in sorted(md_files, key=lambda x: x['path']):
        path = f['path']
        src_text, _ = get_file(SRC, path)
        if src_text is None:
            print(f'  ? 跳过（读不到） {path}')
            continue

        dst_text, dst_sha = get_file(DST, path)
        target = add_banner(path, src_text)

        if dst_text == target:
            same.append(path)
            continue

        changed.append((path, target, dst_sha))
        action = '新增' if dst_sha is None else '更新'
        print(f'  {action}  {path:34} {len(target):>6} 字节')

    print(f'\n需同步 {len(changed)} 个，已一致 {len(same)} 个')

    # assets 也要同步（图标）
    assets = [x for x in files if x['path'].startswith('assets/')]
    pending_assets = []
    for f in assets:
        path = f['path']
        c, d = api(f'/repos/{OWNER}/{DST}/contents/{path}')
        if c == 200 and d.get('size') == f['size']:
            continue
        pending_assets.append(path)
        print(f'  资源  {path}')

    if DRY:
        print('\n[dry-run] 未实际提交')
        return

    if not changed and not pending_assets:
        print('\n全部已同步，无需提交')
        return

    # 写之前先快照 —— 强制覆盖是可回滚的
    print('\n创建回滚点...')
    snapshot_before_sync()

    ok = True
    for path, content, sha in changed:
        if not put_file(DST, path, content, sha, f'📄 同步 {path}（来自 {SRC}）'):
            print(f'  ✗ 失败 {path}')
            ok = False

    for path in pending_assets:
        c, d = api(f'/repos/{OWNER}/{SRC}/contents/{path}')
        if c != 200:
            continue
        _, d2 = api(f'/repos/{OWNER}/{DST}/contents/{path}')
        sha = d2.get('sha') if isinstance(d2, dict) else None
        # 走 put_file 以便享受 409 重试
        raw = base64.b64decode(d['content'])
        if not put_file_raw(DST, path, d['content'], sha, f'🖼️ 同步 {path}'):
            print(f'  ✗ 资源失败 {path}')
            ok = False

    if ok:
        c, _ = api(f'/repos/{OWNER}/{DST}/pages/builds', 'POST')
        print(f'\n✓ 同步完成，Pages 重建 HTTP {c}')
        print(f'  如需撤销：python3 sync_docs.py --rollback')
    else:
        print(f'\n⚠️ 有文件写入失败，可用 --rollback 撤销')


if __name__ == '__main__':
    main()
