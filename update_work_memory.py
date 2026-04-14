#!/usr/bin/env python3
"""
WORK_MEMORY.md 갱신 유틸리티.
  append_entry(category, content)  -- 오늘 날짜 섹션에 항목 추가
  compress_old_entries()           -- compress_memory.py 호출
  git_push(msg)                    -- add+commit+push, 실패 시 bibi-gateway 알림
CLI:
  python3 update_work_memory.py --category "결정" --content "XXX 완료"
  python3 update_work_memory.py --compress
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

WORK_MEMORY_PATH = "/root/docs/WORK_MEMORY.md"
COMPRESS_SCRIPT  = "/root/docs/compress_memory.py"
VENV_PYTHON      = "/root/.hermes/hermes-agent/venv/bin/python3"
BIBI_GATEWAY_URL = "http://localhost:5114/webhook/bibi-incoming"
VALID_CATEGORIES = ["결정", "인사이트", "논의 중", "보류"]


def kst_today():
    ts = datetime.now(timezone.utc).timestamp() + 9 * 3600
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


def notify_telegram(message):
    try:
        import json, urllib.request
        data = json.dumps({"message": message}).encode("utf-8")
        req  = urllib.request.Request(
            BIBI_GATEWAY_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[update_work_memory] 텔레그램 알림 실패: {e}", file=sys.stderr)


def append_entry(category, content):
    if category not in VALID_CATEGORIES:
        print(f"[update_work_memory] 유효하지 않은 카테고리: {category}", file=sys.stderr)
        sys.exit(1)

    with open(WORK_MEMORY_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    today       = kst_today()
    date_header = "### " + today
    cat_header  = "#### " + category
    new_item    = "- " + content

    recent_match = re.search(r"## \[최근 3일\]", raw)
    weekly_match = re.search(r"## \[1~2주 전\]", raw)
    if not recent_match:
        print("[update_work_memory] '## [최근 3일]' 섹션 없음", file=sys.stderr)
        sys.exit(1)

    recent_end     = weekly_match.start() if weekly_match else len(raw)
    before_recent  = raw[:recent_match.end()]
    recent_section = raw[recent_match.end():recent_end]
    after_recent   = raw[recent_end:]

    date_pos = recent_section.find(date_header)
    if date_pos == -1:
        insert = "\n" + date_header + "\n\n" + cat_header + "\n" + new_item + "\n"
        recent_section = insert + recent_section
    else:
        after_date       = recent_section[date_pos + len(date_header):]
        next_date_m      = re.search(r"\n###|\n##", after_date)
        today_block      = after_date[:next_date_m.start()] if next_date_m else after_date
        rest_after_today = after_date[next_date_m.start():] if next_date_m else ""

        cat_pos = today_block.find(cat_header)
        if cat_pos == -1:
            today_block = today_block.rstrip("\n") + "\n\n" + cat_header + "\n" + new_item + "\n"
        else:
            after_cat  = today_block[cat_pos + len(cat_header):]
            next_cat_m = re.search(r"\n####|\n###|\n##", after_cat)
            cat_items  = after_cat[:next_cat_m.start()] if next_cat_m else after_cat
            rest_cat   = after_cat[next_cat_m.start():] if next_cat_m else ""
            cat_items  = cat_items.rstrip("\n") + "\n" + new_item + "\n"
            today_block = today_block[:cat_pos + len(cat_header)] + cat_items + rest_cat

        recent_section = (
            recent_section[:date_pos + len(date_header)]
            + today_block + rest_after_today
        )

    new_raw = before_recent + recent_section + after_recent
    with open(WORK_MEMORY_PATH, "w", encoding="utf-8") as f:
        f.write(new_raw)

    print(f"[update_work_memory] 추가: [{category}] {content}")


def compress_old_entries():
    python = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
    result = subprocess.run([python, COMPRESS_SCRIPT], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[update_work_memory] 압축: {result.stdout.strip()}")
    else:
        print(f"[update_work_memory] 압축 실패: {result.stderr.strip()}", file=sys.stderr)


def git_push(commit_msg=None):
    if commit_msg is None:
        commit_msg = "update: WORK_MEMORY " + kst_today()
    try:
        subprocess.run(["git", "-C", "/root/docs", "add", "WORK_MEMORY.md"],
                       check=True, capture_output=True)
        diff = subprocess.run(["git", "-C", "/root/docs", "diff", "--cached", "--quiet"],
                               capture_output=True)
        if diff.returncode == 0:
            print("[update_work_memory] 변경 없음 -- push 생략")
            return True
        subprocess.run(["git", "-C", "/root/docs", "commit", "-m", commit_msg],
                       check=True, capture_output=True)
        subprocess.run(["git", "-C", "/root/docs", "push"],
                       check=True, capture_output=True)
        print(f"[update_work_memory] push 완료: {commit_msg}")
        return True
    except subprocess.CalledProcessError as e:
        err = (e.stderr.decode(errors="replace") if e.stderr else str(e)).strip()
        msg = "WORK_MEMORY git push 실패\n" + err[:200]
        print(f"[update_work_memory] {msg}", file=sys.stderr)
        notify_telegram(msg)
        return False


def main():
    parser = argparse.ArgumentParser(description="WORK_MEMORY.md 갱신")
    parser.add_argument("--category", "-c")
    parser.add_argument("--content",  "-t")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--no-push",  action="store_true")
    args = parser.parse_args()

    if args.compress:
        compress_old_entries()
        if not args.no_push:
            git_push("update: compress WORK_MEMORY")
        return

    if not args.category or not args.content:
        parser.print_help()
        sys.exit(1)

    append_entry(args.category, args.content)
    if not args.no_push:
        git_push("update: " + args.category + " -- " + args.content[:40])


if __name__ == "__main__":
    main()
