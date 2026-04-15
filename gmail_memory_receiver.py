#!/usr/bin/env python3
"""
Gmail 드래프트에서 [VIVI-MEMORY] 제목 항목을 읽어서 WORK_MEMORY.md에 병합.
읽은 드래프트는 삭제.
"""

CREDENTIALS_PATH = "/root/.hermes/google_client_secret.json"
TOKEN_PATH = "/root/.hermes/google_token_gmail.json"
WORK_MEMORY_PATH = "/root/docs/WORK_MEMORY.md"
SUBJECT_PREFIX = "WORK_MEMORY|"
LAST_RUN_PATH = "/tmp/gmail_poller_last_run"

import os
import base64
import subprocess
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Gmail 토큰 없거나 만료됨. 대표님 재인증 필요.")
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def extract_body(payload):
    """payload에서 text/plain 본문 추출"""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    data = payload.get('body', {}).get('data', '')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    return ''

def get_subject(payload):
    """payload headers에서 Subject 추출"""
    for header in payload.get('headers', []):
        if header.get('name', '').lower() == 'subject':
            return header.get('value', '')
    return ''

def fetch_memory_drafts(service):
    """드래프트 중 WORK_MEMORY| 제목인 것만 가져오고 삭제"""
    results = service.users().drafts().list(userId='me', maxResults=50).execute()
    drafts = results.get('drafts', [])

    entries = []
    for draft_meta in drafts:
        draft = service.users().drafts().get(
            userId='me', id=draft_meta['id'], format='full'
        ).execute()

        payload = draft.get('message', {}).get('payload', {})
        subject = get_subject(payload)

        if SUBJECT_PREFIX not in subject:
            continue

        body = extract_body(payload)
        if body.strip():
            entries.append(body.strip())

        # 드래프트 삭제
        service.users().drafts().delete(userId='me', id=draft_meta['id']).execute()

    return entries

def merge_to_work_memory(entries):
    """새 항목들을 WORK_MEMORY.md의 [최근 3일] 섹션에 병합"""
    if not entries:
        return

    with open(WORK_MEMORY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    today_header = f"### {today}"

    if today_header in content:
        insert_point = content.find(today_header) + len(today_header)
        next_header = content.find('\n### ', insert_point + 1)
        if next_header == -1:
            next_header = content.find('\n## [', insert_point + 1)

        new_content = "\n" + "\n".join(entries) + "\n"
        if next_header != -1:
            content = content[:next_header] + new_content + content[next_header:]
        else:
            content = content[:insert_point] + new_content + content[insert_point:]
    else:
        marker = "## [최근 3일]"
        insert_point = content.find(marker)
        if insert_point != -1:
            insert_point = content.find('\n', insert_point) + 1
            new_section = f"\n{today_header}\n\n" + "\n".join(entries) + "\n"
            content = content[:insert_point] + new_section + content[insert_point:]

    with open(WORK_MEMORY_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def try_compress():
    """Track A의 compress_old_entries() 또는 compress_memory.main() 호출 시도"""
    try:
        import sys
        sys.path.insert(0, '/root/docs')
        import compress_memory as cm
        if hasattr(cm, 'compress_old_entries'):
            cm.compress_old_entries()
        else:
            cm.main()
    except Exception as e:
        print(f"[compress skip] {e}")

def git_push():
    """WORK_MEMORY.md 변경 사항을 GitHub에 자동 push"""
    try:
        repo = '/root/docs'
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        subprocess.run(['git', 'add', 'WORK_MEMORY.md'], cwd=repo, check=True)
        result = subprocess.run(
            ['git', 'commit', '-m', f'auto: sync WORK_MEMORY {now_str}'],
            cwd=repo, capture_output=True, text=True
        )
        if 'nothing to commit' in result.stdout + result.stderr:
            print('[git] 변경 없음, push 생략')
            return
        try:
            subprocess.run(['git', 'pull', '--rebase'], cwd=repo, capture_output=True, text=True)
        except Exception as pull_e:
            print(f'[git] pull 실패 (push 계속 시도): {pull_e}')
        subprocess.run(['git', 'push'], cwd=repo, check=True)
        print(f'[git] push 완료')
    except Exception as e:
        print(f'[git push skip] {e}')

def main():
    try:
        service = get_gmail_service()
        entries = fetch_memory_drafts(service)
        now_str = datetime.now().isoformat()
        if entries:
            merge_to_work_memory(entries)
            print(f"[{now_str}] {len(entries)}건 병합 완료")
            try_compress()
            git_push()
        else:
            print(f"[{now_str}] 새 드래프트 없음")
        # 마지막 실행 시각 기록 (Track B health check 용)
        with open(LAST_RUN_PATH, 'w') as f:
            f.write(now_str + '\n')
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] 에러: {e}")

if __name__ == '__main__':
    main()
