# /root/docs 작업 규칙

## 작업 완료 시 필수 절차

작업이 완료되면 반드시 아래 스크립트로 WORK_MEMORY를 갱신하고 GitHub에 push한다.

```bash
cd /root/docs
python3 update_work_memory.py --category "카테고리" --content "내용"
```

카테고리 종류: `결정`, `완료`, `이슈`, `메모`

push 실패(non-fast-forward) 시:
```bash
git pull --rebase origin main && git push origin main
```

## GitHub 토큰

Remote URL에 토큰이 포함되어 있음. 토큰 갱신 시:
```bash
git remote set-url origin https://x-access-token:[NEW_TOKEN]@github.com/stayz-hue/vivi-memory.git
```

## 파일 구조

- WORK_MEMORY.md — 비비의 작업 기억 (Claude.ai와 공유)
- compress_memory.py — 오래된 항목 압축 (매일 UTC 15:00 자동 실행)
- gmail_memory_receiver.py — Gmail 드래프트 폴링 (*/5 분마다 자동 실행)
- update_work_memory.py — WORK_MEMORY 갱신 + git push 헬퍼
