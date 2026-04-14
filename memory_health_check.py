#!/usr/bin/env python3
"""
memory_health_check.py
기억 공유 시스템 장애 감지 + PAT 만료 사전 알림
- check_pat_expiry()  : GitHub API PAT 유효성 확인, D-7부터 매일 알림
- check_git_push()    : 빈 커밋 push 테스트, 실패 시 즉시 알림
- check_gmail_poller(): 최근 1시간 내 로그 갱신 여부 확인
텔레그램 발신: bibi-gateway(localhost:5114) 경유
"""

import os
import sys
import subprocess
import datetime
import requests
import argparse

DOCS_DIR  = '/root/docs'
GMAIL_LOG = '/root/docs/gmail_memory.log'
BIBI_URL  = 'http://localhost:5114/webhook/bibi-incoming'


# ── 공통 유틸 ────────────────────────────────────────────────────────────────

def send_alert(message: str) -> bool:
    """bibi-gateway(5114) 경유 텔레그램 알림 발송"""
    try:
        resp = requests.post(
            BIBI_URL,
            json={'message': f'시스템알림: [기억시스템]\n{message}'},
            timeout=10
        )
        ok = resp.status_code == 200
        print(f'[ALERT] {"발송완료" if ok else "발송실패"}: {message[:80]}')
        return ok
    except Exception as e:
        print(f'[ERROR] 알림 발송 실패: {e}', file=sys.stderr)
        return False


def get_pat_from_git_config() -> str:
    """git remote URL에서 PAT 추출"""
    try:
        r = subprocess.run(
            ['git', '-C', DOCS_DIR, 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, timeout=10
        )
        url = r.stdout.strip()
        # https://x-access-token:TOKEN@github.com/...
        if '@' in url and ':' in url:
            return url.split('@')[0].split(':')[-1]
    except Exception as e:
        print(f'[WARN] PAT 추출 실패: {e}')
    return None


# ── 3가지 헬스체크 ───────────────────────────────────────────────────────────

def check_pat_expiry() -> bool:
    """GitHub API로 PAT 만료일 확인. 만료 7일 전부터 매일 알림."""
    pat = get_pat_from_git_config()
    if not pat:
        send_alert('PAT 확인 실패\ngit remote URL에서 토큰을 읽을 수 없습니다.')
        return False

    try:
        resp = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {pat}'},
            timeout=15
        )
        if resp.status_code == 401:
            send_alert(
                '[RED] GitHub PAT 만료/무효!\n'
                '/root/docs git push 불가.\n'
                '즉시 PAT를 갱신하세요.'
            )
            return False

        expiry_str = resp.headers.get('github-authentication-token-expiration', '')
        if not expiry_str:
            print('[OK] PAT 유효 (만료일 정보 없음)')
            return True

        expiry_dt = datetime.datetime.strptime(
            expiry_str, '%Y-%m-%d %H:%M:%S UTC'
        ).replace(tzinfo=datetime.timezone.utc)
        days_left = (expiry_dt - datetime.datetime.now(datetime.timezone.utc)).days

        if days_left <= 0:
            send_alert(
                f'[RED] GitHub PAT 만료됨!\n'
                f'만료일: {expiry_str}\n'
                f'즉시 갱신하세요.'
            )
            return False
        elif days_left <= 7:
            send_alert(
                f'[WARNING] GitHub PAT D-{days_left} 만료 예정\n'
                f'만료일: {expiry_str}\n'
                f'미리 갱신하세요 (GitHub > Settings > Developer settings > PAT)'
            )
            return True  # 경고지만 아직 유효
        else:
            print(f'[OK] PAT 유효 (D-{days_left}, 만료: {expiry_str})')
            return True

    except Exception as e:
        send_alert(f'PAT 만료 확인 오류: {e}')
        return False


def check_git_push(fake_remote: str = None) -> bool:
    """
    빈 커밋으로 push 테스트.
    fake_remote: 테스트용 잘못된 remote URL (실패 유도)
    """
    original_url = None
    try:
        if fake_remote:
            r = subprocess.run(
                ['git', '-C', DOCS_DIR, 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, timeout=10
            )
            original_url = r.stdout.strip()
            subprocess.run(
                ['git', '-C', DOCS_DIR, 'remote', 'set-url', 'origin', fake_remote],
                capture_output=True, text=True, timeout=10
            )

        # 빈 커밋 생성
        subprocess.run(
            ['git', '-C', DOCS_DIR, 'commit', '--allow-empty',
             '-m', '[health-check] push connectivity test'],
            capture_output=True, text=True, timeout=10
        )
        # push 시도
        push = subprocess.run(
            ['git', '-C', DOCS_DIR, 'push'],
            capture_output=True, text=True, timeout=30
        )

    finally:
        # 테스트 커밋 항상 되돌리기
        subprocess.run(
            ['git', '-C', DOCS_DIR, 'reset', '--soft', 'HEAD~1'],
            capture_output=True, text=True, timeout=10
        )
        # fake_remote 사용했으면 원래 URL 복원
        if original_url:
            subprocess.run(
                ['git', '-C', DOCS_DIR, 'remote', 'set-url', 'origin', original_url],
                capture_output=True, text=True, timeout=10
            )

    if push.returncode == 0:
        print('[OK] git push 정상')
        return True
    else:
        err = (push.stderr or push.stdout).strip()[:300]
        send_alert(f'[RED] /root/docs git push 실패!\n오류: {err}')
        return False


def check_gmail_poller() -> bool:
    """Gmail 폴링 크론이 최근 1시간 내 실행됐는지 로그로 확인."""
    try:
        if not os.path.exists(GMAIL_LOG):
            send_alert(
                f'Gmail 폴러 로그 없음\n'
                f'경로: {GMAIL_LOG}\n'
                f'크론이 실행되지 않았거나 경로가 변경된 것 같습니다.'
            )
            return False

        mtime = os.path.getmtime(GMAIL_LOG)
        log_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
        elapsed_min = (
            datetime.datetime.now(datetime.timezone.utc) - log_dt
        ).total_seconds() / 60

        if elapsed_min > 60:
            send_alert(
                f'[WARNING] Gmail 폴러 미실행 감지!\n'
                f'마지막 실행: {int(elapsed_min)}분 전\n'
                f'({log_dt.strftime("%Y-%m-%d %H:%M")} UTC)\n'
                f'크론 확인: 15,45 * * * * gmail_memory_receiver.py'
            )
            return False
        else:
            print(f'[OK] Gmail 폴러 정상 ({int(elapsed_min)}분 전 실행)')
            return True

    except Exception as e:
        send_alert(f'Gmail 폴러 확인 오류: {e}')
        return False


# ── 진입점 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='기억 공유 시스템 헬스체크')
    parser.add_argument(
        '--test-push-fail', action='store_true',
        help='git push 실패 시뮬레이션 (잘못된 remote 사용)'
    )
    args = parser.parse_args()

    print(f'=== memory_health_check 시작: {datetime.datetime.now().isoformat()} ===')

    results = {}
    results['pat_expiry']   = check_pat_expiry()
    results['git_push']     = check_git_push(
        fake_remote='https://github.com/invalid/no-such-repo-xyz.git'
        if args.test_push_fail else None
    )
    results['gmail_poller'] = check_gmail_poller()

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
