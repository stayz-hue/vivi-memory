#!/usr/bin/env python3
"""
WORK_MEMORY.md 시간 압축.
- 7일 지난 [최근 3일] 항목 → [1~2주 전]으로 이동 (첫 줄만 유지)
- 14일 지난 [1~2주 전] 항목 → [1개월+]로 이동 (날짜별 한 줄로 병합)
규칙 기반. API 호출 없음.
"""

import re
from datetime import datetime, timedelta, timezone

WORK_MEMORY_PATH = "/root/docs/WORK_MEMORY.md"
COMPRESS_LOG_MARKER = "## [압축 기록]"
MAX_LOG_LINES = 20


def parse_sections(content):
    sections = {
        'recent': '',
        'weekly': '',
        'monthly': '',
        'compress_log': '',
        'header': '',
    }
    recent_start = content.find('## [최근 3일]')
    weekly_start = content.find('## [1~2주 전]')
    monthly_start = content.find('## [1개월+]')
    log_start = content.find(COMPRESS_LOG_MARKER)

    if recent_start == -1 or weekly_start == -1 or monthly_start == -1:
        return None

    sections['header'] = content[:recent_start]
    sections['recent'] = content[recent_start:weekly_start]
    sections['weekly'] = content[weekly_start:monthly_start]

    if log_start != -1:
        sections['monthly'] = content[monthly_start:log_start]
        sections['compress_log'] = content[log_start:]
    else:
        sections['monthly'] = content[monthly_start:]
        sections['compress_log'] = ''

    return sections


def compress_recent(recent_text, weekly_text):
    """7일 지난 항목을 recent에서 weekly로 이동. 압축 기록 반환."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    date_pattern = re.compile(r'### (\d{4}-\d{2}-\d{2})')

    keep_lines = []
    move_lines = []
    compress_log_entries = []  # (원래날짜, 원래줄수, 압축한줄) 튜플
    current_date = None
    current_block = []

    def flush_block(current_date, current_block, cutoff):
        if current_date < cutoff:
            block_line_count = len([l for l in current_block if l.strip()])
            first_item = ""
            for bl in current_block:
                if bl.startswith('- '):
                    first_item = bl[2:].split('.')[0].strip()
                    break
            if first_item:
                compressed = f"- {current_date.strftime('%Y-%m-%d')}: {first_item}"
                return 'move', compressed, block_line_count
            return 'skip', None, block_line_count
        else:
            return 'keep', None, 0

    for line in recent_text.split('\n'):
        match = date_pattern.match(line)
        if match:
            if current_date:
                action, compressed, line_count = flush_block(current_date, current_block, cutoff)
                if action == 'move':
                    move_lines.append(compressed)
                    compress_log_entries.append((
                        current_date.strftime('%Y-%m-%d'),
                        line_count,
                        compressed[len(f"- {current_date.strftime('%Y-%m-%d')}: "):]
                    ))
                elif action == 'keep':
                    keep_lines.extend(current_block)

            current_date_str = match.group(1)
            try:
                current_date = datetime.strptime(current_date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                current_date = None
            current_block = [line]
        else:
            current_block.append(line)

    # 마지막 블록
    if current_date:
        action, compressed, line_count = flush_block(current_date, current_block, cutoff)
        if action == 'move':
            move_lines.append(compressed)
            compress_log_entries.append((
                current_date.strftime('%Y-%m-%d'),
                line_count,
                compressed[len(f"- {current_date.strftime('%Y-%m-%d')}: "):]
            ))
        elif action == 'keep':
            keep_lines.extend(current_block)

    if move_lines:
        weekly_lines = weekly_text.rstrip().split('\n')
        header_line = weekly_lines[0] if weekly_lines else '## [1~2주 전]'
        rest = weekly_lines[1:] if len(weekly_lines) > 1 else []
        weekly_text = header_line + '\n\n' + '\n'.join(move_lines) + '\n' + '\n'.join(rest) + '\n'

    recent_header = '## [최근 3일]\n'
    recent_text = recent_header + '\n'.join(keep_lines) + '\n'
    return recent_text, weekly_text, compress_log_entries


def compress_weekly(weekly_text, monthly_text):
    """14일 지난 항목을 weekly에서 monthly로 이동."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=14)
    keep_lines = []
    move_lines = []

    for line in weekly_text.split('\n'):
        match = re.match(r'- (\d{4}-\d{2}-\d{2}): (.+)', line)
        if match:
            try:
                line_date = datetime.strptime(match.group(1), '%Y-%m-%d').replace(tzinfo=timezone.utc)
                if line_date < cutoff:
                    move_lines.append(line)
                else:
                    keep_lines.append(line)
            except ValueError:
                keep_lines.append(line)
        else:
            keep_lines.append(line)

    if move_lines:
        monthly_text = monthly_text.rstrip() + '\n' + '\n'.join(move_lines) + '\n'
    weekly_text = '\n'.join(keep_lines) + '\n'
    return weekly_text, monthly_text


def update_compress_log(compress_log_text, new_entries):
    """압축 기록 섹션 업데이트. 최근 20줄 유지."""
    if not new_entries:
        return compress_log_text

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # 기존 로그 줄 파싱
    if compress_log_text.strip():
        existing_lines = [
            l for l in compress_log_text.split('\n')
            if l.startswith('- ') and re.match(r'- \d{4}-\d{2}-\d{2}:', l)
        ]
    else:
        existing_lines = []

    # 새 항목 추가
    for orig_date, line_count, summary in new_entries:
        new_line = f"- {today}: '{orig_date} 상세 ({line_count}줄)' → '{summary}'"
        existing_lines.append(new_line)

    # 최근 20줄만 유지
    if len(existing_lines) > MAX_LOG_LINES:
        existing_lines = existing_lines[-MAX_LOG_LINES:]

    return COMPRESS_LOG_MARKER + '\n\n' + '\n'.join(existing_lines) + '\n'


def main():
    with open(WORK_MEMORY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = parse_sections(content)
    if not sections:
        print('구조 파싱 실패 — 건드리지 않음')
        return

    recent, weekly, log_entries = compress_recent(sections['recent'], sections['weekly'])
    weekly, monthly = compress_weekly(weekly, sections['monthly'])
    compress_log = update_compress_log(sections['compress_log'], log_entries)

    new_content = sections['header'] + recent + '\n' + weekly + '\n' + monthly
    if compress_log.strip():
        new_content = new_content.rstrip() + '\n\n' + compress_log

    with open(WORK_MEMORY_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

    compressed_count = len(log_entries)
    print(f"[{datetime.now().isoformat()}] 압축 완료 (이번 실행 압축 항목: {compressed_count}건)")


if __name__ == '__main__':
    main()
