#!/usr/bin/env python3
"""
memory_health_check.py — 기억 공유 시스템 헬스체크
1. Gmail OAuth 토큰 유효성
2. 마지막 수거 시각 (1시간 이내)
3. git push 상태 (unpushed 커밋 여부)
실패 시 bibi-gateway(5114) 경유 텔레그램 알림
"""

import os
import sys
import subprocess
import datetime
import requests

DOCS_DIR       = '/root/docs'
TOKEN_PATH     = '/root/.hermes/google_token_gmail.json'
LAST_RUN_PATH  = '/tmp/gmail_poller_last_run'
BIBI_URL       = 'http://localhost:5114/webhook'
GMAIL_SCOPES   = ['https://www.googleapis.com/auth/gmail.modify']


def send_alert(detail: str) -> bool:
    """bibi-gateway(5114) 경유 텔레그램 알림"""
    try:
        resp = requests.post(
            BIBI_URL,
            json={
                'source': 'health_check',
                'message': f'⚠️ 기억 공유 이상: {detail}'
            },
            timeout=10
        )
        ok = resp.status_code == 200
        print(f'[ALERT] {"발송완료" if ok else f"발송실패({resp.status_code})"}: {detail[:80]}')
        return ok
    except Exception as e:
        print(f'[ERROR] 알림 발송 실패: {e}', file=sys.stderr)
        return False


def check_gmail_oauth() -> bool:
    """Gmail OAuth 토큰 유효성 확인 + 만료 시 자동 갱신 시도"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        if not os.path.exists(TOKEN_PATH):
            send_alert(f'Gmail OAuth 토큰 파일 없음: {TOKEN_PATH}')
            return False

        creds = Credentials.from_authorized_user_file(TOKEN_PATH, GMAIL_SCOPES)

        if creds.valid:
            print('[OK] Gmail OAuth 토큰 유효')
            return True

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
            print('[OK] Gmail OAuth 토큰 자동 갱신 완료')
            return True

        send_alert('Gmail OAuth 토큰 만료 — 재인증 필요 (refresh_token 없음)')
        return False

    except Exception as e:
        send_alert(f'Gmail OAuth 토큰 확인 오류: {e}')
        return False


def check_last_run() -> bool:
    """마지막 수거 시각 확인 — 1시간 이상 경과 시 이상"""
    try:
        if not os.path.exists(LAST_RUN_PATH):
            send_alert('마지막 수거 기록 없음 (gmail_poller 미실행)')
            return False

        with open(LAST_RUN_PATH) as f:
            last_run_str = f.read().strip()

        last_run_dt = datetime.datetime.fromisoformat(last_run_str)
        elapsed_min = (datetime.datetime.now() - last_run_dt).total_seconds() / 60

        if elapsed_min > 60:
            send_alert(
                f'Gmail 폴러 {int(elapsed_min)}분간 미실행\n'
                f'마지막 실행: {last_run_str}'
            )
            return False

        print(f'[OK] 마지막 수거 {int(elapsed_min)}분 전 ({last_run_str})')
        return True

    except Exception as e:
        send_alert(f'마지막 수거 시각 확인 오류: {e}')
        return False


def check_git_status() -> bool:
    """unpushed 커밋 여부 확인"""
    try:
        result = subprocess.run(
            ['git', '-C', DOCS_DIR, 'status'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        if 'ahead' in output:
            lines = [l for l in output.splitlines() if 'ahead' in l]
            send_alert(f'unpushed 커밋 있음: {lines[0].strip() if lines else output[:100]}')
            return False

        print('[OK] git 동기화 정상 (unpushed 커밋 없음)')
        return True

    except Exception as e:
        send_alert(f'git status 확인 오류: {e}')
        return False


def main():
    print(f'=== memory_health_check 시작: {datetime.datetime.now().isoformat()} ===')

    results = {
        'gmail_oauth' : check_gmail_oauth(),
        'last_run'    : check_last_run(),
        'git_status'  : check_git_status(),
    }

    failed = [k for k, v in results.items() if not v]
    print(f'=== 결과: {results} ===')

    if failed:
        print(f'[FAIL] 실패 항목: {failed}')
        sys.exit(1)
    else:
        print('[ALL OK] 모든 헬스체크 통과')
        sys.exit(0)


if __name__ == '__main__':
    main()
